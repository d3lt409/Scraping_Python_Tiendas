from datetime import datetime
import sys
import time
from typing import List, Tuple
from bs4 import BeautifulSoup
from sqlalchemy.exc import OperationalError
from selenium import webdriver
import pandas as pd
import re
from selenium.common.exceptions import InvalidSessionIdException, TimeoutException, WebDriverException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import sqlalchemy
import gc
import os

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

from urllib.request import urlopen
from urllib.parse import quote

FILENAME = "olimpica_precios.xlsx"
MAIN_PAGE = "https://www.olimpica.com"
COLUMNS = ["Departamento", "Categoria", "Sub_categoria", "Nombre_producto", "Precio_oferta", "Cantidad",
           "Unidad", "Precio_normal", "Fecha_resultados", "Hora_resultados"]

def internet_on():
   try:
       urlopen('https://www.google.com/', timeout=10)
       return True
   except Exception as e: 
       return False

def each_departments_cat():
    global current_url_olimpica
     # //div[@class='pa4 pointer vtex-store-drawer-0-x-openIconContainer']
    ready_document()
    dep_button:WebElement = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, "//div[@class='pa4 pointer vtex-store-drawer-0-x-openIconContainer']")))
    driver.execute_script("arguments[0].click();",dep_button)
    dep_element_object: list[WebElement] = WebDriverWait(driver, 30).until(
        EC.presence_of_all_elements_located(
            (By.XPATH, "//div[@class='olimpica-mega-menu-0-x-Level1Container']/a")))
    dep_cat_elements:dict[str,list[list[str]]] = {}
    for el in dep_element_object:
        ActionChains(driver).move_to_element(el).perform()
        dep_cat_elements[el.text]= [
            [ele.text,ele.get_attribute("href")] for ele in WebDriverWait(driver, 30).until(
        EC.presence_of_all_elements_located((By.XPATH, "//div[@class='olimpica-mega-menu-0-x-Level2Container']//a")))] 
    ready_document()
    list_articles = []
    for dep,cats in dep_cat_elements.items():
        if dep.lower() == 'supermercado' or dep.lower() == 'droguería': continue
        for cat in cats:
            current_url_olimpica = cat[1]
            try:
                driver.get(current_url_olimpica)
            except WebDriverException as _:
                crash_refresh_page()
            ready_document()
            list_articles+=get_subcategories(dep,cat[0],cat[1])
    return list_articles

def get_subcategories(dep,cat,url:str):
    global current_url_olimpica
    ready_document()
    list_articles = []
    dep_cat = url.replace("https://www.olimpica.com/","").split("/")
    if (len(dep_cat) != 2):
        count = 1
        while True:
            if (url.__contains__("page=")): current_url_olimpica = re.sub("\d+$","",url)+str(count)
            elif (url.__contains__("?")): current_url_olimpica = f"{url}&page={count}"
            else : current_url_olimpica = f"{url}?page={count}"
            
            driver.get(current_url_olimpica)   
            ready_document()
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                    (By.XPATH, "//div[@class='vtex-search-result-3-x-searchNotFoundInfo flex flex-column ph9']")))
                break
            except TimeoutException:
                pass
            list_articles += get_elements(dep, cat, "")
            count+=1
        return list_articles
    
    sub_categories = get_subcategories_list()
    
    for subcat in sub_categories:
        count = 1
        while True:
            
            current_url_olimpica = f"https://www.olimpica.com/{dep_cat[0]}/{dep_cat[1]}/{subcat}?initialMap=category-1,categoria&initialQuery={dep_cat[0]}/{dep_cat[1]}&map=category-1,category-2,category-3&page={count}"
            try:
                driver.get(current_url_olimpica)   
            except WebDriverException as _:
                crash_refresh_page()
            ready_document()
            try:
                WebDriverWait(driver, 5).until(EC.presence_of_element_located(
                    (By.XPATH, "//div[@class='vtex-search-result-3-x-searchNotFoundInfo flex flex-column ph9']")))
                break
            except TimeoutException:
                pass #               https://www.olimpica.com/supermercado/desayuno/lacteos-y-derivados-refrigerados?initialMap=c,c&initialQuery=supermercado/desayuno&map=category-1,category-2,category-3
            
            list_articles += get_elements(dep, cat, subcat)
            count+=1
    return list_articles

def get_subcategories_list():
    tries = 0
    while True:
        try:
            subcat_button: WebElement = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@class,'--category-3')]/div/div")))
            driver.execute_script("arguments[0].scrollIntoView(true);",subcat_button)
            driver.execute_script("arguments[0].click();",subcat_button)
            time.sleep(2)
            scroll_height: WebElement = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@class,'--category-3')]//div[@data-testid='scrollable-element']/div/div")))
            scroll_element: WebElement = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@class,'--category-3')]//div[@data-testid='scrollable-element']")))
            driver.execute_script("arguments[0].scrollIntoView(true);",scroll_element)
            time.sleep(1)
            for i in [1,2,3]:
                driver.execute_script("arguments[0].scrollTop = arguments[1]",scroll_element,scroll_height.size["height"]*(i/3))
                time.sleep(1)
            ready_document()
            time.sleep(2)
            sub_categories_objects: list[WebElement] = WebDriverWait(driver, 30).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//div[contains(@class,'--category-3')]//div[@data-testid='scrollable-element']//label")))
            return [str(val.get_attribute("for")).replace("category-3-","") for val in sub_categories_objects]
        except TimeoutException as e:
            if tries == 3: print(e,e.args);exit()
            tries+=1
            time.sleep(5)
            driver.refresh()
            ready_document()
        except WebDriverException as _:
            if tries == 3: print(e,e.args);exit()
            tries+=1
            crash_refresh_page()
            ready_document()

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
    while not internet_on(): continue
    if driver: driver.close()
    driver = webdriver.Chrome(
        ChromeDriverManager().install(), options=chrome_options)
    driver.maximize_window()
    driver.get(current_url_olimpica)

