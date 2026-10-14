# -*- coding: utf-8 -*-
"""
OFERTAS DEL CATÁLOGO SOLO EL DÍA QUE LES TOCA (pedido del dueño 2026-10-14: "que se
activen solo el día que corresponde").

Cada oferta del catálogo se reconoce por su título ("Oferta del lunes: ..."). Su día se
deja VISIBLE (visibility=published, availability=in stock) y los demás días, y en
festivos, OCULTA (hidden + out of stock). El resto de los productos no se toca.

Lo usan DOS lados, con la misma regla:
  * catalogo.py al escribir la lista (en el notebook);
  * el robot del repositorio PÚBLICO de fotos (GitHub Actions, cada hora), para que el
    cambio de día ocurra aunque el notebook esté apagado. Por eso este archivo solo usa
    la librería estándar y se copia tal cual al repo público junto con feriados.txt.

Uso suelto:  python ajustar_ofertas.py catalogo.csv [feriados.txt]
"""
import csv
import datetime as dt
import io
import os
import re
import sys

DIAS = {"lunes": 0, "martes": 1, "miércoles": 2, "miercoles": 2, "jueves": 3,
        "viernes": 4, "sábado": 5, "sabado": 5, "domingo": 6}
_OFERTA = re.compile(r"^Oferta del (\w+):", re.IGNORECASE)


def hoy_chile():
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo("America/Santiago")).date()
    except Exception:                       # Windows sin tzdata: el reloj del equipo ya está en Chile
        return dt.date.today()


def leer_feriados(ruta):
    fechas = set()
    try:
        with open(ruta, encoding="utf-8-sig") as f:
            for linea in f:
                linea = linea.split("#")[0].strip()
                if re.match(r"^\d{4}-\d{2}-\d{2}$", linea):
                    fechas.add(dt.date.fromisoformat(linea))
    except OSError:
        pass
    return fechas


def dia_de(titulo):
    m = _OFERTA.match(titulo or "")
    return DIAS.get(m.group(1).lower()) if m else None


def ajustar(filas, hoy, feriados):
    """Pone visibility/availability a cada fila (dicts del CSV). Devuelve las filas."""
    for fila in filas:
        dia = dia_de(fila.get("title", ""))
        if dia is None:
            fila["visibility"] = "published"
            continue
        toca = hoy.weekday() == dia and hoy not in feriados
        fila["visibility"] = "published" if toca else "hidden"
        fila["availability"] = "in stock" if toca else "out of stock"
    return filas


def ajustar_archivo(ruta_csv, ruta_feriados, hoy=None):
    """Reescribe el CSV solo si cambió algo. Devuelve True si lo cambió."""
    with open(ruta_csv, encoding="utf-8", newline="") as f:
        original = f.read()
    lector = csv.DictReader(io.StringIO(original))
    columnas = list(lector.fieldnames or [])
    if "visibility" not in columnas:
        columnas.append("visibility")
    filas = ajustar(list(lector), hoy or hoy_chile(), leer_feriados(ruta_feriados))
    salida = io.StringIO()
    w = csv.DictWriter(salida, fieldnames=columnas, lineterminator="\n")
    w.writeheader()
    w.writerows(filas)
    if salida.getvalue() == original:
        return False
    with open(ruta_csv, "w", encoding="utf-8", newline="") as f:
        f.write(salida.getvalue())
    return True


if __name__ == "__main__":
    csv_ = sys.argv[1] if len(sys.argv) > 1 else "catalogo.csv"
    fer = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(csv_)), "feriados.txt")
    print("cambió" if ajustar_archivo(csv_, fer) else "sin cambios")
