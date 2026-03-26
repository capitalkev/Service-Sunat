from src.application.sunat.get_ticket import GetTicketAPI
from src.application.sunat.get_token_api import GetTokenAPI
from src.application.sunat.get_token_scraping import GetTokenScraping
from src.application.sunat.save_ticket import SaveTicket
from src.infrastructure.api_sunat.get_sunat import APISUNAT
from src.infrastructure.playwright_sunat.scraper import PlaywrightTokenScraper


class OrquestadorDescargas:
    def __init__(self, guardar_ticket: SaveTicket):
        self.token_api = GetTokenAPI(APISUNAT())
        self.token_scraper = GetTokenScraping(PlaywrightTokenScraper())
        self.generar_ticket = GetTicketAPI(APISUNAT())
        self.guardar_ticket = guardar_ticket

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
                token2 = self.token_scraper.execute(ruc, usuario_sol, clave_sol)
                if token2:
                    return token2
            except Exception:
                print(f"[{ruc}] Fallo Crítico en Playwright.")
                return None

        token_acceso = obtener_token()

        tickets = self.generar_ticket.execute(periodos, token_acceso)

        resultados["ruc"] = ruc
        resultados["tickets"] = tickets

        return {"resultados": resultados}
