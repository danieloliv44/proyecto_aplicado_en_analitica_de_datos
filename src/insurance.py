# Librerias
import numpy as np
import pandas as pd

from src.data_loader import load_data
from src.risk_index import (
    calcular_indice_para_fila,
    calcular_payout,
    clasificar_riesgo,
    obtener_probabilidad_perdida,
)


DATA = load_data()

features_hist = DATA["features_hist"]
features_fut = DATA["features_fut"]
clusters = DATA["clusters"]
coef_map = DATA["coef_map"]
variables_indice = DATA["variables_indice"]
parametros = DATA["parametros"]
precios = DATA["precios"]


def _construir_referencias_cluster():
    referencias = {}

    for c in sorted(features_hist["cluster"].unique()):
        df_c = features_hist[features_hist["cluster"] == c]

        referencias[int(c)] = {
            "mean": df_c[variables_indice].mean(),
            "std": df_c[variables_indice].std().replace(0, np.nan),
        }

    return referencias
referencias_cluster = _construir_referencias_cluster()


def _construir_referencias_indice():
    indice_raw_hist = []

    for c in sorted(features_hist["cluster"].unique()):
        c = int(c)
        df_c = features_hist[features_hist["cluster"] == c].copy()

        media = referencias_cluster[c]["mean"]
        std = referencias_cluster[c]["std"]

        x_scaled = (df_c[variables_indice] - media) / std
        x_scaled = x_scaled.replace([np.inf, -np.inf], np.nan).fillna(0)

        pesos = coef_map[str(c)].loc[variables_indice]
        raw = x_scaled.mul(pesos, axis=1).sum(axis=1)

        indice_raw_hist.append(
            pd.DataFrame({
                "cluster": c,
                "indice_raw": raw,
            })
        )

    indice_raw_hist = pd.concat(indice_raw_hist, ignore_index=True)

    return (
        indice_raw_hist
        .groupby("cluster")["indice_raw"]
        .agg(["mean", "std"])
        .reset_index()
    )
referencias_indice = _construir_referencias_indice()


def _construir_indice_historico():
    df_hist = features_hist.copy()

    df_hist["indice_cluster"] = df_hist.apply(
        lambda row: calcular_indice_para_fila(
            row=row,
            variables_indice=variables_indice,
            coef_map=coef_map,
            referencias_cluster=referencias_cluster,
            referencias_indice=referencias_indice,
        ),
        axis=1,
    )

    umbral_perdida = float(parametros["umbral_perdida_rendimiento"])

    df_hist["evento_perdida_global"] = (
        df_hist["Rendimiento (t/ha)"] <= umbral_perdida
    ).astype(int)

    return df_hist
df_hist_indice = _construir_indice_historico()


def _normalizar_municipio(municipio: str) -> str:
    return str(municipio).strip().upper()


def _obtener_base_por_anio(anio: int):
    anio = int(anio)

    if anio <= int(features_hist["anio"].max()):
        return features_hist, "historica"
    return features_fut, "futura"


def _obtener_precio(anio: int) -> float:
    anio = int(anio)

    if "precio_referencia_USD_ton" in precios.columns:
        col_precio = "precio_referencia_USD_ton"
    elif "PM30_prom_USD_ton" in precios.columns:
        col_precio = "PM30_prom_USD_ton"
    else:
        raise ValueError("No se encontró columna de precio compatible.")

    precios_aux = precios.copy()
    precios_aux["anio"] = precios_aux["anio"].astype(int)

    fila = precios_aux[precios_aux["anio"] == anio]

    if fila.empty:
        return float(precios_aux[col_precio].iloc[-1])

    return float(fila[col_precio].iloc[0])


def municipios_disponibles():
    municipios = sorted(
        set(features_hist["municipio"].unique())
        | set(features_fut["municipio"].unique())
    )
    return municipios


def anios_disponibles():
    anios = sorted(
        set(features_hist["anio"].astype(int).unique())
        | set(features_fut["anio"].astype(int).unique())
    )
    return anios


