#!/usr/bin/env python3
"""
Asigna a cada código postal la oficina más cercana (en línea recta).

Uso:
    python oficina_cercana.py cps.csv oficinas.csv [--precision] [--max-km N]

  cps.csv       -> primera columna: código postal
  oficinas.csv  -> primera columna: código postal, segunda: oficina

Las coordenadas salen de GeoNames (ES.zip). Si no está ES.txt en la
carpeta, el script lo descarga solo la primera vez.

Con --precision añade dos columnas: localidades (filas de GeoNames de ese CP)
y dispersion_km (mayor distancia de una localidad al centroide usado).

Con --max-km N añade una última columna lejos: SI si la distancia exacta supera
N km, NO si no. Avisa de asignaciones dudosas; la oficina asignada no cambia.

Resultado: asignacion.csv
"""
import argparse
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
    """Devuelve (coords, precision).

    coords[cp] = (lat, lon): si un CP sale varias veces, hace la media.
    precision[cp] = (n, dispersion_km): localidades del CP en GeoNames y la
    mayor distancia de cualquiera de ellas al centroide medio.
    """
    if not os.path.exists(GEONAMES_TXT):
        descarga_geonames()
    puntos = {}
    with open(GEONAMES_TXT, encoding="utf-8") as f:
        for fila in csv.reader(f, delimiter="\t"):
            cp = normaliza_cp(fila[1])
            if not cp:
                continue
            puntos.setdefault(cp, []).append((float(fila[9]), float(fila[10])))
    coords, precision = {}, {}
    for cp, ps in puntos.items():
        centro = (sum(p[0] for p in ps) / len(ps), sum(p[1] for p in ps) / len(ps))
        coords[cp] = centro
        precision[cp] = (len(ps), max(haversine(p, centro) for p in ps))
    return coords, precision


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


def km_positivo(texto):
    try:
        valor = float(texto)
    except ValueError:
        raise argparse.ArgumentTypeError(f"no es un número: {texto!r}")
    if not valor > 0:  # también rechaza NaN
        raise argparse.ArgumentTypeError(f"debe ser mayor que 0: {texto!r}")
    return valor


def lee_argumentos():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cps", help="CSV con los códigos postales a asignar")
    p.add_argument("oficinas", help="CSV con CP y nombre de cada oficina")
    p.add_argument("--precision", action="store_true",
                   help="añade localidades y dispersion_km de cada CP")
    p.add_argument("--max-km", type=km_positivo, metavar="N",
                   help="añade la columna lejos: SI si la distancia supera N km")
    return p.parse_args()


def main():
    args = lee_argumentos()
    coords, precision = carga_coordenadas()

    oficinas = []
    for fila in lee_csv(args.oficinas):
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
        cabecera = ["codigo_postal", "oficina", "cp_oficina", "distancia_km"]
        if args.precision:
            cabecera += ["localidades", "dispersion_km"]
        if args.max_km is not None:
            cabecera.append("lejos")
        w.writerow(cabecera)
        for fila in lee_csv(args.cps):
            cp = normaliza_cp(fila[0])
            if cp not in coords:
                vacias = (2 if args.precision else 0) + (args.max_km is not None)
                w.writerow([fila[0].strip(), "", "", "SIN COORDENADAS"] + [""] * vacias)
                sin_coords += 1
                continue
            # Empate exacto: gana el menor CP de oficina y luego el nombre, nunca el orden del fichero.
            dist, cp_of, nombre = min((haversine(coords[cp], pos), cp_of, nombre)
                                      for nombre, cp_of, pos in oficinas)
            extra = [precision[cp][0], f"{precision[cp][1]:.1f}"] if args.precision else []
            if args.max_km is not None:
                extra.append("SI" if dist > args.max_km else "NO")
            w.writerow([cp, nombre, cp_of, f"{dist:.1f}"] + extra)

    print(f"Hecho: {SALIDA}")
    if sin_coords:
        print(f"{sin_coords} CPs sin coordenadas (marcados en el fichero).")


if __name__ == "__main__":
    main()
