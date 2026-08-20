# Matriz inicial de resultados

Periodo principal: años completos 2018–2025; si 2025 no está publicado, último año completo disponible. Los datos mensuales o trimestrales se conservarán con su periodo explícito y nunca se compararán como si fueran años completos.

| Bloque | Datos necesarios | Desglose deseado | Fuente oficial prioritaria | Criterio de cumplimiento | Estado inicial |
|---|---|---|---|---|---|
| Población | Población residente y variación anual | España, CCAA, provincia; sexo/edad cuando exista | INE | Serie comparable que cubra 2018 y el último dato hasta 2025 | Cumplido |
| Migración | Inmigración, emigración, saldo migratorio, adquisiciones de nacionalidad y población nacida fuera | País de nacimiento como dimensión principal; progenitores/año de llegada si existe; nacionalidad solo secundaria; territorio | INE | Flujos y stocks separados; naturalizaciones cuantificadas; cobertura y unidad documentadas | Cumplido; progenitores no disponibles en las series recurrentes seleccionadas |
| Crecimiento económico | PIB nominal, volumen, variación real y PIB per cápita | España; CCAA/provincia si existe | INE | No confundir euros corrientes, volumen encadenado y tasas | Cumplido hasta 2024 |
| Precios/poder adquisitivo | IPC general y grupos; índice y variaciones | España, CCAA/provincia cuando exista | INE | Permite deflactar 1.000 € de 2018 frente al último dato | Cumplido hasta 2025 |
| Ingresos | Salarios, coste salarial, renta por hogar/persona | Territorio, sexo/edad/nacionalidad cuando exista | INE/AEAT | Series nominales enlazables con IPC | Cumplido; salario anual hasta 2024 |
| Nivel de vida | Renta disponible, pobreza/AROPE, desigualdad | España y CCAA | INE | Indicadores con año de renta y año de encuesta diferenciados | Cumplido; cautela de año de renta en metadatos |
| Mercado laboral | Ocupados, parados, activos, inactivos y tasas | Territorio, edad, sexo y país de nacimiento; nacionalidad solo secundaria | INE EPA/SEPE | Valores absolutos y tasas; trimestre claramente identificado | Parcial: amplia EPA territorial y por nacionalidad; no se localizó serie recurrente equivalente por país de nacimiento |
| Facilidad de empleo | Duración del paro, vacantes, flujos/colocaciones | Territorio y perfiles | INE/SEPE/MITES | Proxies documentados; no inferir solo desde tasa de paro | Parcial: tasas y vacantes; no se incorporó microdato de duración/colocaciones |
| Vivienda | Precio de compra, alquiler oficial si existe, transacciones e hipotecas | Madrid y España; CCAA/provincia | INE/MIVAU/Banco de España | Precio y renta/salario comparables; m² cuando exista | Parcial: IPV e hipotecas; falta serie homogénea oficial de alquiler y precio €/m² Madrid |
| Historia 1970 | IPC, salarios/renta y vivienda histórica | España/Madrid | INE/Banco de España/MIVAU | Serie histórica separada y advertencias metodológicas | No cubierto: fuera del periodo principal y sin serie homogénea de vivienda comparable |
| Criminalidad registrada | Hechos conocidos por tipología | España, CCAA, provincia/municipio cuando exista | Ministerio del Interior | Años completos homogéneos 2018–último disponible | Cumplido 2018–2024, CCAA y provincia |
| Esclarecimiento | Hechos esclarecidos y tasas | España y territorio, tipología | Ministerio del Interior | Separados de condenas y de hechos conocidos | Cumplido 2018–2024, CCAA y provincia |
| Personas investigadas | Detenidos/investigados | Territorio, tipología, sexo/edad si existe | Ministerio del Interior | Unidad persona diferenciada de número de hechos | Cumplido 2018–2024; Interior ofrece nacionalidad, no nacimiento |
| Condenas/origen disponible | Condenados e infracciones por país de nacimiento si se publica; nacionalidad como variable distinta | Delito, edad, sexo, país de nacimiento y/o nacionalidad | INE | Personas e infracciones separadas; ausencia de origen documentada; población de referencia disponible | Parcial: condenas e infracciones por nacionalidad; país de nacimiento no publicado en estas tablas |
| Denominadores | Población por país de nacimiento, nacionalidad, edad y sexo | España y territorio | INE | Permite tasas separadas; no comparar conteos brutos entre poblaciones | Cumplido como series separadas; no habilita convertir nacionalidad penal en origen |

## Reglas de validación

- Cada fichero tendrá procedencia, URL, fecha de descarga, cobertura real, frecuencia, unidad y granularidad.
- Se conservará el dato original siempre que sea descargable; cualquier conversión será reproducible.
- Se marcarán periodos provisionales, cambios metodológicos y rupturas de serie.
- Nacionalidad, país de nacimiento y condición migratoria son conceptos distintos.
- Hechos conocidos, hechos esclarecidos, detenidos/investigados, procedimientos y condenas son etapas y unidades distintas.
- La inactividad de la EPA incluye estudiantes, jubilados, cuidadores y otras situaciones; no mide por sí misma voluntad de trabajar ni dependencia de prestaciones.
