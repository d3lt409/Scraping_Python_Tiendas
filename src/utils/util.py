from datetime import datetime
import json
import time
import os
import sys
from urllib.request import urlopen
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.common.exceptions import WebDriverException, InvalidSessionIdException
from selenium.webdriver.chrome.service import Service

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

from src.database.database import DataBase


# Opciones del navegador Chrome
chrome_options = Options()
# Modo headless para no mostrar la interfaz gráfica
# chrome_options.add_argument("--headless")
# chrome_options.page_load_strategy = 'eager'
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument("--log-level=3")
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--ignore-certificate-errors")
# chrome_options.add_argument("--remote-debugging-port=9230")
chrome_options.set_capability(
    'goog:loggingPrefs', {'performance': 'ALL'})
chrome_options.add_experimental_option("prefs", {
    "profile.managed_default_content_settings.images": 2,
    "stylesheet": 2})


def init_scraping(page: str, name_database: str):
    while not internet_on():
        continue
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install(
    )), options=chrome_options)                     # Define the driver we are using
    driver.maximize_window()
    driver.get(page)
    db = DataBase(name_database)
    return driver, db


def ready_document(driver: WebDriver, current_url, tries=0):
    if tries == 4:
        return
    timeout = time.time() + 60
    while time.time() <= timeout:
        try:
            page_state = driver.execute_script('return document.readyState;')
            if page_state == 'complete':
                tries = 4
                return
        except WebDriverException as _:
            driver = crash_refresh_page(driver, current_url)
    if tries < 4:
        driver.refresh()
        ready_document(driver, tries+1)
    print("La página se cayó")
    duration = 5  # seconds
    freq = 440  # Hz
    if sys.platform == 'linux':
        os.system('play -nq -t alsa synth {} sine {}'.format(duration, freq))
    exit()


def crash_refresh_page(driver: WebDriver, current_url):
    while not internet_on():
        continue
    try:
        driver.close()
    except WebDriverException:
        pass
    driver = webdriver.Chrome(
        ChromeDriverManager().install(), options=chrome_options)
    driver.maximize_window()
    driver.get(current_url)
    ready_document(driver, current_url)
    return driver


def internet_on():
    try:
        urlopen('https://www.google.com/', timeout=10)
        return True
    except Exception as e:
        return False


def get_data(engine, model):

    time.sleep(7)
    # Obtener los registros de rendimiento
    logs_raw = engine.driver.get_log("performance")
    logs = [json.loads(lr["message"])["message"] for lr in logs_raw if "Network.response" in json.loads(
        lr["message"])["message"]["method"]]

    # Filtrar los logs para encontrar las respuestas JSON
    def log_filter(log_):
        if "response" in log_["params"]:
            return "json" in log_["params"]["response"]["mimeType"]
        return False

    json_logs = filter(log_filter, logs)

    json_data = []
    data_sql = engine.db.consulta_sql([model.nombre_producto],
                                      [model.fecha_resultados == datetime.now().date()])
    nombre_sql = set(
        [product for sub_data in data_sql for product in sub_data])
    for i, log in enumerate(json_logs):
        request_id = log["params"]["requestId"]
        json_data = []
        try:
            json_response = engine.driver.execute_cdp_cmd(
                "Network.getResponseBody", {"requestId": request_id})
            data = json.loads(json_response["body"])
            if "data" in data and "productSearch" in data["data"]:
                json_data = data["data"]["productSearch"]["products"]
            elif "data" in data and "productsByIdentifier" in data["data"] \
                    and "productName" in data["data"]["productsByIdentifier"][0]:
                json_data = data["data"]["productsByIdentifier"]
            if json_data:

                nombre_data = set([product["productName"]
                                  for product in json_data])
                if nombre_data.issubset(nombre_sql):
                    continue
                else:
                    return json_data
        except Exception as e:
            pass
    return []
