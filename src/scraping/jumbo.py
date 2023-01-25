from datetime import datetime
import json, time, re, os
import pandas as pd

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

import sys
sys.path.append(".")

from src.utils.util import  Engine

MAIN_PAGE = "https://www.tiendasjumbo.co"
COLUMNS = ["Departamento", "Categoria", "Sub_categoria", "Nombre_producto", "Precio_oferta", "Cantidad",
           "Unidad", "Precio_normal", "Fecha_resultados", "Hora_resultados"]


def each_departments_categories():
    time.sleep(4)
    tries = 0
    while True:
        try:
            dep_button:WebElement = engine.element_wait_searh(20,By.XPATH,"//*[@id='menu-item-music-store']")
            ActionChains(engine.driver).click_and_hold(dep_button).perform()
            dep_element_object:list[str] = [val.text for val in 
                engine.elements_wait_searh(10,By.XPATH, "//ul[@class='tiendasjumboqaio-jumbo-main-menu-2-x-nav_menu tiendasjumboqaio-jumbo-main-menu-2-x-nav_menu--header-submenu-item']/div/div/li//a")]
            break
        except TimeoutException as e:
            if tries == 3: raise e.with_traceback(e.__traceback__)
            tries += 1
        except Exception as e:
            if tries >= 3: raise e.with_traceback(e.__traceback__)
            tries += 1
            engine.crash_refresh_page()
            engine.ready_document()

    dep_cat_elements: dict[dict[str, list[tuple[str]]]] = {}
    for el in dep_element_object:
        el =  engine.element_wait_searh(10,By.XPATH, f"//ul[@class='tiendasjumboqaio-jumbo-main-menu-2-x-nav_menu tiendasjumboqaio-jumbo-main-menu-2-x-nav_menu--header-submenu-item']/div/div/li//a[contains(text(),'{el}')]")
        text = el.text
        ActionChains(engine.driver).move_to_element(el).perform()
        time.sleep(1)
        try:
            elementos = engine.elements_wait_searh(5,By.XPATH,  "//div[@class='tiendasjumboqaio-jumbo-main-menu-2-x-submenus_wrapper tiendasjumboqaio-jumbo-main-menu-2-x-submenus_wrapper--header-submenu-item']/div/div/ul/li/div")
        except TimeoutException as _:
            continue
        dep_cat_elements[text] = {}
        for elemento in elementos:
            a: list[WebElement] = WebDriverWait(engine.driver, 10).until(
                lambda _: elemento.find_elements(By.TAG_NAME , "a")
            )
            if a[0].get_attribute("href") == "":
                continue
            dep_cat_elements[text][a[0].text] = \
                [(val.text, val.get_attribute("href")) \
                 for val in a[1:] \
                     if len(val.get_attribute("href").replace(MAIN_PAGE, "").split("/")) > 1]
            if len(dep_cat_elements[text][a[0].text]) == 0:
                del dep_cat_elements[text][a[0].text]
    engine.ready_document()
    row = engine.db.last_item_db()
    for dep,cats in dep_cat_elements.items():
        if row and "Departamento" in row and row["Departamento"] != dep: continue
        elif row and "Departamento" in row: del row["Departamento"]
        for cat,subs in cats.items():
            if row and "Categoria" in row and row["Categoria"] != cat: continue
            elif row and "Categoria" in row: del row["Categoria"]
            for sub, href in subs:
                if row and "Sub_categoria" in row and row["Sub_categoria"] != sub: continue
                elif row : row = None
                if len(href.replace(MAIN_PAGE, "").split("/")) == 1:
                    continue
                engine.current_url = href
                engine.ready_document()
                time.sleep(2)
                get_subcategories(dep,cat,sub)



def get_subcategories(dep,cat,sub):
    engine.ready_document()
    url = engine.current_url
    count = 1
    tries = 0
    while True:
        if (url.__contains__("page=")): engine.current_url = re.sub("\d+$","",url)+str(count)
        elif (url.__contains__("?")): engine.current_url = f"{url}&page={count}"
        else : engine.current_url = f"{url}?page={count}"
        try:
            engine.driver.get(engine.current_url)
            time.sleep(5)
            engine.ready_document()
            engine.element_wait_searh(15, By.ID,"gallery-layout-container")
            
            get_elements(dep, cat, sub)
            count+=1
            continue
        except TimeoutException:
            try:
                engine.element_wait_searh(2,By.XPATH,"//div[@class='vtex-search-result-3-x-searchNotFoundInfo flex flex-column ph9']")
                return
            except TimeoutException:
                pass
            try:
                engine.element_wait_searh(2,By.XPATH,"//p[@class='lh-copy vtex-rich-text-0-x-paragraph vtex-rich-text-0-x-paragraph--not-found-opps']")
                return
            except TimeoutException as e:
                count+=1
                continue
        except Exception as e:
            if tries == 3: raise e.with_traceback(e.__traceback__)
            tries +=1
            engine.crash_refresh_page()
            time.sleep(4)


def scroll_down(time_limit, init=0, final_heith=0):
    time.sleep(time_limit)
    if (final_heith == 0):
        final_heith = engine.driver.execute_script(
            "return document.body.scrollHeight")-heigth
    step = int(final_heith*0.03)
    for val in range(init, final_heith, step):
        engine.driver.execute_script(f"window.scrollTo(0, {val});")

