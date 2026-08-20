# -*- coding: utf-8 -*-
"""Desgloses por origen para las respuestas 1 y 2, y comparativa europea para la 3.

Salida: outputs/desgloses.json
"""
import sys, os, json
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ine_lib import load_tempus, load_mir

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAWD = os.path.join(ROOT, "data_raw", "demografia_economia")
RAWC = os.path.join(ROOT, "data_raw", "criminalidad")
EXT = os.path.join(ROOT, "data_external")
OUTD = os.path.join(ROOT, "outputs")
PROC = os.path.join(ROOT, "data_processed")
TOTAL = "TOTAL INFRACCIONES PENALES"


def mir(f):
    d = load_mir(os.path.join(RAWC, f))
    d.columns = [c.replace("﻿", "").strip() for c in d.columns]
    d["anyo"] = d["periodo"].astype(int)
    d["valor"] = (d["Total"].astype(str).str.replace(".", "", regex=False)
                  .replace({"": None, "nan": None}).astype(float))
    return d[d["Comunidades autónomas"] == "TOTAL NACIONAL"]


R = {}

# ============ 1. POBLACIÓN POR ORIGEN ======================================
# 1a. Stock por grupo de NACIONALIDAD, 2018-2025 (única serie que cubre todo el periodo)
p = load_tempus(os.path.join(RAWC, "ine_56942_poblacion_nacionalidad_agrupacion.json"))
n = p[p["Comunidades y Ciudades Autónomas"].isna() & (p["Sexo"] == "Total")
      & (p["Totales de edad"] == "Todas las edades")]
POB = n.pivot_table(index="anyo", columns="Nacionalidad", values="valor", aggfunc="sum").fillna(0)
POB["AFRICA"] = POB["De Africa"]
POB["AMERICA"] = POB["De América del Norte"] + POB["De Centro América y Caribe"] + POB["De Sudamérica"]
POB["ASIA"] = POB["De Asia"]
POB["EUROPA"] = (POB.get("País de la UE28 sin España", 0) + POB.get("País de Europa menos UE28", 0)
                 + POB.get("País de la UE27_2020 sin España", 0) + POB.get("País de Europa menos UE27_2020", 0))
POB["OCEANIA"] = POB["De Oceanía"]
POB.to_csv(os.path.join(PROC, "f_poblacion_continente_nacionalidad.csv"))

d_tot_ext = POB.loc[2025, "Extranjera"] - POB.loc[2018, "Extranjera"]
cont = []
for k, lab in [("AMERICA", "América"), ("AFRICA", "África"), ("EUROPA", "Europa (sin España)"),
               ("ASIA", "Asia"), ("OCEANIA", "Oceanía")]:
    v0, v1 = POB.loc[2018, k], POB.loc[2025, k]
    cont.append({"grupo": lab, "v2018": float(v0), "v2025": float(v1), "delta": float(v1 - v0),
                 "var_pct": (v1 / v0 - 1) * 100,
                 "cuota_del_aumento_extranjero": (v1 - v0) / d_tot_ext * 100})
cont.sort(key=lambda x: -x["delta"])
R["poblacion_continentes_nacionalidad"] = cont
R["delta_extranjeros_total"] = float(d_tot_ext)

# Detalle Sudamérica / Centro América dentro de América
for k, lab in [("De Sudamérica", "Sudamérica"), ("De Centro América y Caribe", "Centroamérica y Caribe"),
               ("De América del Norte", "América del Norte")]:
    v0, v1 = POB.loc[2018, k], POB.loc[2025, k]
    R.setdefault("america_detalle", []).append(
        {"grupo": lab, "v2018": float(v0), "v2025": float(v1), "delta": float(v1 - v0),
         "var_pct": (v1 / v0 - 1) * 100})

