from datetime import datetime
import time
import pandas as pd
import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException

import sys; sys.path.append(".")
from src.utils.util import init_scraping
from mail.send_email import send_email,erorr_msg

COLUMNS = ["Categoria","Sub_categoria","Nombre","Cantidad","Unidad","Precio","Fecha_de_lectura","Hora_de_lectura"]


def all_categories():
    cat_list_object:list[WebElement] = WebDriverWait(driver,10).until(EC.presence_of_all_elements_located(
        (By.XPATH,"//*[@id='csc-mdhz']/div/a")))
    cat_list = [{"text":cat.text, "href":cat.get_attribute("href")} for cat in cat_list_object]
    for cat in cat_list: 
        sub_categories(cat["text"],cat["href"] )


def sub_categories(cat, href):
    driver.get(href)
    subcat_list_object:list[WebElement] = WebDriverWait(driver,10).until(EC.presence_of_all_elements_located(
        (By.XPATH,"//*[@id='csc-mdhz']/a[@href]")))
    subcat_list = [{"text":cat.text, "href":cat.get_attribute("href")} for cat in subcat_list_object]
    products = []
    for subcat in subcat_list:
        driver.get(subcat["href"])
        products += get_products(cat,subcat["text"])
    df = pd.DataFrame(products,columns=COLUMNS)
    lenth["Cantidad elementos"] = lenth.get("Cantidad elementos",0) + len(products)
    db.to_data_base(df)
    print(f"Productos guardados, para la categoría {cat} y sub categoría {subcat['text']}")


def get_products(cat,subcat):
    productos = []
    while True:
        time.sleep(2)
        try:
            product_object:list[WebElement] = WebDriverWait(driver,5).until(
                EC.presence_of_all_elements_located((By.XPATH,"//div[@class='bq-tr']")))
        except TimeoutException as _:
            break
        for product in product_object:
            name = product.find_element(By.CSS_SELECTOR, 'p > span:nth-child(1) > a').text.strip() + \
                " " + product.find_element(By.CSS_SELECTOR, 'p > span:nth-child(2)').text.strip() + \
                " " + product.find_element(By.CSS_SELECTOR, 'p > span:nth-child(3)').text.strip()
            name = name.replace("  ", " ")
            precio = precio_promo(product.find_element(By.CSS_SELECTOR, "div>div>div>span:nth-child(3)").text)
            cantidad_unidad = product.find_element(By.CSS_SELECTOR, "p > span:nth-child(4)")
            cantidad_unidad = unidades_producto(cantidad_unidad.text.strip())
            date = datetime.now()
            productos.append([cat,subcat,name,cantidad_unidad[0],cantidad_unidad[1],precio,date.date(),date.time()])
        try:
            pag:WebElement = WebDriverWait(driver,3).until(EC.presence_of_element_located(
                (By.XPATH,"//a[@class='btn btn-primary btn-paginación' and contains(text(),'Página')]")))
            driver.execute_script("arguments[0].click();",pag)
        except TimeoutException as _:
            break
    return productos    

def precio_promo(valor:str):
    return float("".join(re.findall("\d+",valor)))

def unidades_producto(valor:str):
    try:
        val = re.search(".+(?= \w)",valor).group(0).replace(" ","")
        un = re.search("(?=.+)[a-zA-Z]", valor)
        if un: 
            un = un.group(0).strip()
            return val,un
        return val,"Unidad"
    except AttributeError as _:
        return "Unidad"
    

def main():
    global driver,db
    driver,db = init_scraping("https://losprecios.co/ara_t2","Ara")
    db.init_database_ara()
    lenth["Cantidad"] = db.consulta_sql_unica("select count(*) from D1;")[0]
    all_categories()
    send_email("Ara", lenth)
    driver.close()

lenth = {}