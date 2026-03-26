from src.domain.interfaces import APIClientInterface


class GetTokenAPI:
    def __init__(self):
        self.sunat = APIClientInterface

    def execute(self, ruc, usuario_sol, clave_sol, id, clave):
        token = self.sunat.get_token(ruc, usuario_sol, clave_sol, id, clave)

        return token
