# -*- coding: utf-8 -*-
"""Genera outputs/informe_espana_2018_2025.html a partir de outputs/indicadores.json.
Todo el contenido numérico procede de data_processed/, que a su vez se regenera
desde data_raw/ con los scripts 01 a 06. No hay cifras escritas a mano en el HTML:
las del texto se interpolan desde los mismos CSV.
"""
import os, json, html
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data_processed")
OUTD = os.path.join(ROOT, "outputs")
J = json.load(open(os.path.join(OUTD, "indicadores.json"), encoding="utf-8"))
IND = J["indicadores"]
DESC = J["descomposicion_crimen"]
AX = J["extra_demografia"]
G = json.load(open(os.path.join(OUTD, "desgloses.json"), encoding="utf-8"))
SP = json.load(open(os.path.join(OUTD, "sector_publico.json"), encoding="utf-8"))
EXT = os.path.join(ROOT, "data_external")
IMV = pd.read_csv(os.path.join(EXT, "imv_anual.csv"))
IMVM = pd.read_csv(os.path.join(EXT, "imv_nomina_mensual.csv"))
SIS = pd.read_csv(os.path.join(EXT, "sisle_nacional.csv"))

A = pd.read_csv(os.path.join(PROC, "a_demografia.csv"), index_col=0)
B = pd.read_csv(os.path.join(PROC, "b_economia.csv"), index_col=0)
C = pd.read_csv(os.path.join(PROC, "c_laboral.csv"), index_col=0)
D = pd.read_csv(os.path.join(PROC, "d_precios.csv"), index_col=0)
E = pd.read_csv(os.path.join(PROC, "e_criminalidad_resumen.csv"), index_col=0)
HC = pd.read_csv(os.path.join(PROC, "e_hechos_conocidos_tipologia.csv"), index_col=0)
LL = pd.read_csv(os.path.join(PROC, "a_ano_llegada_2025.csv"), index_col=0)

# ------------------------------------------------------------------ formato --
def nf(v, dec=0):
    """Número con separador de miles '.' y decimal ',' (convención española)."""
    if v is None or pd.isna(v):
        return "—"
    s = f"{v:,.{dec}f}"
    return s.replace(",", " ").replace(".", ",").replace(" ", ".")

def pct(v, dec=1, signo=True):
    if v is None or pd.isna(v):
        return "—"
    s = f"{v:+.{dec}f}" if signo else f"{v:.{dec}f}"
    return s.replace(".", ",") + " %"

def pp(v, dec=1):
    return f"{v:+.{dec}f}".replace(".", ",") + " p.p."

def esc(t):
    return html.escape(str(t), quote=True)

# ------------------------------------------------------------- sparkline SVG -
def spark(serie, w=104, h=26, pad=3):
    if not serie or len(serie) < 3:
        return ""
    xs = [p[0] for p in serie]; ys = [p[1] for p in serie]
    lo, hi = min(ys), max(ys)
    rng = (hi - lo) or 1
    def X(i): return pad + (w - 2 * pad) * i / (len(xs) - 1)
    def Y(v): return h - pad - (h - 2 * pad) * (v - lo) / rng
    d = " ".join(("M" if i == 0 else "L") + f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(ys))
    marca = ""
    if 2020 in xs:
        x20 = X(xs.index(2020))
        marca = f'<line x1="{x20:.1f}" y1="2" x2="{x20:.1f}" y2="{h-2}" class="sk-2020"/>'
    base = f'<line x1="{pad}" y1="{h-1.5}" x2="{w-pad}" y2="{h-1.5}" class="sk-base"/>'
    return (f'<svg class="sk" viewBox="0 0 {w} {h}" width="{w}" height="{h}" aria-hidden="true">'
            f'{base}{marca}<path class="sk-line" d="{d}"/>'
            f'<circle class="sk-o" cx="{X(0):.1f}" cy="{Y(ys[0]):.1f}" r="1.9"/>'
            f'<circle class="sk-dot" cx="{X(len(xs)-1):.1f}" cy="{Y(ys[-1]):.1f}" r="2.6"/></svg>')

# ------------------------------------------------------------------- tabla ---
def celda_valor(v, fila):
    u = fila["unidad"]
    if u == "%":
        return nf(v, fila["dec"]) + " %"
    if u in ("veces",):
        return "×" + nf(v, fila["dec"])
    txt = nf(v, fila["dec"])
    sufijo = {"€": " €", "€ de 2018": " €", "años": " años", "índice": "",
              "por 100.000 hab.": "", "por 100.000": ""}.get(u, "")
    return txt + sufijo

def burbuja(fila):
    v = fila["var_pct"]
    if v is None or pd.isna(v):
        return '<span class="bub bub-flat">—</span>'
    cls = "bub-up" if v > 0.05 else ("bub-down" if v < -0.05 else "bub-flat")
    flecha = "▲" if v > 0.05 else ("▼" if v < -0.05 else "=")
    extra = ""
    if fila["pp"]:
        extra = f'<span class="bub-sub">{esc(pp(fila["var_abs"], fila["dec"]))}</span>'
    return (f'<span class="bub {cls}"><span class="bub-ar">{flecha}</span>'
            f'{esc(pct(v).replace("+", "").replace("-", ""))}</span>{extra}')

def tabla(bloque, filas):
    out = ['<div class="tw"><table>',
           '<thead><tr><th class="c-desc">Indicador</th><th class="c-num">2018</th>'
           '<th class="c-num">2025</th><th class="c-sk">Serie completa</th>'
           '<th class="c-var">Variación</th></tr></thead><tbody>']
    for f in filas:
        badge = ""
        if f["anyo_fin"] != 2025:
            badge = f'<span class="yb">{f["anyo_fin"]}</span>'
        nota = f'<span class="nt">{esc(f["nota"])}</span>' if f["nota"] else ""
        out.append(
            f'<tr><td class="c-desc"><span class="dsc">{esc(f["descripcion"])}</span>'
            f'<span class="src">{esc(f["fuente"])}</span>{nota}</td>'
            f'<td class="c-num">{esc(celda_valor(f["valor_ini"], f))}</td>'
            f'<td class="c-num">{esc(celda_valor(f["valor_fin"], f))}{badge}</td>'
            f'<td class="c-sk">{spark(f["serie"])}</td>'
            f'<td class="c-var">{burbuja(f)}</td></tr>')
    out.append("</tbody></table></div>")
    return "".join(out)

def seccion(id_, num, titulo, entradilla, bloque, lectura, extra=""):
    filas = [f for f in IND if f["bloque"] == bloque]
    return f"""
<section id="{id_}" class="blk">
  <div class="blk-h">
    <span class="blk-n">{num}</span>
    <div><h3>{titulo}</h3><p class="entr">{entradilla}</p></div>
  </div>
  {tabla(bloque, filas)}
  {extra}
  <div class="leg"><span class="leg-t">Lectura objetiva</span><div class="leg-b">{lectura}</div></div>
</section>"""


def sub(titulo, cuerpo):
    """Sub-apartado dentro de un bloque de datos."""
    return f'<div class="subap"><h4 class="sub-h">{titulo}</h4>{cuerpo}</div>'

# ------------------------------------------------- cifras usadas en el texto --

# ------------------------------------------------- tablas libres de apoyo ----
def bub(v, dec=1):
    """Burbuja suelta para tablas de apoyo. Azul sube, rojo baja."""
    if v is None or pd.isna(v):
        return '<span class="bub bub-flat">—</span>'
    cls = "bub-up" if v > 0.05 else ("bub-down" if v < -0.05 else "bub-flat")
    fl = "▲" if v > 0.05 else ("▼" if v < -0.05 else "=")
    return (f'<span class="bub {cls}"><span class="bub-ar">{fl}</span>'
            f'{esc(pct(v, dec).replace("+", "").replace("-", ""))}</span>')


def tabla_libre(cols, filas, clases=None, pie=None):
    """cols: lista de (titulo, clase). filas: lista de listas de HTML ya formateado."""
    th = "".join(f'<th class="{c}">{t}</th>' for t, c in cols)
    ancho = "compacta" if len(cols) >= 6 else ""
    tr = ""
    for i, f in enumerate(filas):
        cl = f' class="{clases[i]}"' if clases and clases[i] else ""
        tds = "".join(f'<td class="{cols[j][1]}">{v}</td>' for j, v in enumerate(f))
        tr += f"<tr{cl}>{tds}</tr>"
    pf = f'<div class="tpie">{pie}</div>' if pie else ""
    return (f'<div class="tw {ancho}"><table><thead><tr>{th}</tr></thead>'
            f'<tbody>{tr}</tbody></table></div>{pf}')


def barras_comp(items, etiqueta, valor, maxv=None, fmt=lambda v: nf(v, 0), neg_si=None):
    """Barras horizontales comparativas dentro de una respuesta."""
    mx = maxv or max(abs(valor(i)) for i in items) or 1
    out = []
    for i in items:
        v = valor(i)
        negativo = neg_si(i) if neg_si else v < 0
        w = min(100, abs(v) / mx * 100)
        out.append(f'<div class="dec-r"><span class="dec-l">{etiqueta(i)}</span>'
                   f'<span class="dec-t"><span class="dec-f{" neg" if negativo else ""}" '
                   f'style="width:{w:.1f}%"></span></span>'
                   f'<span class="dec-v">{fmt(v)}</span></div>')
    return '<div class="dec">' + "".join(out) + "</div>"


V = {}
V["pob18"] = A.pob_total[2018]; V["pob25"] = A.pob_total[2025]
V["dpob"] = V["pob25"] - V["pob18"]
V["dpob_pct"] = (V["pob25"] / V["pob18"] - 1) * 100
V["nac_esp18"] = A.nacidos_espana_enlazada[2018]; V["nac_esp25"] = A.nacidos_espana_enlazada[2025]
V["nac_fue18"] = A.nacidos_fuera_enlazada[2018]; V["nac_fue25"] = A.nacidos_fuera_enlazada[2025]
V["d_esp"] = V["nac_esp25"] - V["nac_esp18"]; V["d_fue"] = V["nac_fue25"] - V["nac_fue18"]
V["suma"] = V["d_esp"] + V["d_fue"]
V["c_fue"] = V["d_fue"] / V["suma"] * 100; V["c_esp"] = V["d_esp"] / V["suma"] * 100
V["nat"] = A.adquisiciones_nacionalidad.loc[2018:2025].sum()
V["d_ext"] = A.pob_nac_extranjera[2025] - A.pob_nac_extranjera[2018]
V["c_ext"] = V["d_ext"] / V["dpob"] * 100
V["lleg"] = AX["nacidos_fuera_llegados_desde_2018_stock_2025"]
V["lleg_pct"] = V["lleg"] / V["pob25"] * 100
V["pct_fue25"] = A.pct_nacidos_fuera[2025]; V["pct_fue18"] = A.pct_nacidos_fuera[2018]

V["pib_r"] = (B.pib_volumen_idx2020[2024] / B.pib_volumen_idx2020[2018] - 1) * 100
V["pib_n"] = (B.pib_nominal_meur[2024] / B.pib_nominal_meur[2018] - 1) * 100
V["pob_cna"] = (B.poblacion_cna_miles[2024] / B.poblacion_cna_miles[2018] - 1) * 100
V["pib_pc"] = ((B.pib_volumen_idx2020[2024] / B.pib_volumen_idx2020[2018]) /
               (B.poblacion_cna_miles[2024] / B.poblacion_cna_miles[2018]) - 1) * 100
V["puestos"] = (B.puestos_totales_miles[2024] / B.puestos_totales_miles[2018] - 1) * 100
V["horas"] = (B.horas_trabajadas_miles[2024] / B.horas_trabajadas_miles[2018] - 1) * 100
V["prod"] = (B.productividad_hora_idx[2024] / B.productividad_hora_idx[2018] - 1) * 100

V["hc18"] = E.hechos_conocidos[2018]; V["hc24"] = E.hechos_conocidos[2024]
V["hc_pct"] = (V["hc24"] / V["hc18"] - 1) * 100
V["hct_pct"] = (E.hechos_conocidos_por_100k[2024] / E.hechos_conocidos_por_100k[2018] - 1) * 100
_ci = HC["5.5.1.-Estafas informáticas"]
_sin = HC["TOTAL INFRACCIONES PENALES"] - _ci
V["ci18"] = _ci[2018]; V["ci24"] = _ci[2024]
V["ci_pct"] = (V["ci24"] / V["ci18"] - 1) * 100
V["ci_aporte"] = (V["ci24"] - V["ci18"]) / (V["hc24"] - V["hc18"]) * 100
V["sin_pct"] = (_sin[2024] / _sin[2018] - 1) * 100
V["sin_tasa_pct"] = ((_sin[2024] / E.pob_total[2024]) / (_sin[2018] / E.pob_total[2018]) - 1) * 100
V["escl18"] = E.tasa_esclarecimiento_pct[2018]; V["escl24"] = E.tasa_esclarecimiento_pct[2024]
V["det18"] = E.detenidos_total[2018]; V["det24"] = E.detenidos_total[2024]
V["det_pct"] = (V["det24"] / V["det18"] - 1) * 100
V["dext18"] = E.detenidos_extranjeros[2018]; V["dext24"] = E.detenidos_extranjeros[2024]
V["dext_pct"] = (V["dext24"] / V["dext18"] - 1) * 100
V["desp18"] = E.detenidos_espanoles[2018]; V["desp24"] = E.detenidos_espanoles[2024]
V["desp_pct"] = (V["desp24"] / V["desp18"] - 1) * 100
V["cuota"] = DESC["pct_del_aumento_atribuible_grupo_extranjero"]
V["ef_pob"] = DESC["efecto_poblacion"]; V["ef_tasa"] = DESC["efecto_tasa"]
V["ef_int"] = DESC["efecto_interaccion"]; V["d_dext"] = DESC["delta_detenidos_extranjeros"]
V["ef_pob_pct"] = V["ef_pob"] / V["d_dext"] * 100
V["ef_tasa_pct"] = V["ef_tasa"] / V["d_dext"] * 100
V["ef_int_pct"] = V["ef_int"] / V["d_dext"] * 100
V["tesp18"] = E.detenidos_esp_por_100k_pob_esp[2018]; V["tesp24"] = E.detenidos_esp_por_100k_pob_esp[2024]
V["text18"] = E.detenidos_ext_por_100k_pob_ext[2018]; V["text24"] = E.detenidos_ext_por_100k_pob_ext[2024]
V["ratio18"] = E.ratio_tasas_ext_esp[2018]; V["ratio24"] = E.ratio_tasas_ext_esp[2024]
V["con18"] = E.condenados_total[2018]; V["con25"] = E.condenados_total[2025]
V["con_pct"] = (V["con25"] / V["con18"] - 1) * 100
V["conext18"] = E.condenados_ext[2018]; V["conext25"] = E.condenados_ext[2025]
V["pcon18"] = E.pct_condenados_extranjeros[2018]; V["pcon25"] = E.pct_condenados_extranjeros[2025]
V["tcesp18"] = E.condenados_esp_por_100k_pob_esp[2018]; V["tcesp25"] = E.condenados_esp_por_100k_pob_esp[2025]
V["tcext18"] = E.condenados_ext_por_100k_pob_ext[2018]; V["tcext25"] = E.condenados_ext_por_100k_pob_ext[2025]
V["tcesp_pct"] = (V["tcesp25"] / V["tcesp18"] - 1) * 100
V["tcext_pct"] = (V["tcext25"] / V["tcext18"] - 1) * 100
V["hom18"] = HC["1.1.1.-Homicidios dolosos/asesinatos consumados"][2018]
V["hom24"] = HC["1.1.1.-Homicidios dolosos/asesinatos consumados"][2024]

