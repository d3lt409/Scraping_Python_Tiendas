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
import sqlalchemy


FILENAME = "Ara_cornershopapp.xlsx"

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
        (By.XPATH,"//div[@class='menu-list-item grid-column width-12']/div/div/p")))
    cat_list = [val.text for val in cat_list_object if not val.text.__contains__("Todo")]
    products = []
    for cat in cat_list:
        driver.execute_script("arguments[0].click();",
                    WebDriverWait(driver,10).until(EC.presence_of_element_located(
        (By.XPATH,f"//div[@class='menu-list-item grid-column width-12']/div/div/p[text()='{cat}']"))))
        products+=get_products(cat)
        driver.get("https://web.cornershopapp.com/store/1520/aisles")
        
    return products


def get_products(cat):
    time.sleep(1)
    scroll_down()
    time.sleep(1)
    productos = []
    soup = BeautifulSoup(driver.page_source,'html5lib')
    product_object:ResultSet = soup.find_all("div",{"class":"product-info"})
    for product in product_object:
        product:PageElement
        name = product.find("h3",{"class":"name"}).text.strip()
        precio = precio_promo(product.find_next("p",{"class":"price"}).find("span").text)
        cantidad_unidad = product.find("p",{"class":"package"})
        if cantidad_unidad: cantidad_unidad = unidades_producto(cantidad_unidad.text.strip())
        else: continue
        productos.append([cat,name,cantidad_unidad[0],cantidad_unidad[1],precio,datetime.now()])
    return productos    

def scroll_down():
    heigth = driver.execute_script("return document.body.scrollHeight")
    driver.execute_script(f"window.scrollTo(0, {heigth});")

def precio_promo(valor:str):
    exp = re.search("\d+(\.\d+)*",valor).group(0)
    return float(exp.replace(".",""))

def unidades_producto(valor:str):
    try:
        val = re.search("\d+[\.\d+]* \w{1,3}|\d+\w{1,3}",valor).group(0)
        if (len(val.split()) == 1): 
            cantidad = re.search("\d+",val).group(0)
            unidad = val.replace(cantidad,"")
            return [cantidad,unidad]
        return val.split()
    except AttributeError as _:
        val = re.search("\w+: \w{1,3}",valor).group(0)
        return val.replace(":","").split()
    

def to_database(df:pd.DataFrame):
        
    connection_uri = "sqlite:///Precio_Tiendas/base_de_datos/Precios.sqlite"
    engine = sqlalchemy.create_engine(connection_uri)
    query = f"""
        CREATE TABLE IF NOT EXISTS Ara_cornershopapp (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
            Categoria text,
            Nombre text,
            Cantidad INTEGER,
            Unidad text,
            Precio REAL,
            Fecha_de_lectura TEXT
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
    df = pd.DataFrame(all_categories(),columns=["Categoria","Nombre","Cantidad","Unidad","Precio","Fecha_de_lectura"])
    to_database(df)
    try:
        df_excel = pd.read_excel(f"Precio_Tiendas/excel_files/{FILENAME}")
        df_total = pd.concat([df_excel,df])
        df_total.to_excel(f"Precio_Tiendas/excel_files/{FILENAME}",index=False)
    except Exception as _:
        df.to_excel(f"Precio_Tiendas/excel_files/{FILENAME}",index=False)

    print(f"Guardado a las {datetime.now()} para {FILENAME}")
    driver.close()

main()