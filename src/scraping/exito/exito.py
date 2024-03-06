from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
import pandas as pd
import gc
import re
import time
import json
from datetime import datetime
from src.scraper.engine.engine import (
    Engine)
import sys
from src.models.models import Exito
sys.path.append(".")


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
            container = engine.element_wait_searh(
                20, By.ID, "gallery-layout-container")
            engine.driver.execute_script(
                "arguments[0].scrollIntoView(true);", container)

            final_height = engine.element_wait_searh(
                10, By.XPATH, "//div[@class='vtex-flex-layout-0-x-flexRow vtex-flex-layout-0-x-flexRow--search-result-web']")
            scroll_down(2, final_heith=final_height.size["height"])
            time.sleep(1)
            elements = engine.elements_wait_searh(
                10, By.CSS_SELECTOR, "div#gallery-layout-container > div > section > a > article")
            break
        except TimeoutException as e:
            if tries == 3:
                try:
                    engine.element_wait_searh(
                        15, By.XPATH, "//div[@class='exito-search-result-4-x-containerNotFoundExito']")
                    return
                except TimeoutException:
                    pass
                engine.crash_refresh_page()
                time.sleep(2)
            tries += 1
            engine.driver.refresh()
            engine.ready_document()
        except Exception as e:
            if tries == 3:
                raise e.with_traceback(e.__traceback__)
            tries += 1
            engine.crash_refresh_page()
            time.sleep(2)
            engine.ready_document()
    return elements


def get_elements(cat, subcat):
    global driver
    time.sleep(3)
    list_elements = []
    elements = charge_elements()
    if not elements:
        return
    time.sleep(2)
    for el in elements:
        try:
            engine.driver.execute_script(
                "arguments[0].scrollIntoView(true);", el)
        except (WebDriverException, TimeoutException) as e:
            print(e, e.args)
            continue

        name = select_name(el)
        precio = select_price(el)
        cant, uni = cant_uni(name)
        precio_norm = precio_normal(el)
        if not precio_norm:
            precio_norm = 0
        if not precio:
            precio = 0

        list_elements.append({"categoria": cat,
                              "sub_categoria": subcat,
                              "nombre_producto": name.replace("\n", " "),
                              "precio_bajo": precio, "cantidad": cant,
                              "unidad": uni, "precio_alto": precio_norm})

    return list_elements


def select_price(element: WebElement):
    try:  # div/div/div/div[4]/div[2]/div/span
        return precio_promo(
            element.find_element(
                By.CSS_SELECTOR, "div.exito-vtex-components-4-x-selling-price.flex.items-center> div > span").text.strip()
        )
    except Exception as e:
        print(e, e.args)
        return float(0)


def select_name(element: WebElement):
    try:
        nombre_cantidad_unidad = element.find_element(
            By.CSS_SELECTOR, "div > div > h3 > span").text.strip()
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
        el = element.find_element(
            By.CSS_SELECTOR, "div.exito-vtex-components-4-x-list-price.t-mini.ttn.strike > span")
    except (WebDriverException) as _:
        return ""
    if el:
        try:
            return precio_promo(el.text.strip())
        except WebDriverException as _:
            return ""
    else:
        ""


def precio_promo(valor: str):
    exp = re.search("\d+[\.\d+]*", valor).group(0)
    return float(exp.replace(".", ""))


def cant_uni(nom_cant: str):
    nom_cant = nom_cant.replace(" T/L/D TODOS LOS DIAS SIN REF", "")

    cant = re.findall(
        "(?<= )\d+[(,|\.)\d+]*(?:\s*[a-zA-Z]+)", nom_cant)
    if len(cant) == 0:
        return "1", "UN"
    elif len(cant) == 1:
        return re.search("\d+[(,|\.)\d+]*", cant[0]).group(0).replace(",", ".").strip(), \
            re.search("[a-zA-Z]+", cant[0]).group(0).strip()
    elif len(cant) > 1:
        return re.search("\d+[(,|\.)\d+]*", cant[-1]).group(0).replace(",", ".").strip(), \
            re.search("[a-zA-Z]+", cant[-1]).group(0).strip()


def main(data):
    global engine, heigth
    try:
        engine = Engine(data[0]["link"], Exito)
        heigth = engine.element_wait_searh(
            15, By.XPATH, "/html/body/div[2]/div/div[1]/div/div[5]").size["height"]
        data = get_elements(data[0]["cat"], data[0]["subcat"])
        engine.db.save_data(engine.db.engine, Exito, data)
        for url in data[1:]:
            if "link" in url:
                engine.driver.get(url["link"])
                data = get_elements(url["cat"], url["subcat"])
                engine.db.save_data(engine.db.engine, Exito, data)
        engine.close()
    except KeyboardInterrupt as _:
        pass