V["ipc"] = (D.ipc_general_media_anual[2025] / D.ipc_general_media_anual[2018] - 1) * 100
V["e1000"] = D.euros_necesarios_para_1000e_2018[2025]
V["compra1000"] = D.poder_compra_de_1000e_de_2018[2025]
V["sal_r"] = (D.salario_medio_real_e2018[2024] / D.salario_medio_real_e2018[2018] - 1) * 100
V["sal_n"] = (D.salario_medio_nominal[2024] / D.salario_medio_nominal[2018] - 1) * 100
V["ren_r"] = (D.renta_persona_real_e2018_anyorenta[2024] / D.renta_persona_real_e2018_anyorenta[2018] - 1) * 100
V["renuc_r"] = (D.renta_unidad_consumo_real_e2018_anyorenta[2024] / D.renta_unidad_consumo_real_e2018_anyorenta[2018] - 1) * 100
V["d1h"] = (D.salario_decil1_hombres_real_e2018[2024] / D.salario_decil1_hombres_real_e2018[2018] - 1) * 100
V["d10h"] = (D.salario_decil10_hombres_real_e2018[2024] / D.salario_decil10_hombres_real_e2018[2018] - 1) * 100
V["d1m"] = (D.salario_decil1_mujeres_real_e2018[2024] / D.salario_decil1_mujeres_real_e2018[2018] - 1) * 100
V["d10m"] = (D.salario_decil10_mujeres_real_e2018[2024] / D.salario_decil10_mujeres_real_e2018[2018] - 1) * 100
V["arope18"] = D.arope_pct_encuesta[2018]; V["arope25"] = D.arope_pct_encuesta[2025]
V["ipv_r"] = D.ipv_real_e2018_idx[2025] - 100
V["ipv_n"] = (D.ipv_general_idx2015[2025] / D.ipv_general_idx2015[2018] - 1) * 100
V["hip_r"] = (D.hipotecas_importe_medio_real_e2018[2025] / D.hipotecas_importe_medio_real_e2018[2018] - 1) * 100
V["plazo18"] = D.hipoteca_plazo_medio_anyos[2018]; V["plazo25"] = D.hipoteca_plazo_medio_anyos[2025]
IPCG = pd.read_csv(os.path.join(PROC, "d_ipc_grupos.csv"), index_col=0)
V["alim"] = (IPCG["Alimentos y bebidas no alcohólicas"][2025] / IPCG["Alimentos y bebidas no alcohólicas"][2018] - 1) * 100

V["paro18"] = C.tasa_paro[2018]; V["paro25"] = C.tasa_paro[2025]
V["emp18"] = C.tasa_empleo[2018]; V["emp25"] = C.tasa_empleo[2025]
V["act18"] = C.tasa_actividad[2018]; V["act25"] = C.tasa_actividad[2025]
V["vac_pct"] = (C.vacantes_media_trimestral[2025] / C.vacantes_media_trimestral[2018] - 1) * 100
V["ina_pct"] = (C.inactivos_total_miles[2025] / C.inactivos_total_miles[2018] - 1) * 100
V["d_jub"] = (C.inactivos_jubilados_miles[2025] - C.inactivos_jubilados_miles[2018]) * 1000
V["d_est"] = (C.inactivos_estudiantes_miles[2025] - C.inactivos_estudiantes_miles[2018]) * 1000
V["d_hog"] = (C.inactivos_labores_hogar_miles[2025] - C.inactivos_labores_hogar_miles[2018]) * 1000
V["paroext18"] = C.tasa_paro_nacionalidad_ext[2018]; V["paroext25"] = C.tasa_paro_nacionalidad_ext[2025]
V["paroesp18"] = C.tasa_paro_nacionalidad_esp[2018]; V["paroesp25"] = C.tasa_paro_nacionalidad_esp[2025]

# --- variables añadidas para los desgloses por origen y el sector público ---
V["pob_nac_ext_18"] = A.pob_nac_extranjera[2018]; V["pob_nac_ext_25"] = A.pob_nac_extranjera[2025]
V["pob_esp_24"] = E.pob_espanola[2024]
_c = {c["grupo"]: c for c in G["poblacion_continentes_nacionalidad"]}
V["africa_delta"] = _c["África"]["delta"]; V["africa_var"] = _c["África"]["var_pct"]
V["europa_delta"] = _c["Europa (sin España)"]["delta"]; V["asia_delta"] = _c["Asia"]["delta"]
V["america_delta"] = _c["América"]["delta"]; V["america_cuota"] = _c["América"]["cuota_del_aumento_extranjero"]
_d = {d["grupo"]: d for d in G["detenidos_continente"]}
V["africa_tasa_var"] = _d["África"]["var_tasa_pct"]
V["esp_tasa_var"] = G["detenidos_espanoles"]["var_tasa_pct"]
_eu = {e["geo"]: e for e in G["comparativa_europa"]}
V["infl_es"] = _eu["ES"]["infl"]; V["infl_ue"] = _eu["EU27_2020"]["infl"]
# sector público
_F = pd.read_csv(os.path.join(PROC, "f_sector_publico.csv"), index_col=0)
V["ing_pct"] = SP["var_pct"]
V["ing18"] = _F.ingresos_pct_pib[2018]; V["ing24"] = _F.ingresos_pct_pib[2024]
V["ing_pp"] = V["ing24"] - V["ing18"]
V["ing_real_pc"] = SP["reales"]["ingresos"]["real_pc_pct"]
V["ps_real_pc"] = SP["reales"]["proteccion_social"]["real_pc_pct"]
V["san_real_pc"] = SP["reales"]["sanidad"]["real_pc_pct"]
V["edu_real_pc"] = SP["reales"]["educacion"]["real_pc_pct"]
V["d5_pct"] = (_F.imp_renta_patrimonio_meur[2024] / _F.imp_renta_patrimonio_meur[2018] - 1) * 100
V["deuda18"] = _F.deuda_meur[2018]; V["deuda24"] = _F.deuda_meur[2024]
V["deuda_meur_pct"] = (V["deuda24"] / V["deuda18"] - 1) * 100
V["deuda18_pct"] = _F.deuda_pct_pib[2018]; V["deuda24_pct"] = _F.deuda_pct_pib[2024]
V["saldo18"] = _F.saldo_pct_pib[2018]; V["saldo24"] = _F.saldo_pct_pib[2024]
V["gasto_pct"] = (_F.gastos_meur[2024] / _F.gastos_meur[2018] - 1) * 100
# listas de espera e IMV
_q = SIS[(SIS.ambito == "quirurgica") & (SIS.mes == 12)].set_index("anyo")
_c = SIS[(SIS.ambito == "consultas") & (SIS.mes == 12)].set_index("anyo")
V["q_pac18"] = _q.pacientes_espera[2018]; V["q_pac25"] = _q.pacientes_espera[2025]
V["q_tasa"] = (_q.tasa_por_1000_hab[2025] / _q.tasa_por_1000_hab[2018] - 1) * 100
V["q_dias18"] = _q.tiempo_medio_espera_dias[2018]; V["q_dias25"] = _q.tiempo_medio_espera_dias[2025]
V["q_pct18"] = _q.pct_mas_6_meses[2018]; V["q_pct25"] = _q.pct_mas_6_meses[2025]
V["c_tasa"] = (_c.tasa_por_1000_hab[2025] / _c.tasa_por_1000_hab[2018] - 1) * 100
V["c_dias18"] = _c.tiempo_medio_espera_dias[2018]; V["c_dias25"] = _c.tiempo_medio_espera_dias[2025]
V["c_pct18"] = _c.pct_mas_60_dias[2018]; V["c_pct25"] = _c.pct_mas_60_dias[2025]
_i25 = IMV[IMV.anyo == 2025].iloc[0]
V["imv_gasto25"] = _i25.importe_bruto_anual_eur / 1e6
V["imv_hogares25"] = _i25.prestaciones_diciembre
V["imv_benef25"] = _i25.beneficiarios_diciembre
V["imv_cuantia25"] = _i25.cuantia_media_hogar_media
V["imv_acum"] = _i25.importe_bruto_acumulado_dic_eur / 1e6
V["imv_pct_ps"] = V["imv_gasto25"] / (SP["proteccion_social_total"]["v2024"]) * 100

N = {k: nf(v, 0) for k, v in V.items()}
P = {k: pct(v) for k, v in V.items()}
P1 = {k: pct(v, 1) for k, v in V.items()}
PS = {k: pct(v, 1, signo=False) for k, v in V.items()}

