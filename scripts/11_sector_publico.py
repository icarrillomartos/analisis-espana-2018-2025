# -*- coding: utf-8 -*-
"""Bloque F: sector público. Ingresos, gasto por función, prestaciones sociales,
déficit y deuda; descomposición del origen del aumento de ingresos.
Salida: data_processed/f_sector_publico.csv y outputs/sector_publico.json
"""
import os, sys, json, math
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT = os.path.join(ROOT, "data_external")
PROC = os.path.join(ROOT, "data_processed")
OUTD = os.path.join(ROOT, "outputs")

COF = json.load(open(os.path.join(EXT, "cofog_etiquetas.json"), encoding="utf-8"))
SUB = {"GF1001": "Enfermedad e incapacidad", "GF1002": "Vejez (pensiones de jubilación)",
       "GF1003": "Supervivencia (viudedad y orfandad)", "GF1004": "Familia e hijos",
       "GF1005": "Desempleo", "GF1006": "Vivienda social",
       "GF1007": "Exclusión social (incluye el Ingreso Mínimo Vital)",
       "GF1008": "I+D en protección social", "GF1009": "Protección social no clasificada"}
NOM = {"EU27_2020": "UE-27", "ES": "España", "DE": "Alemania", "FR": "Francia",
       "IT": "Italia", "PT": "Portugal"}

m = pd.read_csv(os.path.join(EXT, "eurostat_gov_main_meur.csv"))
pg = pd.read_csv(os.path.join(EXT, "eurostat_gov_main_pcgdp.csv"))
cm = pd.read_csv(os.path.join(EXT, "eurostat_gov_cofog_meur.csv"))
cg = pd.read_csv(os.path.join(EXT, "eurostat_gov_cofog_pcgdp.csv"))
cs = pd.read_csv(os.path.join(EXT, "eurostat_gov_cofog_social_meur.csv"))
dd = pd.read_csv(os.path.join(EXT, "eurostat_gov_deuda.csv"))

M = m[m.geo == "ES"].pivot(index="na_item", columns="anyo", values="valor")
P = pg[pg.geo == "ES"].pivot(index="na_item", columns="anyo", values="valor")
C = cm[cm.geo == "ES"].pivot(index="cofog99", columns="anyo", values="valor")
CG = cg[cg.geo == "ES"].pivot(index="cofog99", columns="anyo", values="valor")
S = cs[cs.geo == "ES"].pivot(index="cofog99", columns="anyo", values="valor")
D = dd[dd.geo == "ES"].pivot(index="unit", columns="anyo", values="valor")

# Deflactores nacionales ya calculados en el pipeline español
IPC = pd.read_csv(os.path.join(PROC, "d_precios.csv"), index_col=0)["ipc_general_media_anual"]
POB = pd.read_csv(os.path.join(PROC, "a_demografia.csv"), index_col=0)["pob_total"]
B = pd.read_csv(os.path.join(PROC, "b_economia.csv"), index_col=0)

tab = pd.DataFrame(index=range(2018, 2025))
tab["ingresos_meur"] = M.loc["TR"]
tab["gastos_meur"] = M.loc["TE"]
tab["saldo_meur"] = M.loc["B9"]
tab["ingresos_pct_pib"] = P.loc["TR"]
tab["gastos_pct_pib"] = P.loc["TE"]
tab["saldo_pct_pib"] = P.loc["B9"]
tab["imp_renta_patrimonio_meur"] = M.loc["D5REC"]
tab["imp_produccion_meur"] = M.loc["D2REC"]
tab["cotizaciones_meur"] = M.loc["D61REC"]
tab["imp_renta_patrimonio_pct_pib"] = P.loc["D5REC"]
tab["deuda_meur"] = D.loc["MIO_EUR"]
tab["deuda_pct_pib"] = D.loc["PC_GDP"]
for k, lab in COF.items():
    tab["gasto_" + k] = C.loc[k]
    tab["gastopct_" + k] = CG.loc[k]
for k in SUB:
    if k in S.index:
        tab["social_" + k] = S.loc[k]
# reales por habitante, en euros de 2018
for col in ["ingresos_meur", "gasto_GF10", "gasto_GF07", "gasto_GF09", "gasto_TOTAL"]:
    tab[col + "_real_pc"] = (tab[col] * 1e6 * IPC.loc[2018] / IPC.reindex(tab.index)) / POB.reindex(tab.index)
tab.index.name = "anyo"
tab.to_csv(os.path.join(PROC, "f_sector_publico.csv"))

