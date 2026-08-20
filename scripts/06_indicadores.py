"""Ensambla todos los bloques en una tabla única de indicadores con trazabilidad.
Cada fila lleva: bloque, descripción, valor inicial, valor final, años reales,
unidad, variación, y la fuente (operación + tabla) de la que sale.
Salida: data_processed/indicadores_finales.csv y outputs/indicadores.json
"""
import sys, os, json
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data_processed")
OUTD = os.path.join(ROOT, "outputs")
os.makedirs(OUTD, exist_ok=True)

A = pd.read_csv(os.path.join(PROC, "a_demografia.csv"), index_col=0)
B = pd.read_csv(os.path.join(PROC, "b_economia.csv"), index_col=0)
C = pd.read_csv(os.path.join(PROC, "c_laboral.csv"), index_col=0)
D = pd.read_csv(os.path.join(PROC, "d_precios.csv"), index_col=0)
E = pd.read_csv(os.path.join(PROC, "e_criminalidad_resumen.csv"), index_col=0)
HC = pd.read_csv(os.path.join(PROC, "e_hechos_conocidos_tipologia.csv"), index_col=0)
IPCG = pd.read_csv(os.path.join(PROC, "d_ipc_grupos.csv"), index_col=0)
AX = json.load(open(os.path.join(PROC, "a_extra.json")))
EX = json.load(open(os.path.join(PROC, "e_descomposicion.json")))

filas = []


def add(bloque, desc, serie, y0=2018, y1=None, unidad="", fmt="num", dec=0,
        fuente="", nota="", invertir_color=False, pp=False):
    """invertir_color: True cuando 'subir' es malo (p. ej. paro, precios)."""
    s = serie.dropna()
    if y1 is None:
        y1 = int(s.index.max())
    if y0 not in s.index or y1 not in s.index:
        raise KeyError(f"{desc}: faltan años {y0}/{y1} (disponibles {list(s.index)})")
    v0, v1 = float(s.loc[y0]), float(s.loc[y1])
    serie = [[int(a), float(v)] for a, v in s.loc[y0:y1].items()]
    filas.append({"bloque": bloque, "descripcion": desc, "anyo_ini": int(y0), "anyo_fin": int(y1),
                  "valor_ini": v0, "valor_fin": v1, "unidad": unidad, "fmt": fmt, "dec": dec,
                  "var_pct": (v1 / v0 - 1) * 100 if v0 else None,
                  "var_abs": v1 - v0, "pp": pp, "serie": serie,
                  "fuente": fuente, "nota": nota, "invertir_color": invertir_color})


S = lambda df, col: df[col]

# ========================= BLOQUE 1: POBLACIÓN Y MIGRACIÓN ==================
F_POB = "INE, Cifras de Población / Censo anual · tabla 56942 · población a 1 de enero"
add("poblacion", "Población residente en España", S(A, "pob_total"), 2018, 2025, "personas",
    fuente=F_POB)
add("poblacion", "Población nacida en España", S(A, "nacidos_espana_enlazada"), 2018, 2025, "personas",
    fuente="INE · tabla 9675 (2018) y tabla 70364, Censo anual (2025) · 1 de enero",
    nota="Serie enlazada: 2018 procede de Cifras de Población y 2025 del Censo anual. En el solape (2021-2022) la diferencia entre ambas fuentes es de 40.000 a 103.000 personas.")
add("poblacion", "Población nacida en el extranjero", S(A, "nacidos_fuera_enlazada"), 2018, 2025, "personas",
    fuente="INE · tabla 9675 (2018) y tabla 70364, Censo anual (2025) · 1 de enero",
    nota="País de nacimiento, que es la variable correcta para aproximar origen migratorio. Serie enlazada; ver nota anterior.")
add("poblacion", "Peso de los nacidos en el extranjero sobre el total", S(A, "pct_nacidos_fuera"),
    2018, 2025, "%", dec=1, pp=True,
    fuente="INE · tablas 9675 y 70364")
add("poblacion", "Población con nacionalidad española", S(A, "pob_nac_espanola"), 2018, 2025, "personas",
    fuente=F_POB,
    nota="Nacionalidad jurídica, no origen: incluye a las personas nacidas fuera que se han nacionalizado.")