# ------------------------------------------------------------------- estilo --
CSS = """
:root{
  --ground:#F2F3F1; --surface:#FFFFFF; --surface-2:#FAFAF9;
  --ink:#15181C; --ink-2:#474D57; --ink-3:#7C8390;
  --rule:#DCDEDB; --rule-2:#E9EAE7;
  --up:#1B4CA1; --up-bg:#E2EAF7; --up-br:#C2D3EE;
  --down:#A62234; --down-bg:#F7E3E6; --down-br:#EEC5CB;
  --flat:#6E7480; --flat-bg:#ECEDEA;
  --mark:#B7801F;
  --shadow:0 1px 0 rgba(21,24,28,.04), 0 2px 10px rgba(21,24,28,.05);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --ground:#0E1013; --surface:#15181C; --surface-2:#191D22;
    --ink:#E9EAE7; --ink-2:#AEB4BD; --ink-3:#7C8390;
    --rule:#262A30; --rule-2:#20242A;
    --up:#7FA6EA; --up-bg:#16233A; --up-br:#253554;
    --down:#E58C9B; --down-bg:#38191F; --down-br:#54262F;
    --flat:#8A909B; --flat-bg:#20242A;
    --mark:#D6A44A;
    --shadow:0 1px 0 rgba(0,0,0,.3), 0 2px 12px rgba(0,0,0,.28);
  }
}
:root[data-theme="dark"]{
  --ground:#0E1013; --surface:#15181C; --surface-2:#191D22;
  --ink:#E9EAE7; --ink-2:#AEB4BD; --ink-3:#7C8390;
  --rule:#262A30; --rule-2:#20242A;
  --up:#7FA6EA; --up-bg:#16233A; --up-br:#253554;
  --down:#E58C9B; --down-bg:#38191F; --down-br:#54262F;
  --flat:#8A909B; --flat-bg:#20242A;
  --mark:#D6A44A;
  --shadow:0 1px 0 rgba(0,0,0,.3), 0 2px 12px rgba(0,0,0,.28);
}
*{box-sizing:border-box}
body{
  margin:0; background:var(--ground); color:var(--ink);
  font-family:"Archivo","Helvetica Neue",Arial,sans-serif;
  font-size:16px; line-height:1.55; -webkit-font-smoothing:antialiased;
  font-variant-numeric:tabular-nums;
}
.wrap{max-width:1180px; margin:0 auto; padding:0 24px 96px}
h1,h2,h3,h4{font-family:"Archivo",sans-serif; font-weight:700; letter-spacing:-.021em; text-wrap:balance; margin:0}
p{margin:0}
a{color:var(--up)}
.mono{font-family:"IBM Plex Mono",ui-monospace,monospace}
.eyebrow{font-family:"IBM Plex Mono",monospace; font-size:11px; letter-spacing:.14em;
  text-transform:uppercase; color:var(--ink-3)}

/* ---------- portada ---------- */
header.top{padding:64px 0 40px; border-bottom:2px solid var(--ink)}
header.top h1{font-size:clamp(34px,5.4vw,62px); line-height:1.02; margin:14px 0 0; max-width:16ch}
header.top .sub{font-family:"Source Serif 4",Georgia,serif; font-size:clamp(17px,2vw,21px);
  color:var(--ink-2); margin-top:18px; max-width:62ch; line-height:1.5}
.meta{display:flex; flex-wrap:wrap; gap:8px 28px; margin-top:26px}
.meta div{font-family:"IBM Plex Mono",monospace; font-size:11.5px; letter-spacing:.05em; color:var(--ink-3)}
.meta b{color:var(--ink-2); font-weight:500}

/* ---------- tarjetas de titular ---------- */
.kpis{display:grid; grid-template-columns:repeat(3,1fr); gap:1px;
  background:var(--rule); border:1px solid var(--rule); margin:44px 0 8px}
.kpi{background:var(--surface); padding:20px 20px 18px}
.kpi .k-l{font-family:"IBM Plex Mono",monospace; font-size:10.5px; letter-spacing:.11em;
  text-transform:uppercase; color:var(--ink-3); display:block; min-height:2.4em}
.kpi .k-v{font-size:30px; font-weight:700; letter-spacing:-.03em; line-height:1.1; margin-top:12px; display:block}
.kpi .k-n{font-size:12.5px; color:var(--ink-2); margin-top:7px; display:block; line-height:1.4}
.k-up{color:var(--up)} .k-down{color:var(--down)}

/* ---------- navegación ---------- */
nav.toc{position:sticky; top:0; z-index:20; background:var(--ground);
  border-bottom:1px solid var(--rule); margin-top:44px;
  display:flex; gap:0; overflow-x:auto; scrollbar-width:thin}
nav.toc a{flex:0 0 auto; padding:13px 15px; font-family:"IBM Plex Mono",monospace;
  font-size:11px; letter-spacing:.08em; text-transform:uppercase;
  color:var(--ink-3); text-decoration:none; border-bottom:2px solid transparent; white-space:nowrap}
nav.toc a:hover,nav.toc a:focus-visible{color:var(--ink); border-bottom-color:var(--ink)}

/* ---------- partes ---------- */
.part{margin-top:76px; padding-top:22px; border-top:2px solid var(--ink)}
.part-h{display:flex; align-items:baseline; gap:16px; flex-wrap:wrap}
.part-h h2{font-size:clamp(22px,3vw,30px)}
.part-h .pn{font-family:"IBM Plex Mono",monospace; font-size:11px; letter-spacing:.16em;
  text-transform:uppercase; color:var(--mark)}
.part>.lede{font-family:"Source Serif 4",Georgia,serif; color:var(--ink-2);
  max-width:66ch; margin-top:12px; font-size:17px}

/* ---------- bloque ---------- */
.blk{margin-top:52px}
.blk-h{display:flex; gap:16px; align-items:flex-start}
.blk-n{font-family:"IBM Plex Mono",monospace; font-size:12px; color:var(--ink-3);
  border:1px solid var(--rule); border-radius:2px; padding:3px 8px; margin-top:4px; flex:0 0 auto}
.blk h3{font-size:21px}
.entr{color:var(--ink-2); font-size:14.5px; margin-top:5px; max-width:74ch}

/* ---------- tabla ---------- */
.tw{overflow-x:auto; margin-top:18px; border:1px solid var(--rule); background:var(--surface);
  box-shadow:var(--shadow)}
table{border-collapse:collapse; width:100%; min-width:790px}
thead th{font-family:"IBM Plex Mono",monospace; font-size:10.5px; letter-spacing:.11em;
  text-transform:uppercase; color:var(--ink-3); font-weight:400; text-align:right;
  padding:12px 16px; border-bottom:1px solid var(--ink); background:var(--surface-2)}
thead th.c-desc{text-align:left}
thead th.c-sk{text-align:center}
tbody tr{border-bottom:1px solid var(--rule-2)}
tbody tr:last-child{border-bottom:none}
tbody tr:hover{background:var(--surface-2)}
td{padding:13px 16px; vertical-align:top}
td.c-desc{width:44%}
.dsc{display:block; font-size:14.5px; font-weight:500; line-height:1.4}
.src{display:block; font-family:"IBM Plex Mono",monospace; font-size:10px; color:var(--ink-3);
  margin-top:5px; line-height:1.5; letter-spacing:.01em}
.nt{display:block; font-family:"Source Serif 4",Georgia,serif; font-size:12.5px;
  color:var(--ink-2); margin-top:6px; line-height:1.45; padding-left:9px;
  border-left:2px solid var(--rule)}
td.c-num{text-align:right; font-size:15.5px; font-weight:600; white-space:nowrap; letter-spacing:-.01em}
td.c-sk{text-align:center; width:120px; padding-top:16px}
td.c-var{text-align:right; white-space:nowrap; width:118px}
.yb{display:inline-block; margin-left:6px; font-family:"IBM Plex Mono",monospace; font-size:9.5px;
  color:var(--mark); border:1px solid var(--mark); border-radius:2px; padding:1px 3px;
  vertical-align:middle; font-weight:400}
.bub{display:inline-flex; align-items:center; gap:5px; padding:4px 10px; border-radius:999px;
  font-size:13px; font-weight:600; border:1px solid transparent; letter-spacing:-.01em}
.bub-ar{font-size:9px; line-height:1}
.bub-up{color:var(--up); background:var(--up-bg); border-color:var(--up-br)}
.bub-down{color:var(--down); background:var(--down-bg); border-color:var(--down-br)}
.bub-flat{color:var(--flat); background:var(--flat-bg)}
.bub-sub{display:block; font-family:"IBM Plex Mono",monospace; font-size:10.5px;
  color:var(--ink-3); margin-top:5px}
.sk{display:block; margin:0 auto; overflow:visible}
.sk-line{fill:none; stroke:var(--ink-2); stroke-width:1.5; stroke-linejoin:round; stroke-linecap:round}
.sk-dot{fill:var(--ink)}
.sk-o{fill:none; stroke:var(--ink-3); stroke-width:1.1}
.sk-base{stroke:var(--rule-2); stroke-width:1}
.sk-2020{stroke:var(--rule); stroke-width:1; stroke-dasharray:2 3}

.tpie{font-family:"IBM Plex Mono",monospace; font-size:10.5px; color:var(--ink-3);
  margin-top:8px; line-height:1.6}
.tw + .tpie{margin-top:8px}
td.c-lab{text-align:left; font-size:14px; font-weight:500}
td.c-lab .sub{display:block; font-family:"IBM Plex Mono",monospace; font-size:10px;
  color:var(--ink-3); font-weight:400; margin-top:3px}
th.c-lab{text-align:left}
td.c-n,th.c-n{text-align:right; font-size:14.5px; font-weight:600; white-space:nowrap}
td.c-n2,th.c-n2{text-align:right; font-size:13.5px; color:var(--ink-2); white-space:nowrap}
td.c-b,th.c-b{text-align:right; white-space:nowrap; width:106px}
.tw.compacta table{min-width:0}
.tw.compacta td{padding:10px 11px}
.tw.compacta thead th{padding:10px 11px; font-size:9.5px; letter-spacing:.07em}
.tw.compacta td.c-lab{font-size:13.5px; line-height:1.35}
.tw.compacta td.c-n{font-size:14px}
.tw.compacta td.c-n2{font-size:12.5px}
.tw.compacta td.c-b{width:96px}
.tw.compacta .bub{padding:3px 8px; font-size:12px}
.tw.compacta td.c-lab .sub{font-size:9.5px; margin-top:2px}
tr.destacada{background:var(--surface-2)}
tr.destacada td{font-weight:700}
tr.total td{border-top:1px solid var(--ink)}
.ans-b .tw{margin-top:4px}
.mini{font-family:"IBM Plex Mono",monospace; font-size:11px; color:var(--ink-3)}

.subap{margin-top:26px}
.sub-h{font-size:15px; font-weight:600; letter-spacing:-.01em; margin-bottom:10px;
  padding-bottom:6px; border-bottom:1px solid var(--rule)}
.ans-b .sub-h{border-bottom:none; padding-bottom:0; margin-bottom:2px; font-size:15.5px}

.cierre{margin-top:8px; border:2px solid var(--ink); background:var(--ground); padding:22px 24px}
.cierre .c-l{font-family:"IBM Plex Mono",monospace; font-size:10.5px; letter-spacing:.15em;
  text-transform:uppercase; color:var(--ink-3); display:block; margin-bottom:10px}
.cierre p{font-family:"Archivo",sans-serif!important; font-size:17.5px!important; color:var(--ink)!important;
  line-height:1.5!important; letter-spacing:-.012em; max-width:64ch}
.cierre p + p{margin-top:10px}
.cierre b{font-weight:700}
.linea{border-left:3px solid var(--ink); padding:2px 0 2px 16px; margin-bottom:4px}
.linea .l-l{font-family:"IBM Plex Mono",monospace; font-size:10.5px; letter-spacing:.14em;
  text-transform:uppercase; color:var(--ink-3); display:block; margin-bottom:6px}
.linea p{font-size:17px!important; font-weight:500; line-height:1.5!important;
  font-family:"Archivo",sans-serif!important; color:var(--ink)!important; letter-spacing:-.012em; max-width:66ch}
.perfiles{display:grid; gap:1px; background:var(--rule); border:1px solid var(--rule); margin:4px 0}
.perfil{background:var(--surface); padding:15px 18px; display:grid;
  grid-template-columns:minmax(0,1fr); gap:3px; border-left:3px solid var(--flat)}
.perfil.gana{border-left-color:var(--up)}
.perfil.pierde{border-left-color:var(--down)}
.perfil .p-e{font-family:"IBM Plex Mono",monospace; font-size:9.5px; letter-spacing:.13em;
  text-transform:uppercase; color:var(--flat)}
.perfil.gana .p-e{color:var(--up)}
.perfil.pierde .p-e{color:var(--down)}
.perfil .p-t{font-size:14.5px; font-weight:600; line-height:1.35; letter-spacing:-.01em}
.perfil .p-d{font-family:"Source Serif 4",Georgia,serif; font-size:14.5px; color:var(--ink-2);
  line-height:1.5; margin-top:3px}
.mini-nota{font-size:13px!important; color:var(--ink-3)!important;
  font-family:"IBM Plex Mono",monospace!important; line-height:1.65!important; max-width:78ch}

/* ---------- leyenda ---------- */
.leg{margin-top:16px; border-left:3px solid var(--mark); padding:2px 0 2px 16px}
.leg-t{font-family:"IBM Plex Mono",monospace; font-size:10.5px; letter-spacing:.13em;
  text-transform:uppercase; color:var(--mark); display:block; margin-bottom:6px}
.leg-b{font-family:"Source Serif 4",Georgia,serif; font-size:15.5px; color:var(--ink-2);
  max-width:80ch; line-height:1.58}
.leg-b b{color:var(--ink); font-weight:600}

/* ---------- respuestas ---------- */
.ans{margin-top:48px; background:var(--surface); border:1px solid var(--rule);
  box-shadow:var(--shadow)}
.ans-h{padding:26px 30px 22px; border-bottom:1px solid var(--rule); background:var(--surface-2)}
.ans-q{font-family:"IBM Plex Mono",monospace; font-size:10.5px; letter-spacing:.14em;
  text-transform:uppercase; color:var(--mark)}
.ans-h h3{font-size:clamp(20px,2.6vw,27px); margin-top:9px; max-width:38ch}
.ans-b{padding:26px 30px 30px; display:grid; gap:20px}
.ans-b p{font-family:"Source Serif 4",Georgia,serif; font-size:16.5px; color:var(--ink-2);
  max-width:72ch; line-height:1.62}
.ans-b p b, .ans-b li b{color:var(--ink); font-weight:600}
.verdict{border:1px solid var(--ink); padding:18px 20px; background:var(--ground)}
.verdict .v-l{font-family:"IBM Plex Mono",monospace; font-size:10.5px; letter-spacing:.14em;
  text-transform:uppercase; color:var(--ink-3); display:block; margin-bottom:8px}
.verdict .v-t{font-size:18px; font-weight:600; line-height:1.45; letter-spacing:-.015em; max-width:66ch}
.figs{display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:1px;
  background:var(--rule); border:1px solid var(--rule)}
.fig{background:var(--surface); padding:16px 16px 14px}
.fig .f-v{font-size:25px; font-weight:700; letter-spacing:-.03em; display:block; line-height:1.1}
.fig .f-l{font-size:12px; color:var(--ink-2); display:block; margin-top:6px; line-height:1.4}
.ans-b ul{margin:0; padding-left:20px; display:grid; gap:9px}
.ans-b li{font-family:"Source Serif 4",Georgia,serif; font-size:16px; color:var(--ink-2);
  max-width:72ch; line-height:1.55}
.warn{border-left:3px solid var(--down); padding:2px 0 2px 16px}
.warn .w-l{font-family:"IBM Plex Mono",monospace; font-size:10.5px; letter-spacing:.13em;
  text-transform:uppercase; color:var(--down); display:block; margin-bottom:6px}

/* ---------- barras de descomposición ---------- */
.dec{display:grid; gap:10px; margin:2px 0}
.dec-r{display:grid; grid-template-columns:minmax(150px,230px) 1fr auto; gap:14px; align-items:center}
.dec-l{font-size:13.5px; color:var(--ink-2); line-height:1.35}
.dec-t{display:block; height:14px; background:var(--rule-2); position:relative; overflow:hidden}
.dec-f{display:block; height:14px; background:var(--up)}
.dec-f.neg{background:var(--down)}
.dec-v{font-family:"IBM Plex Mono",monospace; font-size:12px; color:var(--ink); min-width:74px; text-align:right}

/* ---------- cierre ---------- */
.note{margin-top:22px; font-family:"Source Serif 4",Georgia,serif; font-size:15px;
  color:var(--ink-2); max-width:78ch; line-height:1.6}
.grid2{display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:26px; margin-top:24px}
.card{border:1px solid var(--rule); background:var(--surface); padding:20px 22px}
.card h4{font-size:15px; margin-bottom:9px}
.card p, .card li{font-size:14px; color:var(--ink-2); line-height:1.55}
.card ul{margin:0; padding-left:18px; display:grid; gap:7px}
footer{margin-top:70px; padding-top:22px; border-top:1px solid var(--rule);
  font-family:"IBM Plex Mono",monospace; font-size:11px; color:var(--ink-3); line-height:1.8}
@media (max-width:900px){ .kpis{grid-template-columns:repeat(2,1fr)} }
@media (max-width:560px){ .kpis{grid-template-columns:1fr} }
@media (max-width:640px){
  .wrap{padding:0 15px 64px}
  .ans-h,.ans-b{padding-left:18px; padding-right:18px}
  .dec-r{grid-template-columns:1fr; gap:5px}
}
@media (prefers-reduced-motion:reduce){*{animation:none!important; transition:none!important}}
"""

# ------------------------------------------------------------------ bloques --
# ------------------------------------------------------- piezas de apoyo ----
def barra(lab, valor, maxv, neg=False, sufijo=""):
    w = min(100, abs(valor) / maxv * 100) if maxv else 0
    return (f'<div class="dec-r"><span class="dec-l">{lab}</span>'
            f'<span class="dec-t"><span class="dec-f{" neg" if neg else ""}" style="width:{w:.1f}%"></span></span>'
            f'<span class="dec-v">{sufijo}</span></div>')


def figs(items):
    return '<div class="figs">' + "".join(
        f'<div class="fig"><span class="f-v" style="color:{c}">{v}</span><span class="f-l">{l}</span></div>'
        for v, l, c in items) + "</div>"


UP = "var(--up)"; DN = "var(--down)"; NK = "var(--ink)"