# 1b. Stock por PAÍS DE NACIMIENTO, 2018-2022 (tabla 9675): única con detalle de país
b = load_tempus(os.path.join(RAWD, "ine_9675_2018_2022.json"))
bs = b[(b["Sexo"] == "Ambos sexos") & (b["Totales de edad"] == "Total")
       & (b["periodo"] == "1 de enero de") & b["Zonas Geográficas del Resto del Mundo"].isna()]
NAC = bs.pivot_table(index="Países y Continentes", columns="anyo", values="valor")
NAC.to_csv(os.path.join(PROC, "f_stock_pais_nacimiento_2018_2022.csv"))
agr = {"África", "Asia", "Sudamérica", "Centro América y Caribe", "América del Norte", "Oceanía",
       "UE27_2020 sin España", "UE28 sin España", "Europa menos UE27_2020", "Europa menos UE28",
       "España", "Total"}
paises_nac = [{"pais": i, "v2018": float(NAC.loc[i, 2018]), "v2022": float(NAC.loc[i, 2022]),
               "delta": float(NAC.loc[i, 2022] - NAC.loc[i, 2018]),
               "var_pct": (NAC.loc[i, 2022] / NAC.loc[i, 2018] - 1) * 100}
              for i in NAC.index if i not in agr and pd.notna(NAC.loc[i, 2018]) and pd.notna(NAC.loc[i, 2022])]
paises_nac.sort(key=lambda x: -x["delta"])
R["paises_nacimiento_2018_2022"] = paises_nac[:12]
R["nacidos_fuera_2018_2022_delta"] = float(NAC.loc["Total", 2022] - NAC.loc["Total", 2018]
                                           - (NAC.loc["España", 2022] - NAC.loc["España", 2018]))

# 1c. Flujos de entrada por PAÍS DE NACIMIENTO (2018-2020 serie anterior, 2021-2024 nueva EMCR)
fa = load_tempus(os.path.join(RAWD, "ine_24324_2018_2025.json"))
fa = fa[fa["Provincias"].isna() & fa["Zonas Geográficas del Resto del Mundo"].isna()]
FA = fa.pivot_table(index="Países y Continentes", columns="anyo", values="valor")
fb = load_tempus(os.path.join(RAWD, "ine_69694_2018_2025.json"))
fb = fb[fb["Provincias"].isna() & fb["Comunidades y Ciudades Autónomas"].isna()]
FB = fb.pivot_table(index="Países", columns="anyo", values="valor")
FLU = pd.concat([FA[[2018, 2019, 2020]], FB[[2021, 2022, 2023, 2024]]], axis=1)
FLU["acumulado_2018_2024"] = FLU.sum(axis=1)
FLU.to_csv(os.path.join(PROC, "f_flujos_entrada_pais_nacimiento.csv"))
flu = [{"pais": i, "acum": float(FLU.loc[i, "acumulado_2018_2024"]),
        "serie": [float(FLU.loc[i, a]) if pd.notna(FLU.loc[i, a]) else None for a in range(2018, 2025)]}
       for i in FLU.index if i not in agr and pd.notna(FLU.loc[i, "acumulado_2018_2024"])]
flu.sort(key=lambda x: -x["acum"])
R["entradas_por_pais_nacimiento"] = flu[:14]
R["entradas_total_2018_2024"] = float(FLU.loc["Total", "acumulado_2018_2024"])
for pais in ["Ucrania", "Colombia", "Venezuela", "Marruecos"]:
    if pais in FLU.index:
        R.setdefault("series_pais", {})[pais] = [
            float(FLU.loc[pais, a]) if pd.notna(FLU.loc[pais, a]) else None for a in range(2018, 2025)]

