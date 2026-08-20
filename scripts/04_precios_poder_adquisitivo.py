"""Bloque D: precios, salarios, renta, pobreza, vivienda e hipotecas.
Regla de deflactación: valor_real_en_euros_2018 = valor_nominal_t * IPC_2018 / IPC_t
usando la MEDIA ANUAL del IPC general (base 2021 = 100, tabla INE 50902).
Salida: data_processed/d_precios.csv y d_ipc_grupos.csv
"""
import sys, os, json
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ine_lib import load_tempus

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data_raw", "bienestar_empleo")
OUT = os.path.join(ROOT, "data_processed")

# --- IPC media anual, general y por grupos ECOICOP --------------------------
ipc = load_tempus(os.path.join(RAW, "ipc_nacional_mensual_grupos.json"))
idx = ipc[ipc["Índices y Tasas"] == "Índice"]
cnt = idx.groupby(["Grupos ECOICOP", "anyo"])["valor"].count()
assert (cnt == 12).all(), "algún año no tiene los 12 meses"
grupos = idx.groupby(["Grupos ECOICOP", "anyo"])["valor"].mean().unstack(0)
grupos.to_csv(os.path.join(OUT, "d_ipc_grupos.csv"))
IPC = grupos["Índice general"]
defl = lambda serie: serie * IPC.loc[2018] / IPC.reindex(serie.index)

s = {}
s["ipc_general_media_anual"] = IPC
s["euros_necesarios_para_1000e_2018"] = 1000 * IPC / IPC.loc[2018]
s["poder_compra_de_1000e_de_2018"] = 1000 * IPC.loc[2018] / IPC

# --- Salarios: ganancia media anual (EAES, tabla 28200) ---------------------
g = load_tempus(os.path.join(RAW, "ganancia_media_anual_sexo_tipo_contrato.json"))
gn = g[g["Comunidades y Ciudades Autónomas"].isna() & (g["Sexo"] == "Ambos sexos")]
gt = gn[gn["Tipo de contrato o relación laboral"] == "Total"].set_index("anyo")["valor"].sort_index()
s["salario_medio_nominal"] = gt
s["salario_medio_real_e2018"] = defl(gt)

# --- Salario por decil (tabla 10910): solo hay desglose por sexo ------------
d = load_tempus(os.path.join(RAW, "salario_medio_por_decil.json"))
d["decil"] = d["Semiintervalos de percentiles"].fillna(d["Grupos de percentiles"]).fillna(
    d["Percentiles simples"].map({"Total": "Total"}))
for sexo in ["Hombres", "Mujeres"]:
    for dec in ["Decil 1", "Decil 5", "Decil 10"]:
        serie = d[(d["Sexo"] == sexo) & (d["decil"] == dec)].set_index("anyo")["valor"].sort_index()
        if len(serie):
            k = f"salario_{dec.lower().replace(' ', '')}_{sexo.lower()}"
            s[k + "_nominal"] = serie
            s[k + "_real_e2018"] = defl(serie)

# --- Renta ECV (tabla 9947). OJO: la renta se refiere al AÑO ANTERIOR -------
r = load_tempus(os.path.join(RAW, "renta_neta_media_persona_unidad_consumo_ccaa.json"))
rn = r[r["Comunidades y Ciudades Autónomas"].isna()]
for concepto, key in [("Renta neta media por persona", "renta_persona"),
                      ("Renta media por unidad de consumo", "renta_unidad_consumo")]:
    serie = rn[rn["SALDOS CONTABLES"] == concepto].set_index("anyo")["valor"].sort_index()
    # reindexar al AÑO DE RENTA (encuesta t -> renta t-1)
    serie.index = serie.index - 1
    s[key + "_nominal_anyorenta"] = serie
    s[key + "_real_e2018_anyorenta"] = defl(serie)

