import gc
import time
import os
from datetime import datetime
import sys
from urllib.request import urlopen
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.common.exceptions import WebDriverException,InvalidSessionIdException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement

from sqlalchemy import create_engine,text
from sqlalchemy.exc import OperationalError

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options


chrome_options = Options()
# chrome_options.add_argument('--headless')
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
prefs = {'profile.default_content_setting_values': {'images': 2, 'plugins': 2, 'popups': 2, 'geolocation': 2, 'notifications': 2, 'auto_select_certificate': 2, 'fullscreen': 2,
                                                    'mouselock': 2, 'mixed_script': 2, 'media_stream': 2, 'media_stream_mic': 2, 'media_stream_camera': 2, 'protocol_handlers': 2, 'ppapi_broker': 2,
                                                    'automatic_downloads': 2, 'midi_sysex': 2, 'push_messaging': 2, 'ssl_cert_decisions': 2, 'metro_switch_to_desktop': 2,
                                                    'protected_media_identifier': 2, 'app_banner': 2, 'site_engagement': 2, 'durable_storage': 2}}
chrome_options.add_experimental_option("prefs", prefs)
chrome_options.add_argument("--log-level=3")


CONNECTION_URI = "sqlite:///db/Precios.sqlite"
CLICK = "arguments[0].click();"

class DataBase():
    """Genera un objeto de la base de datos
    """
    def __init__(self,name_data_base:str) -> None:
        self.engine = create_engine(CONNECTION_URI, echo = False, encoding = 'utf-8')
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
        
    def init_database_d1(self):
        query = f"""
        CREATE TABLE IF NOT EXISTS D1 (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            Nombre_producto text,
            Categoria text,
            Precio REAL,
            Cantidad int,
            Unidad text,
            Precio_unidad REAL,
            Fecha_resultados TEXT,
            UNIQUE(Nombre_producto,Categoria,Fecha_resultados) ON CONFLICT IGNORE
        );
        """
        self.engine.execute(query)
        
    def init_database_ara(self):

        query = f"""
            CREATE TABLE IF NOT EXISTS {self.name_data_base} (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                Categoria text,
                Sub_categoria text,
                Nombre text,
                Cantidad INTEGER,
                Unidad text,
                Precio REAL,
                Fecha_de_lectura TEXT,
                Hora_de_lectura TEXT,
                UNIQUE(Nombre,Categoria,Cantidad,Fecha_de_lectura) ON CONFLICT IGNORE
            );
            """
        self.engine.execute(query)
        
    def init_database_olimpica(self):

        query = f"""
            CREATE TABLE IF NOT EXISTS {self.name_data_base} (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                Departamento text,
                Categoria text,
                Sub_categoria text,
                Nombre_producto text,
                Precio_oferta REAL,
                Cantidad REAL,
                Unidad text,
                Precio_normal REAL,
                Fecha_resultados TEXT,
                Hora_resultados TEXT,
                UNIQUE(Nombre_producto,Categoria,Fecha_resultados) ON CONFLICT IGNORE
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

    def consulta_sql(self,sql:str):
        with self.engine.connect() as conn:
            return conn.execute(text(sql)).fetchall()
    

    def consulta_sql_unica(self,sql:str):
        with self.engine.connect() as conn:
            res = conn.execute(text(sql)).first()
            if res: return res
            return None 
        
    def last_item_db(self):
        date = datetime.now().strftime("%Y-%m-%d")
        res = self.consulta_sql_unica(f"""select Departamento,Categoria,Sub_categoria from {self.name_data_base} 
                where Fecha_resultados = {date!r} AND id = (select max(id) from {self.name_data_base});""")
        if res:
            res = dict(res)
        return res
    
    def close(self):
        self.engine.dispose()

class Engine():

    def __init__(self, page_url:str, name_database:str,headless:bool = False) -> None:
        self.headless = headless
        self._driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()) 
                              ,options=self.get_options(self.headless))                     # Define the driver we are using
        self._current_url = page_url
        self.init_page()
        self.db = DataBase(name_database)

    
    def _get_driver(self):
        return self._driver

    def _get_current_url(self):
        return self._current_url

    def _set_current_url(self, url):
        self._current_url = url
    
    current_url = property(fget=_get_current_url, fset=_set_current_url)
    driver:WebDriver = property(fget=_get_driver)

    def get_options(self, headless:bool):
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        prefs = {'profile.default_content_setting_values': {'images': 2, 'plugins': 2, 'popups': 2, 'geolocation': 2, 'notifications': 2, 'auto_select_certificate': 2, 'fullscreen': 2,
                                                            'mouselock': 2, 'mixed_script': 2, 'media_stream': 2, 'media_stream_mic': 2, 'media_stream_camera': 2, 'protocol_handlers': 2, 'ppapi_broker': 2,
                                                            'automatic_downloads': 2, 'midi_sysex': 2, 'push_messaging': 2, 'ssl_cert_decisions': 2, 'metro_switch_to_desktop': 2,
                                                            'protected_media_identifier': 2, 'app_banner': 2, 'site_engagement': 2, 'durable_storage': 2}}
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.add_argument("--log-level=3")

    def init_page(self):
        while not internet_on(): continue
        self._driver.maximize_window()
        self._driver.get(self.current_url)
    
    def ready_document(self,tries=0):
        if tries == 4:
            return
        timeout = time.time() + 60
        while time.time() <= timeout:
            try:
                page_state = self._driver.execute_script('return document.readyState;')
                if page_state == 'complete':
                    tries = 4
                    return
            except WebDriverException as _:
                self.crash_refresh_page()

        if tries < 4:
            self._driver.refresh()
            self.ready_document(tries+1)
        print("La página se cayó")
        duration = 5  # seconds
        freq = 440  # Hz
        if sys.platform == 'linux':
            os.system('play -nq -t alsa synth {} sine {}'.format(duration, freq))
        exit()
    
    def crash_refresh_page(self):
        while not internet_on():
            continue
        try:
            self._driver.close()
            self._driver.quit()
            gc.collect(2)
        except WebDriverException:
            pass
        self._driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()) 
                              ,options=self.get_options(self.headless)) 
        self.init_page()
        self.ready_document()

    def element_wait_searh(self, time:int, by, value:str) -> WebElement:
        return WebDriverWait(self._driver, time).until(EC.presence_of_element_located((by, value)))

    def elements_wait_searh(self, time:int, by, value:str) -> list[WebElement]:
        return WebDriverWait(self._driver, time).until(EC.presence_of_all_elements_located((by, value)))
    
    def close(self):
        self._driver.close()
        self._driver.quit()
        self.db.close()

def init_scraping(page: str, name_database:str):
    while not internet_on(): continue
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()) 
                              ,options=chrome_options)                     # Define the driver we are using
    driver.maximize_window()
    driver.get(page)
    db = DataBase(name_database)
    return driver,db


def ready_document(driver: WebDriver,current_url, tries=0):
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
            driver = crash_refresh_page(driver,current_url)
    if tries < 4:
        driver.refresh()
        ready_document(driver,tries+1)
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
    ready_document(driver,current_url)
    return driver


def internet_on():
    try:
        urlopen('https://www.google.com/', timeout=10)
        return True
    except Exception as e:
        return False

