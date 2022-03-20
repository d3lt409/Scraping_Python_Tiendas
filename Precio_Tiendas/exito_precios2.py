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

FILENAME = "exito_precios.xlsx"
MAIN_PAGE = "https://www.exito.com"
LIST_CITY = ["Bogota"]  # ,"Medellin","Barranquilla","Cali","Cartagena","Armenia","Bello","Bucaramanga","Chia","Cucuta","Fusagasuga","Ibage","La ceja","Manizales","Monteria","Neiva","Pasto","Pereita","Popayan","Rionegro","Santa marta", "Sincelejo","Soacha","Tunja","Valledupar","Villavicencio","Zipaquira"]
COLUMNS = ["Departamento", "Categoria", "Sub_categoria", "Nombre_producto", "Precio_oferta", "Cantidad", 
           "Unidad", "Precio_normal", "Fecha_resultados","Hora_resultados"]
current_url = MAIN_PAGE
chrome_options = Options()
# chrome_options.add_argument('--headless')
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument("--disable-extensions")
prefs = {'profile.default_content_setting_values': { 'images': 2,'plugins': 2, 'popups': 2, 
        'geolocation': 2, 'notifications': 2, 'auto_select_certificate': 2, 'fullscreen': 2, 
        'mouselock': 2, 'mixed_script': 2, 'media_stream': 2, 'media_stream_mic': 2, 
        'media_stream_camera': 2, 'protocol_handlers': 2, 'ppapi_broker': 2, 
        'automatic_downloads': 2, 'midi_sysex': 2, 'push_messaging': 2, 'ssl_cert_decisions': 2, 'metro_switch_to_desktop': 2, 
        'protected_media_identifier': 2, 'app_banner': 2, 'site_engagement': 2, 'durable_storage': 2}}
chrome_options.add_experimental_option("prefs", prefs)
chrome_options.add_argument("--log-level=3")
driver = webdriver.Chrome(ChromeDriverManager().install(),options=chrome_options)
driver.maximize_window()
driver.get(MAIN_PAGE)
heigth: int = WebDriverWait(driver, 20).until(EC.presence_of_element_located(
        (By.XPATH, "/html/body/div[2]/div/div[1]/div/div[5]"))).size["height"]

def for_each_city():
    list_products = []
    
    list_products += each_departamentos("Bogota")
    driver.close()
    return list_products


def each_departamentos(city: str):
    global current_url
    ready_document()
    dep_elements:List[WebElement] = WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located(
            (By.XPATH, "//div[@class='exito-header-3-x-dropdownitem exito-header-3-x-categoryOption']")))
    departamentos: List[tuple[str]] = [
        (dep.get_attribute('id'), dep.get_attribute('innerHTML')) for dep in dep_elements]
    list_articles =[]
    for dep in departamentos:
        current_url = link_departamento = f"{MAIN_PAGE}/{dep[0]}"
        driver.get(current_url)
        ready_document()
        try:
            input: WebElement = WebDriverWait(driver, 50).until(
                EC.presence_of_element_located((By.XPATH, "//*[@id='react-select-2-input']")))
            input.send_keys(city)
            input.send_keys(Keys.RETURN)
            driver.execute_script("arguments[0].click();", WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, "//button[@class='exito-geolocation-3-x-primaryButton shippingaddress-confirmar']"))))
        except TimeoutException as e:
            continue
        except WebDriverException as e:
            crash_refresh_page()
            
        list_articles += categories(link_departamento, dep)
    return list_articles


def categories(link_departamento:str, departamento: Tuple[str]):
    global current_url
    WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,"//div[@id='imagen']")))
    scroll_down(2)
    list_elements = []
    cat_objects:list[WebElement] = WebDriverWait(driver, 50).until(EC.presence_of_all_elements_located(
        (By.XPATH, "//div[contains(@class,'--category-2')]/div[2]/div/div/div/div/div/input")))
    categories: List[str] = [
        cat.get_attribute("id").replace("category-2-", "") for cat in cat_objects]
    for cat in categories:
        try:
            current_url = f"{link_departamento}/{cat}?fuzzy=0&initialMap=c&initialQuery={departamento[0]}&map=category-1,category-2&operator=and"
            driver.get(current_url)
            list_elements += sub_categories(link_departamento,cat,departamento)
        except WebDriverException as _:
            crash_refresh_page()
            
    return list_elements