# --------- descomposición del aumento de ingresos ---------------------------
tr0, tr1 = M.loc["TR", 2018], M.loc["TR", 2024]
g_real = B.pib_volumen_idx2020[2024] / B.pib_volumen_idx2020[2018]
defl = ((B.pib_nominal_meur[2024] / B.pib_volumen_idx2020[2024])
        / (B.pib_nominal_meur[2018] / B.pib_volumen_idx2020[2018]))
ratio = P.loc["TR", 2024] / P.loc["TR", 2018]
L = math.log(tr1 / tr0)
R = {"ingresos_2018": float(tr0), "ingresos_2024": float(tr1), "delta": float(tr1 - tr0),
     "var_pct": float((tr1 / tr0 - 1) * 100),
     "identidad_check": float(g_real * defl * ratio),
     "componentes": [
         {"nombre": "Economía real más grande", "factor_pct": (g_real - 1) * 100,
          "cuota": math.log(g_real) / L * 100, "euros": float((tr1 - tr0) * math.log(g_real) / L)},
         {"nombre": "Subida de precios", "factor_pct": (defl - 1) * 100,
          "cuota": math.log(defl) / L * 100, "euros": float((tr1 - tr0) * math.log(defl) / L)},
         {"nombre": "Mayor porcentaje del PIB detraído", "factor_pct": (ratio - 1) * 100,
          "cuota": math.log(ratio) / L * 100, "euros": float((tr1 - tr0) * math.log(ratio) / L)}]}

ipcf = IPC.loc[2024] / IPC.loc[2018]
pobf = POB.loc[2024] / POB.loc[2018]
real = lambda a, b: {"nom_pct": (b / a - 1) * 100, "real_pct": ((b / a) / ipcf - 1) * 100,
                     "real_pc_pct": ((b / a) / ipcf / pobf - 1) * 100}
R["reales"] = {"ingresos": real(tr0, tr1),
               "proteccion_social": real(C.loc["GF10", 2018], C.loc["GF10", 2024]),
               "sanidad": real(C.loc["GF07", 2018], C.loc["GF07", 2024]),
               "educacion": real(C.loc["GF09", 2018], C.loc["GF09", 2024]),
               "gasto_total": real(C.loc["TOTAL", 2018], C.loc["TOTAL", 2024])}

# --------- prestaciones sociales por subfunción -----------------------------
d_ps = C.loc["GF10", 2024] - C.loc["GF10", 2018]
R["proteccion_social_detalle"] = sorted(
    [{"concepto": SUB[k], "v2018": float(S.loc[k, 2018]), "v2024": float(S.loc[k, 2024]),
      "delta": float(S.loc[k, 2024] - S.loc[k, 2018]),
      "var_pct": (S.loc[k, 2024] / S.loc[k, 2018] - 1) * 100 if S.loc[k, 2018] else None,
      "cuota_del_aumento": (S.loc[k, 2024] - S.loc[k, 2018]) / d_ps * 100,
      "pct_del_total_2024": S.loc[k, 2024] / C.loc["GF10", 2024] * 100}
     for k in SUB if k in S.index and S.loc[k, 2018] > 0],
    key=lambda x: -x["v2024"])
R["proteccion_social_total"] = {"v2018": float(C.loc["GF10", 2018]), "v2024": float(C.loc["GF10", 2024]),
                                "delta": float(d_ps)}

# --------- comparación europea ---------------------------------------------
comp = []
for g, lab in NOM.items():
    Pg = pg[pg.geo == g].pivot(index="na_item", columns="anyo", values="valor")
    Cgg = cg[cg.geo == g].pivot(index="cofog99", columns="anyo", values="valor")
    Dg = dd[(dd.geo == g) & (dd.unit == "PC_GDP")].set_index("anyo")["valor"]
    comp.append({"pais": lab, "geo": g,
                 "ing2018": float(Pg.loc["TR", 2018]), "ing2024": float(Pg.loc["TR", 2024]),
                 "ing_dif": float(Pg.loc["TR", 2024] - Pg.loc["TR", 2018]),
                 "ps2018": float(Cgg.loc["GF10", 2018]), "ps2024": float(Cgg.loc["GF10", 2024]),
                 "san2024": float(Cgg.loc["GF07", 2024]),
                 "saldo2024": float(Pg.loc["B9", 2024]),
                 "deuda2018": float(Dg[2018]), "deuda2024": float(Dg[2024])})
R["comparativa_fiscal_europa"] = comp

json.dump(R, open(os.path.join(OUTD, "sector_publico.json"), "w"), ensure_ascii=False, indent=1)
print("f_sector_publico.csv y sector_publico.json escritos")
print(f"ingresos +{R['var_pct']:.1f} % | componentes:",
      [f"{c['nombre']}: {c['cuota']:.0f} %" for c in R["componentes"]])
print("protección social real por habitante:", f"{R['reales']['proteccion_social']['real_pc_pct']:+.1f} %")
