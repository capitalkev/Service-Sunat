from src.domain.interfaces import APIClientInterface


class APIService:
    def __init__(self, repository: APIClientInterface):
        self.sunat = repository

    def execute(self, periodo: str, token_acceso: str, ruc: str):
        numero_ticket = self.sunat.solicitar_descarga(periodo, token_acceso)
        datos_archivo = self.sunat.verificar_estado(
            numero_ticket, token_acceso, periodo
        )

        if datos_archivo and isinstance(datos_archivo, dict):
            archivo_memoria = self.sunat.descargar_archivo(
                datos_archivo, token_acceso, periodo, numero_ticket, ruc
            )

            return {
                "mensaje": "Archivo descargado y extraído exitosamente",
                "ticket": numero_ticket,
                "archivo_memoria": archivo_memoria,
            }
