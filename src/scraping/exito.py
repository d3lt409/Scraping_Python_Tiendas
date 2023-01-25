import sys
sys.path.append(".")
from src.utils.util import (
    Engine)
from datetime import datetime
import json
import time
import re
import gc
import pandas as pd
from selenium.common.exceptions import TimeoutException, WebDriverException,NoSuchElementException,StaleElementReferenceException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains



FILENAME = "exito_precios.xlsx"
MAIN_PAGE = "https://www.exito.com/"
LIST_CITY = ["Bogota"]  # ,"Medellin","Barranquilla","Cali","Cartagena","Armenia","Bello","Bucaramanga","Chia","Cucuta","Fusagasuga","Ibage","La ceja","Manizales","Monteria","Neiva","Pasto","Pereita","Popayan","Rionegro","Santa marta", "Sincelejo","Soacha","Tunja","Valledupar","Villavicencio","Zipaquira"]
COLUMNS = ["Departamento", "Categoria", "Sub_categoria", "Nombre_producto", "Precio_oferta", "Cantidad",
           "Unidad", "Precio_normal", "Fecha_resultados", "Hora_resultados"]


def for_each_city():
    each_departments_cat_sub("Bogota")
    config["Exito"] = True
    with open("src/assets/config.json", "w") as writer:
        json.dump(config, writer)
    engine.driver.close()


def each_departments_cat_sub(city: str):
    time.sleep(3)
    tries = 0
    while True:
        try:
            time.sleep(4)
            dep_button = engine.element_wait_searh(20,By.ID, "category-menu")
            dep_button.click()
            dep_element_object = engine.elements_wait_searh(20,By.XPATH, "//p[contains(@id,'undefined-nivel2-')]")
            break
        except TimeoutException as e:
            if tries == 3: 
                if tries == 5: raise e.with_traceback(e.__traceback__)
                tries+=1
                engine.crash_refresh_page()
                engine.ready_document()
            tries += 1
            engine.driver.refresh()
        except Exception as e:
            if tries >= 3: raise e.with_traceback(e.__traceback__)
            tries += 1
            engine.crash_refresh_page()
            engine.ready_document()

    
    dep_cat_elements: dict[dict[str, list[tuple[str]]]] = {}
    for el in dep_element_object:
        ActionChains(engine.driver).move_to_element(el).perform()
        elementos = engine.elements_wait_searh(20,By.XPATH, "//div[@class='exito-category-menu-3-x-itemSideMenu']")
        dep_cat_elements[el.text] = {}
        for elemento in elementos:
            a: list[WebElement] = WebDriverWait(engine.driver, 20).until(
                lambda _: elemento.find_elements(By.TAG_NAME , "a")
            )
            if a[0].get_attribute("href") == "":
                continue

            dep_cat_elements[el.text][a[0].text] = \
                [(val.text, val.get_attribute("href")) \
                 for val in a[1:] \
                     if len(val.get_attribute("href").replace(MAIN_PAGE, "").split("/")) > 1]
            if len(dep_cat_elements[el.text][a[0].text]) == 0:
                del dep_cat_elements[el.text][a[0].text]

    engine.ready_document()
    row = engine.db.last_item_db()
    for dep, cats in dep_cat_elements.items():
        if row and "Departamento" in row and row["Departamento"] != dep: continue
        elif row and "Departamento" in row: del row["Departamento"]
        for cat, subs in cats.items():
            if row and "Categoria" in row and row["Categoria"] != cat: continue
            elif row and "Categoria" in row: del row["Categoria"]

            for sub, href in subs:
                if row and "Sub_categoria" in row and row["Sub_categoria"] != sub: continue
                elif row : row = None
                if len(href.replace(MAIN_PAGE, "").split("/")) == 1 or sub == "Ver todo":
                    continue
                engine.current_url = href
                engine.ready_document()
                sub_categories(dep, cat, sub)



def sub_categories(departamento, categoria: str, subcategoria):
    engine.ready_document()
    count = 1
    url = engine.current_url
    tries = 0
    while True:
        if (engine.current_url.__contains__("page=")): engine.current_url = re.sub("\d+$", "", engine.current_url)+str(count)
        elif (engine.current_url.__contains__("?")): engine.current_url = f"{url}&page={count}"
        else: engine.current_url = f"{url}?page={count}"
        try:
            engine.driver.get(engine.current_url)
            engine.ready_document()
            engine.element_wait_searh(
                20,By.XPATH, "//*[@id='gallery-layout-container']")
            get_elements(departamento, categoria, subcategoria)
            count += 1
        except TimeoutException as _:
            try:
                engine.element_wait_searh(3,By.XPATH, "//div[@class='exito-search-result-4-x-containerNotFoundExito']")
                return
            except TimeoutException:
                if tries == 2:
                    return []
                tries += 1
                engine.driver.refresh()
                time.sleep(3)
                continue

        


