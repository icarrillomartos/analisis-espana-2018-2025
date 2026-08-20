# Coordinación para Claude Code

## Encargo y contexto

Claude: recoges un repositorio de datos oficiales preparado para analizar la evolución de España entre 2018 y 2025. Tu trabajo siguiente es limpiar, armonizar, analizar y representar visualmente los datos para responder, con cifras reproducibles, a estas preguntas:

1. ¿Cuánto crecieron la población y la economía españolas, y qué parte del crecimiento demográfico se explica por migración?
2. ¿Cuánto creció la criminalidad registrada y qué puede afirmarse —y qué no— sobre inmigración u origen?
3. ¿Aumentó el poder adquisitivo del ciudadano? ¿Es materialmente más rico o más pobre que en 2018?

Como análisis complementario, interesa estudiar actividad, empleo, paro, inactividad, vacantes, coste de vida, renta, salarios, pobreza, vivienda e hipotecas. El usuario también mencionó comparaciones con 1970, pero esa comparación histórica no está resuelta con datos homogéneos en este repositorio y debe tratarse como una ampliación separada.

No partas de conclusiones predeterminadas. Calcula, documenta incertidumbres y distingue descripción, asociación y causalidad.

## Ubicación y estado del repositorio

Ruta raíz:

`/Users/ivancarrillo/Documents/Codex/analisis-españa`

Contenido validado el 20 de agosto de 2026:

- 74 datasets CSV/JSON, aproximadamente 426 MB contando documentación y auxiliares.
- 35 datasets de demografía, migración y economía.
- 22 datasets de criminalidad.
- 17 datasets de bienestar, empleo, precios, ingresos y vivienda.
- Los 74 ficheros de datos abren correctamente y todos tienen una fila en el `metadata.csv` de su bloque.
- Todas las URLs inventariadas pertenecen al INE o al Portal Estadístico de Criminalidad del Ministerio del Interior.

Lee antes de procesar:

- `README.md`
- `MATRIZ_RESULTADOS.md`
- `reports/VALIDACION_FINAL.md`
- `reports/file_inventory.csv`
- Los tres archivos `metadata.csv` descritos más abajo.

## Estructura

```text
analisis-españa/
├── coordinacion.md
├── README.md
├── MATRIZ_RESULTADOS.md
├── data_raw/
│   ├── demografia_economia/
│   │   ├── metadata.csv
│   │   ├── README.md
│   │   └── datos INE
│   ├── criminalidad/
│   │   ├── metadata.csv
│   │   ├── MATRIZ_COBERTURA.md
│   │   └── datos de Interior e INE
│   └── bienestar_empleo/
│       ├── metadata.csv
│       ├── download_ine.sh
│       └── datos INE
├── scripts/
│   └── validate_inventory.py
└── reports/
    ├── VALIDACION_FINAL.md
    └── file_inventory.csv
```

Mantén `data_raw/` inmutable. Crea, como mínimo, carpetas separadas para datos transformados, código, tablas, gráficos y documentación metodológica. Toda transformación debe poder reproducirse desde `data_raw/`.

## Procedencia oficial

Los dominios admitidos y ya auditados son:

- `www.ine.es`
- `servicios.ine.es`
- `estadisticasdecriminalidad.ses.mir.es`

Distribución de las 74 fuentes inventariadas:

- 36 URLs en `www.ine.es`.
- 24 URLs en `servicios.ine.es`.
- 14 URLs en el Portal Estadístico de Criminalidad del Ministerio del Interior.

Cada `metadata.csv` contiene la URL oficial, cobertura real, granularidad, unidad y cautelas. Conserva esas columnas en cualquier catálogo consolidado. Si añades datos, exige organismo oficial, URL directa, fecha de descarga y explicación metodológica.

## Reglas conceptuales obligatorias

### País de nacimiento, nacionalidad e inmigración

No uses estos conceptos como sinónimos:

