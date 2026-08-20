# -*- coding: utf-8 -*-
"""Listas de espera del Sistema Nacional de Salud (SISLE-SNS): indicadores nacionales.

Fuente: Ministerio de Sanidad, Sistema de Información sobre Listas de Espera del SNS
(SISLE-SNS, RD 605/2003). El Ministerio publica DOS cortes al año (30 de junio y 31 de
diciembre) y SOLO en PDF: no existe XLSX, CSV ni API abierta para el agregado nacional.
La conversión a CSV que hace este script es propia y reproducible ejecutándolo de nuevo.

Método: de cada informe se leen las tablas que contienen la fila TOTAL nacional. Las
columnas NO se toman por posición (cambian de un año a otro) sino leyendo la cabecera
de cada página y emparejándola con los valores de la fila TOTAL. Cuando un mismo
indicador aparece en varias páginas del mismo informe se exige que coincidan.

Validación: el informe de diciembre de 2025 trae tabuladas las series Dic-2022 a
Dic-2025 (pacientes y tiempo medio en la lista quirúrgica; tasa por 1.000 y tiempo
medio en consultas). Esa serie se usa como contraste. Si un valor extraído de un PDF
suelto no coincide con el contraste, o si dos páginas del mismo informe se contradicen,
la celda se deja VACÍA y el motivo se anota en la columna 'aviso'. Nunca se rellena
con una estimación.

Salidas:
  data_external/sisle_raw/*.pdf      (informes originales, sin modificar)
  data_external/sisle_nacional.csv
  filas añadidas a data_external/metadata.csv
"""
import os, re, csv, html, unicodedata, urllib.request, urllib.parse

from pypdf import PdfReader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data_external")
CRUDO = os.path.join(OUT, "sisle_raw")
HOY = "2026-08-20"
MIN_ANYO = 2018          # los informes anteriores tienen otra maquetación

SEDE = "https://www.sanidad.gob.es/estadEstudios/estadisticas/inforRecopilaciones/"
PAGINAS = [SEDE + "listaEspera.htm", SEDE + "listaEsperaInfAnt.htm"]
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}

# Solo los informes nacionales de "indicadores resumen"; se excluyen los de detalle
# por comunidad autónoma, la nota de prensa y el informe de situación.
FAMILIAS = ("listas_publicacion", "llee_sns_indicadoresresumen", "indicadores_resumen")
EXCLUIR = ("ccaa", "datos_", "informe_situacion", "nota_resumen")

# --- descriptores de columna -------------------------------------------------
# Se buscan sobre la cabecera de cada página, ya normalizada (sin tildes, sin saltos).
DESCRIPTORES = [
    ("dif",       r"diferencia"),
    ("pacientes", r"total (?:de )?pacientes (?:en espera(?: estructural)?|pendientes)"),
    ("pac6m",     r"pacientes con mas de 6 meses de espera"),
    ("tasa",      r"tasa\s*por\s*1\.?000\s*hab"
                  r"|num\.?\s*pacientes\s+(?:pendientes\s+)?por\s*1\.?000\s*hab"),
    # "porcenta[jl]e": el propio Ministerio escribe "porcentale" en los informes de 2024
    ("pct6m",     r"porcenta[jl]e[^|]{0,40}?mas\s*de\s*6\s*meses"),
    ("pct60d",    r"porcenta[jl]e[^|]{0,60}?(?:sesenta dias|>\s*60\s*dias)"),
    ("tiempo",    r"tiempo medio de espera"),
]
RE_DESCRIPTORES = re.compile("|".join(f"(?P<{k}>{v})" for k, v in DESCRIPTORES))

RE_NUM = re.compile(r"-?\d{1,3}(?:\.\d{3})+(?:,\d+)?|-?\d+(?:,\d+)?")
RANGOS = {"pacientes": (100_000, 2_000_000), "tasa": (1, 250),
          "tiempo": (10, 400), "pct6m": (0, 100), "pct60d": (0, 100)}
POBLACION = (42_000_000, 53_000_000)     # control de coherencia pacientes / tasa

MESES_ES = {6: "junio", 12: "diciembre"}


