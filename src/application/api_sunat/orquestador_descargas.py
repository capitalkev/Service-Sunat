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

        try:
            token_acceso = self.api.sunat.get_token(
                ruc, usuario_sol, clave_sol, client_id, client_secret
            )
        except Exception as e:
            print(f"[{ruc}] Falló la generación de Token API: {e}")

        if not token_acceso:
            print(f"[{ruc}] Obteniendo Token vía Playwright...")
            try:
                token_acceso = self.token_scraper.obtener_token_bearer(
                    ruc, usuario_sol, clave_sol
                )
            except Exception as e:
                return {
                    "detalle": [
                        {"ruc": ruc, "status": "error", "mensaje": f"Sin token: {e}"}
                    ]
                }

        for periodo in periodos:
            res_api = self.api.execute(periodo=periodo, token_acceso=token_acceso)
            resultados.append(
                {"periodo": periodo, "status": "success", "data": res_api}
            )

        return {"detalle": resultados}
