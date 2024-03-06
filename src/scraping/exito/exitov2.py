from src.scraping.exito.constants.constants_exito import *
from src.scraping.exito.exito import main as main_exito
from datetime import datetime
import os
import sqlalchemy

from src.scraper.engine.engine import Engine
from src.models.models import Exito
import traceback

import json
import re
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from gzip import decompress

from selenium.webdriver.common.keys import Keys


import sys
sys.path.append(".")


# from mail.send_email import send_email,erorr_msg

DATE = datetime.now()
# DATE = datetime(2024,1,27)


URL = "https://tienda.exito.com/"


def process_browser_log_entry(entry):
    response = json.loads(entry['message'])['message']
    return response


def parse_links(engine: Engine):
    driver = engine.driver
    driver.implicitly_wait(5)
    try:
        engine.element_wait_click(10, By.ID, "wps-overlay-close-button")
    except TimeoutException:
        pass
    action = ActionChains(driver)
    time.sleep(5)
    engine.element_wait_click(TIME, By.XPATH, XPATH_CATEGORY_BUTTON)
    time.sleep(1)
    engine.element_wait_searh(TIME, By.XPATH, XPATH_LIST_CATEGORY_LI_VERIFY)
    links = {}
    # driver.execute_script("document.body.style.zoom='80%';")
    for el in engine.elements_wait_searh(TIME, By.XPATH, XPATH_LIST_CATEGORY_LI):
        action.move_to_element(el).perform()
        WebDriverWait(driver, TIME).until(
            EC.presence_of_element_located((By.XPATH, XPATH_LIST_SUBVCAT_VERIFY)))

        cat_name = el.text
        sub_categories = el.find_elements(
            By.XPATH, XPATH_CATEGORY_CONTAINER)
        sub_links = {}
        for sub in sub_categories:
            sub_cat_name = sub.find_element(By.XPATH, XPATH_NAME_CATEGORY).text
            sub_categories_links = sub.find_elements(
                By.XPATH, ".//a[contains(@id,'Categorías-nivel3-')]")
            for sub_cat in sub_categories_links[1:]:
                sub_link = sub_cat.get_attribute("href")
                sub_links[sub_cat_name] = sub_links.get(
                    sub_cat_name, [])+[sub_link]
        links[cat_name] = sub_links
    return links


def get_data(engine: Engine):

    time.sleep(5)
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
    data_sql = engine.db.consulta_sql([Exito.nombre_producto],
                                      [Exito.fecha_resultados == datetime.now().date()])
    nombre_sql = set(
        [product for sub_data in data_sql for product in sub_data])
    for i, log in enumerate(json_logs):
        request_id = log["params"]["requestId"]
        products = []
        data = {}
        try:
            json_response = engine.driver.execute_cdp_cmd(
                "Network.getResponseBody", {"requestId": request_id})
            data = json.loads(json_response["body"])
            if "data" in data and "productSearch" in data["data"]:
                products = data["data"]["productSearch"]["products"]
            if not products and "data" in data and "productsByIdentifier" in data["data"] \
                    and "productName" in data["data"]["productsByIdentifier"][0]:
                products = data["data"]["productsByIdentifier"]
            if products:

                nombre_data = set([product["productName"]
                                  for product in products])
                if nombre_data.issubset(nombre_sql):
                    continue
                else:
                    json_data += products
        except Exception as e:
            pass
    return json_data


def get_data_require(engine):
    data_sql = engine.db.consulta_sql([Exito.nombre_producto],
                                      [Exito.fecha_resultados == datetime.now().date()])
    nombre_sql = set(
        [product for sub_data in data_sql for product in sub_data])
    json_data = []
    for req in engine.driver.requests:
        if req.response:
            resp = req.response
            data = {}
            products = []
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
                        products = data["data"]["productSearch"]["products"]
                    if not products and "data" in data and "productsByIdentifier" in data["data"] \
                            and "productName" in data["data"]["productsByIdentifier"][0]:
                        products = data["data"]["productsByIdentifier"]

                except TypeError:
                    pass

                if products:
                    nombre_data = set([product["productName"]
                                      for product in products])
                    if nombre_data.issubset(nombre_sql):
                        continue
                    else:
                        json_data += products
    return json_data


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
        new_data.append({"categoria": categoria, "sub_categoria": sub_categoria,
                        "nombre_producto": nombre_producto, "precio_bajo": precio_bajo,
                         "precio_alto": precio_alto, "cantidad": cantidad,
                         "unidad": unidad,
                         "fecha_resultados": DATE.date(),
                         "hora_resultados": DATE.time()
                         })
    # print(new_data)
    return new_data


