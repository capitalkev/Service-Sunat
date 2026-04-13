import io
import pandas as pd
import numpy as np


class ProcesarComprasETL:
    def execute(self, csv_file_obj: io.BytesIO) -> dict:
        df = pd.read_csv(
            csv_file_obj,
            encoding="utf-8",
            engine="python",
            on_bad_lines="skip",
            dtype=str,
        )

        if df.empty:
            return {"procesados_ok": 0, "df_limpio": df}

        # Las 13 columnas exactas que pediste
        columnas_filtro = [
            "RUC",
            "Apellidos y Nombres o Razón social",
            "Periodo",
            "Fecha de emisión",
            "Fecha Vcto/Pago",
            "Tipo CP/Doc.",
            "Serie del CDP",
            "Nro CP o Doc. Nro Inicial (Rango)",
            "Tipo Doc Identidad",
            "Nro Doc Identidad",
            "Apellidos Nombres/ Razón  Social",
            "Moneda",
            "Tipo de Cambio",
        ]

        # Filtrar solo si existen (evita errores por variaciones de SUNAT)
        df_limpio = df[[c for c in columnas_filtro if c in df.columns]].copy()

        # Mapeo a nombres estándar para tu BD (snake_case)
        mapeo = {
            "RUC": "ruc",
            "Apellidos y Nombres o Razón social": "razon_social",
            "Periodo": "periodo",
            "Fecha de emisión": "fecha_emision",
            "Fecha Vcto/Pago": "fecha_vcto_pago",
            "Tipo CP/Doc.": "tipo_cp_doc",
            "Serie del CDP": "serie_cdp",
            "Nro CP o Doc. Nro Inicial (Rango)": "nro_cp_doc",
            "Tipo Doc Identidad": "tipo_doc_id_proveedor",
            "Nro Doc Identidad": "nro_doc_id_proveedor",
            "Apellidos Nombres/ Razón  Social": "nombre_proveedor",
            "Moneda": "moneda",
            "Tipo de Cambio": "tipo_cambio",
        }
        df_limpio = df_limpio.rename(columns=mapeo)

        # Formateo de datos
        if "tipo_cambio" in df_limpio.columns:
            df_limpio["tipo_cambio"] = pd.to_numeric(
                df_limpio["tipo_cambio"], errors="coerce"
            ).fillna(0.0)

        for col in ["fecha_emision", "fecha_vcto_pago"]:
            if col in df_limpio.columns:
                df_limpio[col] = pd.to_datetime(
                    df_limpio[col], format="%d/%m/%Y", errors="coerce"
                )

        return {
            "procesados_ok": len(df_limpio),
            "df_limpio": df_limpio.replace({np.nan: None, pd.NaT: None}),
        }