add("poblacion", "Población con nacionalidad extranjera", S(A, "pob_nac_extranjera"), 2018, 2025, "personas",
    fuente=F_POB,
    nota="Nacionalidad jurídica, no origen.")
add("poblacion", "Adquisiciones de nacionalidad española (en el año)", S(A, "adquisiciones_nacionalidad"),
    2018, 2025, "personas",
    fuente="INE, Adquisiciones de Nacionalidad Española de Residentes · tabla 15073",
    nota=f"Acumulado 2018-2025: {int(A['adquisiciones_nacionalidad'].loc[2018:2025].sum()):,} personas. Explica por qué la cifra de 'extranjeros' crece menos que la de 'nacidos fuera'.".replace(",", "."))
add("poblacion", "Población de 65 y más años", S(A, "pob_65mas"), 2018, 2025, "personas", fuente=F_POB)
add("poblacion", "Peso de los mayores de 65 años", S(A, "pct_65mas"), 2018, 2025, "%", dec=1, pp=True,
    fuente=F_POB)
add("poblacion", "Población de 15 a 64 años (edad potencialmente activa)", S(A, "pob_15_64"),
    2018, 2025, "personas", fuente=F_POB)

# ========================= BLOQUE 2: ECONOMÍA ===============================
F_CNA = "INE, Contabilidad Nacional Anual, Revisión Estadística 2024"
add("economia", "PIB a precios de mercado (precios corrientes)", S(B, "pib_nominal_meur"), 2018, 2024,
    "millones €", fuente=F_CNA + " · tabla 1", nota="Euros corrientes: incluye el efecto de la inflación.")
add("economia", "PIB real (índice de volumen encadenado, 2020 = 100)", S(B, "pib_volumen_idx2020"),
    2018, 2024, "índice", dec=2, fuente=F_CNA + " · tabla 4",
    nota="Medida real oficial del crecimiento: descuenta los precios.")
add("economia", "PIB per cápita (precios corrientes)", S(B, "pib_percapita_nominal_eur"), 2018, 2024, "€",
    fuente="INE, Contabilidad Regional de España RE2024 · PIB per cápita, Total Nacional")
add("economia", "PIB real por habitante (índice derivado, 2018 = 100)",
    S(B, "pib_real_percapita_idx") / B["pib_real_percapita_idx"].loc[2018] * 100, 2018, 2024, "índice",
    dec=1, fuente="Derivado: índice de volumen del PIB ÷ población media de la CNA",
    nota="Cálculo propio a partir de dos series oficiales; no es una serie publicada por el INE.")
add("economia", "Renta nacional disponible neta per cápita (nominal)", S(B, "rnd_neta_percapita_eur"),
    2018, 2024, "€", fuente=F_CNA + " · Renta nacional disponible")
add("economia", "Remuneración de los asalariados", S(B, "remuneracion_asalariados_meur"), 2018, 2024,
    "millones €", fuente=F_CNA + " · Renta nacional disponible")
add("economia", "Puestos de trabajo totales", S(B, "puestos_totales_miles") * 1000, 2018, 2024, "puestos",
    fuente=F_CNA + " · Empleo total por rama", nota="Puestos de trabajo, no personas.")
add("economia", "Horas efectivamente trabajadas", S(B, "horas_trabajadas_miles") * 1000, 2018, 2024, "horas",
    fuente=F_CNA + " · Horas trabajadas por rama")
add("economia", "Productividad por hora trabajada (índice derivado, 2018 = 100)",
    S(B, "productividad_hora_idx") / B["productividad_hora_idx"].loc[2018] * 100, 2018, 2024, "índice",
    dec=1, fuente="Derivado: índice de volumen del PIB ÷ horas trabajadas (CNA RE2024)")
add("economia", "Población media usada por la Contabilidad Nacional (1 de julio)",
    S(B, "poblacion_cna_miles") * 1000, 2018, 2024, "personas", fuente=F_CNA)

# ========================= BLOQUE 3: MERCADO DE TRABAJO =====================
F_EPA = "INE, Encuesta de Población Activa · media de los cuatro trimestres"
add("laboral", "Tasa de paro", S(C, "tasa_paro"), 2018, 2025, "%", dec=2, pp=True, invertir_color=True,
    fuente=F_EPA + " · tabla 65349")
