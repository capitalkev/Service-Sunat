from src.domain.interfaces import TicketsInterface


class SaveTicket:
    def __init__(self, save_ticket: TicketsInterface):
        self.save_ticket = save_ticket

    def execute(self, ruc, periodo, ticket, tipo_registro="ventas"):
        return self.save_ticket.guardar_ticket(ticket, ruc, periodo, tipo_registro)