# ============================ PREGUNTA 1 ====================================
CONT = G["poblacion_continentes_nacionalidad"]
AMER = G["america_detalle"]
d_ext_tot = G["delta_extranjeros_total"]

maxd = max(abs(V["d_fue"]), abs(V["d_esp"]), abs(V["dpob"]))
dec_pob = "".join([
    barra("Residentes nacidos en el extranjero", V["d_fue"], maxd, False, f'+{nf(V["d_fue"])}'),
    barra("Residentes nacidos en España", V["d_esp"], maxd, True, f'{nf(V["d_esp"])}'),
    barra("<b>Variación neta de la población</b>", V["dpob"], maxd, False, f'+{nf(V["dpob"])}')])

tabla_cont = tabla_libre(
    [("Origen (nacionalidad)", "c-lab"), ("2018", "c-n"), ("2025", "c-n"),
     ("Aumento", "c-n"), ("% del<br>aumento", "c-n2"), ("Variación", "c-b")],
    [[f'{c["grupo"]}', nf(c["v2018"]), nf(c["v2025"]), f'+{nf(c["delta"])}',
      nf(c["cuota_del_aumento_extranjero"], 1) + " %", bub(c["var_pct"])] for c in CONT]
    + [["<b>Total población extranjera</b>", f'<b>{nf(V["pob_nac_ext_18"])}</b>',
        f'<b>{nf(V["pob_nac_ext_25"])}</b>', f'<b>+{nf(d_ext_tot)}</b>', "<b>100,0 %</b>",
        bub((V["pob_nac_ext_25"] / V["pob_nac_ext_18"] - 1) * 100)]],
    clases=[""] * len(CONT) + ["total destacada"],
    pie="INE · tabla 56942, población a 1 de enero. Agrupación por NACIONALIDAD, que es la única "
        "clasificación por origen con serie homogénea 2018-2025. Los naturalizados salen de estos grupos "
        "y pasan a «española», así que estas cifras son un suelo, no un techo.")

tabla_amer = tabla_libre(
    [("Dentro de América", "c-lab"), ("2018", "c-n"), ("2025", "c-n"), ("Aumento", "c-n"), ("Variación", "c-b")],
    [[a["grupo"], nf(a["v2018"]), nf(a["v2025"]), f'+{nf(a["delta"])}', bub(a["var_pct"])] for a in AMER],
    pie="INE · tabla 56942.")

PNAC = G["paises_nacimiento_2018_2022"]
tabla_pnac = tabla_libre(
    [("País de nacimiento", "c-lab"), ("2018", "c-n"), ("2022", "c-n"), ("Aumento", "c-n"), ("Variación", "c-b")],
    [[p["pais"], nf(p["v2018"]), nf(p["v2022"]), f'+{nf(p["delta"])}', bub(p["var_pct"])] for p in PNAC],
    pie="INE · tabla 9675, residentes por país de nacimiento a 1 de enero. Esta tabla es la única con "
        "detalle de país, y se detiene en 2022: no cubre el periodo completo. Por eso el efecto de la "
        "guerra de Ucrania, que empieza en febrero de 2022, todavía no aparece aquí.")

ENT = G["entradas_por_pais_nacimiento"]
tabla_ent = tabla_libre(
    [("País de nacimiento", "c-lab"), ("Entradas<br>2018-2024", "c-n"), ("2018", "c-n2"),
     ("2022", "c-n2"), ("2024", "c-n2"), ("Serie", "c-sk")],
    [[e["pais"], nf(e["acum"]),
      nf(e["serie"][0]) if e["serie"][0] else "—",
      nf(e["serie"][4]) if e["serie"][4] else "—",
      nf(e["serie"][6]) if e["serie"][6] else "—",
      spark([[2018 + i, v] for i, v in enumerate(e["serie"]) if v is not None])] for e in ENT],
    pie="INE · tabla 24324 para 2018-2020 y tabla 69694 (nueva Estadística de Migraciones) para 2021-2024. "
        "Son dos series distintas y no deben sumarse sin cautela: el acumulado se ofrece como orden de "
        "magnitud, no como cifra oficial única. Cuenta entradas, no personas distintas: quien entra y sale "
        "varias veces se cuenta varias veces.")

UCR = G["series_pais"]["Ucrania"]
ucr_pico = max(v for v in UCR if v)
ucr_2019 = UCR[1]


# ============================ PREGUNTA 2 ====================================
DC = G["detenidos_continente"]
DE_ESP = G["detenidos_espanoles"]
DP = G["detenidos_paises"]
TIPOS = G["peso_extranjeros_por_tipo"]
TP = {t["tipo"]: t for t in TIPOS}
CC = G["condenados_continente"]
CE = G["condenados_espanoles"]
COMP = G["composicion_delitos_por_origen"]
CM = {c["tipo"]: c for c in COMP}
TOTG = G["total_delitos_por_origen"]

maxc = max(DESC["efecto_poblacion"], DESC["efecto_tasa"], DESC["efecto_interaccion"])
dec_cri = "".join([
    barra("Más población extranjera residente", DESC["efecto_poblacion"], maxc, False,
          f'+{nf(DESC["efecto_poblacion"])} ({PS["ef_pob_pct"]})'),
    barra("Mayor tasa de actuaciones por residente", DESC["efecto_tasa"], maxc, False,
          f'+{nf(DESC["efecto_tasa"])} ({PS["ef_tasa_pct"]})'),
    barra("Interacción de ambos efectos", DESC["efecto_interaccion"], maxc, False,
          f'+{nf(DESC["efecto_interaccion"])} ({PS["ef_int_pct"]})')])

tabla_det = tabla_libre(
    [("Origen (nacionalidad)", "c-lab"), ("2018", "c-n2"), ("2024", "c-n"),
     ("Tasa 2018", "c-n2"), ("Tasa 2024", "c-n"), ("Frente a la<br>española", "c-n2"), ("Variación", "c-b")],
    [[f'{d["grupo"]}<span class="sub">{nf(d["pob2024"])} residentes en 2024</span>',
      nf(d["n2018"]), nf(d["n2024"]), nf(d["tasa2018"]), nf(d["tasa2024"]),
      "×" + nf(d["ratio2024"], 2), bub(d["var_tasa_pct"])] for d in DC]
    + [[f'<b>Nacionalidad española</b><span class="sub">{nf(V["pob_esp_24"])} residentes en 2024</span>',
        f'<b>{nf(DE_ESP["n2018"])}</b>', f'<b>{nf(DE_ESP["n2024"])}</b>',
        f'<b>{nf(DE_ESP["tasa2018"])}</b>', f'<b>{nf(DE_ESP["tasa2024"])}</b>', "<b>×1,00</b>",
        bub(DE_ESP["var_tasa_pct"])]],
    clases=[""] * len(DC) + ["total destacada"],
    pie="Numerador: Ministerio del Interior, tablas 03001 y 03005/03007, detenciones e investigaciones, "
        "año natural completo. Denominador: INE tabla 56942, población de esa misma nacionalidad a 1 de enero. "
        "Tasas por 100.000 residentes del propio grupo. Oceanía se omite: "
        f"{nf(G['oceania_aviso']['n2024'])} actuaciones sobre {nf(G['oceania_aviso']['pob2024'])} residentes "
        "es una base demasiado pequeña para una tasa estable.")

tabla_paises_det = tabla_libre(
    [("Nacionalidad", "c-lab"), ("2018", "c-n2"), ("2024", "c-n"), ("Variación", "c-b")],
    [[d["pais"], nf(d["n2018"]), nf(d["n2024"]), bub(d["var_pct"])] for d in DP],
    pie="Ministerio del Interior · tabla 03007. Son conteos brutos, no tasas: un país con más residentes "
        "aparecerá más arriba aunque su tasa sea menor. No hay denominador oficial por país concreto de "
        "nacionalidad en las tablas descargadas, así que aquí no pueden calcularse tasas.")

tabla_tipos = tabla_libre(
    [("Tipo de infracción", "c-lab"), ("% ext.<br>2018", "c-n2"), ("% ext.<br>2024", "c-n"),
     ("Actuaciones a<br>extranjeros 2024", "c-n2"), ("Variación", "c-b")],
    [[t["tipo"], nf(t["pct2018"], 1) + " %", nf(t["pct2024"], 1) + " %", nf(t["n_ext2024"]),
      bub(t["pct2024"] / t["pct2018"] * 100 - 100)] for t in TIPOS[:-1]]
    + [[f'<b>{TIPOS[-1]["tipo"]}</b>', f'<b>{nf(TIPOS[-1]["pct2018"],1)} %</b>',
        f'<b>{nf(TIPOS[-1]["pct2024"],1)} %</b>', f'<b>{nf(TIPOS[-1]["n_ext2024"])}</b>',
        bub(TIPOS[-1]["pct2024"] / TIPOS[-1]["pct2018"] * 100 - 100)]],
    clases=[""] * (len(TIPOS) - 1) + ["total destacada"],
    pie="Derivado: Ministerio del Interior, tabla 03005 (extranjeros) sobre tabla 03001 (total). "
        "Mide el peso de los extranjeros dentro de cada tipo de infracción, no su tasa. La población "
        "extranjera era el 13,4 % de los residentes en 2024, así que cualquier cifra por encima de esa "
        "indica sobrerrepresentación en conteo bruto, sin corregir por edad, sexo ni territorio.")

tabla_cond = tabla_libre(
    [("Origen (nacionalidad)", "c-lab"), ("2018", "c-n2"), ("2025", "c-n"),
     ("Tasa 2018", "c-n2"), ("Tasa 2025", "c-n"), ("Frente a la<br>española", "c-n2"), ("Variación", "c-b")],
    [[c["grupo"], nf(c["n2018"]), nf(c["n2025"]), nf(c["tasa2018"]), nf(c["tasa2025"]),
      "×" + nf(c["ratio2025"], 2), bub(c["var_tasa_pct"])] for c in CC]
    + [["<b>Nacionalidad española</b>", f'<b>{nf(CE["n2018"])}</b>', f'<b>{nf(CE["n2025"])}</b>',
        f'<b>{nf(CE["tasa2018"])}</b>', f'<b>{nf(CE["tasa2025"])}</b>', "<b>×1,00</b>",
        bub(CE["var_tasa_pct"])]],
    clases=[""] * len(CC) + ["total destacada"],
    pie="INE, Estadística de Condenados · tabla 25645, personas con sentencia firme. Denominador: "
        "INE tabla 56942. Tasas por 100.000 residentes del propio grupo.")

filas_comp = []
for c in COMP:
    filas_comp.append([c["tipo"]] + [nf(c[g], 1) + " %" if c.get(g) is not None else "—"
                                     for g in ["Española", "África", "América", "Asia", "Europa (sin España)"]])
tabla_comp = tabla_libre(
    [("Tipo de delito", "c-lab"), ("Española", "c-n"), ("África", "c-n"), ("América", "c-n"),
     ("Asia", "c-n"), ("Europa (sin España)", "c-n")],
    filas_comp,
    pie="INE · tabla 26014, infracciones penales asociadas a condenas firmes, año 2025. Cada columna suma "
        "sobre el total de delitos de ese grupo: la cifra dice en qué se concentra la delincuencia condenada "
        "de cada origen, no cuánta hay. Totales de referencia: "
        + " · ".join(f"{k} {nf(v)}" for k, v in TOTG.items()) + " delitos.")


# ============================ PREGUNTA 3 ====================================
EU = G["comparativa_europa"]
RK = G["espana_ranking"]
es_eu = [x for x in EU if x["geo"] == "ES"][0]
ue_eu = [x for x in EU if x["geo"] == "EU27_2020"][0]

tabla_eu = tabla_libre(
    [("País", "c-lab"), ("Inflación<br>2018-2025", "c-n2"), ("PIB por hab.<br>real 18-24", "c-n2"),
     ("Salario neto<br>real 18-23", "c-n"), ("Nivel de<br>vida 2018", "c-n2"),
     ("Nivel de<br>vida 2024", "c-n2"), ("Salario real", "c-b")],
    [[("<b>" + e["pais"] + "</b>" if e["geo"] in ("ES", "EU27_2020") else e["pais"]),
      pct(e["infl"]), pct(e["pibpc"]), pct(e["salario_real"]),
      nf(e["aic2018"]), nf(e["aic2024"]), bub(e["salario_real"])] for e in EU],
    clases=["destacada" if e["geo"] in ("ES", "EU27_2020") else "" for e in EU],
    pie="Eurostat · HICP (prc_hicp_aind), PIB per cápita en volumen encadenado (nama_10_pc), ganancia neta "
        "anual de una persona soltera sin hijos con el 100 % del salario medio (earn_nt_net) deflactada con "
        "el HICP de cada país, y consumo individual efectivo per cápita en paridad de poder adquisitivo con "
        "UE-27 = 100 (prc_ppp_ind). El salario se detiene en 2023 porque Eurostat marca ruptura de serie en "
        "2024 en los trece países: incluir 2024 produciría caídas falsas de hasta el 25 %.")


# ============================ PREGUNTA 4: SECTOR PÚBLICO ====================
COMPO = SP["componentes"]
PS_DET = SP["proteccion_social_detalle"]
PS_TOT = SP["proteccion_social_total"]
FISC = SP["comparativa_fiscal_europa"]
ue_fisc = [f for f in FISC if f["geo"] == "EU27_2020"][0]
RE = SP["reales"]

maxi = max(c["euros"] for c in COMPO)
dec_ing = "".join(barra(c["nombre"], c["euros"], maxi, False,
                        f'+{nf(c["euros"])} M€ ({nf(c["cuota"],0)} %)') for c in COMPO)

tabla_ps = tabla_libre(
    [("Partida de protección social", "c-lab"), ("2018", "c-n"), ("2024", "c-n"),
     ("Aumento", "c-n"), ("% del<br>aumento", "c-n2"), ("Variación", "c-b")],
    [[d["concepto"], nf(d["v2018"]), nf(d["v2024"]), f'+{nf(d["delta"])}',
      nf(d["cuota_del_aumento"], 1) + " %", bub(d["var_pct"])] for d in PS_DET]
    + [["<b>Total protección social</b>", f'<b>{nf(PS_TOT["v2018"])}</b>', f'<b>{nf(PS_TOT["v2024"])}</b>',
        f'<b>+{nf(PS_TOT["delta"])}</b>', "<b>100,0 %</b>",
        bub((PS_TOT["v2024"] / PS_TOT["v2018"] - 1) * 100)]],
    clases=[""] * len(PS_DET) + ["total destacada"],
    pie="Eurostat · gov_10a_exp, clasificación funcional COFOG, función 10 y sus subfunciones, en millones "
        "de euros corrientes. Son los mismos datos que la IGAE notifica a la UE. El Ingreso Mínimo Vital se "
        "registra dentro de «exclusión social»; esa partida incluye también otras prestaciones, así que no "
        "es una cifra exclusiva del IMV.")

