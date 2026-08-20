"""Bloque E: criminalidad registrada (Ministerio del Interior) y condenas (INE).

Unidades separadas y nunca mezcladas:
  hechos conocidos != hechos esclarecidos != detenidos/investigados != condenados != infracciones.
Cobertura Interior: años naturales completos 2018-2024. INE condenados: hasta 2024/2025.

HALLAZGO (ver REGISTRO_CAMBIOS_CLAUDE.md): el universo real de las matrices 03003,
03005 y 03007 NO es el descrito en data_raw/criminalidad/metadata.csv. Verificado
para los siete años:
  - 03001/03002 = TOTAL de detenciones e investigados.
  - 03005/03006 y 03007/03008 = subconjunto de EXTRANJEROS (sus totales coinciden
    exactamente y la lista de nacionalidades de 03007 no incluye España).
  - 03003/03004 = subconjunto de MENORES de 14-17 años (su total coincide
    exactamente con el grupo '14-17 años' de 03009 en los siete años).
Los detenidos de nacionalidad española se obtienen por diferencia 03001 - 03005.
Salida: data_processed/e_*.csv
"""
import sys, os, json
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ine_lib import load_tempus, load_mir

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAWC = os.path.join(ROOT, "data_raw", "criminalidad")
OUT = os.path.join(ROOT, "data_processed")
TOTAL = "TOTAL INFRACCIONES PENALES"


def mir(nombre, solo_nacional=True):
    df = load_mir(os.path.join(RAWC, nombre))
    df.columns = [c.replace("﻿", "").strip() for c in df.columns]
    df["anyo"] = df["periodo"].astype(int)
    df["valor"] = (df["Total"].astype(str).str.replace(".", "", regex=False)
                   .replace({"": None, "nan": None}).astype(float))
    if solo_nacional:
        df = df[df["Comunidades autónomas"] == "TOTAL NACIONAL"]
    return df


# --- Denominadores de población por nacionalidad (1 de enero, INE 56942) ----
pob = load_tempus(os.path.join(RAWC, "ine_56942_poblacion_nacionalidad_agrupacion.json"))
pn = pob[pob["Comunidades y Ciudades Autónomas"].isna() & (pob["Sexo"] == "Total")
         & (pob["Totales de edad"] == "Todas las edades")]
POB = pn.pivot_table(index="anyo", columns="Nacionalidad", values="valor", aggfunc="sum")

# --- 1. Hechos conocidos y esclarecidos por tipología -----------------------
HC = mir("mir_hechos_conocidos_01001.csv").pivot_table(index="anyo", columns="Tipología penal", values="valor")
HE = mir("mir_hechos_esclarecidos_02001.csv").pivot_table(index="anyo", columns="Tipología penal", values="valor")
HC.to_csv(os.path.join(OUT, "e_hechos_conocidos_tipologia.csv"))
HE.to_csv(os.path.join(OUT, "e_hechos_esclarecidos_tipologia.csv"))

# --- 2. Detenidos/investigados: total, extranjeros y (por diferencia) españoles
d01 = mir("mir_detenciones_investigados_03001.csv")
DET_TOT = d01[d01["Tipología penal"] == TOTAL].set_index("anyo")["valor"]
d05 = mir("mir_detenciones_investigados_03005.csv")
DET_EXT = d05[(d05["Tipología penal"] == TOTAL) & (d05["Sexo"] == "Ambos sexos")].set_index("anyo")["valor"]
d07 = mir("mir_detenciones_investigados_03007.csv")
chk = d07[(d07["Nacionalidad"] == "TOTAL") & (d07["Sexo"] == "Ambos sexos")].set_index("anyo")["valor"]
assert (DET_EXT == chk).all(), "03005 y 03007 deberían coincidir (mismo universo: extranjeros)"
d09 = mir("mir_detenciones_investigados_03009.csv")
MEN = d09[(d09["Tipología penal"] == TOTAL) & (d09["Sexo"] == "Ambos sexos")
          & (d09["Grupo de edad"] == "14-17 años")].set_index("anyo")["valor"]
d03 = mir("mir_detenciones_investigados_03003.csv")
chk2 = d03[(d03["Tipología penal"] == TOTAL) & (d03["Sexo"] == "Ambos sexos")
           & (d03["Nacionalidad"] == "Total")].set_index("anyo")["valor"]
assert (MEN == chk2).all(), "03003 debería ser el subconjunto de menores 14-17"
DET_ESP = DET_TOT - DET_EXT

# Detenidos extranjeros por tipología (03005) y por nacionalidad (03007)
DET_EXT_TIP = d05[d05["Sexo"] == "Ambos sexos"].pivot_table(index="anyo", columns="Tipología penal", values="valor")
DET_EXT_NAC = d07[d07["Sexo"] == "Ambos sexos"].pivot_table(index="anyo", columns="Nacionalidad", values="valor")
DET_EXT_TIP.to_csv(os.path.join(OUT, "e_detenidos_extranjeros_tipologia.csv"))
DET_EXT_NAC.to_csv(os.path.join(OUT, "e_detenidos_extranjeros_nacionalidad.csv"))

