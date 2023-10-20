# To call when the code runs the webscrapping
from mail.send_email import send_email, erorr_msg, PASSWORD
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from src.models.models import D1
from src.scraper.engine import CLICK
from src.utils.util import init_scraping
from datetime import datetime
# To allow the code to wait a few second between some lines                 # To scrolldown help from functions when you type (pageElement:single outcome, ResultSet: several outcomes)
import time
# To define de data frame
import pandas as pd
# To Use regular expressions
import re

import sys
sys.path.append(".")


# String with the name of the excel file
FILENAME = "d1_precios.xlsx"
EMAIL = 'dfzd1984@gmail.com'
PASW = '1234567'
TIME_OUT = 30


def login():
    driver.execute_script(CLICK, WebDriverWait(driver, TIME_OUT).until(EC.presence_of_element_located((
        By.XPATH, "//span[@class='user__chevron__link']"))))   # Click on the begin session
    time.sleep(2)
    driver.execute_script(CLICK, WebDriverWait(driver, TIME_OUT).until(EC.presence_of_element_located((
        By.XPATH, "/html/body/div[3]/div/div/div/button[3]"))))  # Click on the log in button
    time.sleep(4)

    while True:
        try:
            email = driver.find_element(By.CSS_SELECTOR, '#signup_email')
            pasw = driver.find_element(By.CSS_SELECTOR, '#signup_password')
            break
        except Exception as _:
            continue

    email.send_keys(EMAIL)
    pasw.send_keys(PASW)

    driver.execute_script(CLICK, driver.find_element(
        By.XPATH, "//*[@id='signup']/div[3]/div/div/div/div/button"))  # click on the login
    time.sleep(3)
    driver.execute_script(CLICK, WebDriverWait(driver, TIME_OUT).until(EC.presence_of_element_located(
        (By.ID, "card-operation-model-DELIVERY"))))  # clear delivery way
    time.sleep(3)
    driver.execute_script(CLICK, WebDriverWait(driver, TIME_OUT).until(EC.presence_of_element_located(
        (By.XPATH, "/html/body/div[5]/div/div[2]/div/div[2]/div[2]/div[1]/div/div"))))   # select adress


def categoires():
    # N=the number of categories the Bot encounter
    global lenth
    time.sleep(3)
    driver.execute_script(CLICK,
                          WebDriverWait(driver, TIME_OUT).until(EC.presence_of_element_located(
                              (By.XPATH,
                               "//button[@class='layout__StyledButton-sc-lp8hl0-0 glTQbP header__categoryTree']")
                          )))  # get into categories

    time.sleep(2)
    cat_list_object = WebDriverWait(driver, TIME_OUT).until(EC.presence_of_all_elements_located(
        (By.XPATH, "//div[@class='ant-menu-submenu-title']")))  # categories list
    cat_list: list[str] = [el.text for el in cat_list_object]

    # Function "pop" take out the defined position, in this case the first position. In This case is "alimentos y despensa" when the code was developed
    category = cat_list.pop(0)
    driver.execute_script(CLICK, WebDriverWait(driver, TIME_OUT).until(EC.presence_of_element_located(
        (By.XPATH, f"//div[@class='ant-menu-submenu-title']//*[contains(text(),'{category}')]"))))  # Click on the first category
    driver.execute_script(CLICK, WebDriverWait(driver, TIME_OUT).until(EC.presence_of_all_elements_located(
        (By.XPATH, f"//div[@class='ant-collapse-header']")))[1])

    # function to Download the webpage information in the category into cat_products object
    sub_categories(category)

    for name in cat_list:
        driver.execute_script(CLICK,
                              WebDriverWait(driver, TIME_OUT).until(EC.presence_of_element_located(
                                  (By.XPATH,
                                   "//button[@class='layout__StyledButton-sc-lp8hl0-0 glTQbP header__categoryTree']")
                              )))  # get into categories

        driver.execute_script(CLICK, WebDriverWait(driver, TIME_OUT).until(EC.presence_of_element_located(
            (By.XPATH, f"//div[@class='ant-menu-submenu-title']//*[contains(text(),'{name}')]"))))  # Click on the first category
        driver.execute_script(CLICK, WebDriverWait(driver, TIME_OUT).until(EC.presence_of_all_elements_located(
            (By.XPATH, f"//div[@class='ant-collapse-header']")))[1])
        sub_categories(name)


def sub_categories(category):
    sub_categories_list = WebDriverWait(driver, TIME_OUT).until(EC.presence_of_all_elements_located(
        (By.XPATH,
         "//label[@class='ant-checkbox-wrapper ant-checkbox-group-item css-1ck3jst']/span[2]")
    ))
    sub_categories_text = [get_text(el.text) for el in sub_categories_list]

    base_url = driver.current_url

    for sub in sub_categories_text:
        try:
            driver.get(f"{base_url}?categories={sub.replace(' ','+')}")
            get_elements(category, sub)
        except TimeoutException as e:
            pass

    # function to Download the webpage information in the category into cat_products object


def get_text(value: str):
    value = re.sub("\s\(\d+\)", "", value)

    return value


def get_elements(cat, sub):
    time.sleep(4)
    # Store in elements all the information within the tree of "product__content"
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)
    elements = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, "//div[@class= 'general__content']")))
    list_elements = []
    for el in elements:  # Definir un loop sobre los elementos descargados para un producto
        precio = precio_promo(el.find_element(
            By.XPATH, ".//p[contains(@class,'base__price')]").text)
        nombre = el.find_element(
            By.XPATH, ".//p[contains(@class,'prod__name')]").text.strip()
        cant_uni_prec = cantidad_uni_prec(
            el.find_element(By.CSS_SELECTOR, "p>span").text)
        data = {"nombre_producto": nombre,
                "categoria": cat,
                "sub_categoria": sub,
                "precio": float(precio),
                "precio_unidad": int(cant_uni_prec[0]),
                "cantidad": cant_uni_prec[1],
                "unidad": float(cant_uni_prec[2])}
        list_elements.append(data)
    db.save_data(db.engine, D1, list_elements)


def precio_promo(valor: str):  # function to download the prices data . Argumentos: string
    # Example: 98.400.  "\d+":98 ;  "(\.\d+)*": .400. Esta última parte al tener asterizco dice que encuentre los números después del punto pero si no existe punto no trae nada . group(0) retorna el objeto que coincide con la búsqueda
    exp = re.search("\d+(\.\d+)*", valor).group(0)
    # Retorna el número reemplazando el punto por nada
    return float(exp.replace(".", ""))


def cantidad_uni_prec(valor: str):
    valor = valor.replace(".", "").replace(",", ".")
    uni = re.search("(?<=\d )[a-zA-Z]", valor).group(0)
    cant = re.search("^\d+\.\d+|^\d+", valor).group(0)
    # {0,1}:  esto define el rango de la longitud de números que trae dentro de (\.\d+)
    preci_uni = re.search("(?<=\$ ).+(?=\))", valor).group(0)
    return cant, uni, preci_uni


def main():
    global driver, db
    # Web page https://domicilios.tiendasd1.com
    driver, db = init_scraping("https://domicilios.tiendasd1.com", D1)
    # login()
    db.model.metadata.create_all(db.engine)
    lenth["Cantidad"] = db.consulta_sql_query_one(
        "select count(*) as count from D1;")["count"]
    categoires()
    send_email("D1", lenth)
    db.close()
    driver.close()
    driver.quit


lenth = {}
