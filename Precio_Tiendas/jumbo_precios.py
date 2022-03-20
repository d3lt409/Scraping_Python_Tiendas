from datetime import datetime
import sys
import time
from typing import List, Tuple
from bs4 import BeautifulSoup
from selenium import webdriver
import pandas as pd
import re
from selenium.common.exceptions import InvalidSessionIdException, TimeoutException, WebDriverException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import sqlalchemy
import gc
import os

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

FILENAME = "jumbo_precios.xlsx"
MAIN_PAGE = "https://www.tiendasjumbo.co/"
LIST_CITY = ["Bogota"]  # ,"Medellin","Barranquilla","Cali","Cartagena","Armenia","Bello","Bucaramanga","Chia","Cucuta","Fusagasuga","Ibage","La ceja","Manizales","Monteria","Neiva","Pasto","Pereita","Popayan","Rionegro","Santa marta", "Sincelejo","Soacha","Tunja","Valledupar","Villavicencio","Zipaquira"]
COLUMNS = ["Ciudad", "Departamento", "Categoria", "Sub_categoria", "Nombre_producto", "Precio_oferta", "Cantidad",
           "Unidad", "Precio_normal", "Fecha_resultados", "Hora_resultados"]
current_url = MAIN_PAGE
chrome_options = Options()
# chrome_options.add_argument('--headless')
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument("--disable-extensions")
prefs = {'profile.default_content_setting_values': {'images': 2, 'plugins': 2, 'popups': 2,
                                                    'geolocation': 2, 'notifications': 2, 'auto_select_certificate': 2, 'fullscreen': 2,
                                                    'mouselock': 2, 'mixed_script': 2, 'media_stream': 2, 'media_stream_mic': 2,
                                                    'media_stream_camera': 2, 'protocol_handlers': 2, 'ppapi_broker': 2,
                                                    'automatic_downloads': 2, 'midi_sysex': 2, 'push_messaging': 2, 'ssl_cert_decisions': 2, 'metro_switch_to_desktop': 2,
                                                    'protected_media_identifier': 2, 'app_banner': 2, 'site_engagement': 2, 'durable_storage': 2}}
chrome_options.add_experimental_option("prefs", prefs)
chrome_options.add_argument("--log-level=3")
driver = webdriver.Chrome(
    ChromeDriverManager().install(), options=chrome_options)
driver.maximize_window()
driver.execute_script("document.body.style.zoom='70 %'")
driver.get(MAIN_PAGE)
heigth: WebElement = WebDriverWait(driver, 20).until(EC.presence_of_element_located(
            (By.ID, "footer"))).size["height"]


def each_departments_categories():
    global current_url
    dep_element: WebElement = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, "//ul[@class='navigation__categories__content']")))
    dep_categories_links: List[str] = re.findall(
        """(?<=href=")\/[a-z-]+\/[a-z-]+(\?\w+=\w+)*""", dep_element.get_attribute("innerHTML"))
    list_articles = []
    ready_document()
    for dep in dep_categories_links:
        current_url = link_departamento = f"{MAIN_PAGE}{dep}"
        driver.get(link_departamento)
        dep_cat = dep.replace("/"," ").strip().split()
        get_subcategories(dep_cat[0],dep_cat[1])
    return list_articles


def get_subcategories(dep,cat):
    global current_url
    ready_document()
    subcategories_object: list[WebElement] = WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located(
            (By.XPATH, "//div[@class='search-multiple-navigator']/fieldset[1]/div/a")))
    sub_categories = [(val.get_attribute("href"),val.text) for val in subcategories_object]
    for subcat in sub_categories:
        current_url = subcat[0]
        driver.get(subcat[0])   
        ready_document()
        get_elements(dep, cat, subcat)


def ready_document(tries=0):
    if tries == 4:
        return
    timeout = time.time() + 2*60
    while time.time() <= timeout:
        try:
            page_state = driver.execute_script('return document.readyState;')
            if page_state == 'complete':
                tries = 3
                return
        except WebDriverException as _:
            crash_refresh_page()
    if tries < 4:
        driver.refresh()
        ready_document(tries+1)
    print("La página se cayó")
    duration = 5  # seconds
    freq = 440  # Hz
    if sys.platform == 'linux':
        os.system('play -nq -t alsa synth {} sine {}'.format(duration, freq))
    exit()