add("laboral", "Tasa de empleo (ocupados sobre población de 16 y más años)", S(C, "tasa_empleo"),
    2018, 2025, "%", dec=2, pp=True, fuente=F_EPA + " · tabla 65349")
add("laboral", "Tasa de actividad", S(C, "tasa_actividad"), 2018, 2025, "%", dec=2, pp=True,
    fuente=F_EPA + " · tabla 65349")
add("laboral", "Tasa de paro · población de nacionalidad española", S(C, "tasa_paro_nacionalidad_esp"),
    2018, 2025, "%", dec=2, pp=True, invertir_color=True, fuente=F_EPA + " · tabla 65336",
    nota="Nacionalidad, no país de nacimiento.")
add("laboral", "Tasa de paro · población de nacionalidad extranjera", S(C, "tasa_paro_nacionalidad_ext"),
    2018, 2025, "%", dec=2, pp=True, invertir_color=True, fuente=F_EPA + " · tabla 65336",
    nota="Nacionalidad, no país de nacimiento.")
add("laboral", "Tasa de actividad · población de nacionalidad extranjera",
    S(C, "tasa_actividad_nacionalidad_ext"), 2018, 2025, "%", dec=2, pp=True,
    fuente=F_EPA + " · tabla 65300", nota="Nacionalidad, no país de nacimiento.")
add("laboral", "Puestos de trabajo vacantes (media trimestral)", S(C, "vacantes_media_trimestral"),
    2018, 2025, "vacantes", fuente="INE, Encuesta Trimestral de Coste Laboral · tabla 6064",
    nota="Vacantes declaradas por las empresas; no mide por sí sola la facilidad individual de encontrar empleo.")
add("laboral", "Población inactiva total", S(C, "inactivos_total_miles") * 1000, 2018, 2025, "personas",
    fuente=F_EPA + " · tabla 65343",
    nota="La inactividad de la EPA incluye jubilados, estudiantes, labores del hogar e incapacidad. No mide dependencia de prestaciones ni rechazo a trabajar.")
add("laboral", "Inactivos: jubilados", S(C, "inactivos_jubilados_miles") * 1000, 2018, 2025, "personas",
    fuente=F_EPA + " · tabla 65343")
add("laboral", "Inactivos: estudiantes", S(C, "inactivos_estudiantes_miles") * 1000, 2018, 2025, "personas",
    fuente=F_EPA + " · tabla 65343")
add("laboral", "Inactivos: labores del hogar", S(C, "inactivos_labores_hogar_miles") * 1000, 2018, 2025,
    "personas", fuente=F_EPA + " · tabla 65343")

# ========================= BLOQUE 4: PRECIOS ================================
F_IPC = "INE, Índice de Precios de Consumo · tabla 50902 · media anual de los 12 meses"
add("precios", "IPC general (media anual, base 2021 = 100)", S(D, "ipc_general_media_anual"), 2018, 2025,
    "índice", dec=2, invertir_color=True, fuente=F_IPC)
add("precios", "Euros de 2025 necesarios para comprar lo que 1.000 € compraban en 2018",
    S(D, "euros_necesarios_para_1000e_2018"), 2018, 2025, "€", dec=0, invertir_color=True, fuente=F_IPC)
add("precios", "Lo que 1.000 € compran hoy, medido en euros de 2018",
    S(D, "poder_compra_de_1000e_de_2018"), 2018, 2025, "€ de 2018", dec=0, fuente=F_IPC)
for g, lab in [("Alimentos y bebidas no alcohólicas", "Precios de alimentos y bebidas no alcohólicas"),
               ("Vivienda, agua, electricidad, gas y otros combustibles",
                "Precios de vivienda, agua, electricidad y gas"),
               ("Transporte", "Precios del transporte"),
               ("Restaurantes y hoteles", "Precios de restaurantes y hoteles"),
               ("Sanidad", "Precios de sanidad"),
               ("Vestido y calzado", "Precios de vestido y calzado")]:
    add("precios", lab + " (índice)", IPCG[g], 2018, 2025, "índice", dec=2, invertir_color=True,
        fuente=F_IPC + " · grupos ECOICOP")

# ========================= BLOQUE 5: RENTAS Y SALARIOS ======================
add("rentas", "Salario bruto medio anual (nominal)", S(D, "salario_medio_nominal"), 2018, 2024, "€",
    fuente="INE, Encuesta Anual de Estructura Salarial · tabla 28200 · ambos sexos, todos los contratos")
