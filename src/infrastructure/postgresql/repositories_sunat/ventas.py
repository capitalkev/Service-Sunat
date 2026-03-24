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
        query = text(
            """
            SELECT 1 FROM ventas_sunat 
            WHERE ruc_cliente = :ruc AND periodo_tributario = :per 
            LIMIT 1
        """
        )
        resultado = self.db.execute(query, {"ruc": ruc, "per": periodo}).fetchone()
        return resultado is not None

    def guardar_lote_ventas(self, df_limpio: pd.DataFrame, ruc: str, periodo: str) -> int:
        if df_limpio.empty:
            return 0

        tabla_temp = f"temp_ventas_{ruc}_{periodo}"

        try:
            conexion = self.db.connection()
            
            df_limpio.to_sql(
                name=tabla_temp, con=conexion, if_exists='replace', index=False, chunksize=1000
            )
            
            query_upsert = text(f"""
                INSERT INTO ventas_sunat (
                    ruc, razon_social, periodo, fecha_emision, fecha_vcto_pago, 
                    tipo_cp_doc, serie_cdp, nro_cp_doc, nro_doc_identidad, 
                    cliente_razon_social, total_cp, moneda, tipo_cambio, ruc_cliente, periodo_tributario
                )
                SELECT 
                    ruc, razon_social, periodo, fecha_emision, fecha_vcto_pago, 
                    tipo_cp_doc, serie_cdp, nro_cp_doc, nro_doc_identidad, 
                    cliente_razon_social, total_cp, moneda, tipo_cambio, :ruc_cliente, :periodo
                FROM {tabla_temp}
                ON CONFLICT (ruc_cliente, tipo_cp_doc, serie_cdp, nro_cp_doc) 
                DO NOTHING;
            """)
            
            self.db.execute(query_upsert, {"ruc_cliente": ruc, "periodo": periodo})

            self.db.execute(text(f"DROP TABLE {tabla_temp};"))
            
            self.db.commit()

        except Exception as e:
            self.db.rollback()
            raise e
            
        return len(df_limpio)
