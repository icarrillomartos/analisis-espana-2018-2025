# Datos externos añadidos en la fase Claude

Este directorio NO existía en la descarga original de Codex. Se crea porque tres preguntas del encargo
no podían responderse solo con INE y Ministerio del Interior:

1. Saber si el crecimiento español del poder adquisitivo es alto o bajo exige compararlo con otros países
   con la misma metodología.
2. Saber de dónde sale el dinero público y en qué se gasta exige las cuentas de las administraciones públicas.
3. Saber si España recauda o gasta mucho o poco exige el contexto europeo.

## Regla aplicada

La misma que exigió Codex en `coordinacion.md` para cualquier dato añadido: **organismo oficial, URL directa,
fecha de descarga y explicación metodológica**. Todo está en `metadata.csv`, con las mismas columnas de
propósito que los `metadata.csv` de `data_raw/`.

## Organismo

**Eurostat**, oficina estadística de la Unión Europea. Dominio: `ec.europa.eu`. Las cuentas de las
administraciones públicas que publica Eurostat son las que la **IGAE** española notifica a la UE bajo el
SEC 2010, así que no son un dato alternativo al oficial español: son el mismo dato en formato comparable.

## Ficheros

| Fichero | Contenido | Cobertura |
|---|---|---|
| `eurostat_hicp.csv` | IPC armonizado, índice medio anual | 2018-2025 |
| `eurostat_pib_pc_real.csv` | PIB per cápita en volumen encadenado | 2018-2024 |
| `eurostat_salario_neto.csv` | Ganancia neta anual, caso-tipo soltero al 100 % del salario medio | 2018-2024 |
| `eurostat_aic_pps.csv` | Consumo individual efectivo per cápita en PPA, UE-27 = 100 | 2018-2024 |
| `eurostat_gov_main_meur.csv` | Ingresos, gastos y saldo de las AAPP, millones de euros | 2018-2024 |
| `eurostat_gov_main_pcgdp.csv` | Lo mismo en porcentaje del PIB | 2018-2024 |
| `eurostat_gov_cofog_meur.csv` | Gasto público por función COFOG, millones de euros | 2018-2024 |
| `eurostat_gov_cofog_pcgdp.csv` | Lo mismo en porcentaje del PIB | 2018-2024 |
| `eurostat_gov_cofog_social_meur.csv` | Protección social desglosada por subfunción | 2018-2024 |
| `eurostat_gov_deuda.csv` | Deuda pública (Protocolo de Déficit Excesivo) | 2018-2024 |
| `cofog_etiquetas.json` | Traducción de los códigos COFOG | — |

## Cautelas que no deben perderse

- **No mezclar deflactores.** El IPC del INE deflacta las series españolas; el IPC armonizado de Eurostat
  deflacta las europeas. Un mismo indicador nunca usa los dos.
- **`earn_nt_net` tiene ruptura de serie en 2024** en los trece países descargados. Comparar 2018 con 2024
  produce caídas falsas de hasta el 25 %. El informe se detiene en 2023 para este indicador.
- **`earn_nt_net` es un caso-tipo**, no el salario medio efectivo: persona soltera sin hijos que cobra
  exactamente el salario medio. Diverge legítimamente de la ganancia media bruta del INE.
- **El consumo individual efectivo en PPA es un índice relativo** con UE-27 = 100. Si España sube puede
  deberse a que mejora o a que los demás empeoran.
- **COFOG «protección social» no es «ayudas»**: incluye pensiones de jubilación, incapacidad, viudedad,
  desempleo, familia, vivienda social y exclusión social. Las pensiones son más de la mitad.
- **El Ingreso Mínimo Vital no aparece por separado**: se registra dentro de la subfunción «exclusión social»
  junto a otras prestaciones. No hay que citar esa cifra como si fuera el IMV.

## Reproducir

```bash
.venv/bin/python scripts/08_eurostat.py         # comparación europea
.venv/bin/python scripts/10_finanzas_publicas.py # cuentas de las AAPP
```

Ambos escriben en este directorio y actualizan `metadata.csv`. La URL exacta usada en cada llamada queda
guardada en la columna `url_exacta`, incluidos los filtros: es reproducible tal cual, pegándola en un navegador.
