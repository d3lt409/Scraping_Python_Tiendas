from datetime import datetime
import sys
import time
from bs4 import BeautifulSoup
import bs4
from bs4 import element
from bs4.element import PageElement, ResultSet
from selenium import webdriver
import pandas as pd
import re
from selenium.webdriver.common.by import By

from selenium.webdriver.remote.webelement import WebElement

def categoria_promo(valor:str):
    cat = re.search("elementor-post elementor-grid-item ecs-post-loop post-[\d]+ productos_rebajon type-productos_rebajon status-publish format-standard has-post-thumbnail hentry tag-destacado categorias_rebajon-[\w]+(-[\w]+)+ zonas_rebajon-nacional",valor)
    cat = cat.group(0)
    cat = re.search("categorias_rebajon-[\w]+(-[\w]+)+",cat)
    cat = cat.group(0)
    cat = cat.replace("categorias_rebajon-","")
    cat = cat.replace("-"," ")
    cat = cat.capitalize()
    return cat

def nombre_cantidad(valor:str):
    valor = valor.replace(".","")
    cant = re.search("( (X|DE) (\d)+ (G|ML|M|CM|UN)(.*))|( (DE|X) \d+ X \d+ (G|ML|M|CM|UN)(.*))|(\(\d+ (G|ML|M|CM|UN)\))",valor)
    print(valor)
    if (cant):
        valor = valor.replace(cant.group(0),"")
        cant = cant.group(0).strip()
        if (cant.startswith("DE")):
            print(cant)
            cant = cant[3:]
            cant_uni = re.search("^\d+ (G|ML|M|CM|UN)|\d+ X \d+ (G|ML|M|CM|UN)",cant)
            adi = cant.replace(cant_uni.group(0),"").strip()
            cant_uni = cant_uni.group(0).split()
            return [valor,cant_uni[0],cant_uni[1],adi]
        elif (cant.startswith("X")):
            print(cant)
            cant = cant[2:]
            cant_uni = re.search("^\d+ (G|ML|M|CM|UN)|\d+ X \d+ (G|ML|M|CM|UN)",cant)
            adi = cant.replace(cant_uni.group(0),"").strip()
            cant_uni = cant_uni.group(0).split()
            return [valor,cant_uni[0],cant_uni[1],adi]
        else:
            cant = cant.replace("(","").replace(")","")
            cant_uni = cant.split()
            return [valor,cant_uni[0],cant_uni[1],""]
    else:
        return [valor,1, "UN",""]

def organizar_articulos(page,cat = None):
    products = []
    for des in page:
        des:PageElement
        
        item = list(des.find_all("h2",{"class":"elementor-heading-title elementor-size-default"}))
        if (str(item[len(item)-1]).__contains__("PROHÍBASE EL EXPENDIO DE BEBIDAS")):
            item.pop(len(item)-1)
        sep = nombre_cantidad(item[1].text.strip())
        print(sep)
        if (cat):
            if (len(item) == 6):
                products.append((sep[0],sep[1],sep[2],sep[3],item[2].text.strip(),item[3].text.strip(),item[5].text.strip(),cat,True))
            elif (len(item) == 5):
                products.append((sep[0],sep[1],sep[2],sep[3],item[2].text.strip(),item[4].text.strip(),cat,False))
            elif (len(item) == 4):
                products.append((sep[0],sep[1],sep[2],sep[3],item[2].text.strip(),None,item[3].text.strip(),cat,False))
            else:
                print("--------------------------NO pasó compa :c -----------------------------------------------------------")
                print(item)
                print(len(item))
        else:
            cat = categoria_promo(str(des))
            if (len(item) == 6):
                products.append((sep[0],sep[1][:len(sep[1])-1],item[2].text.strip(),item[3].text.strip(),item[5].text.strip(),cat,True))
            elif (len(item) == 5):
                products.append((sep[0],sep[1][:len(sep[1])-1],item[2].text.strip(),None,item[4].text.strip(),cat,True))
            else:
                print("--------------------------NO pasó compa :c -----------------------------------------------------------")
                print(item)
    return products

URL = 'https://aratiendas.com/inicio/centro/'

driver = webdriver.Chrome('chrome/chromedriver')
driver.get("https://aratiendas.com/rebajon/centro/")

soup = BeautifulSoup(driver.page_source,'html5lib')
destacados = soup.find_all("article",{"class":re.compile("elementor-post elementor-grid-item ecs-post-loop post-[\d]+ productos_rebajon type-productos_rebajon status-publish format-standard has-post-thumbnail hentry tag-destacado categorias_rebajon-[\w]+(-[\w]+)+ zonas_rebajon-nacional")})
productos = organizar_articulos(destacados)

val = driver.find_elements_by_xpath("//div[@class='filter-rebajon-checkbox']")

productos = []
for v in val:
    v:WebElement
    element = v.find_element_by_tag_name("label")
    while True:
        try:
            element.click()
            break
        except Exception as e:
            driver.fullscreen_window()
            driver.execute_script(f"window.scrollTo(0, {driver.get_window_position()['y']-100});")
            continue
    
    cat = v.find_elements_by_tag_name("div")
    cat = cat[len(cat)-1].text
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source,'html5lib')
    articles = soup.find_all("article",{"class":re.compile("elementor-post elementor-grid-item ecs-post-loop post-[\d]+ productos_rebajon type-productos_rebajon status-publish format-standard has-post-thumbnail hentry categorias_rebajon-[\w]+(-[\w]+)+ zonas_rebajon-nacional")})
    productos+=organizar_articulos(articles,cat)
    while True:
        try:
            element.click()
            break
        except Exception as e:
            driver.fullscreen_window()
            driver.execute_script(f"window.scrollTo(0, {driver.get_window_position()['y']-100});")
            continue

df = pd.DataFrame(productos)#columns=["Nombre producto","Cantidad","Precio promoción","Cantidad por producto","precio normal","Categoria","Mejor promoción"])
df.to_excel("ara.xlsx",engine = 'xlsxwriter',index=False)
driver.close()
