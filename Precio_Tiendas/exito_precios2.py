import sys
sys.path.append(".")
from Util import consulta_sql, consulta_sql_unica, init_scraping, ready_document, crash_refresh_page, to_data_base
from copy import deepcopy
from datetime import datetime
import json
import time
import re
import gc

from bs4 import BeautifulSoup
import pandas as pd
from selenium.common.exceptions import TimeoutException, WebDriverException
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
    list_products = []

    list_products += each_departments_cat_sub("Bogota")
    config["Exito"] = True
    with open("config.json", "w") as writer:
        json.dump(config, writer)
    driver.close()
    return list_products


def each_departments_cat_sub(city: str):
    global current_url_exito, driver
    ready_document(driver, current_url_exito)
    tries = 0
    while True:
        try:
            dep_button: WebElement = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, "category-menu")))
            driver.execute_script("arguments[0].click();", dep_button)
            break
        except TimeoutException as e:
            if tries == 2:
                e.with_traceback()
            tries += 1
            driver.refresh()

    dep_element_object: list[WebElement] = WebDriverWait(driver, 30).until(
        EC.presence_of_all_elements_located(
            (By.XPATH, "//li[@class='exito-category-menu-3-x-itemCategory']/p")))
    dep_cat_elements: dict[dict[str, list[tuple[str]]]] = {}
    for el in dep_element_object:
        ActionChains(driver).move_to_element(el).perform()
        elementos: list[WebElement] = WebDriverWait(driver, 30).until(EC.presence_of_all_elements_located(
            (By.XPATH, "//div[@class='exito-category-menu-3-x-itemSideMenu']")))
        dep_cat_elements[el.text] = {}
        for elemento in elementos:
            a: list[WebElement] = WebDriverWait(driver, 30).until(
                lambda _: elemento.find_elements_by_tag_name("a")
            )
            if a[0].get_attribute("href") == "":
                continue

            dep_cat_elements[el.text][a[0].text] = [(val.text, val.get_attribute("href")) for val in a[1:] if
                                                    len(val.get_attribute("href").replace(MAIN_PAGE, "").split("/")) > 1]
            if len(dep_cat_elements[el.text][a[0].text]) == 0:
                del dep_cat_elements[el.text][a[0].text]

    ready_document(driver, current_url_exito)
    list_articles = []
    if len(list(config["Exito"].keys())) == 0:
        config["Exito"] = dep_cat_elements
    config_copy = deepcopy(config) 
    for dep, cats in config_copy["Exito"].items():
        for cat, subs in cats.items():
            while len(subs) > 0:
                sub = subs.pop()
                if len(sub[1].replace(MAIN_PAGE, "").split("/")) == 1:
                    continue
                current_url_exito = sub[1]
                try:
                    driver.get(current_url_exito)
                except WebDriverException as _:
                    driver = crash_refresh_page(driver, current_url_exito)
                ready_document(driver, current_url_exito)
                list_articles += sub_categories(dep, cat, sub[0])
                config["Exito"][dep][cat] = subs
                with open("config.json", "w") as writer:
                    json.dump(config, writer)
            del config["Exito"][dep][cat]
            with open("config.json", "w") as writer:
                    json.dump(config, writer)
        del config["Exito"][dep]
        with open("config.json", "w") as writer:
                json.dump(config, writer)
    return list_articles


