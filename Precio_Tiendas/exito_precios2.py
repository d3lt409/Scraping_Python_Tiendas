from datetime import datetime
import json
import time,re,sqlalchemy,gc
from typing import Tuple

from bs4 import BeautifulSoup
import pandas as pd
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from Util import init_scraping,ready_document,crash_refresh_page

FILENAME = "exito_precios.xlsx"
MAIN_PAGE = "https://www.exito.com"
LIST_CITY = ["Bogota"]  # ,"Medellin","Barranquilla","Cali","Cartagena","Armenia","Bello","Bucaramanga","Chia","Cucuta","Fusagasuga","Ibage","La ceja","Manizales","Monteria","Neiva","Pasto","Pereita","Popayan","Rionegro","Santa marta", "Sincelejo","Soacha","Tunja","Valledupar","Villavicencio","Zipaquira"]
COLUMNS = ["Departamento", "Categoria", "Sub_categoria", "Nombre_producto", "Precio_oferta", "Cantidad", 
           "Unidad", "Precio_normal", "Fecha_resultados","Hora_resultados"]

with open("config.json","r") as json_path:
    config:dict = json.load(json_path)

current_url = MAIN_PAGE
driver = init_scraping(current_url)
heigth: int = WebDriverWait(driver, 20).until(EC.presence_of_element_located(
        (By.XPATH, "/html/body/div[2]/div/div[1]/div/div[5]"))).size["height"]

def for_each_city():
    list_products = []
    
    list_products += each_departamentos("Bogota")
    driver.close()
    return list_products


def each_departamentos(city: str):
    global current_url,driver
    ready_document(driver)
    dep_elements:list[WebElement] = WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located(
            (By.XPATH, "//div[@class='exito-header-3-x-dropdownitem exito-header-3-x-categoryOption']")))
    departamentos: list[tuple[str]] = [
        (dep.get_attribute('id'), dep.get_attribute('innerHTML')) for dep in dep_elements]
    list_articles =[]
    for dep in departamentos:
        current_url = link_departamento = f"{MAIN_PAGE}/{dep[0]}"
        driver.get(current_url)
        ready_document(driver)
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
            driver = crash_refresh_page(driver,current_url)
            
        list_articles += categories(link_departamento, dep)
    return list_articles


def categories(link_departamento:str, departamento: Tuple[str]):
    global current_url,driver
    WebDriverWait(driver,30).until(
        EC.presence_of_element_located(
            (By.XPATH,"//div[@class='vtex-flex-layout-0-x-flexRow vtex-flex-layout-0-x-flexRow--search-result-web']//div[@id='imagen']")))
    ready_document(driver)
    scroll_down(2)
    cat_view:WebElement = WebDriverWait(driver, 50).until(EC.presence_of_element_located(
        (By.XPATH, "//div[contains(@class,'--category-2')]/div[2]/div/div")))
    driver.execute_script("arguments[0].scrollIntoView(true);",cat_view)
    list_elements = []
    time.sleep(2)
    cat_objects:list[WebElement] = WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located(
        (By.XPATH, "//div[contains(@class,'--category-2')]/div[2]/div/div/div/div/div/input")))
    categories: list[str] = [
        cat.get_attribute("id").replace("category-2-", "") for cat in cat_objects]
    for cat in categories:
        try:
            current_url = f"{link_departamento}/{cat}?fuzzy=0&initialMap=c&initialQuery={departamento[0]}&map=category-1,category-2&operator=and"
            driver.get(current_url)
            list_elements += sub_categories(link_departamento,cat,departamento)
        except WebDriverException as _:
            driver = crash_refresh_page(driver,current_url)
            
    return list_elements


def sub_categories(link_departamento,categoria: str,departamento):
    global current_url
    ready_document(driver)
    listado = []
    subcat_view:WebElement = WebDriverWait(driver, 50).until(EC.presence_of_element_located(
        (By.XPATH, "//div[contains(@class,'--category-3')]")))
    driver.execute_script("arguments[0].scrollIntoView(true);",subcat_view)
    time.sleep(2)
    sub_cat_object: list[WebElement] = WebDriverWait(driver, 50).until(
        EC.presence_of_all_elements_located((By.XPATH, 
                    "//div[contains(@class,'--category-3')]/div[2]/div/div/div/div/div/input")))
    sub_categories: list[str] = [cat.get_attribute("id").replace("category-3-", "") for cat in sub_cat_object]
    for subcat in sub_categories:
        count = 1
        while True:
            current_url = f"{link_departamento}/{categoria}/{subcat}?fuzzy=0&initialMap=c&initialQuery={departamento[0]}&map=category-1,category-2,category-3=and&page={count}"
            driver.get(current_url)
            ready_document(driver)
            try:
                WebDriverWait(driver, 30).until(EC.presence_of_element_located(
                    (By.XPATH, "//h2[@class='tc fw1 exito-search-result-4-x-notFoundText']")))
                break
            except TimeoutException:
                pass
            listado += get_elements(departamento[1],categoria,subcat)
            count+=1
    return listado
            


def scroll_down(time_limit,init=0,final_heith= 0):
    time.sleep(time_limit)
    if (final_heith == 0):
        final_heith = driver.execute_script("return document.body.scrollHeight")-heigth
    step = int(final_heith*0.003)
    for val in range(init,final_heith,step):
        driver.execute_script(f"window.scrollTo(0, {val});")
    # if driver.execute_script("return document.body.scrollHeight")-final_heith >heigth:
    #     scroll_down(0,init=final_heith)

def elementos_cargados():
    global driver
    tries = 0
    while tries < 3:
        try:
            WebDriverWait(driver,30).until(EC.presence_of_element_located((By.XPATH,
                    "//div[@class='exito-filters-0-x-filters--layout ']")))
            break
        except TimeoutException as _:
            tries +=1
            driver = crash_refresh_page(driver,current_url)
            ready_document(driver)
    return tries


def get_elements(dep, cat, subcat):
    ready_document(driver)
    if elementos_cargados() == 3: return []
    try:
        container:WebElement = WebDriverWait(
            driver, 50).until(EC.presence_of_element_located((By.ID, "gallery-layout-container")))
        driver.execute_script("arguments[0].scrollIntoView(true);", container)
        final_height: WebElement = WebDriverWait(driver, 30).until(EC.presence_of_element_located(
                (By.XPATH, "//div[@class='vtex-flex-layout-0-x-flexRow vtex-flex-layout-0-x-flexRow--search-result-web']")))
        scroll_down(2,final_heith=final_height.size["height"])
        elements: list[WebElement] = WebDriverWait(driver,10).until(lambda _: 
                container.find_elements_by_xpath("div/section/a/article/div[3]/div[2]"))
        list_elements = []
    except WebDriverException as _:
        driver.refresh()
        time.sleep(2)
        ready_document(driver)
        container:WebElement = WebDriverWait(
            driver, 50).until(EC.presence_of_element_located((By.ID, "gallery-layout-container")))
        # driver.execute_script("arguments[0].scrollIntoView(true);", container)
        elements: list[WebElement] = WebDriverWait(driver,10).until(lambda _: 
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
        UNIQUE(Nombre_producto,Fecha_resultados) ON CONFLICT IGNORE
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