# ============ 2. CRIMINALIDAD POR ORIGEN ===================================
d07 = mir("mir_detenciones_investigados_03007.csv")
d07 = d07[d07["Sexo"] == "Ambos sexos"]
DET = d07.pivot_table(index="anyo", columns="Nacionalidad", values="valor")
DET.to_csv(os.path.join(PROC, "f_detenidos_extranjeros_nacionalidad.csv"))
d01 = mir("mir_detenciones_investigados_03001.csv")
T = d01[d01["Tipología penal"] == TOTAL].set_index("anyo")["valor"]
d05 = mir("mir_detenciones_investigados_03005.csv")
E = d05[(d05["Tipología penal"] == TOTAL) & (d05["Sexo"] == "Ambos sexos")].set_index("anyo")["valor"]
ESP = T - E

mapa = {"África": "1.-CONTINENTE AFRICANO", "América": "2.-CONTINENTE AMERICANO",
        "Asia": "3.-CONTINENTE ASIÁTICO", "Europa (sin España)": "4.-CONTINENTE EUROPEO"}
clave = {"África": "AFRICA", "América": "AMERICA", "Asia": "ASIA", "Europa (sin España)": "EUROPA"}
det_cont = []
for lab, col in mapa.items():
    k = clave[lab]
    n0, n1 = DET.loc[2018, col], DET.loc[2024, col]
    t0, t1 = n0 / POB.loc[2018, k] * 1e5, n1 / POB.loc[2024, k] * 1e5
    det_cont.append({"grupo": lab, "n2018": float(n0), "n2024": float(n1),
                     "var_n_pct": (n1 / n0 - 1) * 100, "tasa2018": float(t0), "tasa2024": float(t1),
                     "var_tasa_pct": (t1 / t0 - 1) * 100,
                     "pob2024": float(POB.loc[2024, k])})
te0 = ESP[2018] / POB.loc[2018, "Española"] * 1e5
te1 = ESP[2024] / POB.loc[2024, "Española"] * 1e5
for r in det_cont:
    r["ratio2018"] = r["tasa2018"] / te0
    r["ratio2024"] = r["tasa2024"] / te1
det_cont.sort(key=lambda x: -x["tasa2024"])
R["detenidos_continente"] = det_cont
R["detenidos_espanoles"] = {"n2018": float(ESP[2018]), "n2024": float(ESP[2024]),
                            "tasa2018": float(te0), "tasa2024": float(te1),
                            "var_tasa_pct": (te1 / te0 - 1) * 100}
R["oceania_aviso"] = {"n2024": float(DET.loc[2024, "5.-OCEANÍA"]), "pob2024": float(POB.loc[2024, "OCEANIA"])}

# Países concretos
pais_cols = [c for c in DET.columns if c not in list(mapa.values()) + ["5.-OCEANÍA", "6.-OTROS", "TOTAL"]]
dp = [{"pais": c.split(".-")[-1], "n2018": float(DET.loc[2018, c]), "n2024": float(DET.loc[2024, c]),
       "var_pct": (DET.loc[2024, c] / DET.loc[2018, c] - 1) * 100}
      for c in pais_cols if DET.loc[2018, c] and DET.loc[2018, c] > 0]
dp.sort(key=lambda x: -x["n2024"])
R["detenidos_paises"] = dp[:12]

# Tipo de infracción: peso de los extranjeros (03005 sobre 03001)
tot_tip = d01.pivot_table(index="Tipología penal", columns="anyo", values="valor")
ext_tip = d05[d05["Sexo"] == "Ambos sexos"].pivot_table(index="Tipología penal", columns="anyo", values="valor")
tipos = ["1.1.-Homicidios dolosos/asesinatos", "1.2.-Lesiones", "1.3.-Malos tratos ámbito familiar",
         "3.1.-Agresión sexual", "3.2.-Agresión sexual con penetración", "5.1.-Hurtos",
         "5.2.2.-Robos con fuerza en viviendas", "5.3.-Robos con violencia o intimidación",
         "5.5.-Estafas", "5.5.1.-Estafas informáticas", "6.1.-Tráfico de drogas",
         "6.2.-Contra la seguridad vial", "7. FALSEDADES", TOTAL]
