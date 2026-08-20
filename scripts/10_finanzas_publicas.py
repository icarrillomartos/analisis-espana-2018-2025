# -*- coding: utf-8 -*-
"""Finanzas públicas: ingresos, gasto por función, protección social, déficit y deuda.
Fuente: Eurostat (cuentas de las administraciones públicas, SEC 2010), que publica los
mismos datos que la IGAE notifica a la UE y permite además comparar con la UE-27.
Salidas: data_external/eurostat_gov_*.csv y filas añadidas a data_external/metadata.csv
"""
import os, json, csv, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data_external")
BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
HOY = "2026-08-20"
PAISES = ["EU27_2020", "ES", "DE", "FR", "IT", "PT"]
SUBSOC = ["GF1001", "GF1002", "GF1003", "GF1004", "GF1005", "GF1006", "GF1007", "GF1008", "GF1009"]
ANYOS = range(2018, 2025)

COFOG = {"GF01": "Servicios públicos generales", "GF02": "Defensa", "GF03": "Orden público y seguridad",
         "GF04": "Asuntos económicos", "GF05": "Protección del medio ambiente",
         "GF06": "Vivienda y servicios comunitarios", "GF07": "Sanidad",
         "GF08": "Ocio, cultura y religión", "GF09": "Educación", "GF10": "Protección social",
         "TOTAL": "Gasto público total"}

CONSULTAS = {
    "gov_main_meur": dict(ds="gov_10a_main",
        params={"sector": "S13", "unit": "MIO_EUR"},
        multi={"na_item": ["TR", "TE", "B9", "D2REC", "D5REC", "D61REC", "D62PAY", "D3PAY"]},
        indicador="Ingresos, gastos y saldo de las administraciones públicas (millones de euros)",
        nota="SEC 2010. TR = ingresos totales, TE = gastos totales, B9 = capacidad/necesidad de financiación, "
             "D2REC = impuestos sobre producción e importaciones, D5REC = impuestos corrientes sobre renta y "
             "patrimonio, D61REC = cotizaciones sociales, D62PAY = prestaciones sociales distintas de "
             "transferencias en especie, D3PAY = subvenciones."),
    "gov_main_pcgdp": dict(ds="gov_10a_main",
        params={"sector": "S13", "unit": "PC_GDP"},
        multi={"na_item": ["TR", "TE", "B9", "D2REC", "D5REC", "D61REC", "D62PAY"]},
        indicador="Ingresos, gastos y saldo de las administraciones públicas (% del PIB)",
        nota="Mismo concepto que el anterior, expresado sobre el PIB. Es la medida habitual de presión fiscal "
             "y de peso del gasto público."),
    "gov_cofog_meur": dict(ds="gov_10a_exp",
        params={"sector": "S13", "unit": "MIO_EUR", "na_item": "TE"},
        multi={"cofog99": list(COFOG.keys())},
        indicador="Gasto público por función COFOG (millones de euros)",
        nota="Clasificación funcional del gasto público. 'Protección social' incluye pensiones, desempleo, "
             "familia, exclusión social y vivienda social: no es solo 'ayudas'."),
    "gov_cofog_pcgdp": dict(ds="gov_10a_exp",
        params={"sector": "S13", "unit": "PC_GDP", "na_item": "TE"},
        multi={"cofog99": list(COFOG.keys())},
        indicador="Gasto público por función COFOG (% del PIB)",
        nota="Permite ver si una función gana o pierde peso relativo con independencia de la inflación."),
    "gov_cofog_social_meur": dict(ds="gov_10a_exp",
        params={"sector": "S13", "unit": "MIO_EUR", "na_item": "TE"},
        multi={"cofog99": ["GF1001", "GF1002", "GF1003", "GF1004", "GF1005", "GF1006",
                           "GF1007", "GF1008", "GF1009"]},
        indicador="Gasto en protección social por subfunción COFOG (millones de euros)",
        nota="Desglose de la función 10. GF1002 son las pensiones de jubilación y GF1007 la exclusión "
             "social, que es donde se registra el Ingreso Mínimo Vital junto a otras prestaciones: esa "
             "cifra NO es el IMV en solitario."),
    "gov_deuda": dict(ds="gov_10dd_edpt1",
        params={"sector": "S13", "na_item": "GD"},
        multi={"unit": ["PC_GDP", "MIO_EUR"]},
        indicador="Deuda pública bruta consolidada (% del PIB y millones de euros)",
        nota="Deuda según el Protocolo de Déficit Excesivo."),
}


def fetch(ds, params, multi, anyos):
    q = ["format=JSON", "lang=EN"] + [f"{k}={v}" for k, v in params.items()]
    for k, vals in multi.items():
        q += [f"{k}={v}" for v in vals]
    q += [f"geo={g}" for g in PAISES] + [f"time={a}" for a in anyos]
    url = f"{BASE}/{ds}?" + "&".join(q)
    with urllib.request.urlopen(url, timeout=90) as r:
        return json.loads(r.read().decode("utf-8")), url


def tidy(d):
    ids = d["id"]; size = d["size"]
    cats = [[k for k, _ in sorted(d["dimension"][dim]["category"]["index"].items(), key=lambda kv: kv[1])]
            for dim in ids]
    estado = d.get("status", {})
    filas = []
    for key, val in d["value"].items():
        pos = int(key); coords = []
        for i in range(len(size) - 1, -1, -1):
            coords.insert(0, pos % size[i]); pos //= size[i]
        r = {dim: cats[i][coords[i]] for i, dim in enumerate(ids)}
        r["valor"] = val; r["estado"] = estado.get(key, "")
        r["anyo"] = int(r.pop("time"))
        filas.append(r)
    return filas


meta = []
for nombre, cfg in CONSULTAS.items():
    d, url = fetch(cfg["ds"], cfg["params"], cfg["multi"], ANYOS)
    filas = tidy(d)
    cols = [c for c in filas[0].keys()]
    path = os.path.join(OUT, f"eurostat_{nombre}.csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(filas)
    meta.append({"fichero": f"eurostat_{nombre}.csv", "indicador": cfg["indicador"],
                 "organismo": "Eurostat (cuentas de las AAPP, SEC 2010)", "dataset": cfg["ds"],
                 "url_exacta": url, "cobertura": "2018-2024", "geografia": " ".join(PAISES),
                 "fecha_descarga": HOY, "notas": cfg["nota"]})
    print(f"{nombre:18s} {len(filas):4d} obs")

mp = os.path.join(OUT, "metadata.csv")
prev = list(csv.DictReader(open(mp, encoding="utf-8"))) if os.path.exists(mp) else []
prev = [p for p in prev if p["fichero"] not in {m["fichero"] for m in meta}]
with open(mp, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(meta[0].keys())); w.writeheader()
    w.writerows(prev + meta)
json.dump(COFOG, open(os.path.join(OUT, "cofog_etiquetas.json"), "w"), ensure_ascii=False, indent=1)
print("metadata.csv actualizado:", len(prev) + len(meta), "filas")