add("rentas", "Salario bruto medio anual en euros constantes de 2018", S(D, "salario_medio_real_e2018"),
    2018, 2024, "€ de 2018",
    fuente="Derivado: tabla 28200 deflactada con la media anual del IPC general (tabla 50902)")
add("rentas", "Salario mensual del decil 1 (hombres), euros constantes de 2018",
    S(D, "salario_decil1_hombres_real_e2018"), 2018, 2024, "€ de 2018",
    fuente="Derivado: INE tabla 10910 (decil de salarios) deflactada con el IPC",
    nota="La tabla descargada solo publica el desglose por sexo; no existe una serie 'ambos sexos'.")
add("rentas", "Salario mensual del decil 10 (hombres), euros constantes de 2018",
    S(D, "salario_decil10_hombres_real_e2018"), 2018, 2024, "€ de 2018",
    fuente="Derivado: INE tabla 10910 deflactada con el IPC")
add("rentas", "Salario mensual del decil 1 (mujeres), euros constantes de 2018",
    S(D, "salario_decil1_mujeres_real_e2018"), 2018, 2024, "€ de 2018",
    fuente="Derivado: INE tabla 10910 deflactada con el IPC")
add("rentas", "Salario mensual del decil 10 (mujeres), euros constantes de 2018",
    S(D, "salario_decil10_mujeres_real_e2018"), 2018, 2024, "€ de 2018",
    fuente="Derivado: INE tabla 10910 deflactada con el IPC")
add("rentas", "Renta neta media por persona (nominal)", S(D, "renta_persona_nominal_anyorenta"),
    2018, 2024, "€",
    fuente="INE, Encuesta de Condiciones de Vida · tabla 9947 · encuestas 2019 y 2025",
    nota="Etiquetada por AÑO DE RENTA: la ECV pregunta por los ingresos del año anterior a la entrevista.")
add("rentas", "Renta neta media por persona en euros constantes de 2018",
    S(D, "renta_persona_real_e2018_anyorenta"), 2018, 2024, "€ de 2018",
    fuente="Derivado: INE tabla 9947 deflactada con el IPC del año de renta")
add("rentas", "Renta media por unidad de consumo en euros constantes de 2018",
    S(D, "renta_unidad_consumo_real_e2018_anyorenta"), 2018, 2024, "€ de 2018",
    fuente="Derivado: INE tabla 9947 deflactada con el IPC del año de renta",
    nota="La unidad de consumo corrige por tamaño y composición del hogar.")
add("rentas", "Tasa de riesgo de pobreza o exclusión social (AROPE)", S(D, "arope_pct_encuesta"),
    2018, 2025, "%", dec=1, pp=True, invertir_color=True,
    fuente="INE, ECV · tabla 74860 · definición Europa 2030, etiquetado por año de encuesta")
add("rentas", "AROPE en hogares de un adulto con hijos dependientes",
    S(D, "arope_monoparental_pct_encuesta"), 2018, 2025, "%", dec=1, pp=True, invertir_color=True,
    fuente="INE, ECV · tabla 74860")

# ========================= BLOQUE 6: VIVIENDA ===============================
add("vivienda", "Índice de precios de la vivienda (media anual, base 2015 = 100)",
    S(D, "ipv_general_idx2015"), 2018, 2025, "índice", dec=1, invertir_color=True,
    fuente="INE, Índice de Precios de Vivienda · tabla 25173",
    nota="Es un índice de precios, no un precio en euros por metro cuadrado.")
add("vivienda", "Precio real de la vivienda descontada la inflación (2018 = 100)",
    S(D, "ipv_real_e2018_idx"), 2018, 2025, "índice", dec=1, invertir_color=True,
    fuente="Derivado: IPV (tabla 25173) deflactado con el IPC general (tabla 50902)")
add("vivienda", "Hipotecas constituidas sobre viviendas (año completo)",
    S(D, "hipotecas_viviendas_numero"), 2018, 2025, "hipotecas",
    fuente="INE, Estadística de Hipotecas · tabla 76317 · suma de los 12 meses")