def scroll_down(final):
    ready_document()
    step = int(final*0.005)
    for val in range(0,final,step):
        driver.execute_script(f"window.scrollTo(0, {val});")
        
def elementos_cargados():
    tries = 0
    while tries < 3:
        try:
            WebDriverWait(driver, 30).until(EC.presence_of_element_located(
                    (By.XPATH, "//div[@class='false olimpica-dinamic-flags-0-x-listPrices']/div/span")))
            break
        except TimeoutException as _:
            tries +=1
            crash_refresh_page()
            ready_document()
    return tries

def get_elements(dep, cat, subcat):
    time.sleep(2)
    list_elements = []
    if elementos_cargados() == 3: return []
    try:
        final_height: WebElement = WebDriverWait(driver, 30).until(EC.presence_of_element_located(
                (By.XPATH, "//div[@class='vtex-flex-layout-0-x-flexRow vtex-flex-layout-0-x-flexRow--category-content-products-v2']")))
        scroll_down(final_height.size["height"])
        elements: list[WebElement] = WebDriverWait(driver, 30).until(EC.presence_of_all_elements_located(
                (By.XPATH, "//div[@class='vtex-flex-layout-0-x-flexRow vtex-flex-layout-0-x-flexRow--category-content-products-v2']//article")))
        
    except WebDriverException as e:
        crash_refresh_page()
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, "//div[@class='vtex-search-result-3-x-searchNotFoundInfo flex flex-column ph9']")))
            return []
        except TimeoutException:
            pass
        
        elements: list[WebElement] = WebDriverWait(driver, 30).until(EC.presence_of_all_elements_located(
                (By.XPATH, "//div[@class='vtex-flex-layout-0-x-flexRow vtex-flex-layout-0-x-flexRow--category-content-products-v2']//article")))
    for el in elements:
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);",el)
            element = BeautifulSoup(el.get_attribute('innerHTML'),'html5lib')
        except (WebDriverException,TimeoutException) as e:
            print(e,e.args)
            continue
        
        precio = precio_promo(element)
        if not precio: continue
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
    
    while True:
        try:
            to_data_base(df)
            break
        except OperationalError as _:
            print("Base de datos bloquada, por favor guarde los cambios de donde la esté usando")
    print(f"Productos guardados, en la categoría: {cat}, subcategoría: {subcat} a las {datetime.now()} la cantidad de {len(df)}")
    return list_elements


def precio_promo(element: BeautifulSoup):
    try: # div/div/div/div[4]/div[2]/div/span
        return get_price(
            element.find_next("div", {"class":"false olimpica-dinamic-flags-0-x-listPrices"})\
                .find_next("div").find("span").text)
    except Exception as e:
        return None
        print(e,e.args)
    
def get_price(valor: str):
    exp = re.search("\d+[\.\d+]*", valor).group(0)
    return float(exp.replace(".", ""))

def select_name(element: BeautifulSoup):
    try:
        nombre_cantidad_unidad = element.find("h1").text.strip()
    except:
        print("NO se encontró el nombre")
        return ""
    return nombre_cantidad_unidad

def nombre_cantidad(nom_cant: str):
    try:
        cant = re.search("\d+[,\d]*\s{0,1}[a-zA-Z]{1,10}( X\d+ [a-zA-Z]{1,10})*", 
                         nom_cant.replace("  "," ")).group(0).replace(",",".")
    except AttributeError as _:
        print(nom_cant)
        return [nom_cant]+["1","UN"]
    cant = cant.replace("x","").replace("X","").strip()
        #cant = "1 UN"
    if (len(cant.split()) == 1):
        new_cant = re.search("\d+[\.\d]*", cant).group(0)
        cant = cant.replace(new_cant, "").strip()
        cant = f"{new_cant} {cant}"
    if (len(cant.split()) > 2):
        return [nom_cant]+cant.split()[:2]
    return [nom_cant]+cant.split()


def precio_normal(element: BeautifulSoup):
    try:
        precio_normal = get_price(
            element.find_next("div",{"class":"olimpica-dinamic-flags-0-x-strikePrice false"})\
                .find_next("span").text.strip())
        return precio_normal
    except Exception as e :
        return ""
    
    
def to_data_base(data: pd.DataFrame):

    connection_uri = "sqlite:///Precio_Tiendas/base_de_datos/Precios.sqlite"
    engine = sqlalchemy.create_engine(connection_uri)
    query = f"""
    CREATE TABLE IF NOT EXISTS Olimpica (
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
        UNIQUE(Nombre_producto,Fecha_resultados) ON CONFLICT IGNORE
    );
    """
    engine.execute(query)
    data.to_sql("Olimpica",engine, if_exists='append', index=False)
    engine.dispose()


current_url_olimpica = MAIN_PAGE
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
while not  internet_on(): continue
driver = webdriver.Chrome(
    ChromeDriverManager(path='driver').install(), options=chrome_options)
driver.maximize_window()
time.sleep(1)
driver.get(MAIN_PAGE)
driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
heigth: WebElement = WebDriverWait(driver, 20).until(EC.presence_of_element_located(
            (By.XPATH, "//div[@class='vtex-store-footer-2-x-footerLayout']"))).size["height"]



each_departments_cat()