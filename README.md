# España 2018–2025: datos oficiales, análisis e informe

Repositorio reproducible para estudiar población y migración, criminalidad, economía, poder adquisitivo, mercado laboral, sector público y servicios públicos en España entre 2018 y 2025.

## Ver el informe

Abre en cualquier navegador:

`outputs/informe_espana_2018_2025.html`

Es un documento HTML autónomo en cuanto a datos y gráficos. Usa Google Fonts si hay conexión; sin conexión mantiene el contenido y recurre a tipografías del sistema.

https://ivancarrillo.com/recursos/analisis-espana-2018-2025

## Fuentes

Los datos proceden exclusivamente de organismos públicos:

- Instituto Nacional de Estadística.
- Portal Estadístico de Criminalidad del Ministerio del Interior.
- Eurostat.
- Seguridad Social.
- Ministerio de Sanidad.

Cada descarga está documentada en:

- `data_raw/demografia_economia/metadata.csv`
- `data_raw/criminalidad/metadata.csv`
- `data_raw/bienestar_empleo/metadata.csv`
- `data_external/metadata.csv`

Los metadatos registran organismo, URL, cobertura, unidad, granularidad y cautelas de interpretación.

## Instalación

Requiere Python 3.9 o posterior.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/00_prepare_data.py
```

El último comando descomprime `ine_70364_2018_2025.json.gz`. El JSON original supera el límite de 100 MB por fichero de GitHub, pero su contenido completo está incluido de forma comprimida.

## Regenerar el análisis y el HTML

Los datos descargados ya están incluidos. Para regenerar las tablas procesadas y el informe sin volver a descargar fuentes externas:

```bash
for script in \
  01_demografia_migracion \
  02_economia \
  03_laboral \
  04_precios_poder_adquisitivo \
  05_criminalidad \
  09_desglose_origen \
  11_sector_publico \
  06_indicadores \
  07_informe_html
do
  .venv/bin/python "scripts/${script}.py" || break
done
```

Los scripts `09` y `11` consumen los conjuntos ya presentes en `data_external/`. Los scripts `06` y `07` deben ejecutarse después porque ensamblan los 117 indicadores y el HTML final.

## Actualizar fuentes externas

Los siguientes scripts acceden a Internet y pueden cambiar los datos descargados si el organismo ha publicado nuevas revisiones:

```bash
.venv/bin/python scripts/08_eurostat.py
.venv/bin/python scripts/10_finanzas_publicas.py
.venv/bin/python scripts/12_imv.py
.venv/bin/python scripts/13_listas_espera.py
```

Después de actualizarlos, ejecuta `09_desglose_origen`, `11_sector_publico`, `06_indicadores` y `07_informe_html` en ese orden. Revisa siempre coberturas y rupturas de serie antes de publicar una actualización.

## Estructura

- `data_raw/`: 74 datasets originales del INE y Ministerio del Interior. No deben editarse.
- `data_external/`: datos oficiales adicionales de Eurostat, Seguridad Social y Sanidad, incluidos originales XLSX/PDF cuando procede.
- `data_processed/`: tablas derivadas por los scripts.
- `outputs/`: informe final y JSON usados para construirlo.
- `scripts/`: pipeline reproducible.
- `reports/`: validaciones e inventarios.
- `coordinacion.md`: contexto metodológico completo del encargo.
- `REGISTRO_CAMBIOS_CLAUDE.md`: decisiones y hallazgos de la fase de análisis.
- `MATRIZ_ENTREGA_CLAUDE.md`: requisitos y comprobaciones declaradas.

## Advertencias metodológicas esenciales

- País de nacimiento y nacionalidad no son equivalentes. Una persona naturalizada figura con nacionalidad española.
- Las matrices penales utilizadas no publican país de nacimiento. Por ello no permiten atribuir causalmente criminalidad a inmigración u origen.
- Hechos conocidos, hechos esclarecidos, detenidos/investigados, condenados e infracciones son unidades distintas.
- Interior llega a 2024 en las series anuales descargadas; no se mezclan balances parciales de 2025 con años completos.
- Crecimiento nominal no equivale a crecimiento real; el poder adquisitivo se calcula deflactando con IPC.
- La inactividad EPA incluye estudiantes, jubilados, cuidadores, incapacidad y otras situaciones; no mide voluntad de trabajar.
- Algunas series presentan cambios de base o rupturas. Consulta los metadatos y el apartado de limitaciones del informe.
- La comparación de vivienda Madrid–1970 no está resuelta con una serie oficial homogénea y no debe improvisarse.

## Validación

```bash
.venv/bin/python scripts/validate_inventory.py
python3 -m py_compile scripts/*.py
```

La revisión previa a publicación confirmó que:

- Los scripts compilan.
- El HTML contiene 117 indicadores en 10 bloques.
- El informe se regenera de forma determinista a partir de los datos procesados: SHA-256 `b05eaa27ec2b60ea079c6f5c7ae375e25a7c4730f8a65a637a16932e4f70fa58`.
- No hay identificadores HTML duplicados ni recursos locales rotos.

## Alcance y reutilización

Los ficheros de datos conservan las condiciones de reutilización de sus organismos de origen. Antes de redistribuir o reutilizar el proyecto en otro contexto, consulta las condiciones indicadas por cada fuente oficial. No se ha añadido una licencia propia al código o al informe.
