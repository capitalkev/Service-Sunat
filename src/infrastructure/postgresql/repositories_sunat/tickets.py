from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
from src.domain.interfaces import TicketsInterface

class TicketsRepository(TicketsInterface):
    def __init__(self, db: Session):
        self.db = db

    def guardar_ticket(self, ticket: str, ruc: str, periodo: str, tipo_registro: str = "ventas") -> None:
        try:
            query = text(
                """
                INSERT INTO tickets_sunat (ticket, ruc, periodo, estado, tipo_registro) 
                VALUES (:ticket, :ruc, :per, 'PENDIENTE', :tipo)
                """
            )
            self.db.execute(query, {"ticket": ticket, "ruc": ruc, "per": periodo, "tipo": tipo_registro})
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e

    def traer_ticket(self, ruc: str, periodo: str, tipo_registro: str = "ventas") -> Optional[str]:
        query = text(
            """
            SELECT ticket FROM tickets_sunat 
            WHERE ruc = :ruc AND periodo = :per AND tipo_registro = :tipo
            ORDER BY id DESC LIMIT 1
            """
        )
        result = self.db.execute(query, {"ruc": ruc, "per": periodo, "tipo": tipo_registro})
        return result.scalar()