def consulta_ultima_peticion():
    fecha = consulta_sql_unica("select max(Fecha_resultados) FROM Exito;")
    hora = consulta_sql_unica(
        f"select max(Hora_resultados) FROM Exito where Fecha_resultados = {fecha!r};")
    ult_dep = consulta_sql_unica(
        f"SELECT Departamento from Exito where Hora_resultados = {hora!r} and Fecha_resultados = {fecha!r};")
    ult_cat = consulta_sql_unica(
        f"SELECT Categoria from Exito where Hora_resultados = {hora!r} and Fecha_resultados = {fecha!r} and Departamento= {ult_dep!r};")
    ult_sub = consulta_sql_unica(f"""SELECT Sub_categoria from Exito where Hora_resultados = {hora!r} and Fecha_resultados = {fecha!r} 
            and Departamento= {ult_dep!r} and Categoria = {ult_cat!r};""")

    deps = [val[0] for val in consulta_sql(f"select DISTINCT Departamento FROM Exito where Departamento <> {ult_dep!r};")
            if val[0]]
    cats = [val[0] for val in consulta_sql(f"select DISTINCT Categoria FROM Exito where Departamento = {ult_dep!r} and Categoria <> {ult_cat!r};")
            if val[0]]
    subs = [val[0] for val in consulta_sql(f"""select DISTINCT Sub_categoria FROM Exito where Departamento = {ult_dep!r} and Categoria = {ult_cat!r}
            and Sub_categoria <> {ult_sub!r};""") if val[0]]
    return deps, cats, subs


def sub_categories(departamento, categoria: str, subcategoria):
    global current_url_exito
    ready_document(driver, current_url_exito)
    count = 1
    url = current_url_exito
    listado = []
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
            WebDriverWait(driver, 50).until(EC.presence_of_element_located(
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
                (By.XPATH, "//h2[@class='tc fw1 exito-search-result-4-x-notFoundText']")))
            break
        except TimeoutException:
            pass
        listado += get_elements(departamento, categoria, subcategoria)
        count += 1
    return listado


def scroll_down(time_limit, init=0, final_heith=0):
    time.sleep(time_limit)
    if (final_heith == 0):
        final_heith = driver.execute_script(
            "return document.body.scrollHeight")-heigth
    step = int(final_heith*0.003)
    for val in range(init, final_heith, step):
        driver.execute_script(f"window.scrollTo(0, {val});")


def elementos_cargados():
    global driver
    tries = 0
    while tries < 3:
        try:
            WebDriverWait(driver, 30).until(EC.presence_of_element_located(
                (By.XPATH,"//div[@class='exito-filters-0-x-filters--layout ']")))
            break
        except TimeoutException as _:
            tries += 1
            driver = crash_refresh_page(driver, current_url_exito)
            ready_document(driver, current_url_exito)
    return tries


def get_elements(dep, cat, subcat):
    ready_document(driver, current_url_exito)
    if elementos_cargados() == 3:
        return []
    list_elements = []
    try:
        container: WebElement = WebDriverWait(
            driver, 50).until(EC.presence_of_element_located((By.ID, "gallery-layout-container")))
        driver.execute_script("arguments[0].scrollIntoView(true);", container)
        final_height: WebElement = WebDriverWait(driver, 30).until(EC.presence_of_element_located(
            (By.XPATH, "//div[@class='vtex-flex-layout-0-x-flexRow vtex-flex-layout-0-x-flexRow--search-result-web']")))
        scroll_down(2, final_heith=final_height.size["height"])
        elements: list[WebElement] = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located(
            (By.XPATH, "//*[@id='gallery-layout-container']/div/section/a/article")))

    except WebDriverException as _:
        driver.refresh()
        time.sleep(2)
        ready_document(driver, current_url_exito)
        container: WebElement = WebDriverWait(
            driver, 50).until(EC.presence_of_element_located((By.ID, "gallery-layout-container")))
        driver.execute_script("arguments[0].scrollIntoView(true);", container)
        final_height: WebElement = WebDriverWait(driver, 30).until(EC.presence_of_element_located(
            (By.XPATH, "//div[@class='vtex-flex-layout-0-x-flexRow vtex-flex-layout-0-x-flexRow--search-result-web']")))
        scroll_down(2, final_heith=final_height.size["height"])
        elements: list[WebElement] = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located(
            (By.XPATH, "//*[@id='gallery-layout-container']/div/section/a/article")))
    for el in elements:
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", el)
            element = BeautifulSoup(el.get_attribute('innerHTML'), 'html5lib')
        except (WebDriverException, TimeoutException) as e:
            print(e, e.args)
            continue

        precio = select_price(element)
        nombre_cantidad_unidad = nombre_cantidad(select_name(element))
        precio_norm = precio_normal(element)
        date = datetime.now()
        if (len(nombre_cantidad_unidad) == 3):
            list_elements.append(
                (dep, cat, subcat, nombre_cantidad_unidad[0].replace("\n", " "), precio, nombre_cantidad_unidad[1],
                 nombre_cantidad_unidad[2], precio_norm, date.date(), date.time()))
        else:
            list_elements.append(
                (dep, cat, subcat, nombre_cantidad_unidad[0].replace("\n", " "), precio, nombre_cantidad_unidad[1], "",
                 precio_norm, date.date(), date.time()))
    df = pd.DataFrame(list_elements, columns=COLUMNS)
    to_data_base(df, 'Exito')
    print(
        f"Productos guardados, para la categoría {cat} y subcategoría {subcat} a las {datetime.now()}")
    return list_elements