def sub_categories(link_departamento,categoria: str,departamento):
    global current_url
    ready_document()
    listado = []
    scroll_down(2)
    sub_cat_object: list[WebElement] = WebDriverWait(driver, 50).until(
        EC.presence_of_all_elements_located((By.XPATH, 
                    "//div[contains(@class,'--category-3')]/div[2]/div/div/div/div/div/input")))
    sub_categories: List[str] = [cat.get_attribute("id").replace("category-3-", "") for cat in sub_cat_object]
    for subcat in sub_categories:
        count = 1
        while True:
            current_url = f"{link_departamento}/{categoria}/{subcat}?fuzzy=0&initialMap=c&initialQuery={departamento[0]}&map=category-1,category-2,category-3,tipo-de-mascota&operator=and&page={count}"
            driver.get(current_url)
            ready_document()
            try:
                WebDriverWait(driver, 30).until(EC.presence_of_element_located(
                    (By.XPATH, "//h2[@class='tc fw1 exito-search-result-4-x-notFoundText']")))
                break
            except TimeoutException:
                pass
            listado += get_elements(departamento[1],categoria,subcat)
            count+=1
    return listado

# def por_marca(city,link_departamento,departamento,categoria,esp):
#     global current_url
#     listado = []
#     marcas_object:list[WebElement] = WebDriverWait(driver, 30).until(EC.presence_of_all_elements_located(
#                 (By.XPATH, "//div[contains(@class, 'container--brand')]/div[2]/div/div/div/div[2]/div/div/div/input")))
#     for marca in [val.get_attribute("id") for val in marcas_object]:
#         marca:str = marca.replace("brand-","")
#         current_url = f"{link_departamento}/{categoria}/{marca}/{esp}?fuzzy=0&initialMap=c&initialQuery={departamento[0]}&map=category-1,category-3,brand,tipo-de-mascota&operator=and"
#         driver.get(
#             f"{link_departamento}/{categoria}/{marca}/{esp}?fuzzy=0&initialMap=c&initialQuery={departamento[0]}&map=category-1,category-3,brand,tipo-de-mascota&operator=and")
#         ready_document()
#         try:
#             WebDriverWait(driver, 30).until(EC.presence_of_element_located(
#                 (By.XPATH, "//h2[@class='tc fw1 exito-search-result-4-x-notFoundText']")))
#             continue
#         except TimeoutException:
#             pass
#         listado += button_more_items(city,departamento[1],categoria,esp)
#     return listado
    
def ready_document(tries=0):
    if tries == 4: return
    timeout = time.time() + 2*60 
    while time.time() <= timeout:
        try:
            page_state=driver.execute_script('return document.readyState;')
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
    driver = webdriver.Chrome(ChromeDriverManager().install(),options=chrome_options)
    driver.maximize_window()
    driver.get(current_url)
    ready_document()
            
def button_more_items(city, dep, cat, subcat):
    global driver
    list_products = []
    ready_document()
    driver.execute_script(f"window.scrollTo(0, 400);")
    while True:
        try:
            element = WebDriverWait(driver, 20).until(EC.presence_of_element_located(
                    (By.XPATH, "//div[@class='vtex-button__label flex items-center justify-center h-100 ph5 ']")))
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            driver.execute_script("arguments[0].click();", element)
            list_products+=get_elements(city, dep, cat,subcat)
        except (TimeoutException) as _:
            list_products+=get_elements(city,dep, cat, subcat)
            break
        except (InvalidSessionIdException) as _:
            crash_refresh_page()
        
    return list_products


def scroll_down(time_limit,init=0):
    time.sleep(time_limit)
    final_heith = driver.execute_script("return document.body.scrollHeight")-heigth
    step = int(final_heith*0.004)
    for val in range(init,final_heith,step):
        driver.execute_script(f"window.scrollTo(0, {val});")
    if driver.execute_script("return document.body.scrollHeight")-final_heith >heigth:
        scroll_down(0,final_heith)



