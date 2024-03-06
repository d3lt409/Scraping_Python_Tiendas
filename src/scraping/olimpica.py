from mail.send_email import send_email, erorr_msg
from src.scraper.engine.engine import CLICK, Engine
from src.utils.util import crash_refresh_page
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
    dep_element_object = engine.elements_wait_searh(
        20, By.XPATH, "//div[@class='olimpica-mega-menu-0-x-Level1Container']/a")
    dep_cat_elements: dict[str, list[list[str]]] = {}
    for el in dep_element_object:
        ActionChains(engine.driver).move_to_element(el).perform()
        dep_cat_elements[el.text] = [
            [ele.text, ele.get_attribute("href")] for ele in engine.elements_wait_searh(20, By.XPATH, "//div[@class='olimpica-mega-menu-0-x-Level2Container']//a")]

    list_articles = []
    row = engine.db.last_item_db()
    for dep, cats in dep_cat_elements.items():
        print(dep, row)
        if row and "Departamento" in row and row["Departamento"] != dep:
            continue
        elif row and "Departamento" in row:
            del row["Departamento"]
        for cat in cats:
            print(cat, row)
            if row and "Categoria" in row and row["Categoria"] != cat[0]:
                continue
            elif row and "Categoria" in row:
                del row["Categoria"]
            current_url_olimpica = cat[1]
            try:
                engine.driver.get(current_url_olimpica)

                try:
                    engine.element_wait_searh(
                        5, By.XPATH, "//div[@class='vtex-search-result-3-x-searchNotFoundInfo flex flex-column ph9']")
                    continue
                except TimeoutException:
                    pass
            except WebDriverException as _:
                crash_refresh_page()

            list_articles += get_subcategories(dep, cat[0], cat[1])
    return list_articles


def get_subcategories(dep, cat, url: str):
    global current_url_olimpica, driver, row

    list_articles = []
    dep_cat = url.replace("https://www.olimpica.com/", "").split("/")
    if (len(dep_cat) != 2):
        count = 1
        while True:
            if (url.__contains__("page=")):
                current_url_olimpica = re.sub("\d+$", "", url)+str(count)
            elif (url.__contains__("?")):
                current_url_olimpica = f"{url}&page={count}"
            else:
                current_url_olimpica = f"{url}?page={count}"

            engine.driver.get(current_url_olimpica)

            try:
                engine.element_wait_searh(
                    5, By.XPATH, "//div[@class='vtex-search-result-3-x-searchNotFoundInfo flex flex-column ph9']")
                break
            except TimeoutException:
                pass
            list_articles += get_elements(dep, cat, "")
            count += 1
        return list_articles

    sub_categories = get_subcategories_list()

    for subcat in sub_categories:
        if row and "Sub_categoria" in row and row["Sub_categoria"] != subcat:
            continue
        elif row:
            row = None
        count = 1
        while True:

            current_url_olimpica = f"https://www.olimpica.com/{dep_cat[0]}/{dep_cat[1]}/{subcat}?initialMap=category-1,categoria&initialQuery={dep_cat[0]}/{dep_cat[1]}&map=category-1,category-2,category-3&page={count}"
            try:
                engine.driver.get(current_url_olimpica)

            except WebDriverException as _:

                engine.driver.refresh()

            try:
                engine.element_wait_searh(
                    5, By.XPATH, "//div[@class='vtex-search-result-3-x-searchNotFoundInfo flex flex-column ph9']")
                break
            except TimeoutException:
                pass  # https://www.olimpica.com/supermercado/desayuno/lacteos-y-derivados-refrigerados?initialMap=c,c&initialQuery=supermercado/desayuno&map=category-1,category-2,category-3

            list_articles += get_elements(dep, cat, subcat)
            count += 1
    return list_articles


