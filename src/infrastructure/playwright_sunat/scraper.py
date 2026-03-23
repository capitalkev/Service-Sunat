from playwright.sync_api import sync_playwright
from src.domain.interfaces import TokenScraperInterface


class PlaywrightTokenScraper(TokenScraperInterface):
    def obtener_token_bearer(self, ruc: str, usuario_sol: str, clave_sol: str) -> str:
        print(f"[{ruc}] Iniciando Playwright para capturar Token...")
        token_capturado = None

        with sync_playwright() as p:
            # En producción asegúrate de usar headless=True
            browser = p.chromium.launch(channel="msedge", headless=True)
            context = browser.new_context()
            page = context.new_page()

            def capturar_headers(request):
                nonlocal token_capturado
                if "api-sire.sunat.gob.pe" in request.url:
                    headers = request.headers
                    auth_header = headers.get("authorization", "")
                    if auth_header.lower().startswith("bearer"):
                        # Extraemos solo el token, sin la palabra "Bearer "
                        token_capturado = auth_header.split(" ", 1)[1]

            page.on("request", capturar_headers)

            try:
                url_login = "https://api-seguridad.sunat.gob.pe/v1/clientessol/4f3b88b3-d9d6-402a-b85d-6a0bc857746a/oauth2/loginMenuSol?lang=es-PE&showDni=true&showLanguages=false&originalUrl=https://e-menu.sunat.gob.pe/cl-ti-itmenu/AutenticaMenuInternet.htm&state=rO0ABXNyABFqYXZhLnV0aWwuSGFzaE1hcAUH2sHDFmDRAwACRgAKbG9hZEZhY3RvckkACXRocmVzaG9sZHhwP0AAAAAAAAx3CAAAABAAAAADdAAEZXhlY3B0AAZwYXJhbXN0AEsqJiomL2NsLXRpLWl0bWVudS9NZW51SW50ZXJuZXQuaHRtJmI2NGQyNmE4YjVhZjA5MTkyM2IyM2I2NDA3YTFjMWRiNDFlNzMzYTZ0AANleGVweA=="
                page.goto(url_login)

                page.locator("#txtRuc").fill(ruc)
                page.locator("#txtUsuario").fill(usuario_sol)
                page.locator("#txtContrasena").fill(clave_sol)
                page.locator("#btnAceptar").click()

                if (
                    page.get_by_text("Falla en la autenticación").is_visible()
                    or page.get_by_text(
                        "DNI y/o contraseña son incorrectos"
                    ).is_visible()
                ):
                    raise PermissionError(
                        "Acceso denegado: El RUC, Usuario o Clave SOL son incorrectos."
                    )

                page.wait_for_timeout(1000)
                page.evaluate("""
                    const fondo = document.getElementById('divModalCampanaBak');
                    if (fondo) fondo.remove();
                    
                    const modal = document.getElementById('divModalCampana');
                    if (modal) modal.remove();
                    
                    document.body.classList.remove('modal-open');
                    document.body.style.overflow = 'auto';
                """)

                page.locator("#divOpcionServicio2 > h4").first.click()
                page.locator("#nivel1_60 > span.spanNivelDescripcion").first.click()
                page.locator("#nivel2_60_2 > span.spanNivelDescripcion").first.click()
                page.locator("#nivel3_60_2_1 > span.spanNivelDescripcion").first.click()
                page.locator("#nivel4_60_2_1_1_1 > span").first.click()

                for _ in range(10):
                    if token_capturado:
                        break
                    page.wait_for_timeout(1000)

            except Exception as e:
                raise RuntimeError(f"Fallo en Playwright: {e}")
            finally:
                context.close()
                browser.close()

        if not token_capturado:
            raise ValueError("No se pudo capturar el Token Bearer.")

        return token_capturado
