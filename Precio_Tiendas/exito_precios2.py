from datetime import datetime
import time
from typing import List, Tuple
from bs4 import BeautifulSoup
from bs4.element import PageElement, ResultSet
from selenium import webdriver
import pandas as pd
import re
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import sqlalchemy
import gc

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

FILENAME = "exito_precios.xlsx"
MAIN_PAGE = "https://www.exito.com"
LIST_CITY = ["Bogota"]  # ,"Medellin","Barranquilla","Cali","Cartagena","Armenia","Bello","Bucaramanga","Chia","Cucuta","Fusagasuga","Ibage","La ceja","Manizales","Monteria","Neiva","Pasto","Pereita","Popayan","Rionegro","Santa marta", "Sincelejo","Soacha","Tunja","Valledupar","Villavicencio","Zipaquira"]
COLUMNS = ["Ciudad", "Categoria", "Sub_categoria", "Nombre_producto", "Precio_oferta", "Cantidad", 
           "Unidad", "Precio_normal", "Fecha_resultados","Hora_resultados"]

chrome_options = Options()
#chrome_options.add_argument('--headless')
#chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument('--no-sandbox')
#chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument("--disable-extensions")
prefs = {'profile.default_content_setting_values': { 'images': 2, 
                            'plugins': 2, 'popups': 2, 'geolocation': 2, 
                            'notifications': 2, 'auto_select_certificate': 2, 'fullscreen': 2, 
                            'mouselock': 2, 'mixed_script': 2, 'media_stream': 2, 
                            'media_stream_mic': 2, 'media_stream_camera': 2, 'protocol_handlers': 2, 
                            'ppapi_broker': 2, 'automatic_downloads': 2, 'midi_sysex': 2, 
                            'push_messaging': 2, 'ssl_cert_decisions': 2, 'metro_switch_to_desktop': 2, 
                            'protected_media_identifier': 2, 'app_banner': 2, 'site_engagement': 2, 
                            'durable_storage': 2}}
chrome_options.add_experimental_option("prefs", prefs)
chrome_options.add_argument("--log-level=3")
driver = webdriver.Chrome(ChromeDriverManager().install(),chrome_options=chrome_options)
driver.maximize_window()
driver.execute_script("document.body.style.zoom='70 %'")

def for_each_city():
    global driver
    list_products = []
    for city in LIST_CITY:
        driver.get(MAIN_PAGE)
        list_products += each_departamentos(city)
    driver.close()
    del driver
    return list_products


def each_departamentos(city: str):
    departamentos: List[tuple[str]] = [
        (dep.get_attribute('id'), dep.text) for dep in WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located(
            (By.XPATH, "//div[@class='exito-header-3-x-dropdownitem exito-header-3-x-categoryOption']")))]
    list_articles =[]
    for dep in departamentos:
        link_departamento = f"{MAIN_PAGE}/{dep[0]}"
        driver.get(link_departamento)
        try:
            input: WebElement = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//*[@id='react-select-2-input']")))
            input.send_keys(city)
            input.send_keys(Keys.RETURN)
            driver.execute_script("arguments[0].click();", WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, "//button[@class='exito-geolocation-3-x-primaryButton shippingaddress-confirmar']"))))
        except TimeoutException as e:
            e.with_traceback()
        list_articles += categories(city, link_departamento, dep)
    return list_articles


def categories(city: str, link_departamento, departamento: Tuple[str]):
    WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,"//div[@id='imagen']")))
    scroll_down(2)
    list_elements = []
    try:
        categories: List[str] = [
            cat.get_attribute("id").replace("category-3-", "") for cat in WebDriverWait(driver, 50).until(EC.presence_of_all_elements_located(
            (By.XPATH, "//div[@class='exito-filters-0-x-filter__container exito-filters-0-x-filter__container--new-layout-filters bb b--muted-4 exito-filters-0-x-filter__container--category-3']/div[2]/div/div/div/div/div/div/div/input")))]
        for cat in categories:
            driver.get(
                f"{link_departamento}/{cat}?fuzzy=0&initialMap=c&initialQuery={departamento[0]}&map=category-1,category-3&operator=and")
            try:
                WebDriverWait(driver, 30).until(EC.presence_of_element_located(
                    (By.XPATH, "//h2[@class='tc fw1 exito-search-result-4-x-notFoundText']")))
                continue
            except TimeoutException:
                pass
            while True:
                try:
                    WebDriverWait(driver, 5).until(EC.presence_of_element_located(
                        (By.XPATH, "//h1[contains(text(),'504 Gateway Time-out')]")))
                    time.sleep(4)
                    continue
                except TimeoutException:
                    break
            # num_elements = int(WebDriverWait(driver,20).until(EC.presence_of_element_located(By.XPATH,"//div[@class='exito-search-result-total-products exito-search-result-4-x-exitoTotalProducts bt-s pt4-s bb-s pb3-s mb3-s bn-l pt0-l pb0-l mb0-l b--muted-5']/span")).text)
            # if (num_elements > 21):
            if (cat == "accesorios-mascotas"):
                list_elements += categoria_especial(city,link_departamento,cat,departamento)
                continue
            time.sleep(2)
            list_elements+=button_more_items(city,departamento[1],cat)
        return list_elements
    except TimeoutException as e:
        e.with_traceback()
        categories: List[str] = [cat.get_attribute("id").replace("category-2-", "") for cat in WebDriverWait(driver, 50).until(EC.presence_of_all_elements_located(
            (By.XPATH, "//div[@class='exito-filters-0-x-filter__container exito-filters-0-x-filter__container--new-layout-filters bb b--muted-4 exito-filters-0-x-filter__container--category-2']/div[2]/div/div/div/div/div/input")))]
        for cat in categories:
            driver.get(f"{link_departamento}/{cat}")
            time.sleep(2)
            list_elements+=button_more_items(city,departamento[1],cat)
        return list_elements