def get_subcategories_list():
    global driver
    tries = 0

    while True:
        try:
            print(current_url_olimpica)
            subcat_button = engine.element_wait_searh(
                20, By.XPATH, "//div[contains(@class,'--category-3')]/div/div")
            driver.execute_script(
                "arguments[0].scrollIntoView(true);", subcat_button)
            driver.execute_script("arguments[0].click();", subcat_button)
            time.sleep(2)
            scroll_height: WebElement = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@class,'--category-3')]//div[@data-testid='scrollable-element']/div/div")))
            scroll_element: WebElement = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@class,'--category-3')]//div[@data-testid='scrollable-element']")))
            driver.execute_script(
                "arguments[0].scrollIntoView(true);", scroll_element)
            time.sleep(1)
            for i in [1, 2, 3]:
                driver.execute_script(
                    "arguments[0].scrollTop = arguments[1]", scroll_element, scroll_height.size["height"]*(i/3))
                time.sleep(1)

            time.sleep(2)
            sub_categories_objects: list[WebElement] = WebDriverWait(driver, 30).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//div[contains(@class,'--category-3')]//div[@data-testid='scrollable-element']//label")))
            return [str(val.get_attribute("for")).replace("category-3-", "") for val in sub_categories_objects]
        except TimeoutException as e:
            if tries == 3:
                print(e, e.args, "sub_cat timeout")
                raise e.with_traceback(e.__traceback__)
            tries += 1
            time.sleep(5)
            driver.refresh()

        except WebDriverException as e:
            if tries == 3:
                print(e, e.args, "sub_cat web_driver")
                raise e.with_traceback(e.__traceback__)
            tries += 1
            driver = crash_refresh_page(driver, current_url_olimpica)

            init_page()


def scroll_down(final):

    step = int(final*0.009)
    for val in range(0, final, step):
        driver.execute_script(f"window.scrollTo(0, {val});")


def elementos_cargados():
    global driver
    tries = 0
    while tries < 3:
        try:
            WebDriverWait(driver, 30).until(EC.presence_of_element_located(
                (By.XPATH, "//div[@class='false olimpica-dinamic-flags-0-x-listPrices']/div/span")))
            break
        except TimeoutException as _:
            tries += 1
            driver = crash_refresh_page(driver, current_url_olimpica)

            init_page()
    return tries


def get_elements(dep, cat, subcat):
    global driver
    time.sleep(2)
    list_elements = []
    if elementos_cargados() == 3:
        return []
    try:
        final_height: WebElement = WebDriverWait(driver, 30).until(EC.presence_of_element_located(
            (By.XPATH, "//div[@class='vtex-flex-layout-0-x-flexRow vtex-flex-layout-0-x-flexRow--category-content-products-v2']")))
        scroll_down(final_height.size["height"])
        elements: list[WebElement] = WebDriverWait(driver, 30).until(EC.presence_of_all_elements_located(
            (By.XPATH, "//div[@class='vtex-flex-layout-0-x-flexRow vtex-flex-layout-0-x-flexRow--category-content-products-v2']//article/div[2]/div/div/div")))

    except WebDriverException as e:
        driver = crash_refresh_page(driver, current_url_olimpica)
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, "//div[@class='vtex-search-result-3-x-searchNotFoundInfo flex flex-column ph9']")))
            return []
        except TimeoutException:
            pass

        elements: list[WebElement] = WebDriverWait(driver, 30).until(EC.presence_of_all_elements_located(
            (By.XPATH, "//div[@class='vtex-flex-layout-0-x-flexRow vtex-flex-layout-0-x-flexRow--category-content-products-v2']//article/div[2]/div/div/div")))
    for element in elements:
        try:
            driver.execute_script(
                "arguments[0].scrollIntoView(true);", element)
        except (WebDriverException, TimeoutException) as e:
            print(e, e.args)
            continue

        precio = precio_promo(element)
        if not precio:
            continue
        nombre = select_name(element)
        cant, uni = cant_uni(nombre)
        precio_norm = precio_normal(element)
        date = datetime.now()

        list_elements.append((dep, cat, subcat, nombre, precio, cant,
                              uni, precio_norm, date.date(), date.time()))

    df = pd.DataFrame(list_elements, columns=COLUMNS)
    lenth["Cantidad elementos"] = lenth.get(
        "Cantidad elementos", 0) + len(list_elements)
    while True:
        try:
            db.to_data_base(df)
            break
        except OperationalError as _:
            print(
                "Base de datos bloquada, por favor guarde los cambios de donde la esté usando")
    print(
        f"Productos guardados,Departamento {dep} en la categoría: {cat}, subcategoría: {subcat} a las {datetime.now()} la cantidad de {len(df)}")
    return list_elements


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
