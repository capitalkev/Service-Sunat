from src.domain.interfaces import TicketsInterface


class GetTicket:
    def __init__(self, ticket: TicketsInterface):
        self.ticket = ticket

    def execute(self, ruc, periodo):
        resultados = {}
        for p in periodo:
            numero_ticket = self.ticket.traer_ticket(ruc, p)
            resultados[p] = numero_ticket

        return resultados
