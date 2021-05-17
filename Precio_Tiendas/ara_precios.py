from datetime import datetime
import time
from bs4 import BeautifulSoup
from bs4.element import PageElement, ResultSet
from selenium import webdriver
import pandas as pd
import re
from selenium.webdriver.remote.webelement import WebElement

URL = 'https://aratiendas.com/inicio/centro/'
FILENAME = 'ara.xlsx'

def categoria_promo(valor:str):
    cat = re.search("elementor-post elementor-grid-item ecs-post-loop post-[\d]+ productos_rebajon type-productos_rebajon status-publish format-standard has-post-thumbnail hentry tag-destacado categorias_rebajon-[\w]+(-[\w]+)* zonas_rebajon-nacional",valor)
    cat = cat.group(0)
    cat = re.search("categorias_rebajon-[\w]+(-[\w]+)*",cat)
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
    exp = int(valor.replace("$","").replace(".","").strip())
    return exp

def precio_promo(valor:str):
    exp = re.search("\d+(\.\d+)+",valor).group(0)
    return int(exp.replace(".",""))

def organizar_articulos(page:ResultSet,cat,destacado:bool):
    products = []
    for des in page:
        des:PageElement
        if (destacado):
            cat = categoria_promo(str(des))
        item = list(des.find_all("h2"))
        for it in item:
            if (it.text == ""):
                item.remove(it)
        if (str(item[len(item)-1]).__contains__("PROHÍBASE EL EXPENDIO DE BEBIDAS")):
            item.pop(len(item)-1)

        sep = nombre_cantidad(item[1].text.strip())
        precio = precio_promo(item[2].text.strip())
        if (len(item) == 6):
            prec_uni = form_precio_unitario(item[3].text.strip())
            prec_ref = form_precio_referencia(item[5].text.strip()) 
            products.append((sep[0],sep[1],sep[2],sep[3],precio,prec_uni,prec_ref,cat,destacado,datetime.now()))
        elif (len(item) == 5):
            prec_ref = form_precio_referencia(item[4].text.strip()) 
            products.append((sep[0],sep[1],sep[2],sep[3],precio,None,prec_ref,cat,destacado,datetime.now()))
        elif (len(item) == 4):
            prec_uni = form_precio_unitario(item[3].text.strip())
            products.append((sep[0],sep[1],sep[2],sep[3],precio,prec_uni,None,cat,destacado,datetime.now()))
        elif (len(item)== 3):
            products.append((sep[0],sep[1],sep[2],sep[3],precio,None,None,cat,destacado,datetime.now()))
        else:
            print("--------------------------NO pasó compa :c -----------------------------------------------------------")
            print(item)

    return products

def articulos_destacados():

    soup = BeautifulSoup(driver.page_source,'html5lib')
    destacados = soup.find_all("article",{"class":re.compile("elementor-post elementor-grid-item ecs-post-loop post-[\d]+ productos_rebajon type-productos_rebajon status-publish format-standard has-post-thumbnail hentry tag-destacado categorias_rebajon-[\w]+(-[\w]+)* zonas_rebajon-nacional")})
    productos = organizar_articulos(destacados,None,True)
    return productos

def articulos_no_destacados():
    """
        Hace la lectura de los articulos no destacados, que están por categoría 
    """
    productos = []
    val = driver.find_elements_by_xpath("//div[@class='filter-rebajon-checkbox']")
    for v in val:
        v:WebElement
        element = v.find_element_by_tag_name("label")
        driver.execute_script("arguments[0].click();", element)
        time.sleep(3)
        while True:
            try:
                cont = driver.find_element_by_css_selector('#rebajon-content-box > h3')
                if (cont.text == "Cargando los productos..."):
                    time.sleep(4)
                    print("No quiere cargar la página :(")
                    continue
                else:
                    break
            except Exception as _:
                break

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
    return productos

def main():
    global driver
    driver = webdriver.Chrome('chrome/chromedriver')
    driver.get("https://aratiendas.com/rebajon/centro/")
    try:
        productos = articulos_destacados()
        productos+=articulos_no_destacados()
        df = pd.DataFrame(productos, columns=["Nombre producto","Cantidad","Unidad","Adicional","Precio promoción","Precio por unidad","precio Referencia","Categoria","Mejor promoción","Fecha de resultados"])
    except Exception as e:
        print(e)
        return
    try:
        df_excel = pd.read_excel(f"Precio_Tiendas/excel_files/{FILENAME}")
        df_total = df_excel.append(df)
        df_total.to_excel(f"Precio_Tiendas/excel_files/{FILENAME}",engine = 'xlsxwriter',index=False)
    except Exception as _:
        df.to_excel(f"Precio_Tiendas/excel_files/{FILENAME}",engine = 'xlsxwriter',index=False)

    print(f"Guardado a las {datetime.now()} para {FILENAME}")
    driver.close()

main()