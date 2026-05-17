from fastapi import FastAPI
from pydantic import BaseModel

from src.insurance import cotizar_seguro, municipios_disponibles, anios_disponibles

app = FastAPI(title="Seguro Agrícola Café API")

# MODELO DE ENTRADA

class CotizacionRequest(BaseModel):
    municipio: str
    anio: int
    area_ha: float

# ENDPOINTS

@app.get("/")
def root():
    return {"message": "API Seguro Agrícola Café activa"}


@app.get("/municipios")
def get_municipios():
    return municipios_disponibles()


@app.get("/anios")
def get_anios():
    return anios_disponibles()


@app.post("/cotizar")
def cotizar(data: CotizacionRequest):
    resultado = cotizar_seguro(
        municipio=data.municipio,
        anio=data.anio,
        area_ha=data.area_ha
    )
    return resultado