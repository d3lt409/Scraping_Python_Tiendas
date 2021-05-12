from datetime import datetime
import sys
import time
from bs4 import BeautifulSoup
import bs4
from bs4.element import PageElement, ResultSet
from selenium import webdriver
import pandas as pd
import re
from selenium.webdriver.common.by import By

from selenium.webdriver.remote.webelement import WebElement

def categoria_promo(valor:str):
    cat = re.search("elementor-post elementor-grid-item ecs-post-loop post-[\d]+ productos_rebajon type-productos_rebajon status-publish format-standard has-post-thumbnail hentry tag-destacado categorias_rebajon-[\w]+(-[\w]+)+ zonas_rebajon-nacional",valor)
    print(cat)
    cat = cat.group(0)
    cat = re.search("categorias_rebajon-[\w]+(-[\w]+)+",cat)
    cat = cat.group(0)
    cat = cat.replace("categorias_rebajon-","")
    cat = cat.replace("-"," ")
    cat = cat.capitalize()
    return cat

def organizar_articulos(page,cat = None):
    products = []
    for des in page:
        des:PageElement
        item = list(des.find_all("h2",{"class":"elementor-heading-title elementor-size-default"}))
        sep = item[1].text.split(" DE ")
        if (len(sep) <= 1 ):
            sep = item[1].text.split(" X ")  
        if (cat):
            if (len(item) == 6):
                products.append((sep[0],sep[1][:len(sep[1])-1],item[2].text.strip(),item[3].text.strip(),item[5].text.strip(),cat,True))
            elif (len(item) == 5):
                products.append((sep[0],sep[1][:len(sep[1])-1],item[2].text.strip(),item[4].text.strip(),cat,False))
            elif (len(item) == 4):
                products.append((sep[0],sep[1][:len(sep[1])-1],item[2].text.strip(),None,item[3].text.strip(),cat,False))
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
            print(e)
            time.sleep(1)
            continue
    
    cat = v.find_element_by_xpath("//div").text
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source,'html5lib')
    articles = soup.find_all("article",{"class":re.compile("elementor-post elementor-grid-item ecs-post-loop post-[\d]+ productos_rebajon type-productos_rebajon status-publish format-standard has-post-thumbnail hentry categorias_rebajon-[\w]+(-[\w]+)+ zonas_rebajon-nacional")})
    productos+=organizar_articulos(articles,cat)
    while True:
        try:
            element.click()
            break
        except Exception as e:
            print(e)
            time.sleep(1)
            continue

df = pd.DataFrame(productos,columns=["Nombre producto","Cantidad","Precio promoción","Cantidad por producto","precio normal","Categoria","Mejor promoción"])
print(df)