add("vivienda", "Importe medio de la hipoteca sobre vivienda (nominal)",
    S(D, "hipotecas_importe_medio_eur"), 2018, 2025, "€", fuente="INE · tabla 76317")
add("vivienda", "Importe medio de la hipoteca en euros constantes de 2018",
    S(D, "hipotecas_importe_medio_real_e2018"), 2018, 2025, "€ de 2018",
    fuente="Derivado: tabla 76317 deflactada con el IPC")
add("vivienda", "Plazo medio de las nuevas hipotecas sobre vivienda",
    S(D, "hipoteca_plazo_medio_anyos"), 2018, 2025, "años", dec=1,
    fuente="INE, Estadística de Hipotecas · tabla 24458 · media de los 12 meses")

# ========================= BLOQUE 7: CRIMINALIDAD REGISTRADA ================
F_MIR = "Ministerio del Interior, Portal Estadístico de Criminalidad · años naturales completos"
add("crimen", "Infracciones penales conocidas (hechos, no personas)", S(E, "hechos_conocidos"),
    2018, 2024, "hechos", invertir_color=True, fuente=F_MIR + " · tabla 01001")
add("crimen", "Infracciones penales conocidas por 100.000 habitantes", S(E, "hechos_conocidos_por_100k"),
    2018, 2024, "por 100.000 hab.", dec=0, invertir_color=True,
    fuente="Derivado: tabla 01001 ÷ población a 1 de enero (INE tabla 56942)")
_sin = HC["TOTAL INFRACCIONES PENALES"] - HC["5.5.1.-Estafas informáticas"]
add("crimen", "Infracciones penales conocidas excluidas las estafas informáticas", _sin, 2018, 2024,
    "hechos", invertir_color=True, fuente="Derivado: tabla 01001 (total menos epígrafe 5.5.1)")
add("crimen", "Infracciones penales conocidas excluidas las estafas informáticas, por 100.000 hab.",
    _sin / E["pob_total"] * 1e5, 2018, 2024, "por 100.000 hab.", dec=0, invertir_color=True,
    fuente="Derivado: tabla 01001 ÷ población (INE tabla 56942)")
for cod, lab, inv in [("5.5.1.-Estafas informáticas", "Estafas informáticas (ciberestafa)", True),
                      ("5.1.-Hurtos", "Hurtos", True),
                      ("5.2.2.-Robos con fuerza en viviendas", "Robos con fuerza en viviendas", True),
                      ("5.3.-Robos con violencia o intimidación", "Robos con violencia o intimidación", True),
                      ("1.1.1.-Homicidios dolosos/asesinatos consumados",
                       "Homicidios dolosos y asesinatos consumados", True),
                      ("1.3.-Malos tratos ámbito familiar", "Malos tratos en el ámbito familiar", True),
                      ("3. LIBERTAD SEXUAL", "Delitos contra la libertad sexual", True),
                      ("3.2.-Agresión sexual con penetración", "Agresión sexual con penetración", True),
                      ("6.1.-Tráfico de drogas", "Tráfico de drogas", True),
                      ("7. FALSEDADES", "Falsedades documentales", True)]:
    nota = ""
    if "LIBERTAD SEXUAL" in cod or "Agresión sexual" in lab:
        nota = "La LO 10/2022 reordenó los tipos penales sexuales; parte de la variación es reclasificación, no necesariamente más hechos."
    add("crimen", lab, HC[cod], 2018, 2024, "hechos", invertir_color=inv,
        fuente=F_MIR + " · tabla 01001", nota=nota)
add("crimen", "Hechos esclarecidos", S(E, "hechos_esclarecidos"), 2018, 2024, "hechos",
    fuente=F_MIR + " · tabla 02001",
    nota="Un hecho esclarecido no es una condena ni una persona.")
add("crimen", "Tasa de esclarecimiento", S(E, "tasa_esclarecimiento_pct"), 2018, 2024, "%", dec=1, pp=True,
    fuente="Derivado: tabla 02001 ÷ tabla 01001")

# ========================= BLOQUE 8: CRIMINALIDAD Y NACIONALIDAD ============
add("crimen_nac", "Detenidos e investigados (total)", S(E, "detenidos_total"), 2018, 2024, "actuaciones",
    invertir_color=True, fuente=F_MIR + " · tabla 03001",
    nota="Actuaciones policiales sobre personas; una misma persona puede figurar más de una vez. No son condenas.")
