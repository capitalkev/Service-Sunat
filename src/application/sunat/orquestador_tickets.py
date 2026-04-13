from src.application.sunat.create_ticket import CreateTicket
from src.application.sunat.get_token import GetToken
from src.application.sunat.save_ticket import SaveTicket
from src.domain.interfaces import RegistroRepositoryInterface


class OrquestadorTickets:
    def __init__(
        self,
        generar_ticket: CreateTicket,
        get_token: GetToken,
        guardar_ticket: SaveTicket,
        registro_repo: RegistroRepositoryInterface,
        tipo_registro: str = "ventas",
    ):
        self.generar_ticket = generar_ticket
        self.get_token = get_token
        self.guardar_ticket = guardar_ticket
        self.registro_repo = registro_repo
        self.tipo_registro = tipo_registro

    def execute(
        self, ruc, usuario_sol, clave_sol, client_id, client_secret, periodos: list
    ):
        resultados = {}
        token_acceso = self.get_token.execute(
            ruc, usuario_sol, clave_sol, client_id, client_secret
        )

        for periodo in periodos:
            if self.registro_repo.existe_periodo(ruc, periodo):
                resultados[periodo] = {
                    "estado": f"{self.tipo_registro.upper()}_YA_EXISTEN_EN_BD"
                }
                continue
            try:
                # Pasamos el tipo_registro al crear y guardar
                numero_ticket = self.generar_ticket.execute(
                    periodo, token_acceso, self.tipo_registro
                )
                if numero_ticket:
                    self.guardar_ticket.execute(
                        ruc, periodo, numero_ticket, self.tipo_registro
                    )
                    resultados[periodo] = {
                        "ticket": numero_ticket,
                        "estado": "GUARDADO",
                    }
            except Exception as e:
                resultados[periodo] = {"error": str(e)}

        return {"ruc": ruc, "resultados": resultados}
