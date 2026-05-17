from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.insurance import cotizar_seguro, municipios_disponibles, anios_disponibles


app = FastAPI(
    title="Seguro Agrícola Indexado para Café",
    description="API para cotizar prima, riesgo e indemnización estimada.",
    version="1.0.0"
)


class CotizacionRequest(BaseModel):
    municipio: str = Field(default="MANIZALES")
    anio: int = Field(default=2026)
    area_ha: float = Field(default=1.0, gt=0)


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
    try:
        return cotizar_seguro(
            municipio=data.municipio,
            anio=data.anio,
            area_ha=data.area_ha
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))