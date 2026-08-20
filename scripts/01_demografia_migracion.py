"""Bloque A: demografía y migración. Salida: data_processed/a_demografia.csv"""
import sys, os, json
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ine_lib import load_tempus

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data_raw", "demografia_economia")
RAWC = os.path.join(ROOT, "data_raw", "criminalidad")
OUT = os.path.join(ROOT, "data_processed")
os.makedirs(OUT, exist_ok=True)

series = {}

# --- 1. Población total y por nacionalidad (1 de enero), tabla INE 56942 -----
pob = load_tempus(os.path.join(RAWC, "ine_56942_poblacion_nacionalidad_agrupacion.json"))
nac = pob[pob["Comunidades y Ciudades Autónomas"].isna() & (pob["Sexo"] == "Total")
          & (pob["Totales de edad"] == "Todas las edades")]
piv = nac.pivot_table(index="anyo", columns="Nacionalidad", values="valor", aggfunc="sum")
series["pob_total"] = piv["Total"]
series["pob_nac_espanola"] = piv["Española"]
series["pob_nac_extranjera"] = piv["Extranjera"]

# Envejecimiento: 65+ sobre total, misma tabla
edades = pob[pob["Comunidades y Ciudades Autónomas"].isna() & (pob["Sexo"] == "Total")
             & (pob["Nacionalidad"] == "Total")]
g65 = ["De 65 a 69 años", "De 70 a 74 años", "De 75 a 79 años", "De 80 a 84 años",
       "De 85 a 89 años"]
m65 = edades[edades["Grupos de edad"].isin(g65)].groupby("anyo")["valor"].sum()
m90 = edades[edades["Semiintervalos de edad"] == "90 y más años"].groupby("anyo")["valor"].sum()
series["pob_65mas"] = m65 + m90
series["pct_65mas"] = (m65 + m90) / piv["Total"] * 100

# Población 16-64 (edad de trabajar aproximada por grupos quinquenales 15-64)
g1564 = [f"De {a} a {a+4} años" for a in range(15, 65, 5)]
series["pob_15_64"] = edades[edades["Grupos de edad"].isin(g1564)].groupby("anyo")["valor"].sum()

# --- 2. Población por PAÍS DE NACIMIENTO ------------------------------------
# 2018-2022: tabla 9675 (Cifras de Población / serie histórica ECP)
n9675 = load_tempus(os.path.join(RAW, "ine_9675_2018_2022.json"))
s = n9675[(n9675["Sexo"] == "Ambos sexos") & (n9675["Totales de edad"] == "Total")
          & (n9675["periodo"] == "1 de enero de")
          & n9675["Zonas Geográficas del Resto del Mundo"].isna()]
p9675 = s[s["Países y Continentes"].isin(["Total", "España"])].pivot_table(
    index="anyo", columns="Países y Continentes", values="valor")
p9675["fuera"] = p9675["Total"] - p9675["España"]

# 2021-2025: tabla 70364 (Censo anual de población, 1 de enero)
n70364 = load_tempus(os.path.join(RAW, "ine_70364_2018_2025.json"))
s2 = n70364[(n70364["Sexo"] == "Total") & n70364["Provincias"].isna()
            & (n70364["Año de llegada a España"] == "Total")
            & (n70364["Año de llegada a Provincia"] == "Total")]
p70364 = s2.pivot_table(index="anyo", columns="Países", values="valor")

series["nacidos_espana_ecp"] = p9675["España"]
series["nacidos_fuera_ecp"] = p9675["fuera"]
series["nacidos_espana_censo"] = p70364["España"]
series["nacidos_fuera_censo"] = p70364["Extranjero"]

# Serie enlazada de nacidos fuera: ECP 2018-2020, Censo anual 2021-2025
enl_f = pd.concat([p9675["fuera"].loc[2018:2020], p70364["Extranjero"].loc[2021:2025]])
enl_e = pd.concat([p9675["España"].loc[2018:2020], p70364["España"].loc[2021:2025]])
series["nacidos_fuera_enlazada"] = enl_f
series["nacidos_espana_enlazada"] = enl_e
series["pct_nacidos_fuera"] = enl_f / (enl_f + enl_e) * 100

# Salto de serie observado en el solape 2021-2022
salto = pd.DataFrame({"ecp": p9675["fuera"], "censo": p70364["Extranjero"]}).dropna()
salto["dif"] = salto["censo"] - salto["ecp"]

