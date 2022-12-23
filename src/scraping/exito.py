import sys
sys.path.append(".")
from src.utils.util import (
    init_scraping, ready_document, 
    crash_refresh_page)
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
    driver.close()


def each_departments_cat_sub(city: str):
    global current_url_exito, driver
    ready_document(driver, current_url_exito)
    tries = 0
    while True:
        try:
            dep_button: WebElement = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "category-menu")))
            dep_button.click()
            dep_element_object: list[WebElement] = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//p[contains(@id,'undefined-nivel2-')]")))
            break
        except TimeoutException as e:
            if tries == 3: 
                if tries == 5: raise e.with_traceback(e.__traceback__)
                tries+=1
                driver = crash_refresh_page(driver,current_url_exito)
                ready_document(driver,current_url_exito)
            tries += 1
            driver.refresh()
        except Exception as e:
            if tries >= 3: raise e.with_traceback(e.__traceback__)
            tries += 1
            driver = crash_refresh_page(driver,current_url_exito)
            ready_document(driver,current_url_exito)

    
    dep_cat_elements: dict[dict[str, list[tuple[str]]]] = {}
    for el in dep_element_object:
        ActionChains(driver).move_to_element(el).perform()
        elementos: list[WebElement] = WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located(
            (By.XPATH, "//div[@class='exito-category-menu-3-x-itemSideMenu']")))
        dep_cat_elements[el.text] = {}
        for elemento in elementos:
            a: list[WebElement] = WebDriverWait(driver, 20).until(
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

    ready_document(driver, current_url_exito)
    row = db.last_item_db()
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
                current_url_exito = href
                while True:
                    try:
                        driver.get(current_url_exito)
                        break
                    except WebDriverException as _:
                        driver = crash_refresh_page(driver, current_url_exito)
                        ready_document(driver,current_url_exito)
                ready_document(driver, current_url_exito)
                sub_categories(dep, cat, sub)



def sub_categories(departamento, categoria: str, subcategoria):
    global current_url_exito
    ready_document(driver, current_url_exito)
    count = 1
    url = current_url_exito
    tries = 0
    while True:
        if (current_url_exito.__contains__("page=")):
            current_url_exito = re.sub(
                "\d+$", "", current_url_exito)+str(count)
        elif (current_url_exito.__contains__("?")):
            current_url_exito = f"{url}&page={count}"
        else:
            current_url_exito = f"{url}?page={count}"
        try:
            driver.get(current_url_exito)
            ready_document(driver, current_url_exito)
            WebDriverWait(driver, 20).until(EC.presence_of_element_located(
                (By.XPATH, "//div[@class='vtex-flex-layout-0-x-flexRow vtex-flex-layout-0-x-flexRow--search-result-web']")))
        except TimeoutException as _:
            if tries == 2:
                return []
            tries += 1
            driver.refresh()
            time.sleep(3)
            continue
        try:
            WebDriverWait(driver, 3).until(EC.presence_of_element_located(
                (By.XPATH, "//div[@class='exito-search-result-4-x-containerNotFoundExito']")))
            break
        except TimeoutException:
            pass
        get_elements(departamento, categoria, subcategoria)
        count += 1


def scroll_down(time_limit, init=0, final_heith=0):
    time.sleep(time_limit)
    if (final_heith == 0):
        final_heith = driver.execute_script(
            "return document.body.scrollHeight")-heigth
    step = int(final_heith*0.01)
    for val in range(init, final_heith, step):
        driver.execute_script(f"window.scrollTo(0, {val});")




def get_elements(dep, cat, subcat):
    global driver
    time.sleep(2)
    ready_document(driver, current_url_exito)
    list_elements = []
    tries = 1
    while True:
        try:
            container: WebElement = WebDriverWait(
                driver, 20).until(EC.presence_of_element_located((By.ID, "gallery-layout-container")))

            driver.execute_script("arguments[0].scrollIntoView(true);", container)

            final_height: WebElement = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, "//div[@class='vtex-flex-layout-0-x-flexRow vtex-flex-layout-0-x-flexRow--search-result-web']")))
            scroll_down(2, final_heith=final_height.size["height"])
            time.sleep(1)
            elements: list[WebElement] = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div#gallery-layout-container > div > section > a > article")))
            break
        except TimeoutException as e:
            if tries == 3: 
                try:
                    WebDriverWait(driver, 5).until(EC.presence_of_element_located(
                        (By.XPATH, "//div[@class='exito-search-result-4-x-containerNotFoundExito']")))
                    return
                except TimeoutException:
                    pass
                driver = crash_refresh_page(driver,current_url_exito)
                time.sleep(2)
            tries+= 1
            driver.refresh()
            ready_document(driver, current_url_exito)
        except (WebDriverException,StaleElementReferenceException) as e:
            if tries == 3: raise e.with_traceback(e.__traceback__)
            tries+=1
            driver = crash_refresh_page(driver,current_url_exito)
            time.sleep(2)
            ready_document(driver, current_url_exito)
    time.sleep(2)
    for el in elements:
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", el)
        except (WebDriverException, TimeoutException) as e:
            print(e, e.args)
            continue
        
        name = select_name(el)
        print(name, current_url_exito)
        precio = select_price(el)
        cant,uni = cant_uni(name)
        precio_norm = precio_normal(el)
        date = datetime.now()

        list_elements.append(
            (dep, cat, subcat, name.replace("\n", " "), precio, cant,
                 uni, precio_norm, date.date(), date.time()))

    df = pd.DataFrame(list_elements, columns=COLUMNS)
    db.to_data_base(df)
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
    try:
        return precio_promo(
            element.find_next(
                "div", {"class": "exito-vtex-components-4-x-PricePDP"}).find("span").text)
    except Exception as e:
        print(e, e.args);e.with_traceback(e.__traceback__)


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
    except (NoSuchElementException, StaleElementReferenceException) as _:
        return ""
    if el: return precio_promo(el.text.strip())
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
    # try:
    for_each_city()
    # except Exception as e:
    #     e.with_traceback(e.__traceback__)


try:
    with open("src/assets/config.json", "r") as json_path:
        config: dict = json.load(json_path)
    if config["Exito"]: print("Completo");exit()
    current_url_exito = MAIN_PAGE
    driver,db = init_scraping(current_url_exito, 'Exito')
    heigth: int = WebDriverWait(driver, 15).until(EC.presence_of_element_located(
        (By.XPATH, "/html/body/div[2]/div/div[1]/div/div[5]"))).size["height"]

    
except KeyboardInterrupt as _:
    pass
main()
gc.collect(2)
