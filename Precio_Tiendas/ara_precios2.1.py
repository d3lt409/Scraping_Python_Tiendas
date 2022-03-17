from datetime import datetime
from bs4 import BeautifulSoup
from bs4.element import PageElement, ResultSet
import time
from selenium import webdriver
import pandas as pd
import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException,NoSuchElementException

import sqlalchemy

FILENAME = "Ara_cornershopapp.xlsx"
COLUMNS = ["Categoria","Sub_categoria","Nombre","Cantidad","Unidad","Precio","Fecha_de_lectura","Hora_de_lectura"]

chrome_options = Options()
#chrome_options.add_argument('--headless')
#chrome_options.add_argument("--disable-gpu")
#chrome_options.add_argument('--no-sandbox')
#chrome_options.add_argument('--disable-dev-shm-usage')
#chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--log-level=3")
driver = webdriver.Chrome(ChromeDriverManager().install(),options=chrome_options)
driver.get("https://web.cornershopapp.com/store/1520/aisles")

def all_categories():
    global driver
    cat_list_object = WebDriverWait(driver,10).until(EC.presence_of_all_elements_located(
        (By.XPATH,"//div[@class='menu-list-item-content']/div[@class='content-text']/p/span")))
    cat_list:list[str] = [val.text for val in cat_list_object]
    products = []
    for cat in cat_list:
        driver.execute_script("arguments[0].click();",
                    WebDriverWait(driver,10).until(EC.presence_of_element_located(
        (By.XPATH,f"//div[@class='menu-list-item-content']/div[@class='content-text']/p/span[text()='{cat}']"))))
        products+=sub_categories(cat.replace("Todo en ",""))
        driver.get("https://web.cornershopapp.com/store/1520/aisles")
        
    return products


def sub_categories(cat):
    scroll_down(2)
    subcat_list_objects = driver.find_elements_by_xpath("//div[@class='aisle-box card']")
    products = []
    positions_more_elements = []
    for i,subcat_object in enumerate(subcat_list_objects):
        subcat_object:WebElement
        html = subcat_object.get_attribute('innerHTML')
        subcat = WebDriverWait(driver,2).until(lambda _: 
            subcat_object.find_element_by_xpath("div[contains(@class,'card-header')]/h2")).text
        try:
            WebDriverWait(driver,2).until(lambda _:
                subcat_object.find_element_by_xpath("div/div[@class='see-all-cell']/button"))
            positions_more_elements.append(i+1)
        except (TimeoutException,NoSuchElementException):
            products += get_products(html,cat,subcat)
    current = driver.current_url
    for pos in positions_more_elements:
        element:WebElement = WebDriverWait(driver,5).until(lambda _:
            driver.find_element_by_xpath(f"//div[@class='aisle-box card'][{pos}]/div/div[@class='see-all-cell']/button"))
        driver.execute_script("arguments[0].click();",element)
        scroll_down(1)
        subcat = WebDriverWait(driver,2).until(lambda _: 
            driver.find_element_by_xpath("//div[contains(@class,'card-header')]/h2")).text
        products += get_products(driver.page_source,cat,subcat)
        if (pos == positions_more_elements[len(positions_more_elements)-1]): break
        driver.get(current)
        scroll_down(2)
    df = pd.DataFrame(products,columns=COLUMNS)
    to_database(df)
    print(f"Productos guardados, para la categoría {cat}")
    return products

def get_products(html,cat,subcat):
    time.sleep(2)
    productos = []
    soup = BeautifulSoup(html,'html5lib')
    product_object:ResultSet = soup.find_all("div",{"class":"product-info"})
    for product in product_object:
        product:PageElement
        name = product.find("h3",{"class":"name"}).text.strip()
        precio = precio_promo(product.find_next("p",{"class":"price"}).find("span").text)
        cantidad_unidad = product.find("p",{"class":"package"})
        if cantidad_unidad: cantidad_unidad = unidades_producto(cantidad_unidad.text.strip())
        else: continue
        date = datetime.now()
        productos.append([cat,subcat,name,cantidad_unidad[0],cantidad_unidad[1],precio,date.date(),date.time()])
    return productos    

def scroll_down(time_limit,init=0):
    time.sleep(time_limit)
    heigth = driver.execute_script("return document.body.scrollHeight")
    for val in range(init,heigth,4):
        driver.execute_script(f"window.scrollTo(0, {val});")
    if driver.execute_script("return document.body.scrollHeight")-heigth >4:
        scroll_down(0,heigth)

def precio_promo(valor:str):
    exp = re.search("\d+(\.\d+)*",valor).group(0)
    return float(exp.replace(".",""))

def unidades_producto(valor:str):
    try:
        val = re.search("\d+ x \d+ \w+|\d+[\.\d+]* \w{1,6}|\d+[\.\d+]*\w{1,6}",valor).group(0)
        if len(val.split())==4:
            cantidad = re.search("\d+ x \d+",val).group(0)
            unidad = val.replace(cantidad,"").strip()
            return [cantidad.replace(" ",""),unidad]
        if (len(val.split()) == 1): 
            cantidad = re.search("\d+[\.\d+]*",val).group(0)
            unidad = val.replace(cantidad,"")
            return [cantidad,unidad]
        return val.split()
    except AttributeError as _:
        pass
    try:
        val = re.search("\w+: \w{1,3}",valor).group(0)
        return val.replace(":","").split()
    except AttributeError as _:
        return "Unidad"
    

def to_database(df:pd.DataFrame):
        
    connection_uri = "sqlite:///Precio_Tiendas/base_de_datos/Precios.sqlite"
    engine = sqlalchemy.create_engine(connection_uri)
    query = f"""
        CREATE TABLE IF NOT EXISTS Ara_cornershopapp (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
            Categoria text,
            Sub_categoria text,
            Nombre text,
            Cantidad INTEGER,
            Unidad text,
            Precio REAL,
            Fecha_de_lectura TEXT,
            Hora_de_lectura TEXT,
            UNIQUE(Nombre,Fecha_de_lectura) ON CONFLICT IGNORE
        );
        """
    engine.execute(query)
    
    df.to_sql("Ara_cornershopapp",engine,
              if_exists='append', index=False,
            #   dtype={
            #       "Categoria":sqlalchemy.Text,
            #       "Nombre":sqlalchemy.Text,
            #       "Cantidad":sqlalchemy.Integer,
            #       "Unidad":sqlalchemy.Text,
            #       "Precio":sqlalchemy.REAL,
            #       "Fecha_de_lectura":sqlalchemy.Text
            #   }
    )
    engine.dispose()

def main():
    df = pd.DataFrame(all_categories(),columns=COLUMNS)
    try:
        df_excel = pd.read_excel(f"Precio_Tiendas/excel_files/{FILENAME}")
        df_total = pd.concat([df_excel,df])
        df_total.to_excel(f"Precio_Tiendas/x|/{FILENAME}",index=False)
    except Exception as _:
        df.to_excel(f"Precio_Tiendas/excel_files/{FILENAME}",index=False)

    print(f"Guardado a las {datetime.now()} para {FILENAME}")
    driver.close()

main()