# --- 3. Condenados adultos por nacionalidad (INE 25645) ---------------------
cond = load_tempus(os.path.join(RAWC, "ine_25645_condenados_sexo_edad_nacionalidad.json"))
ct = cond[(cond["Sexo"] == "Total") & (cond["Semiintervalos de edad"] == "Total ")
          & cond["Grupos de edad"].isna()]
CON = ct.pivot_table(index="anyo", columns="Nacionalidad", values="valor")
CON["Extranjera"] = CON["Total"] - CON["Española"]
CON.to_csv(os.path.join(OUT, "e_condenados_nacionalidad.csv"))

# --- 4. Delitos sexuales de condenados (INE 28752) --------------------------
sex = load_tempus(os.path.join(RAWC, "ine_28752_delitos_sexuales_nacionalidad.json"))
sx = sex[sex["Delitos Faltas"] == "Contra la libertad e indemnidad sexuales"]
SEX = sx.pivot_table(index="anyo", columns="Nacionalidad", values="valor")
SEX.to_csv(os.path.join(OUT, "e_delitos_sexuales_nacionalidad.csv"))

# --- Resumen con tasas por 100.000 de la MISMA nacionalidad -----------------
res = pd.DataFrame(index=pd.Index(range(2018, 2026), name="anyo"))
res["pob_total"] = POB["Total"]
res["pob_espanola"] = POB["Española"]
res["pob_extranjera"] = POB["Extranjera"]
res["pct_pob_extranjera"] = POB["Extranjera"] / POB["Total"] * 100
res["hechos_conocidos"] = HC[TOTAL]
res["hechos_conocidos_por_100k"] = HC[TOTAL] / POB["Total"] * 1e5
res["hechos_esclarecidos"] = HE[TOTAL]
res["tasa_esclarecimiento_pct"] = HE[TOTAL] / HC[TOTAL] * 100
res["detenidos_total"] = DET_TOT
res["detenidos_extranjeros"] = DET_EXT
res["detenidos_espanoles"] = DET_ESP
res["pct_detenidos_extranjeros"] = DET_EXT / DET_TOT * 100
res["detenidos_esp_por_100k_pob_esp"] = DET_ESP / POB["Española"] * 1e5
res["detenidos_ext_por_100k_pob_ext"] = DET_EXT / POB["Extranjera"] * 1e5
res["ratio_tasas_ext_esp"] = res["detenidos_ext_por_100k_pob_ext"] / res["detenidos_esp_por_100k_pob_esp"]
res["detenidos_menores_14_17"] = MEN
res["condenados_total"] = CON["Total"]
res["condenados_esp"] = CON["Española"]
res["condenados_ext"] = CON["Extranjera"]
res["pct_condenados_extranjeros"] = CON["Extranjera"] / CON["Total"] * 100
res["condenados_esp_por_100k_pob_esp"] = CON["Española"] / POB["Española"] * 1e5
res["condenados_ext_por_100k_pob_ext"] = CON["Extranjera"] / POB["Extranjera"] * 1e5
for c in SEX.columns:
    res["delitos_sexuales_" + c.lower()] = SEX[c]
res.to_csv(os.path.join(OUT, "e_criminalidad_resumen.csv"))

# --- Descomposición shift-share del aumento de detenidos extranjeros --------
y0, y1 = 2018, 2024
P0, P1 = POB.loc[y0, "Extranjera"], POB.loc[y1, "Extranjera"]
r0, r1 = DET_EXT[y0] / P0, DET_EXT[y1] / P1
desc = {
    "delta_detenidos_total": DET_TOT[y1] - DET_TOT[y0],
    "delta_detenidos_espanoles": DET_ESP[y1] - DET_ESP[y0],
    "delta_detenidos_extranjeros": DET_EXT[y1] - DET_EXT[y0],
    "pct_del_aumento_atribuible_grupo_extranjero": (DET_EXT[y1] - DET_EXT[y0]) / (DET_TOT[y1] - DET_TOT[y0]) * 100,
    "efecto_poblacion": (P1 - P0) * r0,
    "efecto_tasa": P0 * (r1 - r0),
    "efecto_interaccion": (P1 - P0) * (r1 - r0),
}
desc["comprobacion_suma"] = desc["efecto_poblacion"] + desc["efecto_tasa"] + desc["efecto_interaccion"]
json.dump({k: float(v) for k, v in desc.items()},
          open(os.path.join(OUT, "e_descomposicion.json"), "w"), indent=2)

pd.set_option("display.width", 320); pd.set_option("display.max_columns", 40)
print(res.round(2).to_string())
print("\nDescomposición shift-share detenidos extranjeros 2018->2024:")
for k, v in desc.items():
    print(f"  {k:48s} {v:>14,.1f}")
print("\n--- Hechos conocidos por tipología principal ---")
top = [t for t in HC.columns if t.split(".")[0].isdigit() and len(t.split(".")[0]) <= 2
       and t.split(".", 1)[1].startswith(" ")]
cmp_ = pd.DataFrame({"2018": HC.loc[2018], "2024": HC.loc[2024]})
cmp_["var_%"] = (cmp_["2024"] / cmp_["2018"] - 1) * 100
print(cmp_.loc[sorted(top, key=lambda x: int(x.split(".")[0])) + [TOTAL]].round(1).to_string())