def get_elements(dep, cat, subcat):
    ready_document()
    scroll_down(1)
    try:
        container:WebElement = WebDriverWait(
            driver, 50).until(EC.presence_of_element_located((By.ID, "gallery-layout-container")))
        driver.execute_script("arguments[0].scrollIntoView(true);", container)
        time.sleep(2)
        elements: List[WebElement] = WebDriverWait(driver,10).until(lambda _: 
                container.find_elements_by_xpath("div/section/a/article/div[3]/div[2]"))
        list_elements = []
    except WebDriverException as _:
        driver.refresh()
        time.sleep(2)
        ready_document()
        container:WebElement = WebDriverWait(
            driver, 50).until(EC.presence_of_element_located((By.ID, "gallery-layout-container")))
        # driver.execute_script("arguments[0].scrollIntoView(true);", container)
        elements: List[WebElement] = WebDriverWait(driver,10).until(lambda _: 
                container.find_elements_by_xpath("div/section/a/article/div[3]/div[2]"))
        list_elements = []
    for el in elements:
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);",el)
            element = BeautifulSoup(el.get_attribute('innerHTML'),'html5lib')
        except (WebDriverException,TimeoutException) as e:
            print(e,e.args)
            continue
        
        precio = select_price(element)
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


def select_price(element: BeautifulSoup):
    try: # div/div/div/div[4]/div[2]/div/span
        return precio_promo(
            element.find_next(
                "div", {"class":"exito-vtex-components-4-x-selling-price flex items-center"}
            ).find_next("div").find_next("span").text)
    except Exception as e:
        print(e,e.args)
        pass
    try:
        return precio_promo(
            element.find_next(
                "div", {"class": "exito-vtex-components-4-x-PricePDP"}).find("span").text)
    except Exception as e:
        print(e,e.args)
        return ""
    


def select_name(element: BeautifulSoup):
    try:
        nombre_cantidad_unidad = element.find_next(
            "div", {"class": "exito-product-summary-3-x-nameContainer undefined "}).find("div").text.strip()
    except:
        pass
    try:
        nombre_cantidad_unidad = element.find(
            "div", {"class": "exito-product-details-3-x-stylePlp"}).text
    except:
        print("NO se encontró el nombre")
        return ""
    return nombre_cantidad_unidad


def precio_normal(element: BeautifulSoup):
    try:
        precio_normal = precio_promo(
            element.find_next("div",{"class":"exito-vtex-components-4-x-list-price t-mini ttn strike"})\
                .find_next("span",{"class":"exito-vtex-components-4-x-currencyContainer"}).text.strip())
        return precio_normal
    except Exception as e :
        return ""


def precio_promo(valor: str):
    exp = re.search("\d+[\.\d+]*", valor).group(0)
    return float(exp.replace(".", ""))


def nombre_cantidad(nom_cant: str):
    nom_cant = nom_cant.replace(" T/L/D TODOS LOS DIAS SIN REF", "")
    try:
        cant = re.search(
            "(?<=. )(\d+[\.\d]* [a-zA-Z ]+$|\d+[\.\d]*[a-zA-Z]+$|\d+[\.\d+]*)$", nom_cant).group(0)
    except:
        cant = "1 UN"
    if (cant.isnumeric()):
        cant += " UN"
    if (len(cant.split()) == 1):
        new_cant = re.search("\d+", cant).group(0)
        cant = cant.replace(new_cant, f"{new_cant} ")

    return [nom_cant]+cant.split()



def to_data_base(data: pd.DataFrame):

    connection_uri = "sqlite:///Precio_Tiendas/base_de_datos/Precios.sqlite"
    engine = sqlalchemy.create_engine(connection_uri)
    query = f"""
    CREATE TABLE IF NOT EXISTS Exito (
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
    data.to_sql("Exito",engine, if_exists='append', index=False)
    engine.dispose()


def main():
    df = pd.DataFrame(for_each_city(), columns=COLUMNS)
    try:
        df_excel = pd.read_excel(f"Precio_Tiendas/excel_files/{FILENAME}")
        df_total = df_excel.append(df)
        df_total.to_excel(
            f"Precio_Tiendas/excel_files/{FILENAME}", engine='xlsxwriter', index=False)
        print(f"Guardado a las {datetime.now()}")
    except FileNotFoundError as _:
        df.to_excel(
            f"Precio_Tiendas/excel_files/{FILENAME}", engine='xlsxwriter', index=False)
        print(f"Guardado a las {datetime.now()}")
    except Exception as _:
        print("No se cargó el archivo")


try:
    main()
except KeyboardInterrupt as _:
    pass
# for_each_category()

gc.collect(2)
