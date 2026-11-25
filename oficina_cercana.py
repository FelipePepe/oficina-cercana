#!/usr/bin/env python3
"""
Asigna a cada código postal la oficina más cercana (en línea recta).

Uso:
    python oficina_cercana.py cps.csv oficinas.csv

  cps.csv       -> primera columna: código postal
  oficinas.csv  -> primera columna: código postal, segunda: oficina

Las coordenadas salen de GeoNames (ES.zip). Si no está ES.txt en la
carpeta, el script lo descarga solo la primera vez.

Resultado: asignacion.csv
"""
import csv
import io
import math
import os
import sys
import urllib.request
import zipfile

GEONAMES_URL = "https://download.geonames.org/export/zip/ES.zip"
GEONAMES_TXT = "ES.txt"
GEONAMES_TIMEOUT = 30  # segundos
GEONAMES_MIN_LINEAS = 1000
GEONAMES_MIN_COLUMNAS = 12
SALIDA = "asignacion.csv"


def normaliza_cp(cp):
    """'8001' -> '08001', ' 28013 ' -> '28013'."""
    cp = str(cp).strip().split(".")[0]  # por si Excel lo dejó como 8001.0
    return cp.zfill(5) if cp.isdigit() else None


def descarga_geonames():
    """Descarga ES.txt de GeoNames; si algo falla, no deja ningún fichero a medias."""
    print("Descargando coordenadas de GeoNames...")
    parcial = GEONAMES_TXT + ".part"
    try:
        with urllib.request.urlopen(GEONAMES_URL, timeout=GEONAMES_TIMEOUT) as r:
            datos = r.read()
        with zipfile.ZipFile(io.BytesIO(datos)) as z:
            texto = z.read(GEONAMES_TXT).decode("utf-8")
    except (OSError, zipfile.BadZipFile) as e:  # URLError y los timeouts son OSError
        sys.exit(f"No se pudo descargar GeoNames ({e}). Revisa la conexión o copia ES.txt a mano.")
    except KeyError:
        sys.exit(f"La descarga de GeoNames no contiene {GEONAMES_TXT}. No se guarda nada.")
    except UnicodeDecodeError:
        sys.exit("La descarga de GeoNames no es texto UTF-8 válido. No se guarda nada.")
    lineas = texto.splitlines()
    if len(lineas) < GEONAMES_MIN_LINEAS or any(
            len(l.split("\t")) < GEONAMES_MIN_COLUMNAS for l in lineas[:20]):
        sys.exit("La descarga de GeoNames no tiene el formato esperado. No se guarda nada.")
    try:
        with open(parcial, "w", encoding="utf-8", newline="") as f:
            f.write(texto)
        os.replace(parcial, GEONAMES_TXT)
    except OSError as e:
        if os.path.exists(parcial):
            os.remove(parcial)
        sys.exit(f"No se pudo guardar {GEONAMES_TXT} ({e}).")


def carga_coordenadas():
    """Devuelve {cp: (lat, lon)}; si un CP sale varias veces, hace la media."""
    if not os.path.exists(GEONAMES_TXT):
        descarga_geonames()
    acum = {}
    with open(GEONAMES_TXT, encoding="utf-8") as f:
        for fila in csv.reader(f, delimiter="\t"):
            cp = normaliza_cp(fila[1])
            if not cp:
                continue
            lat, lon = float(fila[9]), float(fila[10])
            s = acum.setdefault(cp, [0.0, 0.0, 0])
            s[0] += lat
            s[1] += lon
            s[2] += 1
    return {cp: (s[0] / s[2], s[1] / s[2]) for cp, s in acum.items()}


def lee_csv(ruta):
    """Lee CSV con ; o , (lo detecta solo).

    La primera fila se salta solo si parece una cabecera: su primera celda no
    tiene ningún dígito. Una primera fila con dígitos (un CP inválido como
    ABC12) es un dato y sigue el camino normal, así que nunca se pierde en silencio.
    """
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        muestra = f.read(4096)
        f.seek(0)
        try:
            dialecto = csv.Sniffer().sniff(muestra, delimiters=";,\t")
        except csv.Error:
            # El Sniffer falla con filas de distinto ancho: usa el separador más frecuente.
            class dialecto(csv.excel):
                delimiter = max(";,\t", key=muestra.count)
        filas = [fila for fila in csv.reader(f, dialecto) if fila]
    if filas and not any(c.isdigit() for c in filas[0][0]):
        filas = filas[1:]  # cabecera: una primera celda sin ningún dígito ("cp")
    return filas


def haversine(a, b):
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    h = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 2 * 6371 * math.asin(math.sqrt(h))


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    coords = carga_coordenadas()

    oficinas = []
    for fila in lee_csv(sys.argv[2]):
        if len(fila) < 2 or not fila[1].strip():
            print(f"Aviso: fila de oficinas sin nombre, se ignora ({fila[0]})")
            continue
        cp = normaliza_cp(fila[0])
        if cp in coords:
            oficinas.append((fila[1].strip(), cp, coords[cp]))
        else:
            print(f"Aviso: la oficina {fila[1:2]} tiene un CP sin coordenadas ({fila[0]})")
    if not oficinas:
        sys.exit("No hay ninguna oficina con coordenadas. Revisa el fichero.")

    sin_coords = 0
    with open(SALIDA, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["codigo_postal", "oficina", "cp_oficina", "distancia_km"])
        for fila in lee_csv(sys.argv[1]):
            cp = normaliza_cp(fila[0])
            if cp not in coords:
                w.writerow([fila[0].strip(), "", "", "SIN COORDENADAS"])
                sin_coords += 1
                continue
            # Empate exacto: gana el menor CP de oficina y luego el nombre, nunca el orden del fichero.
            dist, cp_of, nombre = min((haversine(coords[cp], pos), cp_of, nombre)
                                      for nombre, cp_of, pos in oficinas)
            w.writerow([cp, nombre, cp_of, f"{dist:.1f}"])

    print(f"Hecho: {SALIDA}")
    if sin_coords:
        print(f"{sin_coords} CPs sin coordenadas (marcados en el fichero).")


if __name__ == "__main__":
    main()