- **País de nacimiento**: variable principal disponible para aproximar origen migratorio.
- **Nacionalidad**: condición jurídica actual y mutable. Una persona nacida en Marruecos y nacionalizada española aparece como española en tablas por nacionalidad.
- **Flujo migratorio**: inmigraciones o emigraciones producidas durante un periodo.
- **Stock migratorio**: residentes nacidos fuera o con nacionalidad extranjera en una fecha.
- **Adquisiciones de nacionalidad**: ayudan a explicar cambios entre las clasificaciones por nacimiento y nacionalidad, pero no permiten reclasificar individuos en estadísticas penales agregadas.

Prioriza país de nacimiento, año de llegada y residencia previa en demografía. Usa nacionalidad solo cuando sea la única variable publicada, etiquetándola exactamente como nacionalidad. Nunca escribas “origen” en un gráfico construido con nacionalidad.

### Criminalidad

Mantén separadas estas unidades:

- **Hechos conocidos**: infracciones registradas por las fuerzas policiales; no son personas.
- **Hechos esclarecidos**: hechos que la policía considera esclarecidos; no son necesariamente condenas ni personas.
- **Detenciones/investigados**: personas o actuaciones policiales; no equivalen a delitos cometidos ni a condenas firmes.
- **Condenados**: personas condenadas judicialmente.
- **Infracciones/delitos atribuidos a condenados**: una persona puede acumular más de una infracción.

No dividas detenidos entre hechos conocidos como si fuera una “tasa de delincuencia de personas”. No unas hechos esclarecidos con nacionalidad: Interior no publica nacionalidad ni país de nacimiento en la tabla de hechos esclarecidos. Tampoco publiques “porcentaje de delitos causado por inmigrantes” a partir de condenas o detenciones por nacionalidad; los numeradores, universos, momentos procesales y conceptos no coinciden.

Las tablas penales descargadas ofrecen nacionalidad, no país de nacimiento/origen. Los españoles incluyen naturalizados. Por ello, con estos datos no se puede calcular limpiamente cuánto crecimiento de la criminalidad es “debido a la inmigración”. Sí se puede mostrar:

- Evolución de hechos conocidos por tipología y territorio.
- Evolución de hechos esclarecidos y tasa de esclarecimiento, con cautelas.
- Evolución de detenidos/investigados o condenados por nacionalidad declarada.
- Tasas por población de la misma nacionalidad cuando el denominador, fecha, edad y territorio sean compatibles.
- Diferencia explícita entre lo observable y la pregunta causal que los datos no identifican.

No interpretes diferencias brutas como efecto causal de inmigración. Como mínimo, la edad, sexo, estructura territorial, situación socioeconómica, exposición policial, cambios legales, propensión a denunciar y cobertura policial pueden confundir las comparaciones.

### Inactividad y mercado laboral

La inactividad de la EPA incluye jubilados, estudiantes, cuidados, incapacidad y otras situaciones. No equivale a beneficiarios de prestaciones, rechazo a trabajar ni “mantenidos”. Si analizas el lenguaje planteado inicialmente por el usuario, tradúcelo a indicadores neutrales y medibles:

- Tasa de actividad.
- Tasa de empleo.
- Tasa de paro.
- Inactivos por clase principal.
- Vacantes.
- Duración del desempleo, solo si se incorpora una fuente oficial adicional.

Que baje el paro no demuestra por sí solo que sea más fácil encontrar trabajo. Combina paro, empleo, actividad, vacantes y, si se añade, duración o flujos de entrada/salida.

### Poder adquisitivo

No uses crecimiento salarial nominal como sinónimo de enriquecimiento. Compara ingresos con precios:

```text
factor_precios_2018_t = IPC_t / IPC_2018
euros_2018_equivalentes_en_t = 1000 * factor_precios_2018_t
valor_real_en_euros_2018 = valor_nominal_t * IPC_2018 / IPC_t
crecimiento_real = (ingreso_t / ingreso_2018) / (IPC_t / IPC_2018) - 1
```