def categoria_especial(city,link_departamento,categoria: str,departamento):
    listado = []
    driver.execute_script("document.body.style.zoom='70 %'")
    scroll_down(2)
    cat_esp: List[str] = [cat.get_attribute("id").replace("tipo-de-mascota-", "") for cat in WebDriverWait(driver, 50).until(EC.presence_of_all_elements_located(
        (By.XPATH, "//div[@class='exito-filters-0-x-filter__container exito-filters-0-x-filter__container--new-layout-filters bb b--muted-4 exito-filters-0-x-filter__container--tipo-de-mascota']/div[2]/div/div/div/div/div/input")))]
    for esp in cat_esp:
        driver.get(
            f"{link_departamento}/{categoria}/{esp}?fuzzy=0&initialMap=c&initialQuery={departamento[0]}&map=category-1,category-3,tipo-de-mascota&operator=and")
        try:
            WebDriverWait(driver, 30).until(EC.presence_of_element_located(
                (By.XPATH, "//h2[@class='tc fw1 exito-search-result-4-x-notFoundText']")))
            continue
        except TimeoutException:
            pass
        
        time.sleep(2)
        listado += button_more_items(city,departamento[1],categoria)
        
    return listado



def button_more_items(city, cat, subcat):
    list_products = []
    while True:
        try:
            element = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                    (By.XPATH, "//div[@class='vtex-button__label flex items-center justify-center h-100 ph5 ']")))
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            driver.execute_script("arguments[0].click();", element)
            list_products+=get_elements(city, cat, subcat)
        except (TimeoutException) as _:
            list_products+=get_elements(city, cat, subcat)
            break
    return list_products


def scroll_down(time_limit,init=0):
    time.sleep(time_limit)
    heigth = driver.execute_script("return document.body.scrollHeight")-500
    step = int(heigth*0.01)
    for val in range(init,heigth,step):
        driver.execute_script(f"window.scrollTo(0, {val});")
    if driver.execute_script("return document.body.scrollHeight")-heigth >500:
        scroll_down(0,heigth)


def get_elements(city, cat, subcat):
    driver.execute_script("document.body.style.zoom='70 %'")
    time.sleep(3)
    container:WebElement = WebDriverWait(
        driver, 20).until(EC.presence_of_element_located((By.ID, "gallery-layout-container")))
    driver.execute_script("arguments[0].scrollIntoView(true);", container)

    elements: List[WebElement] = WebDriverWait(driver,10).until(lambda _: 
            container.find_elements_by_xpath("div/section/a/article/div[3]/div[2]"))
    list_elements = []
    for el in elements:
        driver.execute_script("arguments[0].scrollIntoView(true);",el)
        element = BeautifulSoup(el.get_attribute('innerHTML'),'html5lib')
        precio = select_price(element)
        nombre_cantidad_unidad = nombre_cantidad(select_name(element))
        precio_norm = precio_normal(element)
        date = datetime.now()
        if (len(nombre_cantidad_unidad) == 3):
            list_elements.append(
                (city, cat, subcat, nombre_cantidad_unidad[0].replace("\n"," "), precio, nombre_cantidad_unidad[1], 
                 nombre_cantidad_unidad[2], precio_norm, date.date(),date.time()))
        else:
            list_elements.append(
                (city, cat, subcat, nombre_cantidad_unidad[0].replace("\n"," "), precio, nombre_cantidad_unidad[1], "", 
                 precio_norm, date.date(),date.time()))
        # print(list_elements)
    df = pd.DataFrame(list_elements, columns=COLUMNS)
    to_data_base(df)
    print(f"Productos guardados, para la categoría {cat}")
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
                "div", {
                    "class": "flex f5 fw5 pa0 flex items-center justify-start w-100 search-result-exito-vtex-components-selling-price exito-vtex-components-4-x-alliedDiscountPrice"}).find("span").text)
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
        print(e,e.args)
        return ""


def precio_promo(valor: str):
    exp = re.search("\d+[\.\d+]*", valor).group(0)
    return float(exp.replace(".", ""))


def nombre_cantidad(nom_cant: str):
    nom_cant = nom_cant.replace(" T/L/D TODOS LOS DIAS SIN REF", "")
    try:
        cant = re.search(
            "(?<=. )(\d+[\.\d]* [a-zA-Z ]+|\d+[\.\d]*[a-zA-Z]+|\d{1,3}(\.\d)*)$", nom_cant).group(0)
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
        Ciudad text,
        Categoria text,
        Sub_categoria text,
        Nombre_producto text,
        Precio_oferta REAL,
        Cantidad int,
        Unidad text,
        Precio_normal REAL,
        Fecha_resultados TEXT,
        Hora_resultados TEXT,
        UNIQUE(Categoria,Nombre_producto,Fecha_resultados) ON CONFLICT IGNORE
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