add("crimen_nac", "Detenidos e investigados de nacionalidad española (por diferencia)",
    S(E, "detenidos_espanoles"), 2018, 2024, "actuaciones", invertir_color=True,
    fuente="Derivado: tabla 03001 menos tabla 03005 (universo extranjeros)",
    nota="Incluye a las personas nacidas fuera que han adquirido la nacionalidad española.")
add("crimen_nac", "Detenidos e investigados de nacionalidad extranjera", S(E, "detenidos_extranjeros"),
    2018, 2024, "actuaciones", invertir_color=True, fuente=F_MIR + " · tablas 03005 y 03007",
    nota="Nacionalidad declarada, no país de nacimiento.")
add("crimen_nac", "Peso de los extranjeros en el total de detenidos e investigados",
    S(E, "pct_detenidos_extranjeros"), 2018, 2024, "%", dec=1, pp=True, invertir_color=True,
    fuente="Derivado: tabla 03005 ÷ tabla 03001")
add("crimen_nac", "Peso de la población extranjera sobre la población total",
    S(E, "pct_pob_extranjera"), 2018, 2024, "%", dec=1, pp=True, fuente="INE · tabla 56942")
add("crimen_nac", "Detenidos e investigados españoles por 100.000 residentes españoles",
    S(E, "detenidos_esp_por_100k_pob_esp"), 2018, 2024, "por 100.000", dec=0, invertir_color=True,
    fuente="Derivado: tablas 03001/03005 ÷ población española (INE 56942)")
add("crimen_nac", "Detenidos e investigados extranjeros por 100.000 residentes extranjeros",
    S(E, "detenidos_ext_por_100k_pob_ext"), 2018, 2024, "por 100.000", dec=0, invertir_color=True,
    fuente="Derivado: tabla 03005 ÷ población extranjera (INE 56942)",
    nota="El denominador puede infravalorar a los residentes sin registro, lo que inflaría la tasa.")
add("crimen_nac", "Cociente entre ambas tasas (extranjera ÷ española)", S(E, "ratio_tasas_ext_esp"),
    2018, 2024, "veces", dec=2, invertir_color=True,
    fuente="Derivado: tasa extranjera ÷ tasa española (tablas 03001, 03005 e INE 56942)", nota="Diferencia bruta: no está corregida por edad, sexo, territorio ni situación socioeconómica.")
add("crimen_nac", "Personas condenadas por sentencia firme (total)", S(E, "condenados_total"), 2018, 2025,
    "personas", invertir_color=True, fuente="INE, Estadística de Condenados · tabla 25645")
add("crimen_nac", "Personas condenadas de nacionalidad española", S(E, "condenados_esp"), 2018, 2025,
    "personas", invertir_color=True, fuente="INE · tabla 25645")
add("crimen_nac", "Personas condenadas de nacionalidad extranjera", S(E, "condenados_ext"), 2018, 2025,
    "personas", invertir_color=True, fuente="INE · tabla 25645")
add("crimen_nac", "Condenados españoles por 100.000 residentes españoles",
    S(E, "condenados_esp_por_100k_pob_esp"), 2018, 2025, "por 100.000", dec=0, invertir_color=True,
    fuente="Derivado: tabla 25645 ÷ población española (INE 56942)")
add("crimen_nac", "Condenados extranjeros por 100.000 residentes extranjeros",
    S(E, "condenados_ext_por_100k_pob_ext"), 2018, 2025, "por 100.000", dec=0, invertir_color=True,
    fuente="Derivado: tabla 25645 ÷ población extranjera (INE 56942)")
add("crimen_nac", "Delitos sexuales de personas condenadas (infracciones, no personas)",
    S(E, "delitos_sexuales_total"), 2018, 2025, "infracciones", invertir_color=True,
    fuente="INE, Estadística de Condenados · tabla 28752",
    nota="Cuenta infracciones asociadas a condenas firmes; el año de condena no es el de comisión.")
add("crimen_nac", "Detenidos e investigados menores de 14 a 17 años", S(E, "detenidos_menores_14_17"),
    2018, 2024, "actuaciones", invertir_color=True, fuente=F_MIR + " · tablas 03003 y 03009")