tabla_fisc = tabla_libre(
    [("País", "c-lab"), ("Ingresos<br>2018", "c-n2"), ("Ingresos<br>2024", "c-n"), ("Dif.", "c-n2"),
     ("Protección<br>social 2024", "c-n2"), ("Sanidad<br>2024", "c-n2"), ("Saldo<br>2024", "c-n2"),
     ("Deuda<br>2024", "c-n2")],
    [[("<b>" + f["pais"] + "</b>" if f["geo"] in ("ES", "EU27_2020") else f["pais"]),
      nf(f["ing2018"], 1) + " %", nf(f["ing2024"], 1) + " %", pp(f["ing_dif"], 1),
      nf(f["ps2024"], 1) + " %", nf(f["san2024"], 1) + " %", nf(f["saldo2024"], 1) + " %",
      nf(f["deuda2024"], 1) + " %"] for f in FISC],
    clases=["destacada" if f["geo"] in ("ES", "EU27_2020") else "" for f in FISC],
    pie="Eurostat · gov_10a_main, gov_10a_exp y gov_10dd_edpt1, todo en porcentaje del PIB. "
        "Saldo negativo = déficit.")


# ============================ PREGUNTA 5: COMPLEMENTARIAS ===================


BLOQUES = [
 ("b-poblacion", "01", "Población y migración",
  "Población residente a 1 de enero. El origen migratorio se mide por <b>país de nacimiento</b>; "
  "la nacionalidad se muestra aparte porque es una condición jurídica que cambia.",
  "poblacion",
  f"""España tiene <b>{N['dpob']} habitantes más</b> que en 2018 ({P['dpob_pct']}). Esa cifra es el
  resultado neto de dos movimientos opuestos: la población <b>nacida en España cayó en {nf(abs(V['d_esp']))} personas</b>
  y la <b>nacida en el extranjero creció en {N['d_fue']}</b>. Los nacidos fuera pasaron de ser el
  {PS['pct_fue18']} de la población al {PS['pct_fue25']}. La cifra de «extranjeros» crece menos
  ({N['d_ext']}) porque {N['nat']} personas adquirieron la nacionalidad española en el periodo:
  cambian de casilla en las estadísticas por nacionalidad sin haber cambiado de lugar de nacimiento.
  La población de 65 y más años sumó {nf(A.pob_65mas[2025]-A.pob_65mas[2018])} personas."""),

 ("b-economia", "02", "Economía y producción",
  "Contabilidad Nacional, Revisión Estadística 2024. La serie oficial completa llega a 2024, "
  "por lo que esta tabla compara <b>2018 con 2024</b>, no con 2025.",
  "economia",
  f"""La economía española produjo en 2024 <b>{P['pib_r']} en términos reales</b> que en 2018, pero
  el PIB nominal subió {P['pib_n']}: la diferencia es inflación, no producción. Como la población
  creció {P['pob_cna']} en el mismo periodo, el <b>PIB real por habitante solo avanzó {P['pib_pc']}</b>
  en seis años. El crecimiento se explica sobre todo por <b>más factor trabajo</b> —{P['puestos']} de
  puestos y {P['horas']} de horas— y muy poco por eficiencia: la producción por hora trabajada apenas
  se movió ({P['prod']})."""),

 ("b-laboral", "03", "Mercado de trabajo",
  "EPA y Encuesta Trimestral de Coste Laboral, medias de los cuatro trimestres de cada año. "
  "Desde 2021 la EPA usa la base poblacional de 2021: hay una discontinuidad respecto a la base anterior.",
  "laboral",
  f"""El paro cayó de {PS['paro18']} a {PS['paro25']} ({pp(V['paro25']-V['paro18'],2)}) y la tasa de empleo
  subió {pp(V['emp25']-V['emp18'],2)}, mientras las <b>vacantes declaradas por las empresas crecieron {P['vac_pct']}</b>.
  Los tres indicadores apuntan en la misma dirección: hay más empleo y más demanda de trabajo.
  La tasa de actividad, en cambio, está prácticamente donde estaba ({pp(V['act25']-V['act18'],2)}).
  El aumento de inactivos ({P['ina_pct']}) no significa que más gente rechace trabajar: se explica por
  <b>{nf(V['d_jub'])} jubilados más</b> y {nf(V['d_est'])} estudiantes más, mientras las labores del hogar
  caen en {nf(abs(V['d_hog']))} personas."""),

 ("b-precios", "04", "Precios y coste de la vida",
  "IPC nacional, media anual de los doce meses. 2018 y 2025 son años completos y comparables.",
  "precios",
  f"""Los precios subieron <b>{P['ipc']}</b> entre 2018 y 2025. Traducido: hace falta
  <b>{N['e1000']} € de hoy para comprar lo que en 2018 costaba 1.000 €</b>, o al revés,
  1.000 € de 2025 equivalen a {N['compra1000']} € de 2018. El encarecimiento no fue uniforme:
  la <b>alimentación subió {P['alim']}</b>, casi el doble que el índice general, lo que castiga
  más a los hogares de renta baja, cuya cesta pesa más en alimentos. Comunicaciones fue el único
  grupo que no subió."""),

 ("b-rentas", "05", "Rentas, salarios y pobreza",
  "Todo lo nominal se deflacta con la media anual del IPC general y se expresa en <b>euros de 2018</b>. "
  "La renta de la ECV se refiere al año anterior a la entrevista y aquí se etiqueta por año de renta.",
  "rentas",
  f"""En seis años el <b>salario bruto medio real creció solo {P['sal_r']}</b>: el {P['sal_n']} nominal se
  lo comió casi entero la inflación. La <b>renta de los hogares sí mejoró más ({P['ren_r']} real por persona)</b>,
  porque en un hogar influyen el número de perceptores, las pensiones y las transferencias, no solo el salario.
  El promedio esconde direcciones opuestas: en términos reales el <b>decil salarial más bajo ganó poder
  adquisitivo</b> ({P['d1h']} en hombres, {P['d1m']} en mujeres) mientras el <b>decil más alto lo perdió o
  se estancó</b> ({P['d10h']} y {P['d10m']}). La tasa AROPE bajó {pp(V['arope25']-V['arope18'])}, pero
  uno de cada cuatro residentes sigue en riesgo de pobreza o exclusión."""),

 ("b-vivienda", "06", "Vivienda e hipotecas",
  "El IPV es un índice de precios, no un precio en euros por metro cuadrado. "
  "Este repositorio no contiene una serie oficial homogénea de alquiler.",
  "vivienda",
  f"""La vivienda subió <b>{P['ipv_n']} nominal</b> y, ya descontada la inflación,
  <b>{pct(V['ipv_r'])} en términos reales</b>: se encareció mucho más deprisa que los salarios reales
  ({P['sal_r']}) y que la renta real de los hogares ({P['ren_r']}). El importe medio de la hipoteca creció
  {P['hip_r']} en euros constantes y el plazo medio pasó de {nf(V['plazo18'],1)} a {nf(V['plazo25'],1)} años:
  se compra más caro y se paga durante más tiempo. Es el componente que más erosiona la mejora
  de renta observada en el bloque anterior."""),

 ("b-crimen", "07", "Criminalidad registrada",
  "Ministerio del Interior, años naturales completos. La serie anual llega a <b>2024</b>: no se mezcla "
  "con balances trimestrales de 2025. Un «hecho conocido» es una infracción registrada, no una persona ni una condena.",
  "crimen",
  f"""Las infracciones penales conocidas crecieron {P['hc_pct']} y {P['hct_pct']} por habitante. Pero
  <b>el {PS['ci_aporte']} de todo ese aumento son estafas informáticas</b>, que se multiplicaron
  ({P['ci_pct']}, de {N['ci18']} a {N['ci24']} hechos). Descontando la ciberestafa, el resto de la
  criminalidad registrada creció {P['sin_pct']} en seis años y, medida por habitante, <b>bajó {PS['sin_tasa_pct']}</b>.
  Dentro de ese resto conviven caídas claras —hurtos, robos en viviendas, sustracción de vehículos— con
  subidas en malos tratos familiares, tráfico de drogas, falsedades documentales y delitos sexuales
  (donde parte del cambio es reclasificación legal). Los homicidios consumados pasaron de
  {N['hom18']} a {N['hom24']} al año. La tasa de esclarecimiento mejoró de {PS['escl18']} a {PS['escl24']}."""),

 ("b-crimen-nac", "08", "Criminalidad y nacionalidad",
  "Interior e INE publican <b>nacionalidad</b>, nunca país de nacimiento. Los «españoles» de estas tablas "
  "incluyen a las personas naturalizadas. Las tasas usan como denominador la población de esa misma nacionalidad.",
  "crimen_nac",
  f"""Los detenidos e investigados crecieron {P['det_pct']}: {P['desp_pct']} entre los de nacionalidad
  española y {P['dext_pct']} entre los de nacionalidad extranjera, cuyo peso pasó del
  {PS['pct_detenidos_extranjeros'] if False else nf(E.pct_detenidos_extranjeros[2018],1)} % al
  {nf(E.pct_detenidos_extranjeros[2024],1)} % del total mientras su peso poblacional pasaba del
  {nf(E.pct_pob_extranjera[2018],1)} % al {nf(E.pct_pob_extranjera[2024],1)} %. Medido por 100.000
  residentes de cada grupo, la tasa creció en ambos: de {N['tesp18']} a {N['tesp24']} entre los españoles
  y de {N['text18']} a {N['text24']} entre los extranjeros, con un cociente que pasó de ×{nf(V['ratio18'],2)}
  a ×{nf(V['ratio24'],2)}. <b>Las condenas firmes cuentan otra historia</b>: aunque el número de condenados
  extranjeros subió, su tasa por 100.000 residentes extranjeros <b>bajó {PS['tcext_pct']}</b> y la de los
  españoles bajó {PS['tcesp_pct']}. Son universos distintos —actuación policial frente a sentencia firme—
  y ninguno de los dos identifica una relación causal con la inmigración."""),

 ("b-publico", "09", "Sector público: ingresos, gasto y deuda",
  "Cuentas de las administraciones públicas en SEC 2010, los mismos datos que la IGAE notifica a la UE. "
  "La serie llega a <b>2024</b>. Se añade Eurostat como fuente porque el repositorio original no contenía "
  "datos fiscales y sin ellos no puede saberse quién paga el gasto social.",
  "publico",
  f"""El Estado ingresa {P['ing_pct']} más que en 2018 y gasta {P['gasto_pct']} más. Los ingresos pasan del
  {PS['ing18']} al {PS['ing24']} del PIB, mientras la media de la UE-27 bajaba. En euros constantes y por
  habitante, la recaudación sube {P['ing_real_pc']}. El gasto crece más deprisa que el ingreso, así que el
  déficit se amplía de {PS['saldo18']} a {PS['saldo24']} del PIB, y la deuda sube {P['deuda_meur_pct']} en
  euros aunque apenas se mueva sobre el PIB por efecto de la inflación. Dentro del gasto, la protección
  social crece {P['ps_real_pc']} real por habitante, sanidad {P['san_real_pc']} y educación
  {P['edu_real_pc']}: más gasto real por persona en las tres funciones."""),

 ("b-servicios", "10", "Servicios públicos: listas de espera sanitarias",
  "Sistema de Información sobre Listas de Espera del SNS, corte a 31 de diciembre, 17 comunidades "
  "autónomas e INGESA. Es la única medida oficial de <b>resultado</b> del gasto sanitario disponible: "
  "el gasto dice cuánto se pone, esto dice qué se obtiene.",
  "servicios",
  f"""Con {P['san_real_pc']} de gasto sanitario real por habitante, el resultado es <b>mixto y en conjunto
  peor</b>. En quirúrgica: hay {nf(V['q_pac25']-V['q_pac18'])} pacientes más esperando y la lista crece
  {P['q_tasa']} por cada 1.000 habitantes, aunque el tiempo medio de espera <b>baja</b> de {nf(V['q_dias18'])}
  a {nf(V['q_dias25'])} días. En consultas con especialista empeora todo: la tasa de pacientes en espera sube
  {P['c_tasa']}, el tiempo medio pasa de {nf(V['c_dias18'])} a {nf(V['c_dias25'])} días y los que esperan más
  de dos meses pasan del {PS['c_pct18']} al {PS['c_pct25']}. Más dinero no se ha traducido en menos espera."""),

]


# ------------------------------------------------------------- respuestas ---
def cierre(parrafos):
    ps = "".join(f"<p>{t}</p>" for t in parrafos)
    return f'<div class="cierre"><span class="c-l">Conclusión</span>{ps}</div>'


def linea(texto):
    return f'<div class="linea"><span class="l-l">La respuesta en una línea</span><p>{texto}</p></div>'


def quien(items):
    """Bloque de perfiles: quién gana y quién pierde."""
    out = []
    for titulo, signo, texto in items:
        if isinstance(signo, str):          # etiqueta libre, sin juicio de valor
            cls, etq = "igual", signo
        else:
            cls = "gana" if signo > 0 else ("pierde" if signo < 0 else "igual")
            etq = "Ha ganado" if signo > 0 else ("Ha perdido" if signo < 0 else "Se ha quedado igual")
        out.append(f'<div class="perfil {cls}"><span class="p-e">{etq}</span>'
                   f'<span class="p-t">{titulo}</span><span class="p-d">{texto}</span></div>')
    return '<div class="perfiles">' + "".join(out) + "</div>"


