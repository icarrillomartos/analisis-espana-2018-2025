# Registro de cambios — fase Claude

Agente: Claude Code (Opus 5). Fecha: 2026-08-20. Toma el relevo de Codex a partir de `coordinacion.md`.

## Estado: entregado

`data_raw/` NO se ha tocado. Ni un byte. Todo lo nuevo está en `scripts/`, `data_processed/` y `outputs/`.

## Entorno

```bash
cd /Users/ivancarrillo/Documents/Codex/analisis-españa
python3 -m venv .venv && .venv/bin/pip install pandas
```

Solo se usa `pandas` (y `pillow` opcional, únicamente para capturas de control). Python 3.9 del sistema.

## Cómo regenerar todo desde cero

```bash
for s in 01_demografia_migracion 02_economia 03_laboral 04_precios_poder_adquisitivo 05_criminalidad 06_indicadores 07_informe_html; do
  .venv/bin/python scripts/$s.py || break
done
```

El orden importa: 06 consume los CSV de 01-05 y 07 consume la salida de 06.

## Ficheros nuevos

### `scripts/`
| Fichero | Qué hace |
|---|---|
| `ine_lib.py` | Lector genérico del JSON de la API Tempus del INE (`load_tempus`) y de los CSV del MIR (`load_mir`, con detección de codificación). `dims_of` inspecciona dimensiones sin cargar en memoria un DataFrame. |
| `01_demografia_migracion.py` | Población total y por nacionalidad (56942), por país de nacimiento (9675 + 70364), año de llegada, naturalizaciones (15073), flujos migratorios (24324, 69694, 76246, 24428). |
| `02_economia.py` | Lectura posicional de los CSV de Contabilidad Nacional y Regional RE2024: PIB nominal, volumen encadenado, per cápita, RND, empleo, horas, productividad. |
| `03_laboral.py` | EPA y ETCL. Medias anuales solo de años con los cuatro trimestres completos. |
| `04_precios_poder_adquisitivo.py` | IPC (media anual de 12 meses, con `assert`), deflactación a euros de 2018, salarios, deciles, renta ECV reindexada al año de renta, AROPE, IPV, hipotecas. |
| `05_criminalidad.py` | Hechos conocidos y esclarecidos, detenidos/investigados con la corrección de universos (ver abajo), condenados INE, tasas por 100.000 de la misma nacionalidad y descomposición shift-share. |
| `06_indicadores.py` | Ensambla los 88 indicadores con año inicial, año final real, unidad, fuente, nota y serie completa. |
| `07_informe_html.py` | Genera el informe. Ninguna cifra del texto está escrita a mano: todas se interpolan desde `data_processed/`. |

### `data_processed/`
`a_demografia.csv`, `a_paises_nacimiento.csv`, `a_ano_llegada_2025.csv`, `a_solape_series_nacimiento.csv`, `a_extra.json`,
`b_economia.csv`, `c_laboral.csv`, `d_precios.csv`, `d_ipc_grupos.csv`,
`e_hechos_conocidos_tipologia.csv`, `e_hechos_esclarecidos_tipologia.csv`, `e_detenidos_extranjeros_tipologia.csv`,
`e_detenidos_extranjeros_nacionalidad.csv`, `e_condenados_nacionalidad.csv`, `e_delitos_sexuales_nacionalidad.csv`,
`e_criminalidad_resumen.csv`, `e_descomposicion.json`, `indicadores_finales.csv`.

### `outputs/`
- `informe_espana_2018_2025.html` — **la entrega**. Documento autónomo, se abre con doble clic.
- `informe_artifact_body.html` — mismo contenido sin envoltura `<html>`, para publicar como Artifact.
- `indicadores.json` — los 88 indicadores con sus series, por si se quiere otro front-end.

### Raíz
- `MATRIZ_ENTREGA_CLAUDE.md` — requisitos comprometidos y verificación de cierre.
- `REGISTRO_CAMBIOS_CLAUDE.md` — este fichero.

## HALLAZGO IMPORTANTE: corrección a `data_raw/criminalidad/metadata.csv`