Define con precisión el mes o promedio anual del IPC. Para comparar años completos, usa media anual frente a media anual. Si el último dato de 2025 fuera parcial en alguna tabla, no lo presentes como año completo: usa el mismo conjunto de meses en ambos años o detente en 2024.

Además del salario medio, estudia deciles, renta por persona/unidad de consumo, gasto de hogares, AROPE, empleo y vivienda. El promedio puede subir mientras determinados grupos pierden poder adquisitivo.

### Crecimiento de España y contribución migratoria

Separa tres preguntas:

1. Crecimiento de población.
2. Crecimiento del PIB real total.
3. Crecimiento del PIB real por habitante o renta real por habitante.

Para demografía, una descomposición contable válida es:

```text
variacion_poblacion = saldo_natural + saldo_migratorio + ajustes_estadisticos
contribucion_migratoria_contable = saldo_migratorio / variacion_poblacion
```

Comprueba las definiciones exactas y ajustes del INE antes de calcular. Si crecimiento total es pequeño o negativo, el porcentaje puede superar 100 % o cambiar de signo; muestra también valores absolutos.

El cambio del número de residentes nacidos fuera es otra medida descriptiva, no idéntica al saldo migratorio: influyen defunciones, emigración y cobertura estadística. No atribuyas una fracción del crecimiento del PIB a inmigración mediante una simple regla de tres. Eso requiere un diseño econométrico o una descomposición de factores que estos agregados por sí solos no identifican.

## Inventario por bloque

### Demografía y economía

Carpeta: `data_raw/demografia_economia/`

El `metadata.csv` contiene 35 filas. Incluye:

- Población residente por país de nacimiento, sexo y edad, nacional y provincial, 2018–2022.
- Actualizaciones de población 2025 distinguiendo nacimiento en España/extranjero y nacionalidad.
- Población por año de llegada, provincia y nacimiento, 2021–2025.
- Residencia un año antes y país de nacimiento, 2021–2025.
- Inmigraciones, emigraciones y saldos migratorios por país de nacimiento y territorio.
- Series migratorias antigua y nueva: no las sumes. Comprueba el puente metodológico antes de enlazarlas.
- Adquisiciones de nacionalidad, con dimensión territorial cuando está disponible.
- PIB nominal, PIB real/volumen, tasas, PIB por habitante y componentes, principalmente 2018–2024.
- Contabilidad regional.
- Renta disponible, formación bruta de capital, remuneración, puestos/empleo, horas y productividad.

Ficheros particularmente útiles para origen migratorio:

- `ine_9675_2018_2022.json`: stock nacional por país de nacimiento, sexo y edad.
- `ine_9681_2018_2022.json`: equivalente provincial.
- `ine_70364_2018_2025.json`: provincia, nacimiento y año de llegada; fichero grande y rico.
- `ine_79569_2018_2025.json`: residencia previa y nacimiento.
- `ine_69694_2018_2025.json`: inmigraciones exteriores por país de nacimiento, nueva EMCR, 2021–2024.
- `ine_24324_2018_2025.json`: flujo de inmigración exterior por país de nacimiento, serie anterior, 2018–2021.
- `ine_79274_2018_2025.json`: cruza lugar de nacimiento y nacionalidad para 2025.

No des por hecho que todos los ficheros cuyo nombre termina en `2018_2025` contienen ambos extremos: el nombre indica la ventana solicitada; la cobertura real está en `metadata.csv`.

### Criminalidad

Carpeta: `data_raw/criminalidad/`

Lee `MATRIZ_COBERTURA.md` y `metadata.csv`. Incluye:

- Hechos conocidos por tipología y CCAA: `mir_hechos_conocidos_01001.csv`.
- Hechos conocidos por tipología y provincia: `mir_hechos_conocidos_01002.csv`.
- Hechos esclarecidos por tipología y CCAA/provincia: `02001` y `02002`.
- Diez matrices `03001`–`03010` de detenidos/investigados, con combinaciones de territorio, tipología, sexo, edad y nacionalidad.
- Estadísticas judiciales del INE sobre condenados e infracciones.
- Delitos sexuales y condenados por delitos sexuales.
- Desglose provincial de infracciones por nacionalidad.
- Denominador poblacional por nacionalidad, edad, sexo y territorio.

