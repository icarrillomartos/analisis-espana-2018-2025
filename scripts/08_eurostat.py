# -*- coding: utf-8 -*-
"""Descarga de contexto europeo desde Eurostat (organismo oficial de la UE).

Necesario porque el repositorio original solo contiene INE y Ministerio del Interior,
y esas fuentes no permiten saber si el crecimiento español es alto o bajo comparado
con otros países. Se aplican las mismas reglas que exigió Codex para añadir datos:
organismo oficial, URL directa, fecha de descarga y explicación metodológica.

Salidas: data_external/eurostat_*.csv y data_external/metadata.csv
"""
import os, json, csv, urllib.request, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data_external")
os.makedirs(OUT, exist_ok=True)
BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
HOY = "2026-08-20"

PAISES = ["EU27_2020", "ES", "DE", "FR", "IT", "PT", "NL", "PL", "EL", "IE", "BE", "AT", "SE"]

CONSULTAS = {
    "hicp": dict(
        ds="prc_hicp_aind",
        params={"unit": "INX_A_AVG", "coicop": "CP00"},
        anyos=range(2018, 2026),
        indicador="IPC armonizado, índice medio anual (base 2015 = 100)",
        nota="Índice armonizado europeo. No es idéntico al IPC nacional del INE, pero es el único "
             "comparable entre países. Se usa solo para deflactar y comparar, nunca mezclado con el IPC del INE."),
    "pib_pc_real": dict(
        ds="nama_10_pc",
        params={"unit": "CLV10_EUR_HAB", "na_item": "B1GQ"},
        anyos=range(2018, 2025),
        indicador="PIB per cápita, volumen encadenado (euros de 2010) por habitante",
        nota="Medida real. Último año disponible 2024, con estimaciones provisionales en algunos países."),
    "salario_neto": dict(
        ds="earn_nt_net",
        params={"currency": "EUR", "estruct": "NET", "ecase": "P1_NCH_AW100"},
        anyos=range(2018, 2025),
        indicador="Ganancia neta anual de una persona soltera sin hijos con el 100 % del salario medio (euros)",
        nota="Definición armonizada de Eurostat. Es salario NETO, después de impuestos y cotizaciones, "
             "de un caso-tipo; no es el salario medio efectivo de cada país. Eurostat marca ruptura de "
             "serie ('b') en 2024 para varios países, España incluida."),
    "aic_pps": dict(
        ds="prc_ppp_ind",
        params={"na_item": "VI_PPS_EU27_2020_HAB", "ppp_cat": "A01"},
        anyos=range(2018, 2025),
        indicador="Consumo individual efectivo per cápita en paridad de poder adquisitivo (EU27 = 100)",
        nota="Indicador que la propia Eurostat recomienda para comparar nivel de vida material entre "
             "países, porque corrige diferencias de precios. Es un índice relativo: si España baja, "
             "puede ser porque empeora o porque los demás mejoran más deprisa."),
}


def fetch(ds, params, anyos):
    q = ["format=JSON", "lang=EN"] + [f"{k}={v}" for k, v in params.items()]
    q += [f"geo={g}" for g in PAISES] + [f"time={a}" for a in anyos]
    url = f"{BASE}/{ds}?" + "&".join(q)
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode("utf-8")), url


def tidy(d):
    """Convierte el JSON-stat de Eurostat en filas (geo, anyo, valor, estado)."""
    ids = d["id"]; size = d["size"]
    cats = []
    for dim in ids:
        c = d["dimension"][dim]["category"]["index"]
        cats.append([k for k, _ in sorted(c.items(), key=lambda kv: kv[1])])
    estado = d.get("status", {})
    filas = []
    for pos, val in d["value"].items():
        pos = int(pos); coords = []
        for i in range(len(size) - 1, -1, -1):
            coords.insert(0, pos % size[i]); pos //= size[i]
        r = {dim: cats[i][coords[i]] for i, dim in enumerate(ids)}
        filas.append({"geo": r["geo"], "anyo": int(r["time"]), "valor": val,
                      "estado": estado.get(str(int(list(d["value"].keys())[0])) if False else "", "")})
    # estado por posición original
    for f, k in zip(filas, d["value"].keys()):
        f["estado"] = estado.get(k, "")
    return filas


meta = []
for nombre, cfg in CONSULTAS.items():
    d, url = fetch(cfg["ds"], cfg["params"], cfg["anyos"])
    filas = tidy(d)
    path = os.path.join(OUT, f"eurostat_{nombre}.csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["geo", "anyo", "valor", "estado"])
        w.writeheader(); w.writerows(sorted(filas, key=lambda r: (r["geo"], r["anyo"])))
    meta.append({"fichero": f"eurostat_{nombre}.csv", "indicador": cfg["indicador"],
                 "organismo": "Eurostat (Oficina Estadística de la Unión Europea)",
                 "dataset": cfg["ds"], "url_exacta": url,
                 "cobertura": f"{min(cfg['anyos'])}-{max(cfg['anyos'])}",
                 "geografia": " ".join(PAISES), "fecha_descarga": HOY, "notas": cfg["nota"]})
    print(f"{nombre:14s} {len(filas):4d} obs · {d['label'][:60]}")

with open(os.path.join(OUT, "metadata.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(meta[0].keys()))
    w.writeheader(); w.writerows(meta)
print("metadata.csv escrito con", len(meta), "filas")