El `metadata.csv` describe las matrices 03003, 03005 y 03007 del Ministerio del Interior como desgloses del
total de detenciones e investigaciones. **No lo son.** Comprobado numéricamente para los siete años 2018-2024:

| Matriz | Descripción en metadata.csv | Universo real verificado |
|---|---|---|
| 03001 / 03002 | Total por tipología y territorio | Correcto. Total nacional 2024 = 577.107 |
| 03005 / 03006 | «Por tipología sexo y comunidad» | **Solo EXTRANJEROS.** Total 2024 = 217.377 |
| 03007 / 03008 | «Por nacionalidad sexo y comunidad» | **Solo EXTRANJEROS.** Total idéntico a 03005 los 7 años; su lista de nacionalidades no incluye España |
| 03003 / 03004 | «Por tipología sexo nacionalidad y comunidad» | **Solo MENORES de 14-17 años.** Total idéntico al grupo «14-17 años» de 03009 los 7 años |
| 03009 / 03010 | Por tipología, edad y sexo | Correcto. «TOTAL edad» 2024 = 575.185 |

Consecuencia: **los detenidos de nacionalidad española no están publicados directamente**; se obtienen por
diferencia `03001 − 03005`. El script `05_criminalidad.py` incluye dos `assert` que fallan si esta relación
deja de cumplirse en una descarga futura. Sin esta corrección, cualquier cifra de detenciones por
nacionalidad sería errónea por un factor de más de dos.

No se ha modificado `data_raw/criminalidad/metadata.csv`: el hallazgo se documenta aquí y en el informe.

## Otras decisiones metodológicas que conviene conocer antes de continuar

1. **Población total y por nacionalidad**: se usa una única serie homogénea 2018-2025, la tabla 56942
   (1 de enero). Su valor de 2025 coincide exactamente con el Censo anual (70364), así que ambas son
   la misma base poblacional.
2. **Población por país de nacimiento**: no existe una serie única 2018-2025. Se enlaza 9675 (2018-2020,
   Cifras de Población) con 70364 (2021-2025, Censo anual). El solape 2021-2022 se conserva en
   `a_solape_series_nacimiento.csv`: la diferencia sobre los nacidos fuera es de 39.919 (2021) y 102.805 (2022),
   es decir entre el 0,5 % y el 1,4 %. Está declarado en el informe.
3. **Renta ECV**: reindexada al AÑO DE RENTA (encuesta t → renta t−1) para poder deflactarla con el IPC correcto.
   La comparación 2018-2024 usa por tanto las encuestas 2019 y 2025.
4. **Deflactación**: siempre con la media anual de los doce meses del IPC general (tabla 50902). Hay un `assert`
   que verifica que todos los años tienen 12 observaciones.
5. **Medias anuales EPA/ETCL**: solo se calculan para años con los cuatro trimestres.
6. **Años finales**: Interior llega a 2024; CNA llega a 2024; EAES y ECV (año de renta) llegan a 2024;
   IPC, EPA, IPV, hipotecas, AROPE y condenados INE llegan a 2025. Cada fila del informe marca su año final real.
7. **Salario por decil (tabla 10910)**: la descarga solo contiene el desglose por sexo, no hay «ambos sexos».
   Se publican deciles separados por sexo. No se han promediado.

## Lo que sigue sin resolver (mismo estado que dejó Codex)

- País de nacimiento en estadísticas penales: no existe en ninguna fuente disponible.
- Vivienda en Madrid 1970 vs hoy: no cubierto. Requiere módulo aparte con archivo histórico.
- Serie oficial homogénea de alquiler: no disponible en el repositorio.
- Duración del desempleo y flujos de colocación: no descargados (harían falta SEPE/MITES).
- EPF: la descarga solo contiene 34 subclases COICOP, sin gasto total del hogar, y se detiene en 2023.
  No se ha usado en el informe.
- Análisis territorial (CCAA/provincia): los datos están descargados y los lectores los soportan, pero el
  informe es nacional. Es la ampliación más inmediata si se quiere continuar.

