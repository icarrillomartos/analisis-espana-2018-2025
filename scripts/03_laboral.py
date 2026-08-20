"""Bloque C: mercado laboral (EPA, ETCL). Medias anuales de los 4 trimestres.
Salida: data_processed/c_laboral.csv
"""
import sys, os
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ine_lib import load_tempus

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data_raw", "bienestar_empleo")
OUT = os.path.join(ROOT, "data_processed")

def media_anual(df, valcol="valor"):
    """Media de los cuatro trimestres; solo años con los 4 trimestres presentes."""
    g = df.groupby("anyo")[valcol].agg(["mean", "count"])
    return g.loc[g["count"] % 4 == 0, "mean"]

s = {}

# --- Tasas EPA nacionales (tabla 65349), ambos sexos, Total Nacional --------
epa = load_tempus(os.path.join(RAW, "epa_tasas_actividad_paro_empleo_provincia_sexo_trimestral.json"))
nac = epa[epa["Provincias"].isna() & (epa["Sexo"] == "Ambos sexos")]
for tipo, key in [("Tasa de actividad", "tasa_actividad"),
                  ("Tasa de empleo de la población", "tasa_empleo"),
                  ("Tasa de paro de la población", "tasa_paro")]:
    s[key] = media_anual(nac[nac["Tipo de dato"] == tipo])

# --- Tasas EPA por NACIONALIDAD (tablas 65300/65310/65336) ------------------
for fn, tipo, pref in [("epa_tasa_paro_nacionalidad_sexo_ccaa_trimestral.json", "paro", "paro"),
                       ("epa_tasa_empleo_nacionalidad_sexo_ccaa_trimestral.json", "empleo", "empleo"),
                       ("epa_tasa_actividad_nacionalidad_sexo_ccaa_trimestral.json", "actividad", "actividad")]:
    d = load_tempus(os.path.join(RAW, fn))
    d = d[d["Comunidades y Ciudades Autónomas"].isna() & (d["Sexo"] == "Ambos sexos")]
    for nacion, suf in [("Española", "esp"), ("Extranjera: Total", "ext")]:
        s[f"tasa_{pref}_nacionalidad_{suf}"] = media_anual(d[d["Nacionalidad"] == nacion])

# --- Inactivos por clase (tabla 65343), miles de personas -------------------
ina = load_tempus(os.path.join(RAW, "epa_inactivos_clase_sexo_ccaa_trimestral.json"))
ina = ina[ina["Comunidades y Ciudades Autónomas"].isna() & (ina["Sexo"] == "Ambos sexos")]
for clase, key in [("Total", "inactivos_total_miles"), ("Jubilado", "inactivos_jubilados_miles"),
                   ("Estudiante", "inactivos_estudiantes_miles"),
                   ("Labores del hogar", "inactivos_labores_hogar_miles"),
                   ("Incapacitado permanente", "inactivos_incapacidad_miles")]:
    s[key] = media_anual(ina[ina["SITUACION DE INACTIVIDAD"] == clase])

# --- Vacantes (ETCL tabla 6064) ---------------------------------------------
vac = load_tempus(os.path.join(RAW, "vacantes_ccaa_trimestral.json"))
vac = vac[vac["Comunidades y Ciudades Autónomas"].isna()]
s["vacantes_media_trimestral"] = media_anual(vac)

df = pd.DataFrame(s)
df.index.name = "anyo"
df.to_csv(os.path.join(OUT, "c_laboral.csv"))
print(df.round(2).to_string())
print("\n2018 -> 2025 (media anual):")
for c in df.columns:
    a, b = df[c].get(2018), df[c].get(2025)
    if pd.notna(a) and pd.notna(b):
        print(f"  {c:38s} {a:>10,.2f} -> {b:>10,.2f}  {b-a:+7.2f} pp/abs  ({(b/a-1)*100:+6.2f}%)")