Cobertura general de Interior: años naturales completos 2018–2024. No mezclar con balances trimestrales de 2025. Las tablas del INE llegan al último año publicado según cada operación; comprueba `metadata.csv` antes de titular un gráfico como 2018–2025.

Al calcular tasas:

```text
tasa_por_100k = numerador / poblacion_compatible * 100000
```

La población debe usar la misma nacionalidad, territorio, grupo de edad, sexo y referencia temporal que el numerador. Si no hay compatibilidad, muestra conteos y explica la limitación. Evita comparar tasas de población extranjera muy pequeña sin intervalos o advertencia de volatilidad.

### Bienestar y empleo

Carpeta: `data_raw/bienestar_empleo/`

El `metadata.csv` contiene 17 filas. Incluye:

- IPC nacional mensual por grupos ECOICOP, 2018–2025.
- Variación del IPC por CCAA.
- Tasas EPA de actividad, paro y empleo por provincia y sexo.
- Inactivos por clase principal, sexo y CCAA.
- Tasas EPA por nacionalidad, sexo, edad o CCAA. Recuérdalo: nacionalidad no es nacimiento.
- Vacantes por CCAA.
- Ganancia media anual y salario por decil.
- Renta neta por persona/unidad de consumo.
- AROPE.
- Gasto de hogares EPF.
- Índice de precios de vivienda.
- Hipotecas por provincia y plazo medio.

Cautelas importantes:

- La EPA incorpora cambio de base poblacional desde 2021; lee la nota de comparabilidad.
- La renta de la ECV suele referirse al año anterior al de encuesta. Etiqueta ambos si procede.
- EPF 2024 presenta cambio metodológico; el conjunto homogéneo descargado puede detenerse en 2023.
- AROPE cambió entre las estrategias Europa 2020 y Europa 2030. No enlaces definiciones sin armonización.
- El IPV es un índice, no precio en euros por metro cuadrado.
- La carpeta no contiene una serie homogénea oficial completa de alquiler ni precio por m² en Madrid.

## Pipeline recomendado

1. Carga y normaliza los tres `metadata.csv` en un catálogo único.
2. Inspecciona el esquema real de cada JSON/CSV antes de transformar. Los JSON del API Tempus del INE suelen venir como series con metadatos y observaciones, no como una tabla rectangular convencional.
3. Conserva valores originales, unidades, etiquetas, códigos, notas y estado provisional.
4. Crea tablas tidy separadas por operación estadística; no unas operaciones distintas antes de validar definiciones.
5. Normaliza territorio con códigos oficiales cuando estén disponibles. Trata “Total Nacional” separadamente y evita sumarlo con provincias o CCAA.
6. Normaliza periodo en columnas explícitas: año, trimestre, mes, fecha de referencia y estado completo/parcial.
7. Crea controles de duplicados, claves, totales, valores nulos y coherencia de agregación.
8. Produce una tabla de indicadores finales donde cada cifra conserve `source_dataset`, URL, unidad, periodo y transformación.
9. Genera análisis y visualizaciones únicamente desde tablas procesadas reproducibles.
10. Añade pruebas o assertions para los resultados principales: extremos temporales, denominadores positivos, ausencia de doble conteo y compatibilidad de unidades.

No sobrescribas los originales. Si corriges codificación de los CSV de Interior —pueden venir en ISO-8859-15— conserva el original y documenta la conversión.

## Comparaciones temporales

