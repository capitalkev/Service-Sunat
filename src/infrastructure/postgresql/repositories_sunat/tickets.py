from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
from src.domain.interfaces import TicketsInterface


class TicketsRepository(TicketsInterface):
    def __init__(self, db: Session):
        self.db = db

    def guardar_ticket(self, ticket: str, ruc: str, periodo: str) -> None:
        try:
            query = text(
                """
                INSERT INTO tickets_sunat (ticket, ruc, periodo, estado) 
                VALUES (:ticket, :ruc, :per, 'PENDIENTE')
            """
            )
            self.db.execute(query, {"ticket": ticket, "ruc": ruc, "per": periodo})
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"Error real al guardar en BD: {e}")
            raise e

    # verificar que no se repita el periodo y ruc
    def traer_ticket(self, ruc: str, periodo: str) -> Optional[str]:
        query = text(
            """
            SELECT ticket FROM tickets_sunat 
            WHERE ruc = :ruc AND periodo = :per
            """
        )
        result = self.db.execute(query, {"ruc": ruc, "per": periodo})

        return result.scalar()
