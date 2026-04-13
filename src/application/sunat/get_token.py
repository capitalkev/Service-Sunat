from src.application.sunat.get_token_api import GetTokenAPI
from src.application.sunat.get_token_scraping import GetTokenScraping


class GetToken:
    def __init__(
        self,
        token_api: GetTokenAPI,
        token_scraper: GetTokenScraping,
    ):
        self.token_api = token_api
        self.token_scraper = token_scraper

    def execute(self, ruc, usuario_sol, clave_sol, client_id, client_secret):
        try:
            print(f"[{ruc}] 1. Intentando Token API...")
            token1 = self.token_api.execute(
                ruc, usuario_sol, clave_sol, client_id, client_secret
            )
            if token1:
                return token1
        except Exception:
            print(f"[{ruc}] Falló Token API. Intentando Playwright...")

        try:
            print(f"[{ruc}] 2. Intentando Token Playwright...")
            token2 = self.token_scraper.execute(ruc, usuario_sol, clave_sol)
            if token2:
                return token2
        except ValueError as ve:
            print(f"[{ruc}] Validación fallida: {ve}")
            raise ve
            
        except Exception as e:
            print(f"[{ruc}] Fallo Crítico en Playwright: {e}")
            return None
    
    def nuevo_execute(self, ruc, usuario_sol, clave_sol):
        try:
            print(f"[{ruc}] Intentando Token Playwright...")
            token2 = self.token_scraper.execute(ruc, usuario_sol, clave_sol)
            if token2:
                return token2
        except ValueError:
            print(f"[{ruc}] Validación fallida: ")
            return None
            
        except Exception:
            print(f"[{ruc}] Fallo Crítico en Playwright:")
            return None