def crash_refresh_page():
    global driver
    driver = webdriver.Chrome(
        ChromeDriverManager().install(), options=chrome_options)
    driver.maximize_window()
    driver.get(current_url)

def scroll_down(init=0):
    final_heigth = driver.execute_script("return document.body.scrollHeight")-heigth
    step = int(heigth*0.003)
    for val in range(init,final_heigth,step):
        driver.execute_script(f"window.scrollTo(0, {val});")
    if driver.execute_script("return document.body.scrollHeight")-final_heigth >heigth:
        scroll_down(final_heigth)
        

def get_elements(dep, cat, subcat):
    scroll_down(1)
    try:
        elements: List[WebElement] = WebDriverWait(driver,10).until(lambda _: 
                driver.find_elements_by_xpath("//div[@class='product-item__bottom']"))
        list_elements = []
    except WebDriverException as _:
        crash_refresh_page()
    for el in elements:
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);",el)
            element = BeautifulSoup(el.get_attribute('innerHTML'),'html5lib')
        except (WebDriverException,TimeoutException) as e:
            print(e,e.args)
            continue
        
        precio = precio_promo(element)
        nombre_cantidad_unidad = nombre_cantidad(select_name(element))
        precio_norm = precio_normal(element)
        date = datetime.now()
        if (len(nombre_cantidad_unidad) == 3):
            list_elements.append(
                (dep, cat, subcat, nombre_cantidad_unidad[0].replace("\n"," "), precio, nombre_cantidad_unidad[1], 
                 nombre_cantidad_unidad[2], precio_norm, date.date(),date.time()))
        else:
            list_elements.append(
                (dep, cat, subcat, nombre_cantidad_unidad[0].replace("\n"," "), precio, nombre_cantidad_unidad[1], "", 
                 precio_norm, date.date(),date.time()))
        # print(list_elements)
    df = pd.DataFrame(list_elements, columns=COLUMNS)
    to_data_base(df)
    print(f"Productos guardados, para la categoría {cat} y subcategoría {subcat} a las {datetime.now()}")
    return list_elements


def precio_promo(element: BeautifulSoup):
    try: # div/div/div/div[4]/div[2]/div/span
        return get_price(
            element.find_next(
                "span", {"class":"product-prices__value product-prices__value--best-price"}
            ).text)
    except Exception as e:
        print(e,e.args)
    
def get_price(valor: str):
    exp = re.search("\d+[\.\d+]*", valor).group(0)
    return float(exp.replace(".", ""))

def select_name(element: BeautifulSoup):
    try:
        nombre_cantidad_unidad = element.find_next(
            "a", {"class": "product-item__name"}).find("span").text.strip()
    except:
        print("NO se encontró el nombre")
        return ""
    return nombre_cantidad_unidad

def nombre_cantidad(nom_cant: str):
    cant = re.search(
        "(\d+[\.\d]* [a-zA-Z ]+$|\d+[\.\d]*[a-zA-Z]+$|\d+[\.\d+]*)$", nom_cant).group(0)

        #cant = "1 UN"
    if (len(cant.split()) == 1):
        new_cant = re.search("\d+", cant).group(0)
        cant = cant.replace(new_cant, new_cant).strip()

    return [nom_cant]+cant.split()


def precio_normal(element: BeautifulSoup):
    try:
        precio_normal = precio_promo(
            element.find_next("div",{"class":"product-prices__price product-prices__price--former-price"})\
                .find_next("span",{"class":"product-prices__value"}).text.strip())
        return precio_normal
    except Exception as e :
        return ""
    
    
def to_data_base(data: pd.DataFrame):

    connection_uri = "sqlite:///Precio_Tiendas/base_de_datos/Precios.sqlite"
    engine = sqlalchemy.create_engine(connection_uri)
    query = f"""
    CREATE TABLE IF NOT EXISTS Jumbo (
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
    data.to_sql("Jumbo",engine, if_exists='append', index=False)
    engine.dispose()