etq = {"1.1.-Homicidios dolosos/asesinatos": "Homicidios dolosos y asesinatos",
       "1.2.-Lesiones": "Lesiones", "1.3.-Malos tratos ámbito familiar": "Malos tratos en el ámbito familiar",
       "3.1.-Agresión sexual": "Agresión sexual",
       "3.2.-Agresión sexual con penetración": "Agresión sexual con penetración",
       "5.1.-Hurtos": "Hurtos", "5.2.2.-Robos con fuerza en viviendas": "Robos con fuerza en viviendas",
       "5.3.-Robos con violencia o intimidación": "Robos con violencia o intimidación",
       "5.5.-Estafas": "Estafas", "5.5.1.-Estafas informáticas": "Estafas informáticas",
       "6.1.-Tráfico de drogas": "Tráfico de drogas", "6.2.-Contra la seguridad vial": "Contra la seguridad vial",
       "7. FALSEDADES": "Falsedades documentales", TOTAL: "Todas las infracciones penales"}
R["peso_extranjeros_por_tipo"] = [
    {"tipo": etq[t], "pct2018": float(ext_tip.loc[t, 2018] / tot_tip.loc[t, 2018] * 100),
     "pct2024": float(ext_tip.loc[t, 2024] / tot_tip.loc[t, 2024] * 100),
     "n_ext2024": float(ext_tip.loc[t, 2024]), "n_tot2024": float(tot_tip.loc[t, 2024])}
    for t in tipos]

# Condenados por grupo de nacionalidad y tasas (INE 25645)
c = load_tempus(os.path.join(RAWC, "ine_25645_condenados_sexo_edad_nacionalidad.json"))
ct = c[(c["Sexo"] == "Total") & (c["Semiintervalos de edad"] == "Total ") & c["Grupos de edad"].isna()]
CON = ct.pivot_table(index="anyo", columns="Nacionalidad", values="valor").fillna(0)
CON["EUROPA"] = (CON.get("País de la UE28 sin España", 0) + CON.get("País de Europa menos UE28", 0)
                 + CON.get("País de la UE27_2020 sin España", 0) + CON.get("País de Europa menos UE27_2020", 0))
con_cont = []
for lab, col, k in [("África", "De Africa", "AFRICA"), ("América", "De América", "AMERICA"),
                    ("Asia", "De Asia", "ASIA"), ("Europa (sin España)", "EUROPA", "EUROPA")]:
    n0, n1 = CON.loc[2018, col], CON.loc[2025, col]
    t0, t1 = n0 / POB.loc[2018, k] * 1e5, n1 / POB.loc[2025, k] * 1e5
    con_cont.append({"grupo": lab, "n2018": float(n0), "n2025": float(n1), "var_n_pct": (n1 / n0 - 1) * 100,
                     "tasa2018": float(t0), "tasa2025": float(t1), "var_tasa_pct": (t1 / t0 - 1) * 100})
ce0 = CON.loc[2018, "Española"] / POB.loc[2018, "Española"] * 1e5
ce1 = CON.loc[2025, "Española"] / POB.loc[2025, "Española"] * 1e5
for r in con_cont:
    r["ratio2025"] = r["tasa2025"] / ce1
con_cont.sort(key=lambda x: -x["tasa2025"])
R["condenados_continente"] = con_cont
R["condenados_espanoles"] = {"n2018": float(CON.loc[2018, "Española"]), "n2025": float(CON.loc[2025, "Española"]),
                             "tasa2018": float(ce0), "tasa2025": float(ce1),
                             "var_tasa_pct": (ce1 / ce0 - 1) * 100}

