import io
import pandas as pd
import numpy as np
from src.infrastructure.postgresql.repositories_sunat.ventas import VentasRepository


class ProcesarVentasETL:
    def __init__(self, repository: VentasRepository):
        self.repository = repository

    def execute(self, csv_file_obj: io.BytesIO) -> dict:

        # 1. Leer como texto atrapando comas rotas
        df = pd.read_csv(
            csv_file_obj,
            encoding="utf-8",
            engine="python",
            on_bad_lines="skip",
            dtype=str,
        )

        # 2. Reglas de Negocio
        ruc_str = df["Ruc"].str.strip()
        mask_ruc_malo = ~(ruc_str.str.isnumeric() & (ruc_str.str.len() == 11))

        periodo_str = df["Periodo"].str.strip()
        mes_valido = periodo_str.str[-2:].apply(
            lambda x: str(x).isdigit() and 1 <= int(str(x)) <= 12
        )
        mask_periodo_malo = ~(
            (periodo_str.str.len() == 6) & periodo_str.str.startswith("20") & mes_valido
        )

        fechas_convertidas = pd.to_datetime(
            df["Fecha de emisión"], format="%d/%m/%Y", errors="coerce"
        )
        mask_fecha_mala = fechas_convertidas.isna()

        mask_filas_malas = mask_ruc_malo | mask_periodo_malo | mask_fecha_mala

        df_limpio = df[~mask_filas_malas].copy()

        if not df_limpio.empty:
            columnas_inutiles = [
                "CAR SUNAT",
                "Nro Final (Rango)",
                "Tipo Doc Identidad",
                "Valor Facturado Exportación",
                "BI Gravada",
                "Dscto BI",
                "IGV / IPM",
                "Dscto IGV / IPM",
                "Mto Exonerado",
                "Mto Inafecto",
                "ISC",
                "BI Grav IVAP",
                "IVAP",
                "ICBPER",
                "Otros Tributos",
                "Fecha Emisión Doc Modificado",
                "Tipo CP Modificado",
                "ID Proyecto Operadores Atribución",
                "Tipo de Nota",
                "Est. Comp",
                "Valor FOB Embarcado",
                "Valor OP Gratuitas",
                "Tipo Operación",
                "DAM / CP",
                "CLU",
            ]
            df_limpio = df_limpio.drop(
                columns=[col for col in columnas_inutiles if col in df_limpio.columns]
            )

            mapeo_columnas = {
                "Ruc": "ruc",
                "Razon Social": "razon_social",
                "Periodo": "periodo",
                "Fecha de emisión": "fecha_emision",
                "Fecha Vcto/Pago": "fecha_vcto_pago",
                "Tipo CP/Doc.": "tipo_cp_doc",
                "Serie del CDP": "serie_cdp",
                "Nro CP o Doc. Nro Inicial (Rango)": "nro_cp_doc",
                "Nro Doc Identidad": "nro_doc_identidad",
                "Apellidos Nombres/ Razón Social": "cliente_razon_social",
                "Total CP": "total_cp",
                "Moneda": "moneda",
                "Tipo Cambio": "tipo_cambio",
                "Serie CP Modificado": "serie_cp_modificado",
                "Nro CP Modificado": "nro_cp_modificado",
            }
            df_limpio = df_limpio.rename(columns=mapeo_columnas)

            # Formatear numéricos
            columnas_numericas = ["total_cp", "tipo_cambio"]
            for col in columnas_numericas:
                if col in df_limpio.columns:
                    df_limpio[col] = pd.to_numeric(
                        df_limpio[col], errors="coerce"
                    ).fillna(0.0)

            # Formatear fechas
            columnas_fecha = [
                "fecha_emision",
                "fecha_vcto_pago",
                "fecha_emision_doc_modificado",
            ]
            for col in columnas_fecha:
                if col in df_limpio.columns:
                    df_limpio[col] = pd.to_datetime(
                        df_limpio[col], format="%d/%m/%Y", errors="coerce"
                    )

            # Convertir NaNs a Nones para PostgreSQL
            df_limpio = df_limpio.replace({np.nan: None, pd.NaT: None})

        return {
            "procesados_ok": len(df_limpio) if not df_limpio.empty else 0,
            "df_limpio": df_limpio,
        }
