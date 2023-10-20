from gzip import decompress
import json
import traceback
from mail.send_email import send_email, erorr_msg
from src.scraper.engine import CLICK, Engine
from src.utils.util import crash_refresh_page, get_data
from datetime import datetime
import sys
import time
from sqlalchemy.exc import OperationalError
import pandas as pd
import re
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

import sys
from src.models.models import Olimpica
sys.path.append(".")

FILENAME = "olimpica_precios.xlsx"
MAIN_PAGE = "https://www.olimpica.com"
COLUMNS = ["Departamento", "Categoria", "Sub_categoria", "Nombre_producto", "Precio_oferta", "Cantidad",
           "Unidad", "Precio_normal", "Fecha_resultados", "Hora_resultados"]


def init_page():
    time.sleep(5)
    # form = engine.elements_wait_searh(
    #     20, By.XPATH, "//input[contains(@id,'react-select-input-')]")
    # form[0].send_keys("BOGOTÁ, D.C.")
    # form[0].send_keys(Keys.ENTER)
    # form[1].send_keys("Bogotá, D.C.")
    # form[1].send_keys(Keys.ENTER)

    engine.element_wait_searh(
        10, By.XPATH, "//div[@class='pr0     flex'][div[@class='pa4 pointer vtex-store-drawer-0-x-openIconContainer']]").click()
    # driver.execute_script(CLICK,WebDriverWait(driver, 10).until(
    #     EC.presence_of_element_located(
    #         (By.XPATH, "//div[@class='nowrap olimpica-advance-geolocation-0-x-bottomBarContainer']"))))


def each_departments_cat():
    global current_url_olimpica, row
    # //div[@class='pa4 pointer vtex-store-drawer-0-x-openIconContainer']
    time.sleep(2)

    engine.element_wait_click(
        25, By.XPATH, "//div[@class='pa4 pointer vtex-store-drawer-0-x-openIconContainer']")
    cat_element_object = engine.elements_wait_searh(
        20, By.XPATH, "//div[@class='olimpica-mega-menu-0-x-Level1Container']/a")
    cat_sub_elements: dict[str, list[list[str]]] = {}
    for el in cat_element_object:
        ActionChains(engine.driver).move_to_element(el).perform()
        cat_sub_elements[el.text] = [
            [ele.text, ele.get_attribute("href")] for ele in engine.elements_wait_searh(20, By.XPATH, "//div[@class='olimpica-mega-menu-0-x-Level2Container']//a")]

    list_articles = []
    row = engine.db.last_item_db()
    for cat, subs in cat_sub_elements.items():
        print(cat, row)
        if row and "categoria" in row and row["categoria"] != cat:
            continue
        if row and "categoria" in row:
            del row["categoria"]
        for sub in subs:
            print(sub, row)
            if row and "sub_categoria" in row and row["sub_categoria"] != sub[0]:
                continue
            if row and "sub_categoria" in row:
                del row["sub_categoria"]
            save_data(cat, *sub)


def save_data(cat, sub, link):
    count = 1
    while True:
        if (link.__contains__("page=")):
            link = re.sub("\d+$", "", link)+str(count)
        elif (link.__contains__("?")):
            link = f"{link}&page={count}"
        else:
            link = f"{link}?page={count}"

        while True:
            try:
                engine.driver.get(link)
                break
            except TimeoutException:
                engine.driver.refresh()
                time.sleep(3)

        time.sleep(5)
        try:
            elementos_cargados()
            extract_files(cat, sub, get_data(engine, Olimpica))
            extract_files(cat, sub, get_data_require(engine))
            count += 1

        except TimeoutException:
            traceback.print_exception(*sys.exc_info())
            try:
                engine.element_wait_searh(
                    3, By.XPATH, "//div[@class='vtex-search-result-3-x-searchNotFoundInfo flex flex-column ph9']")
                break
            except TimeoutException:
                engine.driver.refresh()
                time.sleep(2)


def get_data_require(engine):
    data_sql = engine.db.consulta_sql([Olimpica.nombre_producto],
                                      [Olimpica.fecha_resultados == datetime.now().date()])
    nombre_sql = set(
        [product for sub_data in data_sql for product in sub_data])
    json_data = []
    for req in engine.driver.requests:
        if req.response:
            resp = req.response
            data = {}
            json_data = []
            if resp.headers.get("content-type", None) and 'application/json' in resp.headers.get("content-type"):
                try:
                    data = json.loads(resp.body)
                except:
                    try:
                        data = json.loads(decompress(resp.body))
                        # print(resp.body.decode(errors='ignore'))
                    except:
                        pass
                try:
                    if "data" in data and "productSearch" in data["data"]:
                        json_data = data["data"]["productSearch"]["products"]
                    elif "data" in data and "productsByIdentifier" in data["data"] \
                            and "productName" in data["data"]["productsByIdentifier"][0]:
                        json_data = data["data"]["productsByIdentifier"]

                except TypeError:
                    pass

                if json_data:
                    nombre_data = set([product["productName"]
                                      for product in json_data])
                    if nombre_data.issubset(nombre_sql):
                        continue
                    else:
                        break
    return []


