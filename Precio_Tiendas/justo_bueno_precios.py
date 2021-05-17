from datetime import datetime
from shutil import ExecError
import time
from bs4 import BeautifulSoup
from bs4.element import PageElement, ResultSet
from numpy import product
from rasterio.errors import DriverCapabilityError
from selenium import webdriver
import pandas as pd
import re
from selenium.webdriver.remote.webelement import WebElement

FILENAME = "justo_y_bueno.xlsx"

driver = webdriver.Chrome('chrome/chromedriver')
driver.get("https://monedero.justoybueno.com/home")


def start_city():
    time.sleep(2)
    global cities
    cities =[str(val.text) for val in driver.find_elements_by_xpath("//ul[@class='list-group list-group-flush']/li[@class='list-group-item texto-lista ng-star-inserted']")] 
    input_city = driver.find_element_by_css_selector('#toastPositioner > ngb-modal-window > div > div > app-ciudad-modal > div.modal-header > form > input')
    name = re.search("^[A-Z][a-z]+",cities.pop(0)).group(0)
    input_city.send_keys(name)
    driver.execute_script("arguments[0].click();", driver.find_element_by_css_selector('#toastPositioner > ngb-modal-window > div > div > app-ciudad-modal > div.modal-body > ul > li'))
    return all_categories(name)

def for_each_city():
    change = driver.find_element_by_css_selector('#nav-ciudad')
    time.sleep(2)
    driver.execute_script("arguments[0].click();", change)
    time.sleep(3)
    input_city = driver.find_element_by_css_selector('#toastPositioner > ngb-modal-window > div > div > app-ciudad-modal > div.modal-header > form > input')
    name = re.search("^[A-Z][a-z]+",cities.pop(0)).group(0)
    input_city.send_keys(name)
    time.sleep(2)
    driver.execute_script("arguments[0].click();", driver.find_element_by_css_selector('#toastPositioner > ngb-modal-window > div > div > app-ciudad-modal > div.modal-body > ul > li'))
    return all_categories(name)

def all_categories(city:str):
    product_cat = []
    driver.execute_script("arguments[0].click();", driver.find_element_by_xpath("//button[@id='boton-menu']"))
    global categories
    time.sleep(2)
    global_cat = driver.find_elements_by_xpath("//span[@class='texto-categoria']")
    time.sleep(2)
    categories =[str(val.text) for val in global_cat] 

    name_cat = categories.pop(0)
    driver.execute_script("arguments[0].click();",driver.find_element_by_xpath(f"//span[@class='texto-categoria'][contains(text(),'{name_cat}')]"))
    try:
        driver.execute_script("arguments[0].click();",driver.find_element_by_xpath(f"//span[@class='texto-filtrado'][contains(text(),'{name_cat}')]"))
    except Exception as _:
        product_cat+=description_articles(city,name_cat)
    time.sleep(2)
    driver.execute_script("arguments[0].click();", driver.find_element_by_xpath("//button[@id='boton-menu']"))
    time.sleep(3)
    name_cat = categories.pop(0)
    driver.execute_script("arguments[0].click();",driver.find_element_by_xpath(f"//span[@class='texto-categoria'][contains(text(),'{name_cat}')]"))
    time.sleep(3)
    try:
        driver.execute_script("arguments[0].click();",driver.find_element_by_xpath(f"//span[@class='texto-filtrado'][contains(text(),'{name_cat}')]"))
        product_cat+=sub_categories(city,name_cat)
    except Exception as e:
        pass
    return product_cat

def sub_categories(city,cat):
    sub = driver.find_elements_by_xpath("//li[@class='mt-3 row ng-star-inserted']")
    product_sub = []
    for i in range(1,len(sub)):
        time.sleep(2)
        driver.execute_script("arguments[0].click();",sub[i])
        mostrar_todo()
        time.sleep(3)
        product_sub+=description_articles(city,cat,driver.find_element_by_css_selector(f"#toastPositioner > app-root > section > app-main > app-productos > div > div > div.d-none.d-md-block.col-lg-2.col-md-3.px-0.bt-2.ng-star-inserted > div > div:nth-child(2) > div > ul > li:nth-child({i+1}) > div.col.pl-0").text)
    return product_sub

def mostrar_todo():
    time.sleep(2)
    try:
        driver.execute_script("arguments[0].click();",driver.find_element_by_css_selector('#masProductos')) 
        mostrar_todo()
    except Exception as _:
        return

def description_articles(city,cat,sub_categori = ""):
    productos = []
    soup = BeautifulSoup(driver.page_source,'html5lib')
    articles = soup.find_all("div",{"class":"card-body text-center"})
    for art in articles:
        name_cant_uni = nombre_cantidad(art.find("h5").text)
        unidad = precio_unitario(art.find("p",{"class":"card-text"}).text)
        precio = precio_promo(art.find("p",{"class":"currency"}).text)
        productos.append([city,name_cant_uni[0],cat,sub_categori,name_cant_uni[1],name_cant_uni[2],unidad,precio,datetime.now()])
    return productos


def nombre_cantidad(valor:str):
    valor = valor.replace(".","")
    cant_uni = re.search("\d+ (ml|l|g|ud(s){0,1}|und|Ml|L|G|UD(s){0,1}|UND)",valor)
    if (cant_uni):
        cant_uni = cant_uni.group(0).split()
        nombre = valor.replace(cant_uni,valor).strip()
        if (cant_uni[1].startswith("U") or cant_uni[1].startswith("u")):
            cant_uni[1] = "UN"
        return [nombre,int(cant_uni[0]),cant_uni[1]]
    else:
        return [valor,1,"UN"]

def precio_unitario(valor:str):
    precio = valor.replace(".","")
    precio = valor.replace(",",".")
    return precio_promo(precio)

def precio_promo(valor:str):
    exp = re.search("\d+(\.\d+)*",valor).group(0)
    return float(exp.replace(".",""))

producto_final = start_city()
producto_final += for_each_city()

df = pd.DataFrame(producto_final,columns=["Ciudad","Nomnre","Categoria","Sub categoria","Cantidad","Unidad","Precio","Fecha de lectura"])
df.to_excel(f"Precio_Tiendas/excel_files/{FILENAME}",engine = 'xlsxwriter',index=False)
