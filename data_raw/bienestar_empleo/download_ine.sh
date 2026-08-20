#!/bin/zsh
set -euo pipefail

out=${0:A:h}
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

download_table() {
  local id=$1 name=$2
  local url="https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/${id}?tip=AM"
  curl -L --fail --retry 3 --silent --show-error "$url" -o "$tmp/${id}.json"
  jq '[.[] | .Data = ([.Data[]? | select(.Anyo >= 2018 and .Anyo <= 2025)]) | select((.Data|length)>0)]' \
    "$tmp/${id}.json" > "$out/${name}.json"
}

download_table 50902 ipc_nacional_mensual_grupos
download_table 50917 ipc_tasa_variacion_general_ccaa_mensual
download_table 65349 epa_tasas_actividad_paro_empleo_provincia_sexo_trimestral
download_table 65343 epa_inactivos_clase_sexo_ccaa_trimestral
download_table 65300 epa_tasa_actividad_nacionalidad_sexo_ccaa_trimestral
download_table 65310 epa_tasa_empleo_nacionalidad_sexo_ccaa_trimestral
download_table 65336 epa_tasa_paro_nacionalidad_sexo_ccaa_trimestral
download_table 65087 epa_tasa_actividad_nacionalidad_sexo_edad_trimestral
download_table 6064 vacantes_ccaa_trimestral
download_table 28200 ganancia_media_anual_sexo_tipo_contrato
download_table 10910 salario_medio_por_decil
download_table 9947 renta_neta_media_persona_unidad_consumo_ccaa
download_table 74860 arope_europa2030_tipo_hogar
download_table 25198 epf_gasto_medio_hogar_persona_detalle_coicop
download_table 25173 ipv_media_anual_ccaa_tipo_vivienda_base2015
download_table 76317 hipotecas_total_fincas_nacional_provincias
download_table 24458 hipotecas_plazo_medio
