"""Utilidades comunes para leer los JSON de la API Tempus del INE y los CSV del MIR.

No modifica nada en data_raw/. Todo lo que produce va a data_processed/.
"""
import json, os
import pandas as pd

RAW = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data_raw")

def load_tempus(path):
    """Devuelve un DataFrame tidy desde un JSON Tempus (lista de series con MetaData+Data)."""
    with open(path, encoding="utf-8") as fh:
        series = json.load(fh)
    rows = []
    for s in series:
        dims = {m["T3_Variable"]: m["Nombre"] for m in s.get("MetaData", [])}
        codes = {m["T3_Variable"] + "__cod": m.get("Codigo") for m in s.get("MetaData", [])}
        base = {"serie_cod": s.get("COD"), "serie_nombre": s.get("Nombre"),
                "unidad": s.get("T3_Unidad"), "escala": s.get("T3_Escala")}
        base.update(dims); base.update(codes)
        for obs in s.get("Data", []):
            r = dict(base)
            r["anyo"] = obs.get("Anyo"); r["periodo"] = obs.get("T3_Periodo")
            r["fecha"] = obs.get("Fecha"); r["tipo_dato"] = obs.get("T3_TipoDato")
            r["valor"] = obs.get("Valor")
            rows.append(r)
    return pd.DataFrame(rows)

def dims_of(path, n=1):
    with open(path, encoding="utf-8") as fh:
        series = json.load(fh)
    out = {}
    for s in series:
        for m in s.get("MetaData", []):
            out.setdefault(m["T3_Variable"], set()).add(m["Nombre"])
    years = sorted({o["Anyo"] for s in series for o in s.get("Data", [])})
    periods = sorted({o["T3_Periodo"] for s in series for o in s.get("Data", [])})
    return {"n_series": len(series), "years": years, "periods": periods,
            "dims": {k: (len(v), sorted(v)[:12]) for k, v in out.items()}}

def load_mir(path):
    """CSV del Portal de Criminalidad: separador ';', codificación ISO-8859-15 habitual."""
    for enc in ("utf-8", "iso-8859-15", "cp1252"):
        try:
            return pd.read_csv(path, sep=";", encoding=enc, dtype=str)
        except UnicodeDecodeError:
            continue
    raise RuntimeError("codificación no reconocida: " + path)
