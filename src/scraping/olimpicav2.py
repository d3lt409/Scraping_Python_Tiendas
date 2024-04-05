from gzip import decompress
import json
import traceback

import selenium
from src.scraper.engine.constants import FIREFOX
from src.scraper.engine.engine import Engine
from datetime import datetime
import sys
import time

import re
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from urllib3.exceptions import ProtocolError

import sys
from src.models.models import Olimpica
# from src.utils.util import get_data, get_data_firefox, get_data_firefoxV2
sys.path.append(".")

FILENAME = "olimpica_precios.xlsx"
MAIN_PAGE = "https://www.olimpica.com"
COLUMNS = ["Departamento", "Categoria", "Sub_categoria", "Nombre_producto", "Precio_oferta", "Cantidad",
           "Unidad", "Precio_normal", "Fecha_resultados", "Hora_resultados"]


def init_page():
    time.sleep(5)
    # form = engine.elements_wait_search(
    #     20, By.XPATH, "//input[contains(@id,'react-select-input-')]")
    # form[0].send_keys("BOGOTÁ, D.C.")
    # form[0].send_keys(Keys.ENTER)
    # form[1].send_keys("Bogotá, D.C.")
    # form[1].send_keys(Keys.ENTER)

    engine.element_wait_search(
        10, By.XPATH, "//div[@class='pr0     flex'][div[@class='pa4 pointer vtex-store-drawer-0-x-openIconContainer']]").click()
    # driver.execute_script(CLICK,WebDriverWait(driver, 10).until(
    #     EC.presence_of_element_located(
    #         (By.XPATH, "//div[@class='nowrap olimpica-advance-geolocation-0-x-bottomBarContainer']"))))


def each_departments_cat():
    global current_url_olimpica, row
    # //div[@class='pa4 pointer vtex-store-drawer-0-x-openIconContainer']
    time.sleep(2)

    engine.element_wait_click(
        25, By.XPATH, "//div[contains(@class,'pa4 pointer vtex-store-drawer-0-x-openIconContainer')]")
    cat_element_object = engine.elements_wait_search(
        20, By.XPATH, "//div[contains(@class,'olimpica-mega-menu-0-x-second_level_menu')]")
    cat_sub_elements: dict[str, dict[str:list]] = {}
    for el in cat_element_object:

        el: WebElement
        cat = el.find_element(By.XPATH, ".//h1").get_attribute("textContent")
        sub_cats_object = el.find_elements(
            By.XPATH, ".//ul[@class= 'olimpica-mega-menu-0-x-second_level_list']")
        sub_cats = {}
        for sub_cat_object in sub_cats_object:
            sub_cat = sub_cat_object.find_element(
                By.XPATH, ".//h2/a")
            links = sub_cat_object.find_elements(
                By.XPATH, ".//h3/a")
            sub_cats[sub_cat.get_attribute("textContent")] = [
                ele.get_attribute("href") for ele in links]
        cat_sub_elements[cat] = sub_cats

    # for cat, sub in cat_sub_elements.items():
    #     print(cat)
    #     print(sub.keys())
    # exit()
    row = engine.db.last_item_db()
    for cat, subs in cat_sub_elements.items():
        print(cat, row)
        if row and "categoria" in row and row["categoria"] != cat:
            continue
        if row and "categoria" in row:
            del row["categoria"]
        for sub, links in subs.items():
            print(sub, row)
            if row and "sub_categoria" in row and row["sub_categoria"] != sub:
                continue
            if row and "sub_categoria" in row:
                del row["sub_categoria"]
            for link in links:
                save_data(cat, sub, link)


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

        try:

            elementos_cargados()
            esperar_carga()
            # get_data_firefoxV2(engine, Olimpica, engine.proxy)
            extract_files(cat, sub, get_data_require(engine))
            extract_files(cat, sub, get_data(engine, Olimpica))
            # extract_files(cat, sub, get_data_require(engine, cat))
            count += 1

        except selenium.common.exceptions.StaleElementReferenceException as e:
            continue
        except TimeoutException:
            # traceback.print_exception(*sys.exc_info())
            try:
                engine.element_wait_search(
                    3, By.XPATH, "//div[@class='vtex-search-result-3-x-searchNotFoundInfo flex flex-column ph9']")
                break
            except TimeoutException:
                engine.driver.refresh()
                time.sleep(2)


# Función para extraer datos
def scrape_data(engine: Engine):
    for request in engine.driver.requests:
        if request.response:
            if request.response.headers['Content-Type'] == 'application/json':
                json_data = json.loads(request.response.body)
                # extraer y procesar datos
                print(json_data['products'])


