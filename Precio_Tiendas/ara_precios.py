from datetime import datetime
import time
from bs4 import BeautifulSoup
from bs4.element import PageElement, ResultSet
from selenium import webdriver
import pandas as pd
import re
from selenium.webdriver.remote.webelement import WebElement
import sqlite3

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
# import sys
# sys.path.append("./")
# import send_message



URL = 'https://aratiendas.com/rebajon/'
FILENAME = 'ara.xlsx'

def categoria_promo(valor:str):
    cat = re.search("(?<=categorias_rebajon-)[\w]+[-[\w]+]*(?= zonas_rebajon)",valor)
    cat = cat.group(0)
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
            return [valor,int(cant_uni[0]),cant_uni[1],adi]
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

            return [valor,int(cant_uni[0]),cant_uni[1],adi]
        else:
            cant = cant.replace("(","").replace(")","")
            cant_uni = cant.split()
            return [valor,int(cant_uni[0]),cant_uni[1],""]
    else:
        return [valor,1, "UN",""]

def form_precio_unitario(valor:str):
    exp = re.search("\d+(\,\d+)+",valor)
    exp = exp.group(0)
    prec = exp.split(",")
    if (len(prec) > 2 ):
        precio = ""
        for i in range(len(prec)-1):
            precio+=prec[i]
        precio += f".{precio[len(prec)-1]}"
        return float(precio)
    return float(exp.replace(",","."))

def form_precio_referencia(valor:str):
    try:
        exp = int(valor.replace("$","").replace(".","").strip())
    except Exception as _:
        exp = ""
    return exp

def precio_promo(valor:str):
    exp = re.search("\d+(\.\d+)*",valor).group(0)
    return int(exp.replace(".",""))

def organizar_articulos(page:ResultSet,cat,destacado:bool):
    products = []
    for des in page:
        des:PageElement
        
        if (destacado):
            cat = categoria_promo(str(des))
            item = list(des.find_all("p"))
            item.pop(0)
        else:
            delete:PageElement = des.find_next("div").find_next("div").find_next("div").find_next("section",{"class":"rebajon-item-hader rebajon-section"}).find("div")
            delete.extract()
            item = list(des.find_all("h2"))

        if (str(item[len(item)-1]).__contains__("PROHÍBASE EL EXPENDIO DE BEBIDAS")):
            item.pop(len(item)-1)

        if (str(item[0].text).strip() in ["PRECIO BAJO ARA","OFERTA",""]):
            item.pop(0)

        item = [it for it in item if it.text.strip() != "" or len(it.text.strip()) > 1]

        sep = nombre_cantidad(item[0].text.strip())
        precio = precio_promo(item[1].text.strip())
        if (len(item) == 5):
            prec_uni = form_precio_unitario(item[2].text.strip())
            prec_ref = form_precio_referencia(item[4].text.strip()) 
            products.append((sep[0],sep[1],sep[2],sep[3],precio,prec_uni,prec_ref,cat,destacado,datetime.now()))
        elif (len(item) == 4):
            prec_ref = form_precio_referencia(item[3].text.strip()) 
            products.append((sep[0],sep[1],sep[2],sep[3],precio,None,prec_ref,cat,destacado,datetime.now()))
        elif (len(item) == 3):
            prec_uni = form_precio_unitario(item[2].text.strip())
            products.append((sep[0],sep[1],sep[2],sep[3],precio,prec_uni,None,cat,destacado,datetime.now()))
        elif (len(item)== 2):
            products.append((sep[0],sep[1],sep[2],sep[3],precio,None,None,cat,destacado,datetime.now()))
        else:
            print("--------------------------NO pasó compa :c -----------------------------------------------------------")
            print(item)

    return products

def articulos_destacados():

    soup = BeautifulSoup(driver.page_source,'html5lib')
    destacados = soup.find_all("article",{"class":re.compile("elementor-post elementor-grid-item ecs-post-loop post-[\d]+ productos_rebajon type-productos_rebajon status-publish format-standard has-post-thumbnail hentry tag-destacado categorias_rebajon-[\w]+[-[\w]+]* zonas_rebajon-[\w]+")})
    productos = organizar_articulos(destacados,None,True)
    return productos

def articulos_no_destacados(num_cat:int=0):
    """
        Hace la lectura de los articulos no destacados, que están por categoría 
    """
    productos = []
    val = driver.find_elements_by_xpath("//div[@class='filter-rebajon-checkbox']")
    for i in range(num_cat):
        val.pop(0)
    for v in val:
        v:WebElement
        element = v.find_element_by_tag_name("label")
        driver.execute_script("arguments[0].click();", element)
        time.sleep(3)
        try:
            cont = driver.find_element_by_css_selector('#rebajon-content-box > h3')
            if (cont.text == "Cargando los productos..."):
                time.sleep(2)
                driver.refresh()
                time.sleep(2)
                articulos_no_destacados(num_cat)
        except Exception as _:
            pass

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
            productos+=organizar_articulos(articles,cat,False)
        driver.execute_script("arguments[0].click();", element)
        time.sleep(3)
        num_cat +=1
    return productos

def to_data_base(data:pd.DataFrame):
    

    conn = sqlite3.connect("./Precio_Tiendas/base_de_datos/Precios.sqlite")
    cur = conn.cursor()
    query = f"""
    CREATE TABLE IF NOT EXISTS Ara (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        Nombre_producto text,
        Cantidad int,
        Unidad text,
        Adicional text,
        Precio_promocion REAL,
        Precio_unidad REAL,
        precio_referencia REAL,
        Categoria text,
        mejor_promocion Boolean,
        Fecha_resultados TEXT
    );
    """
    cur.executescript(query)
    data[["Precio por unidad","precio Referencia"]] =data[["Precio por unidad","precio Referencia"]].fillna("") 
    data = data.astype("str")
    values = data.values
    q = "INSERT INTO Ara (Nombre_producto,Cantidad,Unidad ,Adicional,Precio_promocion,Precio_unidad,precio_referencia,Categoria,mejor_promocion,Fecha_resultados) VALUES (?,?,?,?,?,?,?,?,?,?)"
    cur.executemany(q,values)
    conn.commit()
    cur.close()
    conn.close()



def main():
    global driver
    
    chrome_options = Options()
    #chrome_options.add_argument('--headless')
    #chrome_options.add_argument("--disable-gpu")
    #chrome_options.add_argument('--no-sandbox')
    #chrome_options.add_argument('--disable-dev-shm-usage')
    #chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--log-level=3")
    driver = webdriver.Chrome(ChromeDriverManager().install(),chrome_options=chrome_options)
    driver.get("https://aratiendas.com/rebajon/centro/")

    productos = articulos_destacados()
    productos+=articulos_no_destacados()
    df = pd.DataFrame(productos, columns=["Nombre producto","Cantidad","Unidad","Adicional","Precio promoción","Precio por unidad","precio Referencia","Categoria","Mejor promoción","Fecha de resultados"])
    to_data_base(df)

    df_excel = pd.read_excel(f"Precio_Tiendas/excel_files/{FILENAME}", engine='openpyxl')
    df_total = df_excel.append(df)
    df_total.to_excel(f"Precio_Tiendas/excel_files/{FILENAME}",engine = 'xlsxwriter',index=False)

    print("Se guardan los archivos para Ara")
    driver.close()

main()