def charge_elements():
    tries = 0
    while True:
        
        try:
            engine.ready_document()
            container = engine.element_wait_searh(20, By.ID,"gallery-layout-container")
            engine.driver.execute_script("arguments[0].scrollIntoView(true);", container)
            scroll_down(2, final_heith=container.size["height"])
            time.sleep(1)
            elements = engine.elements_wait_searh(
                15,By.CSS_SELECTOR,"div#gallery-layout-container > div > section > a > article")
            break
        except TimeoutException as e:
            try:
                time.sleep(2)
                WebDriverWait(engine.driver, 10).until(EC.presence_of_element_located(
                    (By.XPATH, "//div[@class='exito-search-result-4-x-containerNotFoundExito']")))
                return
            except TimeoutException:
                pass
            try:
                WebDriverWait(engine.driver, 5).until(EC.presence_of_element_located(
                    (By.XPATH, "//p[@class='lh-copy vtex-rich-text-0-x-paragraph vtex-rich-text-0-x-paragraph--not-found-opps']")))
            except TimeoutException:
                pass
            if tries == 4: raise e.with_traceback(e.__traceback__)
            if tries == 3: 
                
                engine.crash_refresh_page()
                engine.ready_document()
                time.sleep(2)
                tries +=1
            tries +=1
            try:
                engine.driver.refresh()
                time.sleep(3)
                engine.ready_document()
            except Exception as e:
                if tries==4: raise e.with_traceback(e.__traceback__)
                engine.crash_refresh_page()
                time.sleep(3)
                engine.ready_document()
                tries+=1
            
        except Exception as e:
            if tries == 3: raise e.with_traceback(e.__traceback__)
            tries +=1
            engine.crash_refresh_page()
            time.sleep(3)
            engine.ready_document()
    return elements


def get_elements(dep, cat, subcat):
    list_elements = []
    time.sleep(3)
    elements = charge_elements()
    time.sleep(2)
    for el in elements:
        try:
            engine.driver.execute_script("arguments[0].scrollIntoView(true);",el)
        except (WebDriverException,TimeoutException) as e:
            print(e,e.args)
            continue

        name = select_name(el)
        precio = precio_promo(el)
        if not precio: continue
        cant,uni = nombre_cantidad(name)
        precio_norm = precio_normal(el)
        date = datetime.now()

        list_elements.append((dep, cat, subcat, name.replace("\n"," "), precio, cant, 
                uni, precio_norm, date.date(),date.time()))

        # print(list_elements)
    df = pd.DataFrame(list_elements, columns=COLUMNS)
    engine.db.to_data_base(df)
    print(f"Productos guardados, Departamento {dep} en la categoría: {cat}, subcategoría: {subcat} a las {datetime.now()}, la cantidad de {len(df)} productos")


def precio_promo(element: WebElement):
    try:
        return get_price(
                element.find_element(By.CSS_SELECTOR,"div#items-price >div>div").text)
    except Exception as e:
        print(e, e.args); 
        return float(0)
    
def get_price(valor: str):
    exp = re.search("\d+[\.\d+]*", valor).group(0)
    return float(exp.replace(".", ""))

def select_name(element: WebElement):
    try:

        nombre_cantidad_unidad = element.find_element(By.CSS_SELECTOR,
            "span.vtex-product-summary-2-x-productBrand.vtex-product-summary-2-x-brandName.t-body").text.strip()

        return nombre_cantidad_unidad
    except Exception as e:
        print("Nombre :(", e)
        return ""

def nombre_cantidad(nom_cant: str):
    try:
        cant = re.findall("(?<= )?[xX]?\d+[(,|\.)\d+]*(?:\s*[a-zA-Z]+)", 
                         nom_cant)
        if len(cant) == 0: return "1","UN"
        elif len(cant) == 1: return re.search("\d+[(,|\.)\d+]*", cant[0]).group(0).replace(",",".").strip(),\
                re.search("(?<=[xX])?(?<=[0-9] )?[a-zA-Z]+$", cant[0]).group(0).strip()
        elif len(cant) > 1: return re.search("\d+[(,|\.)\d+]*", cant[-1]).group(0).replace(",",".").strip(),\
                re.search("(?<=[xX])?(?<=[0-9] )?[a-zA-Z]+$", cant[-1]).group(0).strip()
    except AttributeError as _:
        try:
            cant = re.search("(\d+[\.\d]*|\d+[,\d]*)\s{0,1}[a-zA-Z]+\.{0,1}", 
                         nom_cant).group(0).replace(",",".")
        except AttributeError as _:
            return "1","UN"



def precio_normal(element: WebElement):
    try:
        precio_normal = get_price(
            element.find_element(By.CSS_SELECTOR,"div#items-price > div > span:nth-child(2) > div").text)
        return precio_normal
    except Exception as e :
        return ""

def main():
    global heigth, engine
    engine = Engine(MAIN_PAGE,"Jumbo")
    time.sleep(3)
    heigth = engine.element_wait_searh(15,By.XPATH, "//div[@class='vtex-store-footer-2-x-footerLayout']").size["height"]
    each_departments_categories()
    config["Jumbo"] = True
    with open("src/assets/config.json","w") as writer:
            json.dump(config,writer)
    engine.close()

with open("src/assets/config.json","r") as json_path:
        config:dict = json.load(json_path)
