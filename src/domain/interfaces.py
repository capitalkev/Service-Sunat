from typing import Any, Protocol
import io
from typing import Optional
import pandas as pd


class ScriptInterface(Protocol):
    def get_enrolado(self) -> Any: ...
    
    def get_only_enrolado(self, ruc:str) -> Any: ...

    def save_enrolado(self, datos: dict) -> None: ...


class APIClientInterface(Protocol):
    def get_token(
        self, ruc: str, usuario_sol: str, clave_sol: str, id: str, clave: str
    ) -> str: ...

    def _get_headers(self, token_acceso: str) -> dict: ...

    # ¡Agregamos tipo: str = "ventas" a estos 3 métodos!
    def generar_ticket(self, periodo: str, token_acceso: str, tipo: str = "ventas") -> str: ...

    def verificar_estado(
        self, numero_ticket: str, token_acceso: str, periodo: str, tipo: str = "ventas"
    ) -> dict: ...

    def descargar_archivo(
        self,
        datos_archivo,
        token_acceso: str,
        periodo: str,
        numero_ticket: str,
        ruc: str,
        tipo: str = "ventas"
    ) -> io.BytesIO: ...


class TokenScraperInterface(Protocol):
    def obtener_token_bearer(
        self, ruc: str, usuario_sol: str, clave_sol: str
    ) -> str: ...

class VentasSunatInterface(Protocol):
    def obtener_ventas(self, ruc: str, periodo: str, token_acceso: str) -> dict: ...
    
    def save_ticket(self, ruc: str, periodo: str, ticket: str) -> None: ...
    
class TicketsInterface(Protocol):
    def guardar_ticket(self, ticket: str, ruc: str, periodo: str, tipo_registro: str = "ventas") -> None: ...
    
    def traer_ticket(self, ruc: str, periodo: str, tipo_registro: str = "ventas") -> Optional[str]: ...
    
class ProcesarRegistroETLInterface(Protocol):
    def execute(self, csv_file_obj: io.BytesIO) -> dict: ...

class RegistroRepositoryInterface(Protocol):
    def existe_periodo(self, ruc: str, periodo: str) -> bool: ...
    def guardar_lote(self, df_limpio: pd.DataFrame, ruc: str) -> int: ...