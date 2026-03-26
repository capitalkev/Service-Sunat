from src.domain.interfaces import TokenScraperInterface


class GetTokenScraping:
    def __init__(self, sunat_scraper: TokenScraperInterface):
        self.sunat_scraping = sunat_scraper

    def execute(self, ruc, usuario_sol, clave_sol):
        token = self.sunat_scraping.obtener_token_bearer(ruc, usuario_sol, clave_sol)
        
        return token