# --- AROPE (tabla 74860), etiquetado por año de encuesta --------------------
a = load_tempus(os.path.join(RAW, "arope_europa2030_tipo_hogar.json"))
s["arope_pct_encuesta"] = a[a["Tipo de hogar"] == "Total"].set_index("anyo")["valor"].sort_index()
s["arope_monoparental_pct_encuesta"] = a[a["Tipo de hogar"] == "1 adulto con 1 ó más niños dependientes"] \
    .set_index("anyo")["valor"].sort_index()

# --- Vivienda: IPV (tabla 25173), índice base 2015 = 100 --------------------
i = load_tempus(os.path.join(RAW, "ipv_media_anual_ccaa_tipo_vivienda_base2015.json"))
inac = i[i["Comunidades y Ciudades Autónomas"].isna() & (i["Índices y Tasas"] == "Media anual")]
ipv = inac[inac["General, vivienda nueva y de segunda mano"] == "General"].set_index("anyo")["valor"].sort_index()
s["ipv_general_idx2015"] = ipv
s["ipv_real_e2018_idx"] = defl(ipv) / defl(ipv).loc[2018] * 100   # IPV deflactado, 2018 = 100

# --- Hipotecas (tabla 76317), suma anual nacional sobre viviendas -----------
h = load_tempus(os.path.join(RAW, "hipotecas_total_fincas_nacional_provincias.json"))
hn = h[h["Provincias"].isna() & (h["Naturaleza de la finca"] == "Viviendas")]
num = hn[hn["Concepto financiero"] == "Número de hipotecas"].groupby("anyo")["valor"].agg(["sum", "count"])
imp = hn[hn["Concepto financiero"] == "Importe de hipotecas"].groupby("anyo")["valor"].agg(["sum", "count"])
full = num[num["count"] == 12].index.intersection(imp[imp["count"] == 12].index)
s["hipotecas_viviendas_numero"] = num.loc[full, "sum"]
s["hipotecas_importe_medio_eur"] = (imp.loc[full, "sum"] * 1000) / num.loc[full, "sum"]
s["hipotecas_importe_medio_real_e2018"] = defl(s["hipotecas_importe_medio_eur"])

hp = load_tempus(os.path.join(RAW, "hipotecas_plazo_medio.json"))
hpv = hp[hp["Naturaleza de la finca"] == "Viviendas"].groupby("anyo")["valor"].agg(["mean", "count"])
s["hipoteca_plazo_medio_anyos"] = hpv.loc[hpv["count"] == 12, "mean"]

# --- Gasto medio EPF (tabla 25198), serie homogénea hasta 2023 --------------
e = load_tempus(os.path.join(RAW, "epf_gasto_medio_hogar_persona_detalle_coicop.json"))
cols = [c for c in e.columns if "Grupos" in c or "COICOP" in c or "Gasto" in c or "Tipo" in c]
e_tot = e[(e.get("Tipo de gasto", pd.Series(index=e.index)).isna()) | True]
gasto = None
for cand in ["Gasto total", "Total", "TOTAL"]:
    for col in e.columns:
        if e[col].dtype == object and (e[col] == cand).any():
            sel = e[(e[col] == cand)]
            if "Tipo de dato" in e.columns:
                sel2 = sel[sel["Tipo de dato"].astype(str).str.contains("hogar", case=False, na=False)]
                if len(sel2):
                    sel = sel2
            gasto = sel
            break
    if gasto is not None:
        break

df = pd.DataFrame(s)
df.index.name = "anyo"
df.to_csv(os.path.join(OUT, "d_precios.csv"))
pd.set_option("display.width", 300); pd.set_option("display.max_columns", 60)
print(df.round(2).to_string())

print("\n--- IPC por grupos: media anual 2018 vs 2025 ---")
comp = pd.DataFrame({"2018": grupos.loc[2018], "2025": grupos.loc[2025]})
comp["var_%"] = (comp["2025"] / comp["2018"] - 1) * 100
print(comp.round(2).sort_values("var_%", ascending=False).to_string())
