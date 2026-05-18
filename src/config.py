from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PATH_MODEL = PROJECT_ROOT / "data" / "model"

FEATURES_HIST = PATH_MODEL / "features_intra_anuales_2007-2024_clusters.csv"
FEATURES_FUT = PATH_MODEL / "features_intra_anuales_2025-2027.csv"
CLUSTERS = PATH_MODEL / "clusters_municipales.csv"
COEFICIENTES = PATH_MODEL / "coeficientes_indice_por_cluster.csv"
VARIABLES_INDICE = PATH_MODEL / "variables_indice_final.csv"
PARAMETROS = PATH_MODEL / "parametros_seguro.csv"
PRECIOS = PATH_MODEL / "precios_cafe_anual_2007-2027.csv"