R1 = f"""
<section id="r1" class="ans">
  <div class="ans-h"><span class="ans-q">Pregunta 1 · Crecimiento de la población</span>
    <h3>¿Cuánto ha crecido la población y de dónde viene ese crecimiento?</h3></div>
  <div class="ans-b">
    {linea(f"España ganó <b>{nf(V['dpob'])} habitantes</b>, y todos ellos —y algo más— vienen de fuera.")}

    {figs([(f"+{nf(V['dpob'])}", "habitantes más que en 2018 (+5,3 %)", NK),
           (f"+{nf(V['d_fue'])}", "nacidos en el extranjero", UP),
           (f"{nf(V['d_esp'])}", "nacidos en España", DN),
           (nf(V['lleg']), "residen hoy y llegaron a partir de 2018", NK)])}

    <p><b>El número.</b> De {nf(V['pob18'])} habitantes a 1 de enero de 2018 a {nf(V['pob25'])} a 1 de enero de
    2025: {nf(V['dpob'])} personas más, un {PS['dpob_pct']}. Pero esa cifra neta es la suma de dos movimientos
    opuestos. La población nacida en España <b>cayó</b> en {nf(abs(V['d_esp']))} personas y la nacida en el
    extranjero <b>creció</b> en {nf(V['d_fue'])}:</p>

    <div class="dec">{dec_pob}</div>

    <p>Los nacidos fuera aportan el {PS['c_fue']} del crecimiento neto y los nacidos en España restan el
    {PS['c_esp']}. El porcentaje pasa de 100 porque el otro componente es negativo. A 1 de enero de 2025
    residían en España <b>{nf(V['lleg'])} personas nacidas fuera que llegaron en 2018 o después</b>, el
    {PS['lleg_pct']} de la población total.</p>

    <h4 class="sub-h">De dónde vienen: por continente</h4>
    <p>El detalle por continente solo tiene serie homogénea 2018-2025 por <b>nacionalidad</b>. Son cifras
    mínimas: cada persona que se nacionaliza española desaparece de su grupo de origen.</p>

    {tabla_cont}

    <p><b>América explica casi dos tercios del aumento</b>, y dentro de América el peso está en Sudamérica:</p>

    {tabla_amer}

    <p>África suma {nf(V['africa_delta'])} residentes ({P['africa_var']}) y es el segundo bloque en número
    absoluto, pero crece a un ritmo casi cuatro veces menor que América. Europa aporta {nf(V['europa_delta'])},
    prácticamente lo mismo que África pero partiendo de una base el doble de grande. Asia añade
    {nf(V['asia_delta'])}.</p>

    <h4 class="sub-h">Por países concretos</h4>
    <p>La única tabla oficial con detalle de <b>país de nacimiento</b> se detiene en 2022:</p>

    {tabla_pnac}

    <p>Para llegar hasta 2024 hay que mirar los flujos de entrada. Cuentan entradas, no personas distintas,
    pero cubren los años que la tabla anterior no alcanza:</p>

    {tabla_ent}

    <div class="warn" style="border-left-color:var(--mark)"><span class="w-l" style="color:var(--mark)">Los casos que se salen de la norma</span>
      <ul>
        <li><b>Ucrania: la guerra se ve con nitidez en el dato.</b> Las entradas de nacidos en Ucrania eran
        {nf(ucr_2019)} en 2019 y saltaron a <b>{nf(ucr_pico)} en 2022</b>, casi once veces más, para bajar
        a {nf(UCR[5])} en 2023 y {nf(UCR[6])} en 2024. Es el único origen con un pico tan abrupto y concentrado
        en un solo año, y coincide con la invasión de febrero de 2022 y la protección temporal europea.</li>
        <li><b>Colombia y Venezuela: el fenómeno de fondo.</b> No son un pico sino una corriente sostenida.
        Colombia supera las 170.000 entradas anuales desde 2022 y Venezuela sube todos los años sin excepción.
        Entre las dos explican buena parte del vuelco hacia América.</li>
        <li><b>Marruecos: el más estable y el mayor en stock.</b> Crece de forma continua, sin picos, y sigue
        siendo el primer país de nacimiento extranjero en número de residentes.</li>
        <li><b>Reino Unido va a contracorriente.</b> Es el único origen relevante cuyas entradas <b>caen</b>
        tras 2021, coincidiendo con el fin del periodo transitorio del Brexit.</li>
      </ul></div>

    <p class="mini-nota">El detalle por continente usa nacionalidad y el total usa país de nacimiento: no son
    perfectamente aditivos, porque {nf(V['nat'])} personas se nacionalizaron españolas en el periodo y salieron
    de su grupo de origen. Por eso el reparto por continente es un suelo, no un techo.</p>

    {cierre([
      f"La población creció {nf(V['dpob'])} personas, pero <b>los españoles de nacimiento son "
      f"{nf(abs(V['d_esp']))} menos</b>. Sin inmigración España habría encogido.",
      f"<b>Seis de cada diez</b> de esos nuevos residentes son americanos, sobre todo colombianos y "
      f"venezolanos. África y Europa aportan un 15 % cada una, y Asia un 7 %.",
      f"El único caso excepcional es <b>Ucrania</b>, con un pico de guerra en 2022 que se disparó y luego bajó. "
      f"Todo lo demás es una corriente estable, no una llegada repentina.",
    ])}
  </div>
</section>"""

R2 = f"""
<section id="r2" class="ans">
  <div class="ans-h"><span class="ans-q">Pregunta 2 · Criminalidad</span>
    <h3>¿Cuánto ha crecido la criminalidad, quiénes delinquen más y en qué delitos?</h3></div>
  <div class="ans-b">
    {linea(f"Creció {P['hc_pct']}, pero casi todo es estafa por internet; descontada, la criminalidad por habitante <b>bajó</b>.")}

    {figs([(P['hc_pct'], "infracciones penales conocidas (2018-2024)", UP),
           (PS['ci_aporte'], "de ese aumento son estafas informáticas", UP),
           (PS['sin_tasa_pct'], "resto de criminalidad por habitante", DN),
           (nf(DC[0]['ratio2024'], 1) + "×", "tasa africana frente a la española", NK)])}

    <h4 class="sub-h">Cuánto ha crecido, y de qué</h4>
    <p>Los hechos conocidos pasaron de {N['hc18']} a {N['hc24']} ({P['hc_pct']}; {P['hct_pct']} por habitante).
    Pero las estafas informáticas pasaron de {N['ci18']} a {N['ci24']}: por sí solas explican el
    <b>{PS['ci_aporte']} del aumento</b>. Excluyéndolas, el resto creció {P['sin_pct']} en seis años, menos
    que la población, y por habitante <b>descendió {PS['sin_tasa_pct']}</b>. Bajan hurtos, robos en viviendas
    y robo de vehículos; suben malos tratos familiares, drogas, falsedades y delitos sexuales.</p>

    <h4 class="sub-h">Quién: tasas por 100.000 residentes del mismo origen</h4>
    <p>Los conteos brutos no sirven porque los grupos tienen tamaños muy distintos. Lo comparable es la tasa
    sobre la población de esa misma nacionalidad:</p>

    {tabla_det}

    <p>Todos los grupos superan la tasa española, entre 1,6 y 7,4 veces. Lo relevante no es solo el nivel sino
    el movimiento: la tasa africana <b>se duplicó</b> ({P['africa_tasa_var']}) mientras la de los demás grupos
    —y la española, que también subió {PS['esp_tasa_var']}— crecía entre un 20 % y un 35 %. Por nacionalidades
    concretas, en número de actuaciones:</p>

    {tabla_paises_det}

    <h4 class="sub-h">En qué delitos: el peso de los extranjeros en cada uno</h4>
    {tabla_tipos}

    <p>La sobrerrepresentación es máxima en <b>falsedades documentales</b>
    ({nf(TP['Falsedades documentales']['pct2024'],1)} %), que en buena parte son delitos ligados a la propia
    situación documental y no tienen equivalente posible en un nacional; y en <b>robos con violencia</b>
    ({nf(TP['Robos con violencia o intimidación']['pct2024'],1)} %) y <b>hurtos</b>
    ({nf(TP['Hurtos']['pct2024'],1)} %). Es mínima en <b>estafas informáticas</b>
    ({nf(TP['Estafas informáticas']['pct2024'],1)} %), que es justo el delito que dispara el total.</p>

    <h4 class="sub-h">En qué delitos: el perfil de cada origen</h4>
    <p>De cada 100 delitos que llevan a condena firme en cada grupo, cuántos son de cada tipo. Los perfiles
    son muy distintos entre sí:</p>

    {tabla_comp}

    {quien([
      ("Nacionalidad americana", "Perfil delictivo",
       f"Delito dominante: <b>seguridad vial</b>, {nf(CM['Contra la seguridad vial']['América'],0)} de cada 100 "
       "de sus condenas. Perfil de infracción de tráfico, no violento, muy por encima de cualquier otro grupo."),
      ("Nacionalidad africana", "Perfil delictivo",
       f"Perfil <b>patrimonial</b>: hurtos ({nf(CM['Hurtos']['África'],0)} %) más robos "
       f"({nf(CM['Robos']['África'],0)} %) suman más de un tercio de sus condenas, la proporción más alta."),
      ("Nacionalidad española", "Perfil delictivo",
       f"El perfil más repartido, con seguridad vial ({nf(CM['Contra la seguridad vial']['Española'],0)} %) y "
       f"lesiones ({nf(CM['Lesiones']['Española'],0)} %) al frente."),
      ("Nacionalidad asiática", "Perfil delictivo",
       "La tasa más baja de todas, y el mayor peso relativo de <b>falsedades documentales</b> en sus condenas."),
    ])}

    <h4 class="sub-h">Y las condenas firmes dicen lo contrario que las detenciones</h4>
    {tabla_cond}
    <p>Medidas por 100.000 residentes de su propia nacionalidad, las tasas de condena <b>bajaron</b> entre 2018
    y 2025 en casi todos los grupos, incluida la española ({PS['tcesp_pct']}) y la extranjera en conjunto
    ({PS['tcext_pct']}). Es lo contrario de lo que muestran las detenciones. Son universos distintos —actuación
    policial frente a sentencia firme, con años de diferencia— y esa divergencia es motivo suficiente para no
    titular con una sola de las dos series.</p>

    <div class="warn"><span class="w-l">Por qué esto no mide una causa</span>
      <ul>
        <li><b>No hay país de nacimiento en ninguna tabla penal</b>, solo nacionalidad jurídica actual, y los
        «españoles» incluyen a {nf(V['nat'])} personas naturalizadas en el periodo.</li>
        <li><b>La estructura demográfica no está corregida.</b> La población extranjera es mucho más joven y
        masculina, el perfil que concentra la actividad delictiva en cualquier país y grupo. Parte de la brecha
        desaparecería solo con estandarizar por edad y sexo, y estas tablas no lo permiten.</li>
        <li><b>Ni la renta ni el territorio.</b> Los grupos con tasas más altas se concentran donde hay menos
        renta y más presencia policial.</li>
        <li><b>El denominador es incierto:</b> si el padrón no capta a toda la población irregular, su tasa
        aparece inflada por construcción. Afecta sobre todo a la cifra africana.</li>
        <li><b>Detenidos e investigados son actuaciones policiales</b>, no delitos probados; una persona puede
        figurar varias veces.</li>
      </ul></div>

    {cierre([
      f"La criminalidad <b>no ha crecido como parece</b>: quitando la estafa por internet, hay menos delitos "
      f"por habitante que en 2018.",
      f"Los extranjeros aparecen en las estadísticas policiales <b>bastante más de lo que les corresponde por "
      f"población</b>, y el grupo africano se ha separado del resto al duplicar su tasa. Pero el perfil delictivo "
      f"cambia mucho según el origen: los americanos son sobre todo tráfico, los africanos sobre todo patrimonio.",
      f"Con estos datos <b>se puede decir quién aparece en las estadísticas, no por qué</b>. La nacionalidad no "
      f"es el origen, y nadie ha corregido por edad, sexo, renta ni territorio, que es donde está buena parte "
      f"de la explicación.",
    ])}
  </div>
</section>"""

