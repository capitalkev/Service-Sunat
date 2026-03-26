from src.domain.interfaces import VentasSunatInterface


class SaveTicket:
    def __init__(self, save_ticket: VentasSunatInterface):
        self.save_ticket = save_ticket

    def execute(self, ruc, periodo, ticket):
        return self.save_ticket.save_ticket(ruc, periodo, ticket)