def get_data(engine, model):

    # time.sleep(4)
    # Obtener los registros de rendimiento
    logs_raw = engine.driver.get_log("performance")
    logs = [json.loads(lr["message"])["message"] for lr in logs_raw if "Network.response" in json.loads(
        lr["message"])["message"]["method"]]

    # Filtrar los logs para encontrar las respuestas JSON
    def log_filter(log_):
        if "response" in log_["params"]:
            return "json" in log_["params"]["response"]["mimeType"]
        return False

    json_logs = filter(log_filter, logs)

    json_data = []
    data_sql = engine.db.consulta_sql([model.nombre_producto],
                                      [model.fecha_resultados == datetime.now().date()])
    nombre_sql = set(
        [product for sub_data in data_sql for product in sub_data])
    for i, log in enumerate(json_logs):
        request_id = log["params"]["requestId"]
        # json_data = []
        try:
            json_response = engine.driver.execute_cdp_cmd(
                "Network.getResponseBody", {"requestId": request_id})
            data = json.loads(json_response["body"])
            try:
                if "data" in data and "productSearch" in data["data"]:
                    json_data += data["data"]["productSearch"]["products"]
                elif "data" in data and "productsByIdentifier" in data["data"] \
                        and "productName" in data["data"]["productsByIdentifier"][0]:
                    json_data += data["data"]["productsByIdentifier"]

            except TypeError:
                pass

        except Exception as e:
            pass
    if len(json_data) > 0:

        json_data = [product
                     for product in json_data if product["productName"] not in nombre_sql]

    return json_data


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
                        json_data += data["data"]["productSearch"]["products"]
                    elif "data" in data and "productsByIdentifier" in data["data"] \
                            and "productName" in data["data"]["productsByIdentifier"][0]:
                        json_data += data["data"]["productsByIdentifier"]

                except TypeError:
                    pass
    if len(json_data) > 0:

        json_data = [product
                     for product in json_data if product["productName"] not in nombre_sql]
    return json_data

# def get_data_require(engine, cat):
#     data_sql = engine.db.consulta_sql([Olimpica.nombre_producto],
#                                       [Olimpica.fecha_resultados == datetime.now().date()])
#     nombre_sql = set(
#         [product for sub_data in data_sql for product in sub_data])
#     json_data = []
#     for req in engine.driver.requests:

#         if req.response:
#             resp = req.response
#             data = {}
#             # json_data = []
#             if resp.headers.get("content-type", None) and 'application/json' in resp.headers.get("content-type"):
#                 try:
#                     data = json.loads(resp.body)
#                 except:
#                     try:
#                         data = json.loads(decompress(resp.body))
#                     except:
#                         pass
#                 try:
#                     if (
#                         # cat.lower() in resp.body.lower() and
#                             "data" in data and "product" in data["data"] and "productName" in data["data"]["product"]):
#                         json_data.append(data["data"]["product"])

#                 except TypeError:
#                     pass

#     if len(json_data) > 0:
#         json_data = [product
#                      for product in json_data if product["productName"] not in nombre_sql]

#     return json_data


def extract_files(cat, sub, products: list):
    new_data = []
    print(len(products))
    for product in products:
        categoria = cat
        sub_categoria = sub
        nombre_producto = product["productName"]
        precio_bajo = product["items"][0]["sellers"][0]["commertialOffer"]["Price"]
        precio_alto = product["items"][0]["sellers"][0]["commertialOffer"]["PriceWithoutDiscount"]
        cantidad, unidad = cant_uni(nombre_producto)
        precio_alto, precio_bajo = map(lambda x: float(
            x) if x else 0, [precio_alto, precio_bajo])
        if precio_bajo == precio_alto == 0:
            continue
        new_data.append({"categoria": categoria, "sub_categoria": sub_categoria,
                        "nombre_producto": nombre_producto, "precio_bajo": precio_bajo, "precio_alto": precio_alto, "cantidad": cantidad, "unidad": unidad})

    if len(new_data) > 0:
        print(new_data)
        engine.db.save_data(engine.db.engine, Olimpica, new_data)


def scroll_down(final):

    step = int(final*0.009)
    for val in range(0, final, step):
        engine.driver.execute_script(f"window.scrollTo(0, {val});")


def esperar_carga():
    document_state = engine.driver.execute_script("return document.readyState")
    while document_state != "complete":
        time.sleep(0.5)
        document_state = engine.driver.execute_script(
            "return document.readyState")


def elementos_cargados():

    final_height = engine.element_wait_search(
        5, By.XPATH, "//div[@class='vtex-flex-layout-0-x-flexColChild vtex-flex-layout-0-x-flexColChild--search-result-content pb0']")
    engine.driver.execute_script(
        f"window.scrollTo(0, {final_height.location['y'] + final_height.size['height']});")

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
                          nom_cant.replace("  ", " "))  # (?<=(?:X|x))\s?\d+
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
    engine = None
    while True:
        try:
            engine = Engine(current_url_olimpica, Olimpica, wire_requests=True)
            engine.implicitly_wait(20)
            esperar_carga()
            engine.db.model.metadata.create_all(engine.db.engine)
            lenth["Cantidad"] = engine.db.consulta_sql_query_one(
                "select count(*) as count from Olimpica;")["count"]
            # init_page()
            # time.sleep(2)
            engine.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight)")

            each_departments_cat()
            # send_email("Olimipica", lenth)
            engine.close()
        except (WebDriverException, ProtocolError) as e:
            traceback.print_exception(*sys.exc_info())
            if engine:
                engine.close()
            # Espera un momento para permitir que el navegador anterior se cierre completamente
            time.sleep(5)
            # Crea una nueva instancia del driver para reiniciar el navegador
        except Exception as e:
            traceback.print_exception(*sys.exc_info())
            break
        finally:
            print("Cerrada")
            if engine:
                engine.close()
            break


row = None
lenth = {}
current_url_olimpica = MAIN_PAGE
