# src/application/api_sunat/orquestador_descargas.py

from datetime import datetime
from src.application.api_sunat.get_sunat import APIService
from src.domain.interfaces import TokenScraperInterface
from src.application.etl.procesar_ventas import ProcesarVentasETL


class OrquestadorDescargas:
    def __init__(
        self,
        api_service: APIService,
        token_scraper: TokenScraperInterface,
        etl_service: ProcesarVentasETL,
    ):
        self.api = api_service
        self.token_scraper = token_scraper
        self.etl = etl_service

    def execute(
        self, ruc, usuario_sol, clave_sol, client_id, client_secret, periodos: list
    ):
        resultados = []

        periodo_actual = datetime.now().strftime("%Y%m")

        def obtener_token():
            try:
                token = self.api.sunat.get_token(
                    ruc, usuario_sol, clave_sol, client_id, client_secret
                )
                if token:
                    return token
            except Exception:
                print(f"[{ruc}] Falló Token API. Intentando Playwright...")

            try:
                return self.token_scraper.obtener_token_bearer(
                    ruc, usuario_sol.upper(), clave_sol
                )
            except Exception:
                print(f"[{ruc}] Fallo Crítico en Playwright.")
                return None

        token_acceso = obtener_token()
        if not token_acceso:
            return {
                "valido": False,
                "detalle": [
                    {
                        "periodo": p,
                        "status": "error",
                        "mensaje": "Credenciales inválidas.",
                    }
                    for p in periodos
                ],
            }

        for periodo in periodos:
            if periodo != periodo_actual and self.etl.repository.existe_periodo(
                ruc, periodo
            ):
                print(f"[{ruc}] Periodo {periodo} ya está en BD. Saltando descarga...")
                resultados.append(
                    {
                        "periodo": periodo,
                        "status": "success",
                        "mensaje": "Ya existe en BD, omitido.",
                    }
                )
                continue

            reintentos = 0

            while reintentos < 2:
                try:
                    print(f"[{ruc}] Descargando periodo {periodo} desde SUNAT...")
                    res_api = self.api.execute(
                        periodo=periodo, token_acceso=token_acceso, ruc=ruc
                    )

                    # Usamos ÚNICAMENTE la versión en memoria para Cloud Run
                    if "archivo_memoria" in res_api:
                        res_etl = self.etl.execute(
                            res_api["archivo_memoria"], ruc, periodo
                        )

                        # 1. Guardamos las estadísticas del ETL en la respuesta
                        res_api["etl_stats"] = res_etl

                        # 2. Cerramos y eliminamos el buffer para liberar RAM y permitir JSON serialization
                        res_api["archivo_memoria"].close()
                        del res_api["archivo_memoria"]

                    resultados.append(
                        {"periodo": periodo, "status": "success", "data": res_api}
                    )
                    break

                except Exception as e:
                    error_msg = str(e)
                    if "401" in error_msg or "Unauthorized" in error_msg:
                        token_acceso = obtener_token()
                        if not token_acceso:
                            break
                        reintentos += 1
                    else:
                        resultados.append(
                            {
                                "periodo": periodo,
                                "status": "error",
                                "mensaje": error_msg,
                            }
                        )
                        break

        return {"valido": True, "detalle": resultados}
