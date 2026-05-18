import pandas as pd
from pathlib import Path

from src.config import (
    FEATURES_HIST,
    FEATURES_FUT,
    CLUSTERS,
    COEFICIENTES,
    VARIABLES_INDICE,
    PARAMETROS,
    PRECIOS
)

def load_data():

    # CARGA
    features_hist = pd.read_csv(FEATURES_HIST)
    features_fut = pd.read_csv(FEATURES_FUT)
    clusters = pd.read_csv(CLUSTERS)
    coeficientes = pd.read_csv(COEFICIENTES)
    variables = pd.read_csv(VARIABLES_INDICE)
    parametros = pd.read_csv(PARAMETROS)
    precios = pd.read_csv(PRECIOS)

    # LIMPIEZA BÁSICA
    for df in [features_hist, features_fut, clusters]:
        df["municipio"] = df["municipio"].str.strip().str.upper()

    
    # VARIABLES DEL ÍNDICE
    variables_indice = variables["variable"].tolist()

    # COEFICIENTES
    coef_map = coeficientes.set_index("variable")

    # PARÁMETROS
    parametros_dict = parametros.iloc[0].to_dict()

    # PRECIOS
    precios["anio"] = precios["anio"].astype(int)

     # OUTPUT
    return {
        "features_hist": features_hist,
        "features_fut": features_fut,
        "clusters": clusters,
        "coef_map": coef_map,
        "variables_indice": variables_indice,
        "parametros": parametros_dict,
        "precios": precios
    }