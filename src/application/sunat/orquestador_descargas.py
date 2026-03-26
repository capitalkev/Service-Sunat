from src.application.sunat.get_token_api import GetTokenAPI
from src.application.sunat.get_token_scraping import GetTokenScraping
from src.infrastructure.api_sunat.get_sunat import APISUNAT
from src.infrastructure.playwright_sunat.scraper import PlaywrightTokenScraper


class OrquestadorDescargas:
    def __init__(
        self
    ):
        self.token_api = GetTokenAPI(APISUNAT())
        self.token_scraper = GetTokenScraping(PlaywrightTokenScraper())

    def execute(
        self, ruc, usuario_sol, clave_sol, client_id, client_secret, periodos: list
    ):

        resultados = {}

        def obtener_token():
            try:
                print(f"[{ruc}] 1. Intentando obtener Token vía API...")
                token1 = self.token_api.execute(
                    ruc, usuario_sol, clave_sol, client_id, client_secret
                )
                if token1:
                    return token1
            except Exception:
                print(f"[{ruc}] Falló Token API. Intentando Playwright...")

            try:
                print(f"[{ruc}] 2. Intentando obtener Token vía Playwright...")
                token2 = self.token_scraper.execute(
                    ruc, usuario_sol, clave_sol
                )
                if token2:
                    return token2
            except Exception:
                print(f"[{ruc}] Fallo Crítico en Playwright.")
                return None
            
        token_acceso = obtener_token()
        
        resultados["ruc"] = ruc
        resultados["token"] = token_acceso
        

        """
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
            if self.etl.repository.existe_periodo(ruc, periodo):
                print(f"[{ruc}] Periodo {periodo} ya está en BD. Saltando solicitud...")
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
                    print(f"[{ruc}] Solicitando ticket para periodo {periodo} desde SUNAT...")
                    
                    numero_ticket = self.api.sunat.solicitar_descarga(
                        periodo=periodo, token_acceso=token_acceso
                    )

                    self.tickets_repo.guardar_ticket(numero_ticket, ruc, periodo)

                    resultados.append(
                        {
                            "periodo": periodo, 
                            "status": "PENDIENTE", 
                            "ticket": numero_ticket,
                            "mensaje": "Ticket generado y encolado para descarga asíncrona."
                        }
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
        """

        return {"resultados": resultados}
