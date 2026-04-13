from src.application.sunat.get_ticket import GetTicket
from src.application.sunat.get_token import GetToken
from src.domain.interfaces import (
    APIClientInterface,
    ProcesarRegistroETLInterface,
    RegistroRepositoryInterface,
)
from typing import Any


class OrquestadorDescargas:
    def __init__(
        self,
        get_ticket: GetTicket,
        get_token: GetToken,
        sunat_api: APIClientInterface,
        etl_registro: ProcesarRegistroETLInterface,  # Usa la Interfaz
        registro_repo: RegistroRepositoryInterface,  # Usa la Interfaz
        tipo_registro: str = "ventas",  # Bandera ("ventas" o "compras")
    ):
        self.get_ticket = get_ticket
        self.get_token = get_token
        self.sunat_api = sunat_api
        self.etl_registro = etl_registro
        self.registro_repo = registro_repo
        self.tipo_registro = tipo_registro

    def execute(
        self, ruc, usuario_sol, clave_sol, client_id, client_secret, periodos: list
    ):
        resultados: dict[str, dict[str, Any]] = {}

        token_acceso = self.get_token.execute(
            ruc, usuario_sol, clave_sol, client_id, client_secret
        )

        for periodo in periodos:
            if self.registro_repo.existe_periodo(ruc, periodo):
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
                # Nota que aquí le pasamos "self.tipo_registro" para que sepa si es rvie o rce
                estado_info = self.sunat_api.verificar_estado(
                    numero_ticket, token_acceso, periodo, self.tipo_registro
                )
                estado_codigo = estado_info.get("estado")

                if estado_codigo == "06":
                    datos_archivo = estado_info.get("datos_archivo")

                    # También pasamos "self.tipo_registro"
                    archivo_csv_en_memoria = self.sunat_api.descargar_archivo(
                        datos_archivo,
                        token_acceso,
                        periodo,
                        numero_ticket,
                        ruc,
                        self.tipo_registro,
                    )

                    resultado_etl = self.etl_registro.execute(archivo_csv_en_memoria)
                    df_limpio = resultado_etl.get("df_limpio")

                    registros_guardados = 0
                    if df_limpio is not None and not df_limpio.empty:
                        # Ahora usa el método genérico "guardar_lote"
                        registros_guardados = self.registro_repo.guardar_lote(
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
                    print(
                        f"[{ruc}] Ticket {numero_ticket} no está listo. Estado SUNAT: {estado_codigo}"
                    )
                    resultados[periodo] = {
                        "ticket": numero_ticket,
                        "estado": f"PENDIENTE_EN_SUNAT_ESTADO_{estado_codigo}",
                    }

            except Exception as e:
                print(
                    f"[{ruc}] Error al procesar ticket {numero_ticket} (Periodo: {periodo}): {e}"
                )

        return {"ruc": ruc, "resultados": resultados}