def cotizar_seguro(municipio: str, anio: int, area_ha: float):
    municipio = _normalizar_municipio(municipio)
    anio = int(anio)
    area_ha = float(area_ha)

    if area_ha <= 0:
        raise ValueError("El área cultivada debe ser mayor que cero.")

    base, tipo_estimacion = _obtener_base_por_anio(anio)

    base = base.copy()
    base["municipio"] = base["municipio"].astype(str).str.strip().str.upper()

    fila = base[
        (base["municipio"] == municipio)
        & (base["anio"].astype(int) == anio)
    ]

    if fila.empty:
        raise ValueError(
            f"No hay información disponible para municipio={municipio}, anio={anio}."
        )

    fila = fila.iloc[0].copy()

    if "cluster" not in fila.index or pd.isna(fila["cluster"]):
        clusters_aux = clusters.copy()
        clusters_aux["municipio"] = clusters_aux["municipio"].astype(str).str.strip().str.upper()

        fila_cluster = clusters_aux[clusters_aux["municipio"] == municipio]

        if fila_cluster.empty:
            raise ValueError(f"No hay clúster asignado para {municipio}.")

        fila["cluster"] = int(fila_cluster["cluster"].iloc[0])

    fila["cluster"] = int(fila["cluster"])

    indice = calcular_indice_para_fila(
        row=fila,
        variables_indice=variables_indice,
        coef_map=coef_map,
        referencias_cluster=referencias_cluster,
        referencias_indice=referencias_indice,
    )

    trigger = float(parametros["trigger"])
    limite = float(parametros["limite"])
    umbral_medio = float(parametros["umbral_medio_riesgo"])
    exponent = float(parametros["payout_exponent"])

    payout = calcular_payout(
        indice=indice,
        trigger=trigger,
        limite=limite,
        exponent=exponent,
    )

    nivel_riesgo = clasificar_riesgo(
        indice=indice,
        trigger=trigger,
        umbral_medio=umbral_medio,
    )

    probabilidad_perdida = obtener_probabilidad_perdida(
        indice=indice,
        df_hist_indice=df_hist_indice,
    )

    rendimiento_esperado = (
        features_hist
        .loc[features_hist["municipio"] == municipio, "Rendimiento (t/ha)"]
        .mean()
    )

    if pd.isna(rendimiento_esperado):
        rendimiento_esperado = features_hist["Rendimiento (t/ha)"].mean()

    produccion_esperada_t = rendimiento_esperado * area_ha

    precio_usd_ton = _obtener_precio(anio)

    monto_asegurado = produccion_esperada_t * precio_usd_ton

    prima_pura_rate = float(parametros["prima_pura"])
    prima_comercial_rate = float(parametros["prima_comercial"])

    prima_pura_usd = prima_pura_rate * monto_asegurado
    prima_comercial_usd = prima_comercial_rate * monto_asegurado
    indemnizacion_estimada_usd = payout * monto_asegurado

    rendimiento_real = None

    if tipo_estimacion == "historica" and "Rendimiento (t/ha)" in fila.index:
        if not pd.isna(fila["Rendimiento (t/ha)"]):
            rendimiento_real = float(fila["Rendimiento (t/ha)"])

    return {
        "municipio": municipio,
        "anio": anio,
        "area_ha": area_ha,
        "cluster": int(fila["cluster"]),
        "tipo_estimacion": tipo_estimacion,
        "rendimiento_real_t_ha": rendimiento_real,
        "rendimiento_esperado_t_ha": float(rendimiento_esperado),
        "produccion_esperada_t": float(produccion_esperada_t),
        "precio_usd_ton": float(precio_usd_ton),
        "indice_riesgo": float(indice),
        "nivel_riesgo": nivel_riesgo,
        "probabilidad_perdida": float(probabilidad_perdida),
        "payout": float(payout),
        "monto_asegurado_usd": float(monto_asegurado),
        "prima_pura_usd": float(prima_pura_usd),
        "prima_comercial_usd": float(prima_comercial_usd),
        "indemnizacion_estimada_usd": float(indemnizacion_estimada_usd),
    }