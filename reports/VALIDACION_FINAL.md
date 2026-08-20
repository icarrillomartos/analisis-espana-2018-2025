# Validación final de la descarga

Fecha de comprobación: 2026-08-20.

## Resultado técnico

- 74 datasets de datos: 35 de demografía/economía, 22 de criminalidad y 17 de bienestar/empleo.
- Tamaño total del repositorio en la validación: 426 MB.
- 74/74 ficheros CSV o JSON abren y se parsean correctamente.
- 74/74 tienen una fila correspondiente en el `metadata.csv` de su bloque.
- Las coberturas, frecuencias, unidades, desgloses y URLs oficiales están documentadas en los metadatos.
- Los datos de Interior se han limitado a años naturales completos 2018–2024. Las tablas del INE llegan a 2024 o 2025 según calendario de publicación.

## Cobertura sustantiva

- Demografía y migración: stocks por país de nacimiento, año de llegada y territorio; flujos de inmigración/emigración y saldos; adquisiciones de nacionalidad.
- Economía: PIB nominal, volumen/crecimiento real, PIB per cápita, componentes, renta disponible, inversión, empleo, horas, remuneración y productividad.
- Poder adquisitivo: IPC, gasto, salarios, renta, AROPE, EPA, inactividad, vacantes, precios de vivienda e hipotecas.
- Criminalidad: hechos conocidos, hechos esclarecidos, detenidos/investigados, condenados e infracciones, con territorio y tipología según disponibilidad.

## Límites que no deben ocultarse

- Interior no publica país de nacimiento/origen en las matrices descargadas de detenidos/investigados; publica nacionalidad. Una persona naturalizada figura con su nacionalidad actual. No puede reconstruirse origen a partir de esa tabla.
- Los hechos esclarecidos no llevan nacionalidad ni país de nacimiento. No se deben atribuir a inmigración cruzándolos de forma directa con otra unidad estadística.
- La EPA recurrente seleccionada ofrece nacionalidad, no una serie equivalente completa 2018–2025 por país de nacimiento. Los datos demográficos por nacimiento no convierten automáticamente esa clasificación laboral.
- No se reunió una serie oficial homogénea de vivienda en Madrid comparable entre 1970 y hoy. La comparación histórica de 1970 necesita un módulo separado de reconstrucción metodológica.
- La inactividad incluye jubilación, estudios, cuidados, incapacidad y otras situaciones. No mide por sí sola rechazo al trabajo ni condición de beneficiario de ayudas.

## Inventarios

- Cada bloque contiene su propio `metadata.csv`.
- `file_inventory.csv` es un control mecánico adicional de formato y tamaño. La columna de años visibles es exploratoria: números contenidos en valores o códigos pueden parecer años; la cobertura válida es la declarada y comprobada en los metadatos de cada bloque.