# ========================= BLOQUE 9: SECTOR PÚBLICO =========================
F = pd.read_csv(os.path.join(PROC, "f_sector_publico.csv"), index_col=0)
F_EU = ("Eurostat, cuentas de las administraciones públicas (SEC 2010) · "
        "los mismos datos que la IGAE notifica a la UE")
add("publico", "Ingresos totales de las administraciones públicas", S(F, "ingresos_meur"), 2018, 2024,
    "millones €", fuente=F_EU + " · gov_10a_main")
add("publico", "Ingresos públicos sobre el PIB (presión fiscal en sentido amplio)",
    S(F, "ingresos_pct_pib"), 2018, 2024, "%", dec=1, pp=True, fuente=F_EU + " · gov_10a_main",
    nota="Media de la UE-27 en 2024: 46,0 %, frente a 39,0 % en 2018. España recauda menos que la media europea pero es de las que más ha subido.")
add("publico", "Ingresos públicos reales por habitante (euros de 2018)",
    S(F, "ingresos_meur_real_pc"), 2018, 2024, "€ de 2018",
    fuente="Derivado: gov_10a_main deflactado con el IPC (INE 50902) y dividido por la población (INE 56942)")
add("publico", "Impuestos sobre la renta y el patrimonio recaudados", S(F, "imp_renta_patrimonio_meur"),
    2018, 2024, "millones €", fuente=F_EU + " · partida D5 (recursos)",
    nota="Es la partida que más crece. Pasa del 10,5 % al 12,5 % del PIB.")
add("publico", "Cotizaciones sociales recaudadas", S(F, "cotizaciones_meur"), 2018, 2024, "millones €",
    fuente=F_EU + " · partida D61 (recursos)")
add("publico", "Impuestos sobre la producción y las importaciones", S(F, "imp_produccion_meur"),
    2018, 2024, "millones €", fuente=F_EU + " · partida D2 (recursos)",
    nota="IVA e impuestos especiales, principalmente. Pierde peso: del 11,6 % al 11,1 % del PIB.")
add("publico", "Gasto público total", S(F, "gasto_TOTAL"), 2018, 2024, "millones €",
    fuente=F_EU + " · gov_10a_exp")
add("publico", "Gasto público total sobre el PIB", S(F, "gastopct_TOTAL"), 2018, 2024, "%", dec=1, pp=True,
    fuente=F_EU + " · gov_10a_exp")
add("publico", "Déficit público (capacidad o necesidad de financiación)", S(F, "saldo_pct_pib"),
    2018, 2024, "%", dec=1, pp=True, fuente=F_EU + " · gov_10a_main",
    nota="Negativo significa déficit. El Estado gastó cada año más de lo que ingresó durante todo el periodo.")
add("publico", "Deuda pública", S(F, "deuda_meur"), 2018, 2024, "millones €",
    fuente=F_EU + " · gov_10dd_edpt1 (Protocolo de Déficit Excesivo)")
add("publico", "Deuda pública sobre el PIB", S(F, "deuda_pct_pib"), 2018, 2024, "%", dec=1, pp=True,
    fuente=F_EU + " · gov_10dd_edpt1",
    nota="En euros la deuda crece un tercio, pero sobre el PIB apenas se mueve porque el PIB nominal creció mucho por la inflación.")
add("publico", "Gasto en protección social", S(F, "gasto_GF10"), 2018, 2024, "millones €",
    fuente=F_EU + " · clasificación funcional COFOG, función 10",
    nota="Incluye pensiones, incapacidad, viudedad, desempleo, familia, vivienda social y exclusión social. No es solo «ayudas».")
add("publico", "Gasto en protección social real por habitante (euros de 2018)",
    S(F, "gasto_GF10_real_pc"), 2018, 2024, "€ de 2018",
    fuente="Derivado: COFOG función 10 deflactada con el IPC y dividida por la población")
add("publico", "Gasto en sanidad", S(F, "gasto_GF07"), 2018, 2024, "millones €",
    fuente=F_EU + " · COFOG función 7")
add("publico", "Gasto en sanidad real por habitante (euros de 2018)", S(F, "gasto_GF07_real_pc"),
    2018, 2024, "€ de 2018", fuente="Derivado: COFOG función 7 deflactada con el IPC y dividida por la población")