def scroll_down(time_limit, init=0, final_heith=0):
    time.sleep(time_limit)
    if (final_heith == 0):
        final_heith = engine.driver.execute_script(
            "return document.body.scrollHeight")-heigth
    step = int(final_heith*0.03)
    for val in range(init, final_heith, step):
        engine.driver.execute_script(f"window.scrollTo(0, {val});")


def charge_elements():
    tries = 1
    while True:
        try:
            engine.ready_document()
            container = engine.element_wait_searh(20,By.ID, "gallery-layout-container")
            engine.driver.execute_script("arguments[0].scrollIntoView(true);", container)

            final_height = engine.element_wait_searh(
                10,By.XPATH, "//div[@class='vtex-flex-layout-0-x-flexRow vtex-flex-layout-0-x-flexRow--search-result-web']")
            scroll_down(2, final_heith=final_height.size["height"])
            time.sleep(1)
            elements = engine.elements_wait_searh(10,By.CSS_SELECTOR, "div#gallery-layout-container > div > section > a > article")
            break
        except TimeoutException as e:
            if tries == 3: 
                try:
                    engine.element_wait_searh(15,By.XPATH, "//div[@class='exito-search-result-4-x-containerNotFoundExito']")
                    return
                except TimeoutException:
                    pass
                engine.crash_refresh_page()
                time.sleep(2)
            tries+= 1
            engine.driver.refresh()
            engine.ready_document()
        except Exception as e:
            if tries == 3: raise e.with_traceback(e.__traceback__)
            tries+=1
            engine.crash_refresh_page()
            time.sleep(2)
            engine.ready_document()
    return elements


def get_elements(dep, cat, subcat):
    global driver
    time.sleep(3)
    list_elements = []
    elements = charge_elements()
    if not elements: return
    time.sleep(2)
    for el in elements:
        try:
            engine.driver.execute_script("arguments[0].scrollIntoView(true);", el)
        except (WebDriverException, TimeoutException) as e:
            print(e, e.args)
            continue
        
        name = select_name(el)
        print(name)
        precio = select_price(el)
        cant,uni = cant_uni(name)
        precio_norm = precio_normal(el)
        date = datetime.now()

        list_elements.append((dep, cat, subcat, name.replace("\n", " "), precio, cant,
                 uni, precio_norm, date.date(), date.time()))

    df = pd.DataFrame(list_elements, columns=COLUMNS)
    engine.db.to_data_base(df)
    print(
        f"Productos guardados, para la categoría {cat} y subcategoría {subcat} a las {datetime.now()}")


def select_price(element: WebElement):
    try:  # div/div/div/div[4]/div[2]/div/span
        return precio_promo(
            element.find_element(
                By.CSS_SELECTOR,"div.exito-vtex-components-4-x-selling-price.flex.items-center> div > span").text.strip()
        )
    except Exception as e:
        print(e, e.args); 
        return float(0)



def select_name(element: WebElement):
    try:
        nombre_cantidad_unidad = element.find_element(By.CSS_SELECTOR,"div > div > h3 > span").text.strip()
        return nombre_cantidad_unidad
    except:
        pass
    try:
        nombre_cantidad_unidad = element.find_element(
            By.CSS_SELECTOR,  "div.exito-product-details-3-x-stylePlp").text.strip()
        return nombre_cantidad_unidad
    except:
        print("No se encontró el nombre")
    
    return ""
    

def precio_normal(element: WebElement):
    try:
        el =  element.find_element(
                By.CSS_SELECTOR,"div.exito-vtex-components-4-x-list-price.t-mini.ttn.strike > span")
    except (WebDriverException) as _:
        return ""
    if el: 
        try:
            return precio_promo(el.text.strip())
        except WebDriverException as _:
            return ""
    else: ""


def precio_promo(valor: str):
    exp = re.search("\d+[\.\d+]*", valor).group(0)
    return float(exp.replace(".", ""))


def cant_uni(nom_cant: str):
    nom_cant = nom_cant.replace(" T/L/D TODOS LOS DIAS SIN REF", "")

    cant = re.findall(
        "(?<= )\d+[(,|\.)\d+]*(?:\s*[a-zA-Z]+)", nom_cant)
    if len(cant) == 0: return "1","UN"
    elif len(cant) == 1: 
        return re.search("\d+[(,|\.)\d+]*", cant[0]).group(0).replace(",",".").strip(),\
                re.search("[a-zA-Z]+", cant[0]).group(0).strip()
    elif len(cant) > 1: 
        return re.search("\d+[(,|\.)\d+]*", cant[-1]).group(0).replace(",",".").strip(),\
                re.search("[a-zA-Z]+", cant[-1]).group(0).strip()
    


def main():
    global engine, heigth
    try:
        engine = Engine(MAIN_PAGE, 'Exito')
        engine.ready_document()
        heigth = engine.element_wait_searh(15,By.XPATH,"/html/body/div[2]/div/div[1]/div/div[5]").size["height"]
        for_each_city()
        engine.close()
    except KeyboardInterrupt as _:
        pass

with open("src/assets/config.json", "r") as json_path:
        config: dict = json.load(json_path)

    