def select_address(engine: Engine):
    city = engine.element_wait_searh(20, By.XPATH, XPATH_INPUT_LOCATION)
    # city.click()
    city.send_keys("B")
    city.send_keys(Keys.ENTER)
    time.sleep(2)
    # location.click()
    _, location = engine.elements_wait_searh(
        10, By.XPATH, XPATH_INPUT_LOCATION)
    location.send_keys("B")
    location.send_keys(Keys.ENTER)
    time.sleep(1)
    engine.element_wait_click(5, By.XPATH, XPATH_BUTTON_CONFIRM)


def first_iteration(cat, sub, link, engine: Engine):
    engine.driver.get(link)
    # try:
    #     select_address(engine)
    # except TimeoutException:
    #     pass
    try:
        # engine.ready_document()
        engine.element_wait_searh(
            5, By.XPATH, "//div[@class='exito-search-result-4-x-containerNotFoundExito']")
        return
    except TimeoutException as e:
        pass
    try:
        container = engine.element_wait_searh(
            TIME, By.ID, "gallery-layout-container")
        engine.driver.execute_script(
            "arguments[0].scrollIntoView(true);", container)
        engine.elements_wait_searh(
            TIME, By.CSS_SELECTOR, "div#gallery-layout-container > div > section > a > article")

        json_response = get_data(engine)
        if json_response or len(json_response) > 0:
            data = extract_files(cat, sub, json_response)
            try:
                engine.db.save_data(engine.db.engine, Exito, data)
            except sqlalchemy.exc.OperationalError:
                pass

        data = get_data_require(engine)
        if data:
            data = extract_files(cat, sub, data)
            try:
                engine.db.save_data(engine.db.engine, Exito, data)
            except sqlalchemy.exc.OperationalError:
                pass
        else:
            data_links.append({"link": link, "cat": cat, "subcat": sub})
    except TimeoutException:
        return
    count = 0
    action = ActionChains(engine.driver)
    while True:
        try:

            final_height = engine.element_wait_searh(
                5, By.XPATH, "//div[@class='vtex-flex-layout-0-x-flexRow vtex-flex-layout-0-x-flexRow--search-result-web']")
            engine.driver.execute_script(
                f"window.scrollTo(0, {final_height.location['y'] + final_height.size['height']} -200);")
            # time.sleep(1)
            engine.element_wait_click(
                TIME, By.XPATH, XPATH_BUTTON_NEXT_ELEMENT)

        except TimeoutException:
            break
        try:
            # engine.ready_document()
            engine.element_wait_searh(
                5, By.XPATH, "//div[@class='exito-search-result-4-x-containerNotFoundExito']")
            break
        except TimeoutException as e:
            pass
        try:
            # container = engine.element_wait_searh(
            #     TIME, By.ID, "gallery-layout-container")
            # engine.driver.execute_script(
            #     "arguments[0].scrollIntoView(true);", container)
            # engine.elements_wait_searh(
            #     TIME, By.CSS_SELECTOR, "div#gallery-layout-container > div > section > a > article")

            json_response = get_data(engine)
            if json_response or len(json_response) > 0:
                data = extract_files(cat, sub, json_response)
                try:
                    engine.db.save_data(engine.db.engine, Exito, data)
                except sqlalchemy.exc.OperationalError:
                    pass

            data = get_data_require(engine)
            if data:
                data = extract_files(cat, sub, data)
                try:
                    engine.db.save_data(engine.db.engine, Exito, data)
                except sqlalchemy.exc.OperationalError:
                    pass
            # else: data_links.append({"link":link,"cat":cat,"subcat":sub})
            count += 1
        except TimeoutException:
            break


