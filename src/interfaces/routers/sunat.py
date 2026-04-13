# src/interfaces/routers/sunat.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime

from src.application.enrolados.get_enrolados import GetEnrolado
from src.application.enrolados.get_only_enrolados import GetOnlyEnrolado
from src.application.sunat.orquestador_descargas import OrquestadorDescargas
from src.application.sunat.orquestador_tickets import OrquestadorTickets
from src.application.sunat.get_token import GetToken

from src.interfaces.dependencias.enrolado import (
    dp_get_enrolado,
    dp_get_only_enrolado,
    dp_get_token,
    dp_orquestador_tickets_compras,
    dp_orquestador_tickets_ventas,
    #dp_orquestador_descargas_ventas,
    dp_orquestador_descargas_compras,
)

router = APIRouter(prefix="/api-sunat", tags=["api-sunat"])


class CredencialesNuevas(BaseModel):
    ruc: str
    usuario_sol: str
    clave_sol: str


class CredencialesManuales(BaseModel):
    ruc: str
    usuario_sol: str
    clave_sol: str
    client_id: str
    client_secret: str
    email: str


def generar_periodos(cantidad_meses: int) -> list:
    """
    Genera una lista de periodos en formato YYYYMM, comenzando desde el mes actual
    hacia atrás, según la cantidad de meses especificada.
    """
    hoy = datetime.now()
    periodos = []
    for i in range(cantidad_meses):
        mes = hoy.month - i
        año = hoy.year
        while mes <= 0:
            mes += 12
            año -= 1
        periodos.append(f"{año}{mes:02d}")
    return periodos


@router.post("/enrolate")
def autenticar_usuario(
    datos: CredencialesNuevas,
    get_token: GetToken = Depends(dp_get_token),
):
    resultado = get_token.nuevo_execute(
        ruc=datos.ruc,
        usuario_sol=datos.usuario_sol.upper(),
        clave_sol=datos.clave_sol,
    )

    if resultado:
        return {
            "status": "success",
            "mensaje": "Autenticación exitosa. Token obtenido.",
            "token": resultado,
        }
    else:
        raise HTTPException(
            status_code=401,
            detail="Autenticación fallida. Verifica las credenciales SOL.",
        )


@router.post("/manual/generar-tickets/{ruc}")
def generar_tickets_manual(
    ruc: str,
    tipo: str,
    #orq_ventas: OrquestadorTickets = Depends(dp_orquestador_tickets_ventas),
    orq_compras: OrquestadorTickets = Depends(dp_orquestador_tickets_compras),
    repo: GetOnlyEnrolado = Depends(dp_get_only_enrolado),
):
    enrolado = repo.execute(ruc=ruc)
    if not enrolado:
        raise HTTPException(status_code=404, detail="RUC no enrolado")

    #orquestador = orq_ventas if tipo == "ventas" else orq_compras
    orquestador = orq_compras
    resultado = orquestador.execute(
        ruc=enrolado["ruc"],
        usuario_sol=enrolado["usuario_sol"],
        clave_sol=enrolado["clave_sol"],
        client_id=enrolado["client_id"],
        client_secret=enrolado["client_secret"],
        periodos=generar_periodos(13),
    )
    return {
        "status": "success",
        "tipo": tipo,
        "detalle": resultado.get("resultados", {}),
    }


@router.post("/manual/descargar/{ruc}")
def descargar_manual(
    ruc: str,
    tipo: str,
    #orq_ventas: OrquestadorDescargas = Depends(dp_orquestador_descargas_ventas),
    orq_compras: OrquestadorDescargas = Depends(dp_orquestador_descargas_compras),
    repo: GetOnlyEnrolado = Depends(dp_get_only_enrolado),
):
    enrolado = repo.execute(ruc=ruc)
    if not enrolado:
        raise HTTPException(status_code=404, detail="RUC no enrolado")

    #orquestador = orq_ventas if tipo == "ventas" else orq_compras
    orquestador = orq_compras
    resultado = orquestador.execute(
        ruc=enrolado["ruc"],
        usuario_sol=enrolado["usuario_sol"],
        clave_sol=enrolado["clave_sol"],
        client_id=enrolado["client_id"],
        client_secret=enrolado["client_secret"],
        periodos=generar_periodos(13),
    )
    return {
        "status": "success",
        "tipo": tipo,
        "detalle": resultado.get("resultados", {}),
    }


@router.post("/generar-tickets-automaticos")
def procesar_tickets_automatico(
    orq_ventas: OrquestadorTickets = Depends(dp_orquestador_tickets_ventas),
    orq_compras: OrquestadorTickets = Depends(dp_orquestador_tickets_compras),
    repo: GetEnrolado = Depends(dp_get_enrolado),
):
    enrolados = repo.execute()
    periodos = generar_periodos(1)
    resultados_lote = []

    for emp in enrolados:
        cred = {
            "ruc": emp["ruc"],
            "usuario_sol": emp["usuario_sol"],
            "clave_sol": emp["clave_sol"],
            "client_id": emp["client_id"],
            "client_secret": emp["client_secret"],
            "periodos": periodos,
        }
        #res_ventas = orq_ventas.execute(**cred)
        res_compras = orq_compras.execute(**cred)

        resultados_lote.append(
            {
                "ruc": emp["ruc"],
                #"tickets_ventas": res_ventas.get("resultados"),
                "tickets_compras": res_compras.get("resultados"),
            }
        )

    return {"status": "success", "resultados": resultados_lote}


@router.get("/descargar-archivos")
def descargar_archivos_automatico(
    #orq_ventas: OrquestadorDescargas = Depends(dp_orquestador_descargas_ventas),
    orq_compras: OrquestadorDescargas = Depends(dp_orquestador_descargas_compras),
    repo: GetEnrolado = Depends(dp_get_enrolado),
):
    enrolados = repo.execute()
    periodos = generar_periodos(1)
    resultados_lote = []

    for emp in enrolados:
        cred = {
            "ruc": emp["ruc"],
            "usuario_sol": emp["usuario_sol"],
            "clave_sol": emp["clave_sol"],
            "client_id": emp["client_id"],
            "client_secret": emp["client_secret"],
            "periodos": periodos,
        }
        #res_ventas = orq_ventas.execute(**cred)
        res_compras = orq_compras.execute(**cred)

        resultados_lote.append(
            {
                "ruc": emp["ruc"],
                #"descarga_ventas": res_ventas.get("resultados"),
                "descarga_compras": res_compras.get("resultados"),
            }
        )

    return {"status": "success", "resultados": resultados_lote}
