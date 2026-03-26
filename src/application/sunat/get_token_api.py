from src.domain.interfaces import APIClientInterface


class GetTokenAPI:
    def __init__(self, sunat_client: APIClientInterface):
        self.sunat = sunat_client

    def execute(self, ruc, usuario_sol, clave_sol, id, clave):
        token = self.sunat.get_token(ruc, usuario_sol, clave_sol, id, clave)

        return token
