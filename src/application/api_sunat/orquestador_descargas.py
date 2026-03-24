from src.application.api_sunat.get_sunat import APIService
from src.domain.interfaces import TokenScraperInterface


class OrquestadorDescargas:
    def __init__(
        self,
        api_service: APIService,
        token_scraper: TokenScraperInterface,
    ):
        self.api = api_service
        self.token_scraper = token_scraper

    def execute(
        self,
        ruc,
        usuario_sol,
        clave_sol,
        client_id,
        client_secret,
        periodos: list,
    ):
        resultados = []
        token_acceso = None
        playwright_usado = False

        # 1. Intentamos generar token por API primero (Es mucho más rápido que abrir Playwright)
        try:
            token_acceso = self.api.sunat.get_token(
                ruc, usuario_sol, clave_sol, client_id, client_secret
            )
            if token_acceso:
                print(f"[{ruc}] Token obtenido por API exitosamente.")
        except Exception as e:
            print(f"[{ruc}] Falló la generación de Token API: {e}")

        # 2. Procesamiento de los periodos
        for periodo in periodos:
            reintento_por_401 = False

            while True:
                if not token_acceso:
                    if playwright_usado:
                        resultados.append(
                            {
                                "periodo": periodo,
                                "status": "error",
                                "mensaje": "Token de Playwright también fue rechazado.",
                            }
                        )
                        break

                    try:
                        print(f"[{ruc}] Obteniendo Token vía Playwright...")
                        token_acceso = self.token_scraper.obtener_token_bearer(
                            ruc, usuario_sol.upper(), clave_sol
                        )
                        playwright_usado = True
                    except Exception as e:
                        idx_actual = periodos.index(periodo)
                        for p in periodos[idx_actual:]:
                            resultados.append(
                                {
                                    "periodo": p,
                                    "status": "error",
                                    "mensaje": f"Fallo inicio Playwright: {e}",
                                }
                            )
                        return {"detalle": resultados}

                try:
                    res_api = self.api.execute(
                        periodo=periodo, token_acceso=token_acceso
                    )
                    resultados.append(
                        {"periodo": periodo, "status": "success", "data": res_api}
                    )

                except Exception as e:
                    error_msg = str(e)

                    if (
                        ("401" in error_msg or "Unauthorized" in error_msg)
                        and not reintento_por_401
                        and not playwright_usado
                    ):
                        print(
                            f"[{ruc}] Token API dio error 401 en periodo {periodo}. Refrescando con Playwright..."
                        )
                        token_acceso = None
                        reintento_por_401 = True
                        continue
                    else:
                        resultados.append(
                            {
                                "periodo": periodo,
                                "status": "error",
                                "mensaje": error_msg,
                            }
                        )
                    break
        return {"detalle": resultados}