def select_price(element: BeautifulSoup):
    try:  # div/div/div/div[4]/div[2]/div/span
        return precio_promo(
            element.find_next(
                "div", {
                    "class": "exito-vtex-components-4-x-selling-price flex items-center"}
            ).find_next("div").find_next("span").text)
    except Exception as e:
        print(e, e.args)
        pass
    try:
        return precio_promo(
            element.find_next(
                "div", {"class": "exito-vtex-components-4-x-PricePDP"}).find("span").text)
    except Exception as e:
        print(e, e.args)
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
            element.find_next(
                "div", {"class": "exito-vtex-components-4-x-list-price t-mini ttn strike"})
            .find_next("span", {"class": "exito-vtex-components-4-x-currencyContainer"}).text.strip())
        return precio_normal
    except Exception as e:
        return ""


def precio_promo(valor: str):
    exp = re.search("\d+[\.\d+]*", valor).group(0)
    return float(exp.replace(".", ""))


def nombre_cantidad(nom_cant: str):
    nom_cant = nom_cant.replace(" T/L/D TODOS LOS DIAS SIN REF", "")
    try:
        cant = re.search(
            "(?<=. )(\d+[\.\d]* [a-zA-Z ]+(\.)*$|\d+[\.\d]*[a-zA-Z]+$)$", nom_cant).group(0)
    except:
        cant = "1 UN"
    if (cant.isnumeric()):
        cant += " UN"
    if (len(cant.split()) == 1):
        new_cant = re.search("\d+", cant).group(0)
        cant = cant.replace(new_cant, f"{new_cant} ")

    return [nom_cant]+cant.split()


def main():
    try:
        df = pd.DataFrame(for_each_city(), columns=COLUMNS)
    except Exception as e:
        config["Exito"] = False
        with open("config.json", "w") as writer:
            json.dump(config, writer)
        e.with_traceback()
    try:
        df_excel = pd.read_excel(f"Precio_Tiendas/excel_files/{FILENAME}")
        df_total = pd.concat([df_excel, df])
        df_total.to_excel(
            f"Precio_Tiendas/excel_files/{FILENAME}", index=False)
        print(f"Guardado a las {datetime.now()}")
    except FileNotFoundError as _:
        df.to_excel(
            f"Precio_Tiendas/excel_files/{FILENAME}", index=False)
        print(f"Guardado a las {datetime.now()}")
    except Exception as _:
        print("No se cargó el archivo")


try:
    with open("config.json", "r") as json_path:
        config: dict = json.load(json_path)
    current_url_exito = MAIN_PAGE
    driver = init_scraping(current_url_exito, 'Exito')
    heigth: int = WebDriverWait(driver, 20).until(EC.presence_of_element_located(
        (By.XPATH, "/html/body/div[2]/div/div[1]/div/div[5]"))).size["height"]

    main()
except KeyboardInterrupt as _:
    pass

gc.collect(2)
