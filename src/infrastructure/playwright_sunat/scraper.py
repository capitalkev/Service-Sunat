from playwright.sync_api import sync_playwright
from src.domain.interfaces import TokenScraperInterface


class PlaywrightTokenScraper(TokenScraperInterface):
    def obtener_token_bearer(self, ruc: str, usuario_sol: str, clave_sol: str) -> str:
        print(f"[{ruc}] 1. Iniciando Playwright para capturar Token...")
        token_capturado = None

        with sync_playwright() as p:
            # headless=False si quieres ver cómo el navegador se mueve solo
            browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"]) 
            context = browser.new_context(viewport={"width": 1366, "height": 768},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
            page = context.new_page()

            # Interceptor de peticiones
            def capturar_headers(request):
                nonlocal token_capturado
                if "api-sire.sunat.gob.pe" in request.url:
                    headers = request.headers
                    if "authorization" in headers and headers["authorization"].startswith("Bearer"):
                        token_capturado = headers["authorization"]

            page.on("request", capturar_headers)

            try:
                # 1. Login
                url_login = "https://api-seguridad.sunat.gob.pe/v1/clientessol/4f3b88b3-d9d6-402a-b85d-6a0bc857746a/oauth2/loginMenuSol?lang=es-PE&showDni=true&showLanguages=false&originalUrl=https://e-menu.sunat.gob.pe/cl-ti-itmenu/AutenticaMenuInternet.htm&state=rO0ABXNyABFqYXZhLnV0aWwuSGFzaE1hcAUH2sHDFmDRAwACRgAKbG9hZEZhY3RvckkACXRocmVzaG9sZHhwP0AAAAAAAAx3CAAAABAAAAADdAAEZXhlY3B0AAZwYXJhbXN0AEsqJiomL2NsLXRpLWl0bWVudS9NZW51SW50ZXJuZXQuaHRtJmI2NGQyNmE4YjVhZjA5MTkyM2IyM2I2NDA3YTFjMWRiNDFlNzMzYTZ0AANleGVweA=="
                page.goto(url_login)
                
                page.locator("#txtRuc").fill(ruc)
                page.locator("#txtUsuario").fill(usuario_sol)
                page.locator("#txtContrasena").fill(clave_sol)
                page.locator("#btnAceptar").click()
                page.wait_for_timeout(1000)
                #Si las claves son incorrectas.
                error_locator = page.locator("#lblHeader")
                if error_locator.is_visible():
                    texto_error = error_locator.inner_text()
                    if "Falla en la autenticación" in texto_error:
                        raise ValueError(f"ATENCIÓN: El RUC {ruc} tiene claves incorrectas.")
                # Si aparece un modal luego del login la eliminamos.
                page.evaluate("""
                    const fondo = document.getElementById('divModalCampanaBak');
                    if (fondo) fondo.remove();
                    
                    const modal = document.getElementById('divModalCampana');
                    if (modal) modal.remove();
                    
                    document.body.classList.remove('modal-open');
                    document.body.style.overflow = 'auto';
                """)

                print("Navegando al menú SIRE...")
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
                print(f"Error en Playwright: {e}")
            finally:
                browser.close()
        print(f"[{ruc}] 2. Token capturado: {token_capturado}")
        if not token_capturado:
            raise ValueError("No se pudo capturar el Token Bearer.")
        return token_capturado