def extract_files(cat, sub, products: list):
    new_data = []
    for product in products:
        categoria = cat
        sub_categoria = sub
        nombre_producto = product["productName"]
        precio_bajo = product["priceRange"]["sellingPrice"]["lowPrice"]
        precio_alto = product["priceRange"]["sellingPrice"]["lowPrice"]
        if not precio_bajo or not precio_alto:
            precio_bajo = product["priceRange"]["listPrice"]["lowPrice"]
            precio_alto = product["priceRange"]["listPrice"]["lowPrice"]
        cantidad, unidad = cant_uni(nombre_producto)
        precio_alto, precio_bajo = map(lambda x: float(
            x) if x else 0, [precio_alto, precio_bajo])
        if precio_bajo == precio_alto == 0:
            continue
        new_data.append({"categoria": categoria, "sub_categoria": sub_categoria,
                        "nombre_producto": nombre_producto, "precio_bajo": precio_bajo, "precio_alto": precio_alto, "cantidad": cantidad, "unidad": unidad})
    print(new_data)
    if len(new_data) > 0:
        engine.db.save_data(engine.db.engine, Olimpica, new_data)


def scroll_down(final):

    step = int(final*0.009)
    for val in range(0, final, step):
        driver.execute_script(f"window.scrollTo(0, {val});")


def elementos_cargados():
    WebDriverWait(engine.driver, 10).until(EC.presence_of_element_located(
        (By.XPATH, "//span[@class='vtex-product-summary-2-x-productBrand vtex-product-summary-2-x-brandName t-body']")))


def precio_promo(element: WebElement):
    try:  # div/div/div/div[4]/div[2]/div/span
        return get_price(
            element.find_element(
                By.CSS_SELECTOR, "div:nth-child(2) > div:nth-child(1) > div > div > span").text
        )
    except Exception as e:
        return None


def get_price(valor: str):
    exp = re.search("\d+[\.\d+]*", valor).group(0)
    return float(exp.replace(".", ""))


def select_name(element: WebElement):
    try:
        nombre_cantidad_unidad = element.find_element(
            By.CSS_SELECTOR, "div > div > h3 > span").text.strip()
    except:
        print("NO se encontró el nombre")
        return ""
    return nombre_cantidad_unidad


def cant_uni(nom_cant: str):
    try:
        cant = re.findall("(?<= )\d+[,\d+]*",
                          nom_cant.replace("  ", " "))
        if len(cant) == 0:
            cant = re.search("(?<=X)\d+", nom_cant.replace("  ", " ")).group(0)
            return cant, 'UN'
        elif len(cant) > 1:
            cant = cant[1]
        else:
            cant = cant[0]
        uni = re.findall(
            "(?:(?<=\d[,|\.])(?:\d+\s*)|(?<= )(?:\d+\s*))[a-zA-Z]+", nom_cant.replace("  ", " "))
        if len(uni) > 1:
            uni = re.search("[a-zA-Z]+", uni[1]).group(0)
        else:
            uni = re.search("[a-zA-Z]+", uni[0]).group(0)
    except (AttributeError, IndexError) as _:
        return "1", "UN"

    return cant, uni


def precio_normal(element: WebElement):
    try:
        precio_normal = get_price(
            element.find_element(
                By.XPATH, "//div[@class='olimpica-dinamic-flags-0-x-strikePrice false']/span").text.strip())
        return precio_normal
    except Exception as e:
        return ""


def main():
    global engine
    engine = Engine(current_url_olimpica, Olimpica)
    engine.db.model.metadata.create_all(engine.db.engine)
    lenth["Cantidad"] = engine.db.consulta_sql_query_one(
        "select count(*) as count from Olimpica;")["count"]
    init_page()
    time.sleep(2)
    engine.driver.execute_script(
        "window.scrollTo(0, document.body.scrollHeight)")

    each_departments_cat()
    send_email("Olimipica", lenth)
    engine.close()


row = None
lenth = {}
current_url_olimpica = MAIN_PAGE