---

# Ampliación · 2026-08-20 (segunda tanda)

## Scripts nuevos

| Fichero | Qué hace |
|---|---|
| `08_eurostat.py` | Descarga de Eurostat el IPC armonizado, el PIB per cápita real, la ganancia neta anual y el consumo individual efectivo en PPA, para 13 economías. Necesario para saber si el crecimiento español es alto o bajo. |
| `09_desglose_origen.py` | Desgloses por origen: población por continente y país, flujos de entrada, criminalidad por continente con denominadores compatibles, peso de extranjeros por tipo de infracción, composición del delito por origen y comparativa europea. |
| `10_finanzas_publicas.py` | Cuentas de las administraciones públicas: ingresos, gasto por función COFOG, protección social por subfunción, déficit y deuda. |
| `11_sector_publico.py` | Consolida lo anterior y descompone el aumento de ingresos en economía real, precios y mayor detracción. |
| `12_imv.py` | Rastrea, descarga y parsea las nóminas mensuales del Ingreso Mínimo Vital de la Seguridad Social. |
| `13_listas_espera.py` | Rastrea, descarga y parsea los informes del Sistema de Información sobre Listas de Espera del SNS. |

## Directorio nuevo: `data_external/`

Ver su propio `README.md`. Contiene 13 conjuntos de datos con `metadata.csv` en el mismo formato de columnas
que los `metadata.csv` de `data_raw/`: fichero, indicador, organismo, dataset, url_exacta, cobertura,
geografia, fecha_descarga, notas. Organismos: Eurostat, Seguridad Social y Ministerio de Sanidad.

## Hallazgos y cautelas nuevas

1. **`earn_nt_net` de Eurostat tiene ruptura de serie en 2024 en los trece países.** Comparar 2018 con 2024
   produce caídas falsas de hasta el 25 % (Países Bajos pasa de 45.156 a 34.223 €). El informe se detiene
   en 2023 para ese indicador.
2. **El IMV no existía en 2018**: se creó en junio de 2020. Además la serie descargable en XLSX solo empieza
   en enero de 2024; los enlaces anteriores devuelven 404 y datos.gob.es no tiene ningún dataset de IMV.
   No hay forma de reconstruir 2020-2023 con fuente oficial descargable.
3. **Las listas de espera solo existen en PDF.** El Ministerio de Sanidad no publica el SISLE-SNS nacional en
   ningún formato de datos. La API de INCLASNS existe pero requiere clave que se solicita por formulario.
   `13_listas_espera.py` parsea los PDF; las cifras de 2018 y 2025 se han verificado a mano contra el texto
   original. Falta diciembre de 2019: ese PDF parte la fila de totales al extraer el texto y se deja el hueco
   en vez de estimarlo.
4. **En el SISLE hay que descartar la página de «procesos seleccionados»**, que es un subconjunto de 11
   intervenciones (295.275 pacientes en diciembre de 2025) y no el total del SNS. El parser lo excluye.
5. **COFOG «protección social» no es «ayudas»**: las pensiones de jubilación son el 55 % del total y explican
   el 56 % de su aumento. Conviene no citar la cifra agregada como si fueran prestaciones asistenciales.
6. **La partida «exclusión social» no es el IMV**: lo incluye junto a otras prestaciones. Para el IMV en
   solitario hay que usar `imv_anual.csv`.

## Cambios en la estructura del informe

- Parte I pasa de 8 a **10 bloques** (añadidos «09 Sector público» y «10 Servicios públicos»), 117 indicadores.
- Parte II pasa de 4 a **5 respuestas**. Cada una abre con una frase de respuesta, desarrolla con sus tablas
  específicas y cierra con un bloque «Conclusión» en lenguaje llano. La pregunta 1 ya no habla de PIB.
- Componentes visuales nuevos: `linea()` para la respuesta en una frase, `cierre()` para la conclusión final,
  `quien()` para las segmentaciones por perfil, `tabla_libre()` para tablas de apoyo y `sub()` para
  subapartados dentro de un bloque.