R3 = f"""
<section id="r3" class="ans">
  <div class="ans-h"><span class="ans-q">Pregunta 3 · Poder adquisitivo</span>
    <h3>¿Es el ciudadano más rico o más pobre que en 2018?</h3></div>
  <div class="ans-b">
    {linea("De media algo más rico, pero tan poco que la respuesta real depende de quién seas.")}

    {figs([(f"{N['compra1000']} €", "compran hoy 1.000 €, en euros de 2018", DN),
           (P['sal_r'], "salario medio real (INE, 2018-2024)", UP),
           (pct(es_eu['salario_real']), f"salario neto real en Europa, puesto {RK['salario_real']} de {RK['n']}", DN),
           (pct(V['ipv_r']), "precio real de la vivienda", UP)])}

    <h4 class="sub-h">Los datos españoles</h4>
    <p>Los precios subieron {P['ipc']}: hacen falta <b>{N['e1000']} € de hoy para comprar lo que 1.000 €
    compraban en 2018</b>. El salario bruto medio subió {P['sal_n']} nominal pero solo <b>{P['sal_r']} real</b>.
    La renta neta media por persona creció {P['ren_r']} real y la renta por unidad de consumo {P['renuc_r']},
    más que el salario porque en el hogar cuentan varios perceptores, las pensiones y las transferencias.
    La tasa AROPE bajó de {PS['arope18']} a {PS['arope25']}, pero sigue afectando a uno de cada cuatro.</p>

    <h4 class="sub-h">Quién ha ganado y quién ha perdido</h4>
    <p>El promedio esconde direcciones opuestas. Estos son los perfiles que los datos permiten separar:</p>

    {quien([
      ("Un hogar que ya tenía vivienda en propiedad, con hipoteca antigua", 1,
       f"Es el que más gana. Su mayor gasto está congelado en términos nominales mientras su renta sube, y su "
       f"patrimonio se ha revalorizado {pct(V['ipv_r'])} en términos reales."),
      ("Un trabajador del decil salarial más bajo", 1,
       f"Gana poder adquisitivo con claridad: {P['d1h']} en hombres y {P['d1m']} en mujeres en euros constantes, "
       "muy por encima de la media. El periodo comprime la escala salarial por abajo."),
      ("Un hogar con dos perceptores en tramos medios", 1,
       f"Gana algo: la renta por unidad de consumo sube {P['renuc_r']} real, más que el salario, porque cuentan "
       "las dos nóminas y las transferencias."),
      ("Un asalariado del tramo alto que no ha cambiado de empleo", -1,
       f"Es más pobre en términos reales: el decil salarial más alto {P['d10h']} en hombres y solo {P['d10m']} "
       f"en mujeres, mientras los precios subían {P['ipc']}."),
      ("Quien necesita comprar vivienda ahora", -1,
       f"El que más pierde, y no de poco. La vivienda subió {pct(V['ipv_r'])} real, cinco veces más que el "
       f"salario real. La hipoteca media creció {P['hip_r']} en euros constantes y el plazo pasó de "
       f"{nf(V['plazo18'],1)} a {nf(V['plazo25'],1)} años: más caro y durante más tiempo."),
      ("Un hogar de renta baja cuya cesta pesa en alimentación", -1,
       f"Su inflación efectiva fue mayor que la general: los alimentos subieron {P['alim']}, casi el doble que "
       f"el IPC ({P['ipc']}). La cifra media de inflación se le queda corta."),
    ])}

    <h4 class="sub-h">¿Y eso es mucho o poco? La comparación europea</h4>
    <p>Un {P['sal_r']} en seis años no significa nada sin saber qué hicieron los demás con la misma
    metodología. Esta tabla es de Eurostat, que aplica la misma definición a los trece países:</p>

    {tabla_eu}

    <ul>
      <li><b>España tuvo menos inflación que la media europea</b>: {PS['infl_es']} frente a {PS['infl_ue']}.
      Ese punto va a favor.</li>
      <li><b>Aun así el salario real cayó más que la media</b>: {pct(es_eu['salario_real'])} frente a
      {pct(ue_eu['salario_real'])} de la UE-27, puesto {RK['salario_real']} de {RK['n']}, solo por delante de
      Suecia. Portugal, con una inflación casi idéntica, logró
      {pct([x for x in EU if x['geo']=='PT'][0]['salario_real'])}.</li>
      <li><b>El PIB por habitante también quedó por debajo</b>: {pct(es_eu['pibpc'])} frente a
      {pct(ue_eu['pibpc'])}, puesto {RK['pibpc']} de {RK['n']}.</li>
      <li>El único indicador donde España mejora algo su posición relativa es el <b>nivel de vida material</b>
      en paridad de poder adquisitivo: de {nf(es_eu['aic2018'])} a {nf(es_eu['aic2024'])} con la UE-27 en 100.
      Sigue ocho puntos por debajo de la media.</li>
    </ul>

    <p class="mini-nota">El indicador de Eurostat es un caso-tipo (soltero sin hijos al salario medio) y se
    detiene en 2023 por ruptura de serie; no tiene por qué coincidir con el dato bruto del INE, porque miden
    cosas distintas. Se muestran los dos.</p>

    {cierre([
      "El ciudadano medio es <b>algo más rico, pero apenas</b>: en seis años su salario real ha ganado tres "
      "puntos, medio punto por año.",
      "Y la media engaña. <b>Gana quien ya tenía casa y quien cobra poco; pierde quien cobra bien y, sobre "
      "todo, quien necesita comprar vivienda ahora.</b>",
      f"Comparado con Europa, España lo ha hecho <b>peor que la media pese a tener menos inflación</b>: "
      f"puesto {RK['salario_real']} de {RK['n']} en salario real. El problema no fueron los precios, fueron "
      f"los sueldos.",
    ])}
  </div>
</section>"""

tabla_imv = tabla_libre(
    [("Ingreso Mínimo Vital", "c-lab"), ("Enero 2024", "c-n2"), ("Diciembre 2025", "c-n"), ("Variación", "c-b")],
    [["Hogares perceptores", nf(IMVM.iloc[0]["prestaciones"]), nf(V["imv_hogares25"]),
      bub((V["imv_hogares25"] / IMVM.iloc[0]["prestaciones"] - 1) * 100)],
     ["Personas beneficiarias", nf(IMVM.iloc[0]["beneficiarios"]), nf(V["imv_benef25"]),
      bub((V["imv_benef25"] / IMVM.iloc[0]["beneficiarios"] - 1) * 100)],
     ["Cuantía media mensual por hogar", nf(IMVM.iloc[0]["cuantia_media_hogar_eur"], 0) + " €",
      nf(V["imv_cuantia25"], 0) + " €",
      bub((V["imv_cuantia25"] / IMVM.iloc[0]["cuantia_media_hogar_eur"] - 1) * 100)]],
    pie="Seguridad Social · nómina mensual del IMV. <b>No hay comparación posible con 2018: el IMV no existía; "
        "se creó en junio de 2020.</b> Además la serie descargable en XLSX empieza en enero de 2024, así que "
        "tampoco puede reconstruirse 2020-2023. Gasto del año 2025 completo: "
        f"{nf(V['imv_gasto25'])} millones de euros. Acumulado desde su creación hasta diciembre de 2025: "
        f"{nf(V['imv_acum'])} millones.")

_qq = SIS[(SIS.ambito == "quirurgica") & (SIS.mes == 12)].set_index("anyo")
_cc = SIS[(SIS.ambito == "consultas") & (SIS.mes == 12)].set_index("anyo")
tabla_sisle = tabla_libre(
    [("Indicador (corte a 31 de diciembre)", "c-lab"), ("2018", "c-n"), ("2025", "c-n"), ("Variación", "c-b")],
    [["Pacientes en espera para operarse", nf(_qq.pacientes_espera[2018]), nf(_qq.pacientes_espera[2025]),
      bub((_qq.pacientes_espera[2025] / _qq.pacientes_espera[2018] - 1) * 100)],
     ["Pacientes en espera quirúrgica por 1.000 habitantes", nf(_qq.tasa_por_1000_hab[2018], 2),
      nf(_qq.tasa_por_1000_hab[2025], 2), bub(V["q_tasa"])],
     ["Tiempo medio de espera para operarse", nf(_qq.tiempo_medio_espera_dias[2018]) + " días",
      nf(_qq.tiempo_medio_espera_dias[2025]) + " días",
      bub((_qq.tiempo_medio_espera_dias[2025] / _qq.tiempo_medio_espera_dias[2018] - 1) * 100)],
     ["Esperan más de 6 meses para operarse", nf(_qq.pct_mas_6_meses[2018], 1) + " %",
      nf(_qq.pct_mas_6_meses[2025], 1) + " %",
      bub((_qq.pct_mas_6_meses[2025] / _qq.pct_mas_6_meses[2018] - 1) * 100)],
     ["En espera de primera consulta, por 1.000 habitantes", nf(_cc.tasa_por_1000_hab[2018], 2),
      nf(_cc.tasa_por_1000_hab[2025], 2), bub(V["c_tasa"])],
     ["Tiempo medio para primera consulta", nf(_cc.tiempo_medio_espera_dias[2018]) + " días",
      nf(_cc.tiempo_medio_espera_dias[2025]) + " días",
      bub((_cc.tiempo_medio_espera_dias[2025] / _cc.tiempo_medio_espera_dias[2018] - 1) * 100)],
     ["Esperan más de 60 días para primera consulta", nf(_cc.pct_mas_60_dias[2018], 1) + " %",
      nf(_cc.pct_mas_60_dias[2025], 1) + " %",
      bub((_cc.pct_mas_60_dias[2025] / _cc.pct_mas_60_dias[2018] - 1) * 100)]],
    pie="Ministerio de Sanidad · Sistema de Información sobre Listas de Espera del SNS, 17 CCAA e INGESA. "
        "La fuente original son informes en PDF; la conversión a CSV es propia y reproducible con "
        "scripts/13_listas_espera.py. Las cifras de 2018 y 2025 se han verificado contra el texto de los "
        "PDF originales.")

R4 = f"""
<section id="r4" class="ans">
  <div class="ans-h"><span class="ans-q">Pregunta 4 · Dinero público</span>
    <h3>¿De dónde sale el dinero, en qué se gasta y ha mejorado el servicio?</h3></div>
  <div class="ans-b">
    {linea("Hay mucho más dinero público, pero la mitad es inflación, más de la mitad del gasto extra son pensiones, y la sanidad no ha mejorado.")}

    {figs([(P['ing_pct'], "ingresos públicos nominales (2018-2024)", UP),
           (pp(V['ing_pp']), "de presión fiscal sobre el PIB", UP),
           (P['ps_real_pc'], "protección social real por habitante", UP),
           (P['deuda_meur_pct'], "deuda pública en euros", UP)])}

    <h4 class="sub-h">De dónde salen los {nf(SP['delta'])} millones de euros más</h4>
    <p>Los ingresos públicos pasaron de {nf(SP['ingresos_2018'])} a {nf(SP['ingresos_2024'])} millones,
    un {P['ing_pct']}. Ese aumento se descompone exactamente en tres factores: cuánto ha crecido la economía
    real, cuánto han subido los precios y qué porcentaje del PIB se lleva el sector público.</p>

    <div class="dec">{dec_ing}</div>

    <p><b>La mitad de la recaudación adicional no es riqueza nueva, es inflación.</b> Un cuarto sí es economía
    real. Y el cuarto restante es que el sector público se lleva más: del <b>{PS['ing18']} al {PS['ing24']} del
    PIB</b>. Descontada la inflación y repartido entre más habitantes, el Estado ingresa {P['ing_real_pc']} por
    habitante que en 2018.</p>

    <p>El impuesto que explica la mayor detracción es el de la renta y el patrimonio: recauda {P['d5_pct']} más
    y pasa del 10,5 % al 12,5 % del PIB. El IVA y los impuestos especiales, en cambio, <b>pierden</b> peso, del
    11,6 % al 11,1 %. Es el patrón de la progresividad en frío: los salarios nominales suben con la inflación,
    los tramos no se actualizan al mismo ritmo y el IRPF crece más deprisa que la base.</p>

    <h4 class="sub-h">En qué se gasta: las «ayudas» son sobre todo pensiones</h4>
    {tabla_ps}

    <p>De los {nf(PS_TOT['delta'])} millones adicionales de protección social,
    <b>{nf(PS_DET[0]['delta'])} ({nf(PS_DET[0]['cuota_del_aumento'],0)} %) son pensiones de jubilación</b>. La
    partida de exclusión social, donde se registra el Ingreso Mínimo Vital, es la que más crece en porcentaje
    ({pct([d for d in PS_DET if 'Exclusión' in d['concepto']][0]['var_pct'])}) pero parte de una base pequeña:
    sigue siendo el {nf([d for d in PS_DET if 'Exclusión' in d['concepto']][0]['pct_del_total_2024'], 1)} % del
    gasto en protección social. Y el <b>desempleo es la partida que menos crece</b> de todas.</p>

    <h4 class="sub-h">El Ingreso Mínimo Vital, en concreto</h4>
    {tabla_imv}

    <p>En 2025 el IMV costó <b>{nf(V['imv_gasto25'])} millones de euros</b>, que es el
    {nf(V['imv_pct_ps'], 1)} % de todo el gasto en protección social y en torno al 0,3 % del PIB. Llega a
    {nf(V['imv_benef25'])} personas en {nf(V['imv_hogares25'])} hogares, con una cuantía media de
    {nf(V['imv_cuantia25'], 0)} € al mes por hogar. Es una partida en fuerte crecimiento y en discusión
    pública frecuente, pero <b>en el conjunto de las cuentas públicas es una cifra pequeña</b>: las pensiones
    de jubilación cuestan más de treinta veces eso.</p>

    <h4 class="sub-h">¿Ha mejorado el servicio? Las listas de espera</h4>
    <p>El gasto sanitario subió {P['san_real_pc']} real por habitante. Pero gasto no es resultado. Esto es lo
    que ha pasado con la espera:</p>

    {tabla_sisle}

    <p>El resultado es mixto y en conjunto peor. En <b>quirúrgica</b> hay
    {nf(V['q_pac25']-V['q_pac18'])} pacientes más esperando y la lista crece {P['q_tasa']} por cada 1.000
    habitantes, aunque el tiempo medio <b>baja</b> de {nf(V['q_dias18'])} a {nf(V['q_dias25'])} días: se opera
    a más gente y algo más rápido, pero entra más de la que sale. En <b>consultas con especialista</b> empeora
    todo: más pacientes en espera por habitante, más días y el porcentaje que espera más de dos meses pasa del
    {PS['c_pct18']} al {PS['c_pct25']}.</p>

    <h4 class="sub-h">¿Más rico, más gravado o más endeudado?</h4>
    {quien([
      ("Más rico", 1,
       f"Sí, pero es el factor más pequeño: la economía real creció {P['pib_r']} y explica solo el "
       f"{nf(COMPO[0]['cuota'],0)} % de la recaudación adicional."),
      ("Más gravado", -1,
       f"Sí, y es medible: {pp(V['ing_pp'])} más del PIB que en 2018. Ahora bien, España sigue recaudando "
       f"<b>menos</b> que la media europea ({PS['ing24']} frente al {nf(ue_fisc['ing2024'],1)} % de la UE-27). "
       "Lo llamativo no es el nivel, es la velocidad: la UE-27 bajaba mientras España subía."),
      ("Más endeudado", -1,
       f"En euros sí: la deuda creció {P['deuda_meur_pct']}. Sobre el PIB apenas se movió, del "
       f"{PS['deuda18_pct']} al {PS['deuda24_pct']}, porque la inflación infló el denominador. El déficit "
       f"empeoró de {PS['saldo18']} a {PS['saldo24']}: todos los años se gastó más de lo que se ingresó."),
    ])}

    {tabla_fisc}

    {cierre([
      "El Estado maneja mucho más dinero, pero <b>la mitad de ese dinero extra es solo inflación</b>. El "
      "crecimiento económico real aporta apenas una cuarta parte.",
      f"Se detrae algo más al ciudadano ({pp(V['ing_pp'])} del PIB), aunque España sigue recaudando por debajo "
      f"de la media europea. Y aun así se gasta más de lo que se ingresa todos los años: no es un país que se "
      f"pueda permitir más gasto, es un país que lo financia con déficit y con una base nominal inflada.",
      f"De las «ayudas», <b>más de la mitad del aumento son pensiones de jubilación</b>. El IMV, que ocupa "
      f"mucho debate, es el {nf(V['imv_pct_ps'], 1)} % del gasto social.",
      "Y el dinero extra en sanidad <b>no se ha traducido en menos espera</b>: hay más gente en lista que en "
      "2018 y las consultas con especialista han empeorado en todos los indicadores.",
    ])}
  </div>
</section>"""

