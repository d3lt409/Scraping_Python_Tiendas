from os import replace
import time
from bs4 import BeautifulSoup
from bs4 import element
from bs4.element import PageElement
from selenium import webdriver
import pandas as pd
import re

from selenium.webdriver.remote.webelement import WebElement


URL = 'https://aratiendas.com/inicio/centro/'

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
    if (cant):
        valor = valor.replace(cant.group(0),"")
        cant = cant.group(0).strip()
        if (cant.startswith("DE")):
            cant = cant[3:]
            try:
                cant_uni = re.search("^\d+ (G|ML|M|CM|UN)",cant)
                adi = cant.replace(cant_uni.group(0),"").strip()
                cant_uni = cant_uni.group(0).split()
            except Exception as _:
                cantidad = re.search("^\d+ X \d+",cant).group(0)
                unidad = re.search("(G|ML|M|CM|UN)",cant).group(0)
                adi = cant.replace(cantidad,"").replace(unidad,"").strip()
                cant_uni = [cantidad,unidad]
            return [valor,cant_uni[0],cant_uni[1],adi]
        elif (cant.startswith("X")):
            cant = cant[2:]
            try:
                cant_uni = re.search("^\d+ (G|ML|M|CM|UN)",cant)
                adi = cant.replace(cant_uni.group(0),"").strip()
                cant_uni = cant_uni.group(0).split()
            except Exception as _:
                cantidad = re.search("^\d+ X \d+",cant).group(0)
                unidad = re.search("(G|ML|M|CM|UN)",cant).group(0)
                adi = cant.replace(cantidad,"").replace(unidad,"").strip()
                cant_uni = [cantidad,unidad]

            return [valor,cant_uni[0],cant_uni[1],adi]
        else:
            cant = cant.replace("(","").replace(")","")
            cant_uni = cant.split()
            return [valor,cant_uni[0],cant_uni[1],""]
    else:
        return [valor,1, "UN",""]

def form_precio_unitario(valor:str):
    exp = re.search("\d+(\,\d+)+",valor).group(0)
    return float(exp.replace(",","."))
def form_precio_referencia(valor:str):
    exp = valor.replace("$","").replace(".","").strip()
    return exp

def organizar_articulos(page,cat = None):
    products = []
    for des in page:
        des:PageElement
        
        item = list(des.find_all("h2",{"class":"elementor-heading-title elementor-size-default"}))
        if (str(item[len(item)-1]).__contains__("PROHÍBASE EL EXPENDIO DE BEBIDAS")):
            item.pop(len(item)-1)
        sep = nombre_cantidad(item[1].text.strip())
        precio = item[2].text.replace(".","").replace("$","").strip()
        if (cat):
            if (len(item) == 6):
                prec_uni = form_precio_unitario(item[3].text.strip())
                prec_ref = form_precio_referencia(item[5].text.strip()) 
                products.append((sep[0],sep[1],sep[2],sep[3],precio,prec_uni,prec_ref,cat,True))
            elif (len(item) == 5):
                products.append((sep[0],sep[1],sep[2],sep[3],precio,item[3].text.strip(),item[4].text.strip(),cat,False))
            elif (len(item) == 4):
                prec_uni = form_precio_unitario(item[3].text.strip())
                products.append((sep[0],sep[1],sep[2],sep[3],precio,precio_uni,None,cat,True))
            else:
                print("--------------------------NO pasó compa :c -----------------------------------------------------------")
                print(item)
                print(len(item))
        else:
            cat = categoria_promo(str(des))
            if (len(item) == 4):
                products.append((sep[0],sep[1],sep[2],sep[3],precio,None,item[3].text.strip(),cat,False))
            if (len(item) == 6):
                products.append((sep[0],sep[1],sep[2],sep[3],precio,item[3].text.strip(),item[5].text.strip(),cat,True))
            elif (len(item) == 5):
                products.append((sep[0],sep[1],sep[2],sep[3],precio,None,item[4].text.strip(),cat,True))
            else:
                print("--------------------------NO pasó compa :c -----------------------------------------------------------")
                print(item)
    return products

def articulos_destacados():

    soup = BeautifulSoup(driver.page_source,'html5lib')
    destacados = soup.find_all("article",{"class":re.compile("elementor-post elementor-grid-item ecs-post-loop post-[\d]+ productos_rebajon type-productos_rebajon status-publish format-standard has-post-thumbnail hentry tag-destacado categorias_rebajon-[\w]+(-[\w]+)+ zonas_rebajon-nacional")})
    productos = organizar_articulos(destacados)
    return productos

driver = webdriver.Chrome('chrome/chromedriver')
driver.get("https://aratiendas.com/rebajon/centro/")
productos = articulos_destacados()

val = driver.find_elements_by_xpath("//div[@class='filter-rebajon-checkbox']")
for v in val:
    v:WebElement
    element = v.find_element_by_tag_name("label")
    driver.execute_script("arguments[0].click();", element)
    time.sleep(3)
    xpath_pages = "//div[@id='rebajon-content-box']/div/nav/div"
    pages:list = driver.find_elements_by_xpath(xpath_pages)
    for i in range(len(pages)):
        ele = driver.find_element_by_css_selector(f"#rebajon-content-box > div > nav > div:nth-child({i+1})")
        driver.execute_script("arguments[0].click();", ele)
        time.sleep(3)
        cat = v.find_elements_by_tag_name("div")
        cat = cat[len(cat)-1].text
        soup = BeautifulSoup(driver.page_source,'html5lib')
        content = soup.find("div",{"id":"rebajon-content-box"})
        articles = content.find_all("article",{"class":re.compile("elementor-post elementor-grid-item ecs-post-loop post-[\d]+ productos_rebajon type-productos_rebajon status-publish format-standard has-post-thumbnail hentry categorias_rebajon-[\w]+(-[\w]+)+ zonas_rebajon-nacional")})
        productos+=organizar_articulos(articles,cat)
    driver.execute_script("arguments[0].click();", element)
    time.sleep(3)

df = pd.DataFrame(productos)#columns=["Nombre producto","Cantidad","Unidad","Adicional","Precio promoción","Precio por unidad","precio Referencia","Categoria","Mejor promoción"])
df.to_excel("ara.xlsx",engine = 'xlsxwriter',index=False)
driver.close()
