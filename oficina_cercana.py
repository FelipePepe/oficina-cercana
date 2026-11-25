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
SALIDA = "asignacion.csv"


def normaliza_cp(cp):
    """'8001' -> '08001', ' 28013 ' -> '28013'."""
    cp = str(cp).strip().split(".")[0]  # por si Excel lo dejó como 8001.0
    return cp.zfill(5) if cp.isdigit() else None


def descarga_geonames():
    print("Descargando coordenadas de GeoNames...")
    with urllib.request.urlopen(GEONAMES_URL) as r:
        with zipfile.ZipFile(io.BytesIO(r.read())) as z:
            z.extract(GEONAMES_TXT)


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
    """Lee CSV con ; o , (lo detecta solo) y salta la cabecera si la hay."""
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
    if filas and not normaliza_cp(filas[0][0]):
        filas = filas[1:]  # cabecera
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
            nombre, cp_of, pos = min(oficinas, key=lambda o: haversine(coords[cp], o[2]))
            w.writerow([cp, nombre, cp_of, f"{haversine(coords[cp], pos):.1f}"])

    print(f"Hecho: {SALIDA}")
    if sin_coords:
        print(f"{sin_coords} CPs sin coordenadas (marcados en el fichero).")


if __name__ == "__main__":
    main()