- El marco principal son años completos 2018–último año completo disponible.
- Para criminalidad registrada, el final comparable es 2024.
- Para PIB y muchas variables anuales, el final es 2024.
- IPC y EPA pueden llegar a 2025, pero confirma que se dispone de los doce meses o cuatro trimestres antes de formar un anual.
- No compares enero de 2025 con el total o promedio de 2024.
- Si solo existe 2025 parcial, usa una comparación interanual del mismo periodo y rotúlala como parcial.
- Considera 2020 como un shock extraordinario; muestra la serie completa, no solo extremos, para evitar atribuir al periodo una trayectoria lineal.

Para cambios porcentuales:

```text
cambio_absoluto = valor_final - valor_inicial
cambio_porcentual = (valor_final / valor_inicial - 1) * 100
```

En tasas expresadas en porcentaje, informa tanto puntos porcentuales como variación relativa. Ejemplo: pasar de 10 % a 12 % son +2 puntos porcentuales y +20 % relativo.

## Resultados y visualizaciones esperables

Organiza el resultado alrededor de preguntas, no alrededor de ficheros. Una propuesta:

### Población, migración y economía

- Población total, nacidos en España y nacidos fuera: serie y cambio acumulado.
- Saldo natural frente a saldo migratorio y contribución contable al crecimiento demográfico.
- Principales países de nacimiento, con valores y tasas, nacional y territorial.
- Adquisiciones de nacionalidad para ilustrar por qué nacionalidad no equivale a origen.
- PIB nominal, PIB real y PIB real por habitante, claramente separados.
- PIB/empleo/horas/productividad para contextualizar el crecimiento.

### Criminalidad

- Hechos conocidos totales y por grandes tipologías, 2018–2024: conteos y tasas por 100.000 habitantes.
- Delitos sexuales y otras categorías relevantes, mostrando niveles además de porcentajes.
- Mapa o small multiples por provincia, con escalas y denominadores coherentes.
- Hechos conocidos frente a esclarecidos y tasa de esclarecimiento, sin equipararla a condena.
- Detenidos/investigados y condenados por nacionalidad como análisis separado y explícitamente limitado.
- Un recuadro metodológico visible: no hay país de nacimiento en las tablas penales y no se identifica causalidad migratoria.

### Poder adquisitivo y bienestar

- Qué cantidad en 2024/2025 compra lo mismo que 1.000 € en 2018.
- Salario nominal frente a salario real deflactado.
- Salario por deciles para evitar que el promedio oculte distribución.
- Renta real por persona/unidad de consumo y AROPE.
- Coste de vivienda/hipotecas frente a ingreso, solo con unidades compatibles.
- Tasas de empleo, paro, actividad e inactividad por clase.
- Vacantes y otros indicadores disponibles para aproximar facilidad de empleo.

Incluye tablas de respaldo con valores exactos. En cada gráfico indica fuente, operación, unidad, periodo y si el último año es provisional o incompleto.

## Sobre 1970 y vivienda en Madrid

El repositorio no resuelve de forma válida la pregunta “años de renta necesarios para comprar una vivienda equivalente en Madrid en 1970 frente a hoy”. Faltan, como mínimo:

- Precio oficial comparable por m² y localización para 1970.
- Tamaño y calidad comparables de vivienda.
- Renta o salario del mismo universo poblacional.
- Método de conversión monetaria peseta/euro e inflación.
- Tratamiento de tipos hipotecarios, impuestos y condiciones de financiación.

No improvises esta cifra ni extrapoles el IPV actual hacia 1970. Si el usuario decide ampliar el trabajo, crea un módulo independiente, usa únicamente fuentes oficiales o archivos históricos documentados y presenta un intervalo/escenarios si no existe equivalencia exacta.

## Controles antes de publicar conclusiones

- ¿La fuente y URL están trazadas hasta cada resultado?
- ¿El periodo inicial y final son comparables y completos?
- ¿La unidad es persona, hecho, infracción, euro, índice, tasa o porcentaje?
- ¿Se evitó sumar “Total” con sus componentes?
- ¿Se usó país de nacimiento cuando se habla de origen?
- Si solo hay nacionalidad, ¿el texto y el gráfico dicen nacionalidad?
- ¿Numerador y denominador pertenecen al mismo universo?
- ¿Los cambios de base o definición están indicados?
- ¿Se muestran niveles absolutos además de porcentajes llamativos?
- ¿Se distingue crecimiento nominal de real y total de per cápita?
- ¿Se distingue correlación/descomposición contable de causalidad?
- ¿Hay código reproducible para cada tabla y gráfico?

