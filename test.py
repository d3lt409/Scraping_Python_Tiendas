import json
import time
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# Opciones del navegador Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")  # Modo headless para no mostrar la interfaz gráfica
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--log-level=3")
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--ignore-certificate-errors")
chrome_options.add_argument("--remote-debugging-port=9230")
chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
chrome_options.add_experimental_option("prefs", {
    "profile.managed_default_content_settings.images": 2,
    "stylesheet": 2,
    "images": 2,
})

# Crear una nueva instancia del navegador Chrome
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Navegar a la página deseada
driver.get("https://www.exito.com/moda-y-accesorios/arkitect-francesca-miranda")

# Esperar hasta que la página esté completamente cargada
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div#gallery-layout-container > div > section > a > article")))

# Esperar unos segundos para que se complete el tráfico de red
time.sleep(10)

# Obtener los registros de rendimiento
logs_raw = driver.get_log("performance")
logs = [json.loads(lr["message"])["message"] for lr in logs_raw if "Network.response" in json.loads(lr["message"])["message"]["method"]]

# Filtrar los logs para encontrar las respuestas JSON
def log_filter(log_):
    if "response" in log_["params"]:
        return "json" in log_["params"]["response"]["mimeType"]
    return False

json_logs = filter(log_filter, logs)

# Extraer las respuestas JSON
json_data = {}
for i, log in enumerate(json_logs):
    request_id = log["params"]["requestId"]
    try:
        json_response = driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
        data = json.loads(json_response["body"])
        if "data" in data and "productSearch" in data["data"]:
            json_data = data["data"]["productSearch"]["products"]
            break
    except Exception as e:
        print(f"Error al obtener JSON para la solicitud {request_id}: {e}")

# Cerrar el navegador
driver.quit()

# Guardar los datos JSON en el archivo "finalv2.json"
with open("finalv2.json", "w") as fp:
    json.dump(json_data, fp, indent=4)

print("Datos JSON guardados correctamente en 'finalv2.json'.")
