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
            WHERE ruc = :ruc AND periodo = :per 
            LIMIT 1
        """
        )
        resultado = self.db.execute(query, {"ruc": ruc, "per": periodo}).fetchone()
        return resultado is not None

    def guardar_lote_ventas(
        self, df_limpio: pd.DataFrame, ruc: str
    ) -> int:
        if df_limpio.empty:
            return 0

        tabla_temp = f"temp_ventas_{ruc}"

        with self.engine.begin() as conn:
            # 1. Subimos la data temporal consolidada
            df_limpio.to_sql(
                name=tabla_temp,
                con=conn,
                if_exists="replace",
                index=False,
                chunksize=4000,
                method='multi'  
            )

            # 2. UPSERT a la tabla real (Añadiendo CAST a las fechas y números)
            query_upsert = text(
                f"""
                INSERT INTO ventas_sunat (
                    ruc, razon_social, periodo, fecha_emision, fecha_vcto_pago, 
                    tipo_cp_doc, serie_cdp, nro_cp_doc, nro_doc_identidad, 
                    cliente_razon_social, total_cp, moneda, tipo_cambio, 
                    serie_cp_modificado, nro_cp_modificado
                )
                SELECT 
                    ruc, 
                    razon_social, 
                    periodo, 
                    CAST(fecha_emision AS DATE), 
                    CAST(fecha_vcto_pago AS DATE), 
                    tipo_cp_doc, 
                    serie_cdp, 
                    nro_cp_doc, 
                    nro_doc_identidad, 
                    cliente_razon_social, 
                    CAST(total_cp AS NUMERIC), 
                    moneda, 
                    CAST(tipo_cambio AS NUMERIC), 
                    serie_cp_modificado, 
                    nro_cp_modificado
                FROM {tabla_temp}
                ON CONFLICT (ruc, tipo_cp_doc, serie_cdp, nro_cp_doc) 
                DO NOTHING;
            """
            )

            conn.execute(query_upsert)
            conn.execute(text(f"DROP TABLE {tabla_temp};"))

        return len(df_limpio)