# Composición del delito por grupo de nacionalidad (INE 26014, infracciones, 2025)
dd = load_tempus(os.path.join(RAWC, "ine_26014_delitos_nacionalidad.json"))
d25 = dd[dd["anyo"] == 2025]
DL = d25.pivot_table(index="Delitos Faltas", columns="Nacionalidad", values="valor").fillna(0)
DL["EUROPA"] = (DL.get("País de la UE27_2020 sin España", 0) + DL.get("País de Europa menos UE27_2020", 0))
grupos = [("Española", "Española"), ("De Africa", "África"), ("De América", "América"),
          ("De Asia", "Asia"), ("EUROPA", "Europa (sin España)")]
familias = ["Contra la seguridad vial", "Hurtos", "Lesiones", "Robos", "Contra el orden público",
            "Contra la Administración de Justicia", "Contra la libertad", "Contra la salud pública",
            "Estafas", "Falsedades", "Contra la libertad e indemnidad sexuales"]
comp = []
for fam in familias:
    fila = {"tipo": fam}
    for col, lab in grupos:
        tot_g = DL.loc["Delitos", col]
        fila[lab] = float(DL.loc[fam, col] / tot_g * 100) if tot_g else None
        fila["n_" + lab] = float(DL.loc[fam, col])
    comp.append(fila)
comp.sort(key=lambda x: -(x["Española"] or 0))
R["composicion_delitos_por_origen"] = comp
R["total_delitos_por_origen"] = {lab: float(DL.loc["Delitos", col]) for col, lab in grupos}

# ============ 3. COMPARATIVA EUROPEA =======================================
NOM = {"EU27_2020": "UE-27", "ES": "España", "DE": "Alemania", "FR": "Francia", "IT": "Italia",
       "PT": "Portugal", "NL": "Países Bajos", "PL": "Polonia", "EL": "Grecia", "IE": "Irlanda",
       "BE": "Bélgica", "AT": "Austria", "SE": "Suecia"}
h = pd.read_csv(os.path.join(EXT, "eurostat_hicp.csv")).pivot(index="geo", columns="anyo", values="valor")
g = pd.read_csv(os.path.join(EXT, "eurostat_pib_pc_real.csv")).pivot(index="geo", columns="anyo", values="valor")
sa = pd.read_csv(os.path.join(EXT, "eurostat_salario_neto.csv")).pivot(index="geo", columns="anyo", values="valor")
ai = pd.read_csv(os.path.join(EXT, "eurostat_aic_pps.csv")).pivot(index="geo", columns="anyo", values="valor")
eu = []
for geo in h.index:
    eu.append({"pais": NOM.get(geo, geo), "geo": geo,
               "infl": float((h.loc[geo, 2025] / h.loc[geo, 2018] - 1) * 100),
               "pibpc": float((g.loc[geo, 2024] / g.loc[geo, 2018] - 1) * 100),
               "salario_real": float(((sa.loc[geo, 2023] / sa.loc[geo, 2018])
                                      / (h.loc[geo, 2023] / h.loc[geo, 2018]) - 1) * 100),
               "aic2018": float(ai.loc[geo, 2018]), "aic2024": float(ai.loc[geo, 2024]),
               "aic_dif": float(ai.loc[geo, 2024] - ai.loc[geo, 2018])})
eu.sort(key=lambda x: -x["salario_real"])
R["comparativa_europa"] = eu
es = [x for x in eu if x["geo"] == "ES"][0]
R["espana_ranking"] = {
    "n": len(eu),
    "salario_real": sorted([x["salario_real"] for x in eu], reverse=True).index(es["salario_real"]) + 1,
    "pibpc": sorted([x["pibpc"] for x in eu], reverse=True).index(es["pibpc"]) + 1,
    "infl": sorted([x["infl"] for x in eu], reverse=True).index(es["infl"]) + 1,
}

json.dump(R, open(os.path.join(OUTD, "desgloses.json"), "w"), ensure_ascii=False, indent=1)
print("outputs/desgloses.json escrito")
for k, v in R.items():
    print(f"  {k}: {len(v) if hasattr(v,'__len__') else v}")
