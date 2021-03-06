import time
import os
import sys
from urllib.request import urlopen
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.common.exceptions import WebDriverException,InvalidSessionIdException
from  sqlalchemy import create_engine,text
from sqlalchemy.exc import OperationalError

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options


chrome_options = Options()
# chrome_options.add_argument('--headless')
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument("--disable-extensions")
prefs = {'profile.default_content_setting_values': {'images': 2, 'plugins': 2, 'popups': 2, 'geolocation': 2, 'notifications': 2, 'auto_select_certificate': 2, 'fullscreen': 2,
                                                    'mouselock': 2, 'mixed_script': 2, 'media_stream': 2, 'media_stream_mic': 2, 'media_stream_camera': 2, 'protocol_handlers': 2, 'ppapi_broker': 2,
                                                    'automatic_downloads': 2, 'midi_sysex': 2, 'push_messaging': 2, 'ssl_cert_decisions': 2, 'metro_switch_to_desktop': 2,
                                                    'protected_media_identifier': 2, 'app_banner': 2, 'site_engagement': 2, 'durable_storage': 2}}
chrome_options.add_experimental_option("prefs", prefs)
chrome_options.add_argument("--log-level=3")


connection_uri = "sqlite:///Precio_Tiendas/base_de_datos/Precios.sqlite"
engine = create_engine(connection_uri)

class DataBase():
    """Genera un objeto de la base de datos
    """
    def __init__(self,name_data_base:str) -> None:
        self.engine = create_engine(connection_uri)
        self.name_data_base = name_data_base
        
    def init_database(self):
        query = f"""
        CREATE TABLE IF NOT EXISTS {self.name_data_base} (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
            Departamento text,
            Categoria text,
            Sub_categoria text,
            Nombre_producto text,
            Precio_oferta REAL,
            Cantidad int,
            Unidad text,
            Precio_normal REAL,
            Fecha_resultados TEXT,
            Hora_resultados TEXT,
            UNIQUE(Departamento,Nombre_producto,Fecha_resultados) ON CONFLICT IGNORE
        );
        """
        self.engine.execute(query)
        
    def to_data_base(self,data):
        while True:
            try:
                data.to_sql(self.name_data_base,self.engine, if_exists='append', index=False)
                break
            except OperationalError:
                print("Por favor guarde cambios en la base de datos")
                time.sleep(5)
                continue

def init_scraping(page: str, name_database:str):
    while not internet_on(): continue
    init_database(name_database)
    driver = webdriver.Chrome(
        ChromeDriverManager().install(), options=chrome_options)
    driver.maximize_window()
    driver.get(page)
    return driver

def init_database(name_database:str):
    
    query = f"""
    CREATE TABLE IF NOT EXISTS {name_database} (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        Departamento text,
        Categoria text,
        Sub_categoria text,
        Nombre_producto text,
        Precio_oferta REAL,
        Cantidad int,
        Unidad text,
        Precio_normal REAL,
        Fecha_resultados TEXT,
        Hora_resultados TEXT,
        UNIQUE(Departamento,Nombre_producto,Fecha_resultados) ON CONFLICT IGNORE
    );
    """
    engine.execute(query)
    
def to_data_base(data,name_database:str):
    while True:
        try:
            data.to_sql(name_database,engine, if_exists='append', index=False)
            break
        except OperationalError:
            print("Por favor guarde cambios en la base de datos")
            time.sleep(5)
            continue

def consulta_sql(sql:str):
    with engine.connect() as conn:
        return conn.execute(text(sql)).fetchall()
    
def consulta_sql_unica(sql:str):
    with engine.connect() as conn:
        res = conn.execute(text(sql)).fetchone()[0]
        if res: return str(res)
        return None 

def ready_document(driver: WebDriver,current_url, tries=0):
    if tries == 4:
        return
    timeout = time.time() + 2*60
    while time.time() <= timeout:
        try:
            page_state = driver.execute_script('return document.readyState;')
            if page_state == 'complete':
                tries = 4
                return
        except WebDriverException as _:
            driver = crash_refresh_page(driver,current_url)
    if tries < 4:
        driver.refresh()
        ready_document(driver,tries+1)
    print("La p??gina se cay??")
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
    ready_document(driver,current_url)
    return driver


def internet_on():
    try:
        urlopen('https://www.google.com/', timeout=10)
        return True
    except Exception as e:
        return False