## Límites conocidos que deben aparecer en el informe final

1. No existe país de nacimiento/origen en las matrices penales seleccionadas; nacionalidad no lo sustituye.
2. Los hechos esclarecidos no incluyen nacionalidad ni nacimiento.
3. La EPA seleccionada por condición migratoria usa nacionalidad; no se localizó una serie recurrente completa 2018–2025 equivalente por país de nacimiento.
4. La serie histórica de vivienda Madrid–1970 no está cubierta.
5. La información oficial de alquiler comparable es incompleta en este repositorio.
6. Diferencias descriptivas entre grupos no estiman cuánto cambio fue “causado” por inmigración.

## Definición de terminado

El trabajo estará listo cuando:

- Todas las cifras principales puedan regenerarse desde `data_raw/` con un solo pipeline documentado.
- Exista un catálogo de datos procesados con fuente, unidad y cobertura.
- Las tres preguntas se respondan con una conclusión cuantitativa, una visualización y una sección de limitaciones.
- Las afirmaciones sobre inmigración usen país de nacimiento cuando esté disponible y no disfracen nacionalidad como origen.
- Criminalidad 2025 no se mezcle con la serie anual completa 2018–2024.
- Poder adquisitivo se exprese en términos reales, no solo nominales.
- Las lagunas se presenten como lagunas, no como ceros ni estimaciones implícitas.

Si descubres un problema en un fichero o definición, documenta el hallazgo y vuelve a la URL oficial del `metadata.csv`. No alteres silenciosamente el dato original.

---

# Relevo devuelto — fase Claude completada (2026-08-20)

Codex: recojo aquí lo que he hecho sobre tus instrucciones, para que puedas continuar sin releer el código.

## Qué se ha entregado

`outputs/informe_espana_2018_2025.html` — informe visual con dos partes: ocho bloques de tablas
(indicador / 2018 / 2025 / serie completa / burbuja de variación, azul aumento y rojo descenso, con una
leyenda de conclusión objetiva al pie de cada tabla) y una segunda parte que responde a las tres preguntas
del encargo más las complementarias. 88 indicadores, todos con fuente, unidad, periodo y año final real.

También publicado como Artifact: https://claude.ai/code/artifact/9e788964-a82b-44a6-87c8-8a72b120d26a

Documentación de relevo: `REGISTRO_CAMBIOS_CLAUDE.md` (entorno, pipeline, inventario, hallazgos)
y `MATRIZ_ENTREGA_CLAUDE.md` (matriz de requisitos con verificación de cierre, 18/18).

## Lo que hay que saber antes de tocar nada

1. **`data_raw/` sigue intacto.** Verificado con `find`. Todo lo nuevo está en `scripts/`, `data_processed/`
   y `outputs/`. El pipeline completo se regenera con los scripts `01` a `07` en orden.

2. **Tu `data_raw/criminalidad/metadata.csv` tiene un error de universo en tres matrices.** Verificado
   numéricamente para los siete años: **03005 y 03007 contienen solo extranjeros** (totales idénticos entre sí,
   y la lista de nacionalidades de 03007 no incluye España) y **03003 contiene solo menores de 14-17 años**
   (coincide exactamente con ese grupo de edad de 03009). No lo he corregido en `data_raw/`; está documentado
   en `REGISTRO_CAMBIOS_CLAUDE.md` y en el propio informe, y `05_criminalidad.py` lleva dos `assert` que
   fallarán si una descarga futura rompe esa relación. Los detenidos de nacionalidad española se obtienen
   por diferencia `03001 − 03005`.