def limpio(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().lower()


def num(tok):
    return float(tok.replace(".", "").replace(",", "."))


# --- 1. localizar y descargar los informes -----------------------------------
def catalogo():
    """Devuelve {(anyo, mes): (nombre_fichero, url)} de los informes nacionales."""
    encontrados = {}
    for pagina in PAGINAS:
        with urllib.request.urlopen(urllib.request.Request(pagina, headers=UA), timeout=90) as r:
            texto = r.read().decode("iso-8859-1", "replace")
        for m in re.finditer(r'href="([^"]+?\.pdf)"', texto, re.I):
            href = html.unescape(m.group(1)).strip()
            if "boe.es" in href:
                continue
            nombre = urllib.parse.unquote(href.split("/")[-1])
            bajo = nombre.lower()
            if not bajo.startswith(FAMILIAS) or any(x in bajo for x in EXCLUIR):
                continue
            fecha = re.search(r"(dic(?:iembre)?|jun(?:io)?)[_\s]*((?:19|20)\d{2}|\d{2})", bajo)
            if not fecha:
                continue
            mes = 12 if fecha.group(1).startswith("dic") else 6
            anyo = int(fecha.group(2))
            anyo += 2000 if anyo < 100 else 0
            if anyo < MIN_ANYO:
                continue
            url = urllib.parse.urljoin(pagina, href)
            encontrados.setdefault((anyo, mes), (nombre, url))
    return dict(sorted(encontrados.items()))


def bajar(url, destino):
    if os.path.exists(destino) and os.path.getsize(destino) > 20000:
        return
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r:
        datos = r.read()
    with open(destino, "wb") as fh:
        fh.write(datos)


# --- 2. leer una página y sacar la fila TOTAL --------------------------------
def cabecera(texto):
    """Texto de la página hasta la primera fila de datos (etiqueta + 2 o más números)."""
    lineas = []
    for linea in texto.split("\n"):
        if re.match(r"^\s*[^\d\s][^\d]{2,}?\s+-?\d[\d.,]*\s+-?\d[\d.,]*", linea):
            break
        lineas.append(linea)
    return limpio(" ".join(lineas))


def columnas(texto_cabecera):
    """Orden de las columnas de la tabla, leído de la cabecera."""
    orden, vistos = [], set()
    for m in RE_DESCRIPTORES.finditer(texto_cabecera):
        clave = m.lastgroup
        if clave in ("dif", "pac6m"):
            orden.append(None)              # columna real pero que no nos interesa
        elif clave not in vistos:
            vistos.add(clave)
            orden.append(clave)
        else:
            orden.append(None)
    return orden


def fila_total(texto):
    """Números de la fila TOTAL de la tabla. Solo se acepta si están en la misma
    línea que la etiqueta: cuando el PDF parte la celda (dic-2019) no hay forma
    fiable de saber a qué columna corresponde cada cifra, así que se descarta."""
    for linea in texto.split("\n"):
        if re.match(r"^\s*TOTAL\b", linea):
            toks = RE_NUM.findall(linea)
            if len(toks) >= 3:
                return toks
    return None


def ambito_de(texto):
    cab = limpio(texto[:400])
    if "quirurgica" in cab:
        return "quirurgica"
    if "consulta" in cab:
        return "consultas"
    return None


def leer_pagina(texto):
    """-> (ambito, {metrica: valor}, incidencia) o None si la página no sirve."""
    amb = ambito_de(texto)
    toks = fila_total(texto)
    if not amb or not toks:
        return None
    cab = cabecera(texto)
    if "procesos seleccionados" in cab:
        return None          # subconjunto de 11 intervenciones, no el total del SNS
    cols = columnas(cab)
    if not cols or not any(cols):
        return None
    incidencia = ""
    if len(toks) > len(cols):
        return None                                     # no sabemos mapear: se descarta
    if len(toks) < len(cols):
        # al extraer el PDF se pierden celdas vacías, siempre por la izquierda;
        # se alinean los valores por la derecha y las columnas sobrantes quedan sin dato
        cols = cols[len(cols) - len(toks):]
        incidencia = "fila TOTAL con columnas incompletas en el PDF"
    datos = {}
    for clave, tok in zip(cols, toks):
        if clave is None or clave in datos:
            continue
        v = num(tok)
        lo, hi = RANGOS[clave]
        if lo <= abs(v) <= hi:
            datos[clave] = v
    return amb, datos, incidencia


# --- 3. serie de contraste del informe de diciembre de 2025 ------------------
def serie_contraste(ruta_pdf):
    """{('quirurgica'|'consultas', anyo, mes): {metrica: valor}} desde los gráficos
    de evolución, que traen la serie ya tabulada."""
    lector = PdfReader(ruta_pdf)
    salida = {}
    for pag in lector.pages:
        texto = pag.extract_text() or ""
        if "evoluci" not in limpio(texto[:300]):
            continue
        amb = ambito_de(texto)
        etiquetas = re.findall(r"\b(Dic|Jun)\s*(\d{2})\b", texto)
        if not amb or len(etiquetas) < 4:
            continue
        periodos = [(2000 + int(a), 12 if m == "Dic" else 6) for m, a in etiquetas]
        n = len(periodos)
        toks = texto.split()
        miles = [t for t in re.findall(r"\b\d{3}\.\d{3}\b", texto)]
        decs = _primera_racha(toks, r"^\d{1,3},\d{1,2}$", n)
        enteros = _primera_racha(toks, r"^\d{2,3}$", n)
        series = {}
        if len(miles) >= n:
            series["pacientes"] = [num(t) for t in miles[:n]]
        if decs:
            series["tasa"] = [num(t) for t in decs]
        if enteros:
            series["tiempo"] = [num(t) for t in enteros]
        for i, per in enumerate(periodos):
            for metrica, vals in series.items():
                if metrica == "pacientes" and amb != "quirurgica":
                    continue
                if metrica == "tasa" and amb != "consultas":
                    continue
                salida.setdefault((amb,) + per, {})[metrica] = vals[i]
    return salida


def _primera_racha(toks, patron, n):
    """Primeros n elementos de la primera racha de al menos n tokens seguidos
    que casan con el patrón (los ejes de los gráficos van siempre después)."""
    rx = re.compile(patron)
    racha = []
    for t in toks:
        if rx.match(t):
            racha.append(t)
            if len(racha) == n:
                return racha
        else:
            racha = []
    return None


# --- 4. ejecución ------------------------------------------------------------
os.makedirs(CRUDO, exist_ok=True)
informes = catalogo()
print(f"Informes nacionales localizados desde {MIN_ANYO}: {len(informes)}")

rutas = {}
for (anyo, mes), (nombre, url) in informes.items():
    destino = os.path.join(CRUDO, nombre)
    bajar(url, destino)
    rutas[(anyo, mes)] = (destino, url)

ref = rutas.get((2025, 12))
contraste = serie_contraste(ref[0]) if ref else {}
print(f"Serie de contraste (informe dic-2025): {len(contraste)} cortes")

METRICAS = ["pacientes", "tasa", "tiempo", "pct6m", "pct60d"]
filas = []
for (anyo, mes), (ruta, url) in rutas.items():
    lector = PdfReader(ruta)
    candidatos = {"quirurgica": [], "consultas": []}
    incidencias = {"quirurgica": set(), "consultas": set()}
    for pag in lector.pages:
        res = leer_pagina(pag.extract_text() or "")
        if not res:
            continue
        amb, datos, inc = res
        if datos:
            candidatos[amb].append(datos)
            if inc:
                incidencias[amb].add(inc)

    for amb in ("quirurgica", "consultas"):
        ref_corte = contraste.get((amb, anyo, mes), {})
        valores, avisos = {}, []
        for metrica in METRICAS:
            vistos = sorted({d[metrica] for d in candidatos[amb] if metrica in d})
            if not vistos:
                continue
            if len(vistos) > 1:
                extra = (f"; la serie de contraste da {ref_corte[metrica]:g}"
                         if metrica in ref_corte else "")
                avisos.append(f"{metrica}: páginas del informe discrepan "
                              f"({', '.join(str(v) for v in vistos)}){extra}; celda vacía")
                continue
            valores[metrica] = vistos[0]

        # coherencia interna: pacientes / tasa debe dar una población plausible
        if "pacientes" in valores and "tasa" in valores and valores["tasa"]:
            pob = valores["pacientes"] / valores["tasa"] * 1000
            if not (POBLACION[0] <= pob <= POBLACION[1]):
                avisos.append(f"pacientes descartado: pacientes/tasa implica "
                              f"{pob/1e6:.1f} M de habitantes, fuera de rango")
                valores.pop("pacientes")

        # contraste con la serie tabulada del informe de diciembre de 2025
        for metrica, esperado in ref_corte.items():
            if metrica in valores and abs(valores[metrica] - esperado) > 0.051:
                avisos.append(f"{metrica}: el PDF da {valores[metrica]:g} y la serie de "
                              f"contraste {esperado:g}; celda vacía")
                valores.pop(metrica)
        contrastado = "si" if ref_corte else "no"

        if not candidatos[amb]:
            avisos.append("ninguna tabla de este informe da una fila TOTAL legible: "
                          "el PDF parte la celda al extraer el texto")
        for inc in sorted(incidencias[amb]):
            if any(m not in valores for m in ("pacientes", "tasa", "tiempo")):
                avisos.append(inc)
                break
        if amb == "consultas":
            avisos.append("SISLE-SNS no publica el número absoluto de pacientes en "
                          "consultas externas, solo la tasa por 1.000 habitantes")

        filas.append({
            "fecha_corte": f"{anyo}-{mes:02d}-{30 if mes == 6 else 31}",
            "anyo": anyo, "mes": mes, "corte": f"{MESES_ES[mes]} {anyo}",
            "ambito": amb,
            "pacientes_espera": valores.get("pacientes"),
            "tasa_por_1000_hab": valores.get("tasa"),
            "tiempo_medio_espera_dias": valores.get("tiempo"),
            "pct_mas_6_meses": valores.get("pct6m"),
            "pct_mas_60_dias": valores.get("pct60d"),
            "contrastado_con_serie": contrastado,
            "fichero_origen": os.path.basename(ruta),
            "url_origen": url,
            "aviso": " | ".join(avisos),
        })

filas.sort(key=lambda r: (r["anyo"], r["mes"], r["ambito"]))
COLS = list(filas[0].keys())
ruta_csv = os.path.join(OUT, "sisle_nacional.csv")
with open(ruta_csv, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=COLS)
    w.writeheader()
    w.writerows(filas)

# --- 5. metadatos ------------------------------------------------------------
anyos = sorted({r["anyo"] for r in filas})
meta = [{
    "fichero": "sisle_nacional.csv",
    "indicador": ("Listas de espera del SNS: pacientes en espera estructural, tasa por 1.000 "
                  "habitantes, tiempo medio de espera en días y porcentaje de esperas largas, "
                  "para lista quirúrgica y para consultas externas"),
    "organismo": "Ministerio de Sanidad · Sistema de Información sobre Listas de Espera del SNS (SISLE-SNS)",
    "dataset": "SISLE-SNS, indicadores resumen (RD 605/2003), cortes de 30 de junio y 31 de diciembre",
    "url_exacta": rutas[(2025, 12)][1] if (2025, 12) in rutas else PAGINAS[0],
    "cobertura": f"{anyos[0]}-{anyos[-1]} (dos cortes al año)",
    "geografia": "ES",
    "fecha_descarga": HOY,
    "notas": ("La fuente original es PDF: el Ministerio de Sanidad no publica el agregado "
              "nacional en XLSX, CSV ni API abierta (INCLASNS tiene API pero exige clave). "
              "La conversión a CSV es propia y reproducible con scripts/13_listas_espera.py. "
              "Las columnas se leen de la cabecera de cada página, no por posición. Cuando dos "
              "páginas del mismo informe discrepan, o el valor no cuadra con la serie de "
              "contraste tabulada en el informe de diciembre de 2025, la celda se deja vacía y "
              "el motivo va en la columna 'aviso'. Para consultas externas no hay número "
              "absoluto de pacientes: SISLE-SNS solo publica la tasa por 1.000 habitantes. "
              "El porcentaje de espera larga es '>6 meses' en la lista quirúrgica y '>60 días' "
              "en consultas: no son comparables entre sí."),
}]

mp = os.path.join(OUT, "metadata.csv")
prev = list(csv.DictReader(open(mp, encoding="utf-8"))) if os.path.exists(mp) else []
campos = list(prev[0].keys()) if prev else list(meta[0].keys())
prev = [p for p in prev if p["fichero"] not in {m["fichero"] for m in meta}]
with open(mp, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=campos)
    w.writeheader()
    w.writerows(prev + meta)

vacias = sum(1 for r in filas for m in ("pacientes_espera", "tasa_por_1000_hab",
                                        "tiempo_medio_espera_dias", "pct_mas_6_meses",
                                        "pct_mas_60_dias") if r[m] is None)
print(f"\nsisle_nacional.csv  {len(filas)} filas  ({anyos[0]}-{anyos[-1]})  celdas vacías: {vacias}")
print(f"metadata.csv actualizado: {len(prev) + len(meta)} filas")
