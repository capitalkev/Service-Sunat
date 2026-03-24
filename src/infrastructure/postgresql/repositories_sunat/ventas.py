# src/infrastructure/postgresql/repositories_sunat/ventas.py

from sqlalchemy import text
from sqlalchemy.orm import Session
import pandas as pd

class VentasRepository:
    def __init__(self, db: Session):
        self.db = db
        self.engine = db.get_bind()

    def existe_periodo(self, ruc: str, periodo: str) -> bool:
        """Verifica si ya existen ventas para este cliente y periodo en la BD."""
        query = text("""
            SELECT 1 FROM ventas_sunat 
            WHERE ruc_cliente = :ruc AND periodo_tributario = :per 
            LIMIT 1
        """)
        resultado = self.db.execute(query, {"ruc": ruc, "per": periodo}).fetchone()
        return resultado is not None

    def guardar_lote_ventas(self, df_limpio: pd.DataFrame, ruc: str, periodo: str) -> int:
        if df_limpio.empty:
            return 0

        with self.engine.begin() as conn:
            query_borrar = text("""
                DELETE FROM ventas_sunat 
                WHERE ruc_cliente = :ruc AND periodo_tributario = :per
            """)
            conn.execute(query_borrar, {"ruc": ruc, "per": periodo})
            
            df_limpio.to_sql(
                name='ventas_sunat', con=conn, if_exists='append', index=False, chunksize=1000
            )
        return len(df_limpio)