def iter_pages(cat, sub, engine: Engine, link):
    global data_links
    while True:
        try:
            engine.driver.get(link)
            break
        except TimeoutException:
            engine.driver.refresh()
            time.sleep(4)
    try:
        # engine.ready_document()
        engine.element_wait_searh(
            5, By.XPATH, "//div[@class='exito-search-result-4-x-containerNotFoundExito']")
        return
    except TimeoutException as e:
        pass
    try:
        # container = engine.element_wait_searh(
        #     TIME, By.ID, "gallery-layout-container")
        # engine.driver.execute_script(
        #     "arguments[0].scrollIntoView(true);", container)
        # engine.elements_wait_searh(
        #     TIME, By.CSS_SELECTOR, "div#gallery-layout-container > div > section > a > article")
        json_response = get_data(engine)
        if json_response or len(json_response) > 0:
            data = extract_files(cat, sub, json_response)
            try:
                engine.db.save_data(engine.db.engine, Exito, data)
            except sqlalchemy.exc.OperationalError:
                pass

        data = get_data_require(engine)
        if data:
            data = extract_files(cat, sub, data)
            try:
                engine.db.save_data(engine.db.engine, Exito, data)
            except sqlalchemy.exc.OperationalError:
                pass
        # else: data_links.append({"link":link,"cat":cat,"subcat":sub})
    except TimeoutException:
        return
    last_link = engine.driver.current_url
    while True:
        try:

            final_height = engine.element_wait_searh(
                5, By.XPATH, "//div[@class='vtex-flex-layout-0-x-flexRow vtex-flex-layout-0-x-flexRow--search-result-web']")
            engine.driver.execute_script(
                f"window.scrollTo(0, {final_height.location['y'] + final_height.size['height']} - 200);")
            engine.element_wait_click(
                TIME, By.XPATH, XPATH_BUTTON_NEXT_ELEMENT)

        except TimeoutException:
            break
        try:
            # engine.ready_document()
            engine.element_wait_searh(
                5, By.XPATH, "//div[@class='exito-search-result-4-x-containerNotFoundExito']")
            break
        except TimeoutException as e:
            pass
        try:
            if engine.driver.current_url == last_link:
                break
            last_link = engine.driver.current_url
            json_response = get_data(engine)
            if json_response or len(json_response) > 0:
                data = extract_files(cat, sub, json_response)
                try:
                    engine.db.save_data(engine.db.engine, Exito, data)
                except sqlalchemy.exc.OperationalError:
                    pass

            data = get_data_require(engine)
            if data:
                data = extract_files(cat, sub, data)
                try:
                    engine.db.save_data(engine.db.engine, Exito, data)
                except sqlalchemy.exc.OperationalError:
                    pass
            # else: data_links.append({"link":link,"cat":cat,"subcat":sub})
            # if int(re.search("(?<=page=)[0-9]+",engine.driver.current_url).group()) % 20 == 0:
            #     engine.driver.refresh()
            #     time.sleep(6)

        except TimeoutException:
            break


def cant_uni(nom_cant: str):
    nom_cant = nom_cant.replace(" T/L/D TODOS LOS DIAS SIN REF", "")

    cant = re.findall(
        "(?<= )\d+[(,|\.)\d+]*(?:\s*[a-zA-Z]{1,4})$", nom_cant)
    if len(cant) == 0:
        return "1", "UN"
    elif len(cant) == 1:
        return re.search("\d+[(,|\.)\d+]*", cant[0]).group(0).replace(",", ".").strip(), \
            re.search("[a-zA-Z]+", cant[0]).group(0).strip()
    elif len(cant) > 1:
        return re.search("\d+[(,|\.)\d+]*", cant[-1]).group(0).replace(",", ".").strip(), \
            re.search("[a-zA-Z]+", cant[-1]).group(0).strip()


def main():
    global data_links
    data_links = []
    try:
        engine = Engine(URL, Exito)

        Exito.metadata.create_all(engine.db.engine)
        engine.ready_document()
        engine.driver.find_element(By.TAG_NAME, "html").send_keys(
            Keys.CONTROL+Keys.SUBTRACT)
        time.sleep(2)
        links = parse_links(engine)
        res = None  # engine.db.last_item_db()
        res = engine.db.last_item_db(DATE)
        # res = {"categoria":"Electrodomésticos","sub_categoria":"Mundo hogar"}
        for cat, sub_dict in links.items():
            if res and cat != res["categoria"]:
                continue
            if res:
                del res["categoria"]
            for sub, sub_links in sub_dict.items():
                if res and sub != res["sub_categoria"]:
                    continue
                count = 0
                if res:
                    print("-"*10)
                    print(sub_links)
                    print("-"*10)
                    while count < len(sub_links):
                        try:
                            link = sub_links[count]
                            if "taeq" in link:
                                count += 1
                                continue
                            first_iteration(cat, sub, link, engine)
                            count += 1
                            break
                        except TimeoutException:
                            count += 1
                            continue
                if res:
                    res = None
                for link in sub_links[count:]:

                    iter_pages(cat, sub, engine, link)

    except sqlalchemy.exc.OperationalError:
        os.mkdir("db")
    except Exception:
        traceback.print_exception(*sys.exc_info())
    finally:
        print("Cerrada")
        print(link)
        if engine:
            engine.close()

    time.sleep(2)
    if len(data_links) > 0:
        main_exito(data_links)
