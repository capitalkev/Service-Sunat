from src.domain.interfaces import APIClientInterface


class GetTicketAPI:
    def __init__(self, sunat_client: APIClientInterface):
        self.sunat = sunat_client

    def execute(self, periodo, token_acceso):
        resultados = {}
        for p in periodo:
            ticket = self.sunat.generar_ticket(p, token_acceso)
            resultados[p] = ticket

        return resultados
