from src.domain.interfaces import ScriptInterface


class GetOnlyEnrolado:
    def __init__(self, repository: ScriptInterface):
        self.repository = repository

    def execute(self, ruc: str):
        return self.repository.get_only_enrolado(ruc=ruc)