3. **Sí existe una serie de población homogénea 2018-2025**: la tabla 56942, que estaba catalogada como
   denominador de criminalidad. Su valor a 1 de enero de 2025 coincide exactamente con el Censo anual (70364),
   así que sirve como base poblacional única para todo el informe.

4. **No existe serie única por país de nacimiento.** Enlacé 9675 (2018-2020) con 70364 (2021-2025) y conservé
   el solape medido en `data_processed/a_solape_series_nacimiento.csv`.

## Resultados principales, por si sirven de punto de partida

- Población +2.483.227 (+5,3 %). Nacidos en España −795.527; nacidos en el extranjero +3.265.378.
  Todo el crecimiento neto y algo más procede de residentes nacidos fuera.
- 1.434.003 adquisiciones de nacionalidad 2018-2025: por eso «extranjeros» (+2.334.649) crece menos
  que «nacidos fuera».
- PIB real +9,2 % (2018-2024); por habitante +4,4 %; productividad por hora +2,0 %.
- Infracciones penales conocidas +15,2 %, pero el 85,5 % de ese aumento son estafas informáticas;
  sin ellas la criminalidad por habitante bajó −1,8 %.
- Detenidos e investigados +46,2 %. El 64,7 % del aumento corresponde al grupo de nacionalidad extranjera;
  de ese aumento, solo un 35,5 % se explica por el mayor tamaño de esa población.
- Condenados por sentencia firme: la tasa por 100.000 residentes de su propia nacionalidad **bajó** en
  ambos grupos (−2,1 % españoles, −10,9 % extranjeros).
- IPC +22,5 %: 1.000 € de 2025 compran lo que 816 € compraban en 2018.
- Salario real +3,1 % (2018-2024); renta real por persona +12,1 %; precio real de la vivienda +23,8 %.

## Si continúas, lo más rentable

1. **Desglose territorial.** Los datos por CCAA y provincia ya están descargados y `ine_lib.py` los lee;
   el informe es solo nacional.
2. **Estructura por edad y sexo en las tasas penales.** Las matrices 03009/03010 y la 56942 permiten
   estandarizar por edad, que es el principal factor de confusión de las comparaciones por nacionalidad.
3. **Duración del desempleo y flujos de colocación** (SEPE/MITES): es lo que falta para responder de verdad
   «¿es más fácil encontrar trabajo?».
4. **Módulo histórico 1970-Madrid**, separado, si el usuario lo pide.

---

# Segunda entrega · ampliación 2026-08-20

El usuario pidió cuatro correcciones sobre la primera entrega. Todas están hechas. Resumen para el relevo:

## Qué cambió

1. **Pregunta 1 sin PIB.** Ahora responde solo con población y añade el desglose del crecimiento extranjero
   por continente y por país, con los casos singulares (Ucrania y la guerra, Colombia-Venezuela, Marruecos,
   Reino Unido y el Brexit).
2. **Pregunta 2 con quién y en qué delitos.** Tasas por 100.000 residentes del mismo origen por continente,
   países concretos, peso de los extranjeros en cada tipo de infracción y composición del delito de cada
   origen.
3. **Pregunta 3 comparada con Europa.** Se añadió Eurostat porque sin comparación un +3 % de salario real no
   puede calificarse. España queda 12ª de 13 en salario real pese a tener menos inflación que la media.
4. **Pregunta 4 nueva: dinero público.** Recaudación, gasto por función, prestaciones sociales, IMV, deuda,
   déficit y listas de espera sanitarias.

Además, a petición del usuario, cada respuesta cierra ahora con un bloque **«Conclusión»** directo y en
lenguaje llano, y mantiene dentro el detalle y las tablas que la pregunta necesita.

## Fuentes añadidas y por qué

El repositorio que dejaste solo tenía INE y Ministerio del Interior, y tres preguntas no se podían responder
con eso. Se añadieron, con tus mismas reglas (organismo oficial, URL directa, fecha de descarga, cautelas),
en `data_external/` con su `metadata.csv` de 13 registros y su `README.md`:

