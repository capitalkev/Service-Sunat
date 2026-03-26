# src/infrastructure/postgresql/repositories_sunat/tickets.py
from sqlalchemy import text
from sqlalchemy.orm import Session

class TicketsRepository:
    def __init__(self, db: Session):
        self.db = db

    def guardar_ticket(self, ticket: str, ruc: str, periodo: str) -> None:
        query = text("""
            INSERT INTO tickets_sunat (ticket, ruc, periodo, estado) 
            VALUES (:ticket, :ruc, :per, 'PENDIENTE')
            ON CONFLICT (ticket) DO NOTHING
        """)
        self.db.execute(query, {"ticket": ticket, "ruc": ruc, "per": periodo})
        self.db.commit()

    def obtener_tickets_pendientes(self, limite: int = 50) -> list[dict]:
        """Obtiene tickets pendientes junto con las credenciales del cliente."""
        query = text("""
            SELECT t.ticket, t.ruc, t.periodo, 
                   e.usuario_sol, e.clave_sol, e.client_id, e.client_secret
            FROM tickets_sunat t
            JOIN enrolados e ON t.ruc = e.ruc
            WHERE t.estado = 'PENDIENTE'
            LIMIT :limite
        """)
        result = self.db.execute(query, {"limite": limite})
        return [dict(row) for row in result.mappings()]

    def actualizar_estado(self, ticket: str, estado: str, mensaje: str = None) -> None:
        query = text("""
            UPDATE tickets_sunat 
            SET estado = :estado, mensaje = :mensaje 
            WHERE ticket = :ticket
        """)
        self.db.execute(query, {"estado": estado, "mensaje": mensaje, "ticket": ticket})
        self.db.commit()