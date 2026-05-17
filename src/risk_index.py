import numpy as np
import pandas as pd

# CÁLCULO DEL ÍNDICE CLIMÁTICO

def calcular_indice_para_fila(
    row,
    variables_indice,
    coef_map,
    referencias_cluster,
    referencias_indice
):

    c = int(row["cluster"])

    media = referencias_cluster[c]["mean"]
    std = referencias_cluster[c]["std"]

    X = row[variables_indice].astype(float)

    X_scaled = (X - media) / std
    X_scaled = X_scaled.replace([np.inf, -np.inf], np.nan).fillna(0)

    # 🔥 IMPORTANTE: columnas como string
    pesos = coef_map[str(c)].loc[variables_indice]

    indice_raw = (X_scaled * pesos).sum()

    ref_idx = referencias_indice[
        referencias_indice["cluster"] == c
    ].iloc[0]

    if ref_idx["std"] == 0 or pd.isna(ref_idx["std"]):
        indice = 0.0
    else:
        indice = (indice_raw - ref_idx["mean"]) / ref_idx["std"]

    return float(indice)

# FUNCIÓN DE PAGO (PAYOUT)
def calcular_payout(indice, trigger, limite, exponent=1.0):

    if indice >= trigger:
        return 0.0

    if indice <= limite:
        return 1.0

    payout = ((trigger - indice) / (trigger - limite)) ** exponent

    return float(np.clip(payout, 0, 1))

# CLASIFICACIÓN DE RIESGO
def clasificar_riesgo(indice, trigger, umbral_medio):

    if indice <= trigger:
        return "Alto"
    elif indice <= umbral_medio:
        return "Medio"
    else:
        return "Bajo"

# PROBABILIDAD DE PÉRDIDA
def obtener_probabilidad_perdida(indice, df_hist_indice):
    # Distancia entre índices
    df_hist_indice["dist"] = np.abs(
        df_hist_indice["indice_cluster"] - indice
    )

    # Tomar vecinos más cercanos
    vecinos = df_hist_indice.nsmallest(50, "dist")

    prob = vecinos["evento_perdida_global"].mean()

    return float(prob)