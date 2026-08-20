# Matriz de cobertura: criminalidad 2018-2025

| Necesidad | Nacional | CCAA | Provincia | Tipología | Sexo | Edad | Nacionalidad | Cobertura | Estado |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| Hechos conocidos | Sí | Sí | Sí | Sí | No | No | No | 2018-2024 | Completo hasta último anual disponible en Portal |
| Hechos esclarecidos | Sí | Sí | Sí | Sí | No | No | No | 2018-2024 | Completo hasta último anual disponible en Portal |
| Detenciones/investigados | Sí | Sí | Sí | Sí | Sí | Sí | Sí | 2018-2024 | Diez matrices completas |
| Condenados adultos | Sí | No | Indirecto | Sí | Sí | Sí | Sí | 2018-2025 | Series INE anuales completas |
| Condenados/delitos sexuales | Sí | No | No | Sí | Sí | Sí | Sí | 2018-2025 | Series INE anuales completas |
| Delitos de condenados por provincia | Sí | No | Sí | No | No | No | Sí | 2018-2025 | Disponible; provincia es lugar de condena |
| Denominadores de población por nacionalidad | Sí | Sí | Sí | N/A | Sí | Sí | Sí | 2018-2025 | Solo 1 de enero de cada año; definición compatible con nacionalidad |
| País de nacimiento/origen de detenidos o condenados | No | No | No | No | No | No | No | N/D | No publicado en estas operaciones; no sustituir con nacionalidad |

Todos los CSV del Ministerio son conversiones oficiales completas en formato de base de datos separada por punto y coma, recortadas de forma fiel a años naturales 2018-2024. Los JSON del INE proceden de la API Tempus y se recortaron a 2018-2025. No se incluyeron balances trimestrales para evitar comparar periodos parciales con años completos.

## Advertencias analíticas esenciales

- Nacionalidad jurídica no mide país de nacimiento, origen ni condición migratoria. Una persona nacida fuera puede ser española por naturalización, y una extranjera puede haber nacido en España.
- Hechos conocidos, hechos esclarecidos, detenciones/investigaciones, delitos en sentencia y personas condenadas son unidades distintas. No deben restarse ni atribuirse causalmente entre sí.
- Para tasas por nacionalidad hacen falta denominadores de población con la misma definición, territorio, sexo, edad y fecha. Las cuentas brutas inducen sesgo de composición.
- La pandemia de 2020 alteró exposición, movilidad y registro. Además existen cambios de cobertura policial y de tipificación señalados por las fuentes.