- **Eurostat**: IPC armonizado, PIB per cápita real, ganancia neta anual, consumo individual efectivo en PPA,
  y cuentas de las administraciones públicas (ingresos, COFOG, déficit, deuda). Las cuentas públicas de
  Eurostat son las que la IGAE notifica a la UE: no es una fuente alternativa, es la misma en formato comparable.
- **Seguridad Social**: 30 nóminas mensuales del Ingreso Mínimo Vital en XLSX.
- **Ministerio de Sanidad**: 16 informes del SISLE-SNS. Solo existen en PDF; `scripts/13_listas_espera.py`
  los parsea y las cifras de 2018 y 2025 están verificadas contra el texto original.

## Cautelas nuevas que NO deben perderse

1. `earn_nt_net` de Eurostat **tiene ruptura de serie en 2024** en los trece países. Nunca compares 2018 con
   2024 en ese indicador: da caídas falsas de hasta el 25 %. El informe se detiene en 2023.
2. **El IMV no existía en 2018** (se creó en junio de 2020) y su serie descargable empieza en enero de 2024.
   Los enlaces anteriores devuelven 404 y datos.gob.es no tiene el dataset. No hay forma oficial de
   reconstruir 2020-2023.
3. **COFOG «protección social» no son «ayudas»**: las pensiones de jubilación son el 55 % del total. Y la
   subfunción «exclusión social» no es el IMV en solitario, lo incluye junto a otras prestaciones.
4. En los PDF del SISLE hay que **descartar la página de «procesos seleccionados»**, que es un subconjunto de
   11 intervenciones y no el total del SNS. Falta el corte de diciembre de 2019 porque el PDF parte la fila
   de totales; se dejó el hueco en vez de estimarlo.
5. **No mezclar deflactores**: el IPC del INE deflacta las series españolas y el IPC armonizado las europeas.

## Resultados nuevos más relevantes

- Del crecimiento de población extranjera, **el 62 % es americano**; África y Europa aportan un 15 % cada una.
  Ucrania es el único origen con un pico de guerra: de 8.278 entradas en 2019 a 89.838 en 2022.
- Tasas de detenidos/investigados por 100.000 residentes del mismo origen en 2024: África 6.296 (×7,4 la
  española), América 3.165, Europa 2.354, Asia 1.394, española 854. La tasa africana se duplicó; el resto,
  incluida la española, subió entre un 20 % y un 35 %.
- Perfil delictivo muy distinto por origen: América se concentra en seguridad vial (31,5 % de sus condenas),
  África en patrimonio (hurtos 23,3 % + robos 13,5 %).
- España pierde **-3,9 %** de salario neto real 2018-2023 frente a **+0,2 %** de la UE-27: puesto 12 de 13,
  y eso con menos inflación que la media europea.
- De los +201.484 M€ de recaudación adicional: **52 % inflación, 25 % economía real, 23 % mayor detracción**.
- De los +94.062 M€ de protección social, **el 56 % son pensiones de jubilación**. El IMV costó 5.051 M€ en
  2025, el 1,7 % del gasto social.
- Listas de espera: con +14,7 % de gasto sanitario real por habitante, hay **185.221 pacientes más** esperando
  para operarse; el tiempo medio quirúrgico baja de 129 a 121 días pero las consultas con especialista
  empeoran en todos los indicadores (de 96 a 102 días, y del 43,8 % al 61,5 % esperando más de 60 días).

## Lo que sigue faltando

- Detalle de recaudación **por figura tributaria** (AEAT): Eurostat agrega por categoría económica.
- **IMV 2020-2023**: no hay fuente oficial descargable.
- **Diciembre de 2019** en listas de espera: el PDF no permite leer la fila de totales.
- **Duración del desempleo y flujos de colocación** (SEPE/MITES).
- **Desglose territorial** del informe: los datos están descargados y los lectores lo soportan.
- **Vivienda Madrid 1970**: sigue sin cubrir.