add("publico", "Gasto en educación", S(F, "gasto_GF09"), 2018, 2024, "millones €",
    fuente=F_EU + " · COFOG función 9")
add("publico", "Gasto en educación real por habitante (euros de 2018)", S(F, "gasto_GF09_real_pc"),
    2018, 2024, "€ de 2018", fuente="Derivado: COFOG función 9 deflactada con el IPC y dividida por la población")
add("publico", "Gasto en pensiones de jubilación (vejez)", S(F, "social_GF1002"), 2018, 2024, "millones €",
    fuente=F_EU + " · COFOG 10.2",
    nota="Es el 55,5 % de todo el gasto en protección social y explica por sí solo más de la mitad de su aumento.")
add("publico", "Gasto en prestaciones por desempleo", S(F, "social_GF1005"), 2018, 2024, "millones €",
    fuente=F_EU + " · COFOG 10.5")
add("publico", "Gasto en familia e hijos", S(F, "social_GF1004"), 2018, 2024, "millones €",
    fuente=F_EU + " · COFOG 10.4")
add("publico", "Gasto en exclusión social (partida donde se registra el Ingreso Mínimo Vital)",
    S(F, "social_GF1007"), 2018, 2024, "millones €", fuente=F_EU + " · COFOG 10.7",
    nota="Es la partida que más crece en términos relativos, pero sigue siendo el 3,7 % del gasto en protección social.")
add("publico", "Gasto en orden público y seguridad", S(F, "gasto_GF03"), 2018, 2024, "millones €",
    fuente=F_EU + " · COFOG función 3")

# ================== BLOQUE 10: SERVICIOS PÚBLICOS (listas de espera) ========
SI = pd.read_csv(os.path.join(ROOT, "data_external", "sisle_nacional.csv"))
SI = SI[SI["mes"] == 12].set_index("anyo")
Q = SI[SI["ambito"] == "quirurgica"]
C_ = SI[SI["ambito"] == "consultas"]
F_SI = ("Ministerio de Sanidad, Sistema de Información sobre Listas de Espera del SNS · "
        "corte a 31 de diciembre · 17 CCAA e INGESA")
add("servicios", "Pacientes en espera para intervención quirúrgica", Q["pacientes_espera"],
    2018, 2025, "pacientes", fuente=F_SI,
    nota="Espera estructural. La fuente original es PDF; la conversión a CSV es propia y reproducible con scripts/13_listas_espera.py.")
add("servicios", "Pacientes en espera quirúrgica por 1.000 habitantes", Q["tasa_por_1000_hab"],
    2018, 2025, "por 1.000 hab.", dec=2, fuente=F_SI,
    nota="Corrige por el crecimiento de la población: es la medida comparable en el tiempo.")
add("servicios", "Tiempo medio de espera para intervención quirúrgica", Q["tiempo_medio_espera_dias"],
    2018, 2025, "días", fuente=F_SI)
add("servicios", "Pacientes que esperan más de 6 meses para operarse", Q["pct_mas_6_meses"],
    2018, 2025, "%", dec=1, pp=True, fuente=F_SI)
add("servicios", "Pacientes en espera de primera consulta con especialista, por 1.000 habitantes",
    C_["tasa_por_1000_hab"], 2018, 2025, "por 1.000 hab.", dec=2, fuente=F_SI,
    nota="El SISLE no publica el número absoluto de pacientes en consultas externas, solo la tasa.")
add("servicios", "Tiempo medio de espera para primera consulta con especialista",
    C_["tiempo_medio_espera_dias"], 2018, 2025, "días", fuente=F_SI)
add("servicios", "Pacientes que esperan más de 60 días para una primera consulta",
    C_["pct_mas_60_dias"], 2018, 2025, "%", dec=1, pp=True, fuente=F_SI)

df = pd.DataFrame([{k: v for k, v in f.items() if k != "serie"} for f in filas])
df.to_csv(os.path.join(PROC, "indicadores_finales.csv"), index=False)
json.dump({"indicadores": filas, "descomposicion_crimen": EX, "extra_demografia": AX},
          open(os.path.join(OUTD, "indicadores.json"), "w"), ensure_ascii=False, indent=1)
print(f"{len(df)} indicadores en {len(df['bloque'].unique())} bloques")
print(df.groupby("bloque").size().to_string())
