# src/interfaces/routers/sunat.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime

from src.application.enrolados.get_enrolados import GetEnrolado
from src.application.enrolados.save_enrolados import SaveEnrolado
from src.application.api_sunat.orquestador_descargas import OrquestadorDescargas

from src.interfaces.dependencias.enrolado import (
    dp_get_enrolado,
    dp_save_enrolado,
    get_orquestador_service,
)

router = APIRouter(prefix="/api-sunat", tags=["api-sunat"])


class CredencialesManuales(BaseModel):
    ruc: str
    usuario_sol: str
    clave_sol: str
    client_id: str
    client_secret: str


def generar_periodos(meses_hacia_atras: int, incluir_mes_actual: bool = True) -> list:
    """
    Genera periodos en formato YYYYMM.
    Si incluir_mes_actual es True, empieza a contar desde el mes actual.
    Si es False, empieza a contar desde el mes anterior.
    """
    hoy = datetime.now()
    anio_actual, mes_actual = hoy.year, hoy.month
    periodos = []

    # Si no queremos el mes actual, retrocedemos un mes antes de empezar
    if not incluir_mes_actual:
        mes_actual -= 1
        if mes_actual == 0:
            mes_actual = 12
            anio_actual -= 1

    for _ in range(meses_hacia_atras):
        periodos.append(f"{anio_actual}{mes_actual:02d}")
        mes_actual -= 1
        if mes_actual == 0:
            mes_actual = 12
            anio_actual -= 1

    return periodos


@router.post("/manual")
def descargar_manual(
    datos: CredencialesManuales,
    orquestador: OrquestadorDescargas = Depends(get_orquestador_service),
    save_repo: SaveEnrolado = Depends(dp_save_enrolado),
):
    periodos = generar_periodos(15, incluir_mes_actual=True)

    resultado = orquestador.execute(
        ruc=datos.ruc,
        usuario_sol=datos.usuario_sol,
        clave_sol=datos.clave_sol,
        client_id=datos.client_id,
        client_secret=datos.client_secret,
        periodos=periodos,
    )

    if not resultado.get("valido"):
        raise HTTPException(
            status_code=401, 
            detail="Error de autenticación. Verifica que el RUC, Usuario y Clave SOL sean correctos."
        )

    try:
        save_repo.execute(datos.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar en BD: {e}")

    return {
        "status": "success",
        "tipo": "manual_historico",
        "total_procesados": len(resultado["detalle"]),
        "detalle": resultado["detalle"],
    }


@router.post("/procesar-lote-automatico")
def procesar_lote_automatico(
    limit: int = 2,
    orquestador: OrquestadorDescargas = Depends(get_orquestador_service),
    repo: GetEnrolado = Depends(dp_get_enrolado),
):
    enrolados = repo.execute(limite=limit)
    if not enrolados:
        raise HTTPException(
            status_code=404, detail="No hay enrolados en la base de datos."
        )

    periodos = generar_periodos(3, incluir_mes_actual=True) 
    resultados_lote = []

    for emp in enrolados:
        resultado = orquestador.execute(
            ruc=emp["ruc"],
            usuario_sol=emp["usuario_sol"],
            clave_sol=emp["clave_sol"],
            client_id=emp["client_id"],
            client_secret=emp["client_secret"],
            periodos=periodos,
        )
        resultados_lote.append(
            {
                "ruc": emp["ruc"],
                "detalle": resultado.get("detalle", []),
            }
        )

    return {
        "status": "success",
        "tipo": "automatico_lote",
        "periodo_procesado": periodos[0],
        "total_enrolados": len(enrolados),
        "resultados": resultados_lote,
    }
