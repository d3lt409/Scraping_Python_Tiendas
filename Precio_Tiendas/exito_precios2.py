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
from selenium.webdriver.common.action_chains import ActionChains
import sqlite3
import gc

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

FILENAME = "exito_precios.xlsx"
MAIN_PAGE = "https://www.exito.com"
LIST_CITY = ["Bogota"]  # ,"Medellin","Barranquilla","Cali","Cartagena","Armenia","Bello","Bucaramanga","Chia","Cucuta","Fusagasuga","Ibage","La ceja","Manizales","Monteria","Neiva","Pasto","Pereita","Popayan","Rionegro","Santa marta", "Sincelejo","Soacha","Tunja","Valledupar","Villavicencio","Zipaquira"]


chrome_options = Options()
#chrome_options.add_argument('--headless')
#chrome_options.add_argument("--disable-gpu")
#chrome_options.add_argument('--no-sandbox')
#chrome_options.add_argument('--disable-dev-shm-usage')
#chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--log-level=3")
driver = webdriver.Chrome(ChromeDriverManager().install(),chrome_options=chrome_options)
driver.maximize_window()

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
    departamentos: List[tuple] = [(str(dep.get_attribute('id')), str(dep.text.strip())) for dep in WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.XPATH, "//div[@class='exito-header-3-x-dropdownitem exito-header-3-x-categoryOption']")))]
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
        except TimeoutException as _:
            pass
        list_articles += categories(city, link_departamento, dep)
    return list_articles


def categories(city: str, link_departamento, departamento: Tuple[str]):
    WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,"//div[@id='imagen']")))
    heigth = driver.execute_script("return document.body.scrollHeight")
    scroll_down(round(heigth*0.3))
    list_elements = []
    try:
        categories: List[str] = [cat.get_attribute("id").replace("category-3-", "") for cat in WebDriverWait(driver, 50).until(EC.presence_of_all_elements_located(
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
            list_elements+=get_elements(city,departamento[1],cat)
        print(pd.DataFrame(list_elements))
        return list_elements
    except TimeoutException as _:
        categories: List[str] = [cat.get_attribute("id").replace("category-2-", "") for cat in WebDriverWait(driver, 50).until(EC.presence_of_all_elements_located(
            (By.XPATH, "//div[@class='exito-filters-0-x-filter__container exito-filters-0-x-filter__container--new-layout-filters bb b--muted-4 exito-filters-0-x-filter__container--category-2']/div[2]/div/div/div/div/div/input")))]
        for cat in categories:
            driver.get(f"{link_departamento}/{cat}")
            time.sleep(2)
            list_elements+=get_elements(city,departamento[1],cat)
        return list_elements



def categoria_especial(city,link_departamento,categoria: str,departamento):
    listado = []
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
        button_more_items()
        listado += get_elements(city,departamento[1],categoria)
        
    return listado



def button_more_items():
    while True:
        try:
            driver.execute_script("arguments[0].click();", WebDriverWait(
                driver, 10).until(EC.presence_of_element_located(
                    (By.XPATH, "//div[@class='vtex-button__label flex items-center justify-center h-100 ph5 ']"))))
        except (TimeoutException) as _:
            heigth = driver.execute_script("return document.body.scrollHeight")
            scroll_down(round(heigth*0.9))
            break


def scroll_down(heigth, init: int = 0):
    for i in range(init, heigth, round(heigth*0.3)):
        driver.execute_script(f"window.scrollTo(0, {i});")
        time.sleep(2)


def get_elements(city, cat, subcat):
    time.sleep(2)
        
    soup = BeautifulSoup(driver.page_source, 'html5lib')
    container: PageElement = soup.find(
        "div", {"id": 'gallery-layout-container'})
    if not container:
        soup = BeautifulSoup(driver.page_source, 'html5lib')
        container: PageElement = soup.find(
            "div", {"id": 'gallery-layout-container'})
    elements: ResultSet = container.find_all(
        "div", {"class": "vtex-flex-layout-0-x-flexRow vtex-flex-layout-0-x-flexRow--product-info-container"})
    list_elements = []
    for el in elements:
        el: PageElement
        precio = select_price(el)
        nombre_cantidad_unidad = nombre_cantidad(select_name(el))
        precio_norm = precio_normal(el)
        if (len(nombre_cantidad_unidad) == 3):
            list_elements.append(
                (city, cat, subcat, nombre_cantidad_unidad[0], precio, nombre_cantidad_unidad[1], nombre_cantidad_unidad[2], precio_norm, datetime.now()))
        else:
            list_elements.append(
                (city, cat, subcat, nombre_cantidad_unidad[0], precio, nombre_cantidad_unidad[1], "", precio_norm, datetime.now()))
        # print(list_elements)
    return list_elements


def select_price(element: PageElement):
    try:
        return precio_promo(
            element.find_next(
                "div", {"class":"mb1 exito-vtex-components-4-x-alliedPrices"}
            ).find_next("span").find_next("div").find_next("div").find("div").text)
    except:
        pass
    try:
        return precio_promo(
            element.find_next(
                "div", {
                    "class": "flex f5 fw5 pa0 flex items-center justify-start w-100 search-result-exito-vtex-components-selling-price exito-vtex-components-4-x-alliedDiscountPrice"}).find("span").text)
    except:
        return ""
    


def select_name(element: PageElement):
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


def precio_normal(element: PageElement):
    try:
        precio_normal = precio_promo(
            element.find_next("del").find("span").text.strip())
        return precio_normal
    except:
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

    conn = sqlite3.connect("./Precio_Tiendas/base_de_datos/Precios.sqlite")
    cur = conn.cursor()
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
        Fecha_resultados TEXT
    );
    """
    cur.executescript(query)
    data = data.fillna("")
    data = data.astype("str")
    values = data.values
    q = "INSERT INTO Exito (Ciudad,Categoria,Sub_categoria,Nombre_producto,Precio_oferta,Cantidad,Unidad ,Precio_normal,Fecha_resultados) VALUES (?,?,?,?,?,?,?,?,?)"
    cur.executemany(q, values)
    conn.commit()
    cur.close()
    conn.close()


def main():
    df = pd.DataFrame(for_each_city(), columns=["Ciudad", "Categoria", "Sub_categoria",
                      "Nombre_producto", "Precio_oferta", "Cantidad", "Unidad ", "Precio_normal", "Fecha_resultados"])
    #df = df.drop_duplicates(subset=["Ciudad","Categoria","Nombre_producto","Precio_oferta","Cantidad","Unidad ","Precio_normal"],keep='last',ignore_index=True)
    print(df)
    to_data_base(df)
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