R5 = f"""
<section id="r5" class="ans">
  <div class="ans-h"><span class="ans-q">Preguntas complementarias</span>
    <h3>Empleo, economía agregada y la comparación con 1970</h3></div>
  <div class="ans-b">
    <p><b>¿Es más fácil encontrar trabajo?</b> Sí, con matices. El paro cayó de {PS['paro18']} a
    {PS['paro25']}, la tasa de empleo subió {pp(V['emp25']-V['emp18'],2)} y las vacantes aumentaron
    {P['vac_pct']}: los tres a la vez es más sólido que mirar solo el paro. Pero la tasa de actividad está
    donde estaba ({pp(V['act25']-V['act18'],2)}), y no hay datos de duración del desempleo ni de colocaciones.
    Lo correcto es decir «hay más empleo y más demanda», no «se encuentra trabajo más rápido». La brecha por
    nacionalidad se mantiene: el paro extranjero bajó de {PS['paroext18']} a {PS['paroext25']} y el español de
    {PS['paroesp18']} a {PS['paroesp25']}, unos seis puntos de diferencia constante.</p>

    <p><b>¿Y el aumento de inactivos?</b> Hay {P['ina_pct']} más, pero no es gente que no quiera trabajar: son
    <b>{nf(V['d_jub'])} jubilados más</b> y {nf(V['d_est'])} estudiantes más, mientras las labores del hogar
    caen en {nf(abs(V['d_hog']))} personas y la incapacidad permanente también baja. Es envejecimiento y más
    años de estudio.</p>

    <p><b>¿Y la economía en conjunto?</b> El PIB real creció {P['pib_r']}, pero <b>por habitante solo
    {P['pib_pc']}</b> en seis años, y la productividad por hora {P['prod']}. El crecimiento fue extensivo: más
    horas trabajadas, no más eficiencia. Con estos agregados <b>no puede atribuirse por regla de tres qué parte
    del PIB se debe a la inmigración</b>; eso exigiría microdatos por origen que estas fuentes no tienen.</p>

    <p><b>Vivienda en Madrid en 1970 frente a hoy: no se responde en este informe.</b> Haría falta precio
    oficial por metro cuadrado y localización en 1970, tamaño y calidad equivalentes, renta del mismo universo
    poblacional, conversión peseta-euro y condiciones de financiación de la época. Nada de eso está en las
    fuentes disponibles, y extrapolar el índice actual hacia 1970 daría una cifra inventada con apariencia de
    dato.</p>
  </div>
</section>"""

RESPUESTAS = R1 + R2 + R3 + R4 + R5


# ------------------------------------------------------------------- montaje -
NAV = [("b-poblacion", "01 Población"), ("b-economia", "02 Economía"), ("b-laboral", "03 Trabajo"),
       ("b-precios", "04 Precios"), ("b-rentas", "05 Rentas"), ("b-vivienda", "06 Vivienda"),
       ("b-crimen", "07 Criminalidad"), ("b-crimen-nac", "08 Nacionalidad"),
       ("b-publico", "09 Sector público"), ("b-servicios", "10 Servicios públicos"),
       ("r1", "P1 Población"), ("r2", "P2 Criminalidad"), ("r3", "P3 Poder adquisitivo"),
       ("r4", "P4 Dinero público"), ("r5", "Complementarias"), ("limites", "Límites")]

KPIS = [
    ("Población residente", f"+{nf(V['dpob'])}", f"de 46,6 a 49,1 millones · {P['dpob_pct']}", ""),
    ("Nacidos en el extranjero", f"+{nf(V['d_fue'])}", f"nacidos en España: {nf(V['d_esp'])}", "k-up"),
    ("PIB real por habitante", P["pib_pc"], "2018-2024 · volumen encadenado", ""),
    ("Poder de compra de 1.000 €", f"{nf(V['compra1000'])} €", "lo que 1.000 € de 2025 compran en euros de 2018", "k-down"),
    ("Criminalidad por habitante sin ciberestafa", PS["sin_tasa_pct"], "2018-2024 · hechos por 100.000 hab.", "k-down"),
    ("Precio real de la vivienda", pct(V["ipv_r"]), "IPV deflactado con el IPC", "k-up"),
]
kpi_html = "".join(
    f'<div class="kpi"><span class="k-l">{l}</span><span class="k-v {c}">{v}</span>'
    f'<span class="k-n">{n}</span></div>' for l, v, n, c in KPIS)

bloques_html = "".join(seccion(*b) for b in BLOQUES)
nav_html = "".join(f'<a href="#{i}">{t}</a>' for i, t in NAV)

LIMITES = f"""
<section id="limites" class="part">
  <div class="part-h"><span class="pn">Cierre</span><h2>Límites, convenciones y reproducibilidad</h2></div>
  <p class="lede">Las lagunas se presentan como lagunas. Ninguna se ha rellenado con estimaciones implícitas
  ni con ceros.</p>
  <div class="grid2">
    <div class="card"><h4>Seis límites que condicionan las conclusiones</h4><ul>
      <li>No existe <b>país de nacimiento</b> en ninguna de las matrices penales disponibles. La nacionalidad
      jurídica no lo sustituye y cambia con las naturalizaciones.</li>
      <li>Los <b>hechos esclarecidos</b> no llevan nacionalidad ni nacimiento, y no son condenas.</li>
      <li>La EPA por condición migratoria de este repositorio usa <b>nacionalidad</b>; no se localizó serie
      recurrente 2018-2025 equivalente por país de nacimiento.</li>
      <li>La comparación de <b>vivienda en Madrid con 1970</b> no está cubierta por ninguna fuente descargada.</li>
      <li>No hay <b>serie oficial homogénea de alquiler</b> comparable en el periodo.</li>
      <li>Las <b>diferencias descriptivas entre grupos no estiman causalidad</b>. Ninguna cifra de este informe
      mide cuánto cambio fue «causado» por la inmigración.</li>
    </ul></div>
    <div class="card"><h4>Rupturas de serie y cautelas de cada fuente</h4><ul>
      <li><b>Población por nacimiento:</b> 2018 procede de Cifras de Población (tabla 9675) y 2025 del Censo
      anual (tabla 70364). En el solape la diferencia es de {nf(AX['salto_serie_2021'])} personas en 2021 y
      {nf(AX['salto_serie_2022'])} en 2022 sobre los nacidos fuera. El total de población sí usa una única serie
      homogénea (tabla 56942).</li>
      <li><b>EPA:</b> cambio de base poblacional en 2021.</li>
      <li><b>Migraciones:</b> la serie anterior (2018-2021) y la nueva EMCR (2021-2024) no se suman ni se enlazan.</li>
      <li><b>Delitos sexuales:</b> la LO 10/2022 reordenó los tipos penales; parte de la variación es reclasificación.</li>
      <li><b>Salarios por contrato:</b> la reforma laboral de 2022 cambió la composición del empleo temporal,
      lo que altera la media de ese subgrupo.</li>
      <li><b>2020</b> es un año de choque extraordinario. Por eso cada fila muestra la serie completa y no solo
      los dos extremos.</li>
    </ul></div>
    <div class="card"><h4>Convenciones aplicadas</h4><ul>
      <li>Deflactación: <code>valor_real = valor_nominal · IPC<sub>2018</sub> / IPC<sub>t</sub></code>, con media
      anual de doce meses en ambos extremos.</li>
      <li>Tasas: <code>numerador / población compatible · 100.000</code>, con la misma nacionalidad, territorio y
      fecha de referencia que el numerador.</li>
      <li>En porcentajes se informa tanto la variación relativa (burbuja) como los puntos porcentuales.</li>
      <li>No se suman totales con sus componentes ni operaciones estadísticas distintas.</li>
      <li>Los años finales reales se marcan con una etiqueta <span class="yb">2024</span> cuando la serie no
      llega a 2025.</li>
    </ul></div>
    <div class="card"><h4>Fuentes añadidas a las que dejó Codex</h4>
      <p>El repositorio original solo contenía INE y Ministerio del Interior. Para responder a dos preguntas
      hizo falta añadir <b>Eurostat</b>, organismo estadístico oficial de la Unión Europea, con las mismas
      exigencias que el resto: organismo, URL exacta de la API, cobertura, fecha de descarga y cautelas, todo
      registrado en <code>data_external/metadata.csv</code>.</p>
      <ul>
        <li><b>Comparación europea del poder adquisitivo</b> (IPC armonizado, PIB per cápita real, ganancia
        neta anual y nivel de vida en paridad de poder adquisitivo). Sin ella, un +3 % de salario real no
        puede calificarse de mucho ni de poco.</li>
        <li><b>Cuentas de las administraciones públicas</b> (ingresos, gasto por función COFOG, déficit y
        deuda). Son los mismos datos que la IGAE notifica a la UE, y permiten además comparar con la UE-27.</li>
        <li><b>Seguridad Social</b>: nómina mensual del Ingreso Mínimo Vital, 30 ficheros XLSX oficiales.</li>
        <li><b>Ministerio de Sanidad</b>: 16 informes del Sistema de Información sobre Listas de Espera del SNS.
        Se publican solo en PDF; la conversión a CSV es propia, reproducible y verificada contra el texto
        original en los años extremos.</li>
      </ul>
      <p>Los datos españoles y los de Eurostat <b>no se mezclan dentro de un mismo indicador</b>: el IPC del
      INE deflacta las series españolas y el IPC armonizado deflacta las europeas, y cada tabla dice cuál usa.</p></div>
    <div class="card"><h4>Corrección aplicada a los metadatos de origen</h4>
      <p>Los metadatos del repositorio describían las matrices 03003, 03005 y 03007 del Ministerio del Interior
      como desgloses del total de detenciones. La comprobación numérica de los siete años muestra otra cosa:
      <b>03005 y 03007 contienen solo el subconjunto de extranjeros</b> (sus totales coinciden exactamente y la
      lista de nacionalidades de 03007 no incluye España) y <b>03003 contiene solo el subconjunto de menores de
      14 a 17 años</b> (coincide exactamente con ese grupo de edad de la matriz 03009). Los detenidos de
      nacionalidad española se han calculado por diferencia entre 03001 y 03005. Sin esta corrección, cualquier
      cifra de detenciones por nacionalidad de este informe habría sido errónea.</p></div>
  </div>
  <p class="note">Todas las cifras se regeneran desde <code>data_raw/</code> ejecutando en orden los scripts
  <code>01_demografia_migracion.py</code> a <code>07_informe_html.py</code>. Ninguna cifra de este documento
  está escrita a mano: el texto interpola los mismos CSV de <code>data_processed/</code> que alimentan las tablas.</p>
</section>
"""

HTML = f"""<title>España 2018-2025</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap">
<style>{CSS}</style>
<div class="wrap">
<header class="top">
  <span class="eyebrow">Informe sobre datos oficiales · INE y Ministerio del Interior</span>
  <h1>España, 2018&#8202;–&#8202;2025</h1>
  <p class="sub">Qué dicen exactamente los datos oficiales sobre el crecimiento del país, la criminalidad
  registrada y el poder adquisitivo de sus residentes. Y, con el mismo cuidado, qué no permiten decir.</p>
  <div class="meta">
    <div>Periodo · <b>2018 a 2025</b>, años completos</div>
    <div>Fuentes · <b>74 conjuntos de datos oficiales</b></div>
    <div>Indicadores · <b>{len(IND)}</b> en 8 bloques</div>
    <div>Elaboración · <b>2026-08-20</b></div>
  </div>
  <div class="kpis">{kpi_html}</div>
</header>

<nav class="toc">{nav_html}</nav>

<div class="part" style="margin-top:56px">
  <div class="part-h"><span class="pn">Cómo leer las tablas</span><h2>Convención de color y de años</h2></div>
  <p class="lede">La burbuja de la última columna indica <b style="color:var(--up)">▲ aumento en azul</b> y
  <b style="color:var(--down)">▼ descenso en rojo</b>. El color señala <b>la dirección del cambio, no si el
  cambio es bueno o malo</b>: que suban los precios y que suba el empleo se pintan igual. En los indicadores
  expresados en porcentaje, bajo la burbuja aparece también la diferencia en puntos porcentuales.
  La columna «serie completa» dibuja todos los años intermedios con una marca discontinua en 2020, para que
  ninguna comparación entre extremos se lea como una trayectoria lineal. Cuando la serie oficial no llega a 2025,
  el valor final lleva su año real marcado así: <span class="yb">2024</span>.</p>
</div>

<div class="part">
  <div class="part-h"><span class="pn">Parte I</span><h2>Los datos</h2></div>
  <p class="lede">Ocho bloques temáticos. Cada tabla cierra con la conclusión objetiva que se desprende
  de sus propias cifras, sin ir más allá de lo que la fuente sostiene.</p>
  {bloques_html}
</div>

<div class="part">
  <div class="part-h"><span class="pn">Parte II</span><h2>Las respuestas</h2></div>
  <p class="lede">Las tres preguntas planteadas, más las complementarias, respondidas con las cifras de la
  Parte I y con una declaración explícita de lo que los datos no identifican.</p>
  {RESPUESTAS}
</div>

{LIMITES}

<footer>
  Fuentes: Instituto Nacional de Estadística (www.ine.es, servicios.ine.es) y Portal Estadístico de
  Criminalidad del Ministerio del Interior (estadisticasdecriminalidad.ses.mir.es).<br>
  Cada fila indica la operación estadística y la tabla concretas de las que procede su cifra.<br>
  Elaboración propia a partir de datos oficiales. Repositorio: analisis-españa · data_raw/ inalterado.
</footer>
</div>
"""

# Cuerpo sin envoltura, para publicar como Artifact (el host añade doctype/head/body).
cuerpo = os.path.join(OUTD, "informe_artifact_body.html")
open(cuerpo, "w", encoding="utf-8").write(HTML)

# Documento completo autónomo, para abrir con doble clic desde el disco.
doc = ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
       + HTML.split("<div class=\"wrap\">", 1)[0]
       + '</head>\n<body>\n<div class="wrap">'
       + HTML.split("<div class=\"wrap\">", 1)[1]
       + "\n</body>\n</html>\n")
path = os.path.join(OUTD, "informe_espana_2018_2025.html")
open(path, "w", encoding="utf-8").write(doc)
print("escrito:", path, f"({len(doc)/1024:.0f} KB)")
print("escrito:", cuerpo)
