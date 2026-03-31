from src.application.sunat.get_token_api import GetTokenAPI
from src.application.sunat.get_token_scraping import GetTokenScraping
from src.application.sunat.get_ticket import GetTicket
from src.domain.interfaces import APIClientInterface
from src.application.etl.procesar_ventas import ProcesarVentasETL
from src.infrastructure.postgresql.repositories_sunat.ventas import VentasRepository
from typing import Any
import os


class OrquestadorDescargas:
    def __init__(
        self,
        token_api: GetTokenAPI,
        token_scraper: GetTokenScraping,
        get_ticket: GetTicket,
        sunat_api: APIClientInterface,
        etl_ventas: ProcesarVentasETL,
        ventas_repo: VentasRepository,
    ):
        self.token_api = token_api
        self.token_scraper = token_scraper
        self.get_ticket = get_ticket
        self.sunat_api = sunat_api
        self.etl_ventas = etl_ventas
        self.ventas_repo = ventas_repo

    def execute(
        self, ruc, usuario_sol, clave_sol, client_id, client_secret, periodos: list
    ):
        resultados: dict[str, dict[str, Any]] = {}

        def obtener_token():
            try:
                print(f"[{ruc}] 1. Intentando Token API...")
                token1 = self.token_api.execute(
                    ruc, usuario_sol, clave_sol, client_id, client_secret
                )
                if token1:
                    return token1
            except Exception:
                print(f"[{ruc}] Falló Token API. Intentando Playwright...")

            try:
                print(f"[{ruc}] 2. Intentando Token Playwright...")
                token2 = self.token_scraper.execute(ruc, usuario_sol, clave_sol)
                if token2:
                    return token2
            except Exception:
                print(f"[{ruc}] Fallo Crítico en Playwright.")
                return None

        token_acceso = obtener_token()

        for periodo in periodos:
            if self.ventas_repo.existe_periodo(ruc, periodo):
                print(
                    f"[{ruc}] El periodo {periodo} ya existe en BD. Omitiendo descarga."
                )
                resultados[periodo] = {"estado": "YA_EXISTE_EN_BD"}
                continue

            numero_ticket = self.get_ticket.execute(ruc, periodo)

            if not numero_ticket:
                resultados[periodo] = {"estado": "TICKET_NO_ENCONTRADO"}
                continue

            try:
                estado_info = self.sunat_api.verificar_estado(
                    numero_ticket, token_acceso, periodo
                )
                estado_codigo = estado_info.get("estado")

                if estado_codigo == "06":
                    datos_archivo = estado_info.get("datos_archivo")

                    archivo_csv_en_memoria = self.sunat_api.descargar_archivo(
                        datos_archivo, token_acceso, periodo, numero_ticket, ruc
                    )

                    print(
                        f"[{ruc}] Procesando CSV con ETL para el periodo {periodo}..."
                    )
                    resultado_etl = self.etl_ventas.execute(archivo_csv_en_memoria)
                    df_limpio = resultado_etl.get("df_limpio")

                    registros_guardados = 0
                    if df_limpio is not None and not df_limpio.empty:
                        registros_guardados = self.ventas_repo.guardar_lote_ventas(
                            df_limpio, ruc
                        )
                        print(
                            f"[{ruc}] {registros_guardados} registros guardados exitosamente en BD."
                        )

                    resultados[periodo] = {
                        "ticket": numero_ticket,
                        "estado": "PROCESADO_Y_GUARDADO",
                        "procesados_ok": resultado_etl.get("procesados_ok"),
                    }
                else:
                    resultados[periodo] = {
                        "ticket": numero_ticket,
                        "estado": "PROCESADO_Y_GUARDADO",
                        "procesados_ok": resultado_etl.get("procesados_ok"),
                    }

            except Exception as e:
                print(f"[{ruc}] Error al procesar ticket {numero_ticket} (Periodo: {periodo}): {e}")
                
                if archivo_csv_en_memoria is not None:
                    # Crear carpeta si no existe
                    os.makedirs("csv_errores_sunat", exist_ok=True)
                    ruta_guardado = f"csv_errores_sunat/error_{ruc}_{periodo}.csv"
                    
                    archivo_csv_en_memoria.seek(0)
                    
                    # Escribimos los bytes físicos al disco duro
                    with open(ruta_guardado, "wb") as f:
                        f.write(archivo_csv_en_memoria.read())
                        
                    print(f"[{ruc}] Archivo problemático guardado localmente en '{ruta_guardado}' para tu análisis!")

                resultados[periodo] = {"estado": "ERROR_PROCESO", "error": str(e)}

        return {"ruc": ruc, "resultados": resultados}
