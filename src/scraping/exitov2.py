from src.utils.util import Engine
from src.scraping.constants.constants_exito import *
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

from sqlalchemy.orm import Session
from sqlalchemy import insert

import sys
sys.path.append(".")

# from mail.send_email import send_email,erorr_msg


def process_browser_log_entry(entry):
    response = json.loads(entry['message'])['message']
    return response


def parse_links(engine: Engine):
    driver = engine.driver
    driver.implicitly_wait(5)
    action = ActionChains(driver)
    
    engine.element_wait_click(TIME, By.XPATH, XPATH_CATEGORY_BUTTON)
    engine.element_wait_searh(TIME, By.XPATH, XPATH_LIST_CATEGORY_LI_VERIFY)
    time.sleep(8)
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
                sub_links[sub_cat_name] = sub_links.get(sub_cat_name, [])+[sub_link]
        links[cat_name] = sub_links
    return links


def get_data(engine):

    time.sleep(3)
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

    # Extraer las respuestas JSON
    json_data = {}
    for i, log in enumerate(json_logs):
        request_id = log["params"]["requestId"]
        try:
            json_response = engine.driver.execute_cdp_cmd(
                "Network.getResponseBody", {"requestId": request_id})
            data = json.loads(json_response["body"])
            if "data" in data and "productSearch" in data["data"]:
                json_data = data["data"]["productSearch"]["products"]
            if "data" in data and "productsByIdentifier" in data["data"] \
                    and "productName" in data["data"]["productsByIdentifier"][0]:
                json_data = data["data"]["productsByIdentifier"]
        except Exception as e:
            pass

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
                        "nombre_producto": nombre_producto, "precio_bajo": precio_bajo, "precio_alto": precio_alto, "cantidad": cantidad, "unidad": unidad})
    print(new_data)
    return new_data


def iter_pages(cat, sub, engine: Engine, link):
    count = 2
    engine.driver.get(link)
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

        data = extract_files(cat, sub, get_data(engine))
        save_data(engine.db.engine, data)
    except TimeoutException:
        return
    while True:
        if (link.__contains__("page=")):
            link = re.sub("\d+$", "", link)+str(count)
        elif (link.__contains__("?")):
            link = f"{link}&page={count}"
        else:
            link = f"{link}?page={count}"
        engine.driver.get(link)
        try:
            # engine.ready_document()
            engine.element_wait_searh(
                5, By.XPATH, "//div[@class='exito-search-result-4-x-containerNotFoundExito']")
            break
        except TimeoutException as e:
            pass
        try:
            container = engine.element_wait_searh(
                TIME, By.ID, "gallery-layout-container")
            engine.driver.execute_script(
                "arguments[0].scrollIntoView(true);", container)
            engine.elements_wait_searh(
                TIME, By.CSS_SELECTOR, "div#gallery-layout-container > div > section > a > article")

            data = extract_files(cat, sub, get_data(engine))
            save_data(engine.db.engine, data)
            count += 1
        except TimeoutException:
            break


def cant_uni(nom_cant: str):
    nom_cant = nom_cant.replace(" T/L/D TODOS LOS DIAS SIN REF", "")

    cant = re.findall(
        "(?<= )\d+[(,|\.)\d+]*(?:\s*[a-zA-Z]{1,4})$", nom_cant)
    if len(cant) == 0:
        return "1", "UN"
    elif len(cant) == 1:
        return re.search("\d+[(,|\.)\d+]*", cant[0]).group(0).replace(",", ".").strip(),\
            re.search("[a-zA-Z]+", cant[0]).group(0).strip()
    elif len(cant) > 1:
        return re.search("\d+[(,|\.)\d+]*", cant[-1]).group(0).replace(",", ".").strip(),\
            re.search("[a-zA-Z]+", cant[-1]).group(0).strip()


def save_data(engine, data):
    with Session(engine) as session:
        session.execute(
            insert(Exito).prefix_with("OR IGNORE"),
            data
        )
        session.commit()


def main():

    try:
        engine = Engine("https://www.exito.com", "Exito")
        Exito.metadata.create_all(engine.db.engine)
        engine.ready_document()
        links = parse_links(engine)
        
        for cat, sub_dict in links.items():
            for sub, sub_links in sub_dict.items():
                for link in sub_links:
                    iter_pages(cat, sub, engine, link)

    except Exception:
        traceback.print_exception(*sys.exc_info())
        print("Cerrada")
        engine.close()