# --- 3. Residentes nacidos fuera por año de llegada (stock 1-ene-2025) ------
lleg = n70364[(n70364["Sexo"] == "Total") & n70364["Provincias"].isna()
              & (n70364["Año de llegada a Provincia"] == "Total")
              & (n70364["Países"] == "Extranjero") & (n70364["anyo"] == 2025)
              & (n70364["Año de llegada a España"] != "Total")]
lleg_s = lleg.groupby("Año de llegada a España")["valor"].sum()
desde2018 = lleg_s.loc[[a for a in ["2018", "2019", "2020", "2021", "2022", "2023", "2024"]
                        if a in lleg_s.index]].sum()

# --- 4. Adquisiciones de nacionalidad española (tabla 15073) ----------------
adq = load_tempus(os.path.join(RAW, "ine_15073_2018_2025.json"))
adq_t = adq[(adq["Nacionalidad"] == "Total") & (adq["Países y Continentes"] == "Total")
            & (adq["Zonas Geográficas del Resto del Mundo"].isna())]
series["adquisiciones_nacionalidad"] = adq_t.groupby("anyo")["valor"].sum()

# --- 5. Flujos: inmigraciones exteriores ------------------------------------
# Serie anterior (2018-2021): tabla 24324. Nueva EMCR (2021-2024): tabla 69694.
i24324 = load_tempus(os.path.join(RAW, "ine_24324_2018_2025.json"))
a = i24324[i24324["Provincias"].isna() & (i24324["Países y Continentes"] == "Total")
           & i24324["Zonas Geográficas del Resto del Mundo"].isna()]
series["inmigraciones_serie_antigua"] = a.groupby("anyo")["valor"].sum()

i69694 = load_tempus(os.path.join(RAW, "ine_69694_2018_2025.json"))
b = i69694[i69694["Provincias"].isna() & i69694["Comunidades y Ciudades Autónomas"].isna()
           & (i69694["Países"] == "Total")]
series["inmigraciones_serie_nueva"] = b.groupby("anyo")["valor"].sum()

# Emigraciones (nueva EMCR, tabla 76246, nacional)
e76246 = load_tempus(os.path.join(RAW, "ine_76246_2018_2025.json"))
e = e76246[(e76246["Sexo"] == "Ambos sexos") & (e76246["Países"] == "Total")
           & (e76246["Año de llegada a España"] == "Total")]
series["emigraciones_serie_nueva"] = e.groupby("anyo")["valor"].sum()

# Saldo migratorio exterior (tabla 24428, semestral -> anual, 2018-2022)
s24428 = load_tempus(os.path.join(RAW, "ine_24428_2018_2025.json"))
sm = s24428[s24428["Provincias"].isna() & (s24428["Países y Continentes"] == "Total")
            & s24428["Zonas Geográficas del Resto del Mundo"].isna()]
series["saldo_migratorio_ext"] = sm.groupby("anyo")["valor"].sum()

# --- 6. Principales países de nacimiento (stock 2018 vs último ECP 2022) ----
top = s[~s["Países y Continentes"].isin(["Total", "España"])]
excl = {"UE27_2020 sin España", "UE28 sin España", "Europa menos UE27_2020",
        "Europa menos UE28", "África", "América del Norte", "Centro América y Caribe",
        "Sudamérica", "Asia", "Oceanía"}
topc = top[~top["Países y Continentes"].isin(excl)]
top_piv = topc.pivot_table(index="Países y Continentes", columns="anyo", values="valor")

df = pd.DataFrame(series)
df.index.name = "anyo"
df.to_csv(os.path.join(OUT, "a_demografia.csv"))
top_piv.to_csv(os.path.join(OUT, "a_paises_nacimiento.csv"))
lleg_s.to_csv(os.path.join(OUT, "a_ano_llegada_2025.csv"))
salto.to_csv(os.path.join(OUT, "a_solape_series_nacimiento.csv"))

extra = {"nacidos_fuera_llegados_desde_2018_stock_2025": float(desde2018),
         "salto_serie_2021": float(salto.loc[2021, "dif"]),
         "salto_serie_2022": float(salto.loc[2022, "dif"])}
json.dump(extra, open(os.path.join(OUT, "a_extra.json"), "w"), indent=2)

print(df.round(1).to_string())
print("\nSolape ECP vs Censo (nacidos fuera):\n", salto.to_string())
print("\nExtra:", extra)
