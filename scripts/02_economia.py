"""Bloque B: economía (Contabilidad Nacional y Regional, RE2024).
Los XLSX oficiales se descargaron ya recortados a CSV; aquí se leen posicionalmente
las filas identificadas por su etiqueta y las columnas de año del encabezado.
Salida: data_processed/b_economia.csv
"""
import sys, os, csv
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data_raw", "demografia_economia")
OUT = os.path.join(ROOT, "data_processed")
os.makedirs(OUT, exist_ok=True)
ANYOS = [2018, 2019, 2020, 2021, 2022, 2023, 2024]


def read_rows(path):
    with open(path, encoding="utf-8") as fh:
        return list(csv.reader(fh))


def year_cols(rows, header_hint="2018"):
    """Devuelve {anyo: indice_columna} a partir de la fila de encabezado."""
    for r in rows:
        cells = [c.strip() for c in r]
        if any(c.startswith("2018") for c in cells) and any(c.startswith("2024") for c in cells):
            m = {}
            for i, c in enumerate(cells):
                c = c.replace(".0", "").split(" ")[0]
                if c[:4].isdigit() and 2018 <= int(c[:4]) <= 2024:
                    m[int(c[:4])] = i
            return m
    raise RuntimeError("encabezado de años no encontrado en " + str(path))


def grab(path, label, occurrence=1):
    rows = read_rows(path)
    cols = year_cols(rows)
    seen = 0
    for r in rows:
        cells = [c.strip() for c in r]
        if label in cells:
            seen += 1
            if seen == occurrence:
                out = {}
                for y, i in cols.items():
                    v = cells[i] if i < len(cells) else ""
                    out[y] = float(v) if v not in ("", "-") else None
                return pd.Series(out).sort_index()
    raise RuntimeError(f"fila '{label}' no encontrada en {path}")


s = {}
P = lambda f: os.path.join(RAW, f)

# PIB nominal (Tabla 1, precios corrientes, millones de euros)
s["pib_nominal_meur"] = grab(P("ine_cna_pib95_24_sheet2_2018_2024.csv"),
                             "PRODUCTO INTERIOR BRUTO A PRECIOS DE MERCADO")
# PIB volumen encadenado, referencia 2020 = 100 (medida real)
s["pib_volumen_idx2020"] = grab(P("ine_cna_pib95_24_sheet5_2018_2024.csv"),
                                "PRODUCTO INTERIOR BRUTO A PRECIOS DE MERCADO")
# Componentes nominales
for lbl, key in [("    Gasto en consumo final", "consumo_final_meur"),
                 ("    Formación bruta de capital", "fbc_meur")]:
    try:
        s[key] = grab(P("ine_cna_pib95_24_sheet2_2018_2024.csv"), lbl)
    except RuntimeError:
        pass

# Renta nacional disponible (precios corrientes)
rnd = P("ine_cna_rnd_95_24_sheet1_2018_2024.csv")
s["rnb_disponible_meur"] = grab(rnd, "RENTA NACIONAL BRUTA DISPONIBLE")
s["rnd_neta_percapita_eur"] = grab(rnd, "Renta nacional disponible neta per cápita (euros) (*)")
s["remuneracion_asalariados_meur"] = grab(rnd, "Remuneración de los asalariados")
s["poblacion_cna_miles"] = grab(rnd, "Población total (miles de habitantes) (*)")

# Empleo, horas y productividad
s["puestos_totales_miles"] = grab(P("ine_cna_rem_empleo95_24_sheet3_2018_2024.csv"), "TOTAL", 1)
s["horas_trabajadas_miles"] = grab(P("ine_cna_rem_empleo95_24_sheet5_2018_2024.csv"), "TOTAL", 1)
s["personas_ocupadas_miles"] = grab(P("ine_cna_rem_empleo95_24_sheet6_2018_2024.csv"), "TOTAL", 1)

# PIB per cápita nominal (Contabilidad Regional, Total Nacional)
rows = read_rows(P("ine_contabilidad_regional_tabla_2_2018_2024.csv"))
hdr = [i for i, r in enumerate(rows) if r and r[0].strip() == "Comunidad Autónoma"][0]
ycols = {}
for i, c in enumerate(rows[hdr]):
    c = c.strip().split(" ")[0].replace(".0", "")
    if c[:4].isdigit():
        ycols[int(c[:4])] = i        # sub-columna 'Valor' = misma posición
tot = [r for r in rows if r and r[0].strip() == "Total Nacional"][0]
s["pib_percapita_nominal_eur"] = pd.Series(
    {y: float(tot[i]) for y, i in ycols.items() if tot[i].strip()}).sort_index()

df = pd.DataFrame(s)
df.index.name = "anyo"

# Derivados reales
df["pib_real_percapita_idx"] = (df["pib_volumen_idx2020"] / df["poblacion_cna_miles"]) * 1000
df["productividad_hora_idx"] = (df["pib_volumen_idx2020"] / df["horas_trabajadas_miles"]) * 1e6
df["deflactor_pib"] = df["pib_nominal_meur"] / df["pib_volumen_idx2020"]

df.to_csv(os.path.join(OUT, "b_economia.csv"))
print(df.round(2).to_string())
print("\nCrecimiento 2018->2024:")
for c in df.columns:
    a, b = df[c].loc[2018], df[c].loc[2024]
    if pd.notna(a) and pd.notna(b) and a:
        print(f"  {c:34s} {a:>14,.2f} -> {b:>14,.2f}  {(b/a-1)*100:+7.2f}%")
