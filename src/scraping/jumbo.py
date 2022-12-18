from datetime import datetime
import json
import time
from bs4 import BeautifulSoup
import pandas as pd
import re
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

import sys
sys.path.append(".")

from src.utils.util import  crash_refresh_page, init_scraping,ready_document

FILENAME = "jumbo_precios.xlsx"
MAIN_PAGE = "https://www.tiendasjumbo.co"
COLUMNS = ["Departamento", "Categoria", "Sub_categoria", "Nombre_producto", "Precio_oferta", "Cantidad",
           "Unidad", "Precio_normal", "Fecha_resultados", "Hora_resultados"]


def each_departments_categories():
    global current_url_jumbo
    ready_document(driver,current_url_jumbo)
    dep_button:WebElement = WebDriverWait(driver,30).until(EC.presence_of_element_located(
                (By.XPATH,"//*[@id='menu-item-music-store']")
            ))
    time.sleep(2)
    ActionChains(driver).click_and_hold(dep_button).perform()
    dep_element_object:list[str] =[el.get_attribute("href") for el in WebDriverWait(driver, 30).until(
        EC.presence_of_all_elements_located(
            (By.XPATH, "//ul[@class='tiendasjumboqaio-jumbo-main-menu-2-x-nav_menu tiendasjumboqaio-jumbo-main-menu-2-x-nav_menu--header-submenu-item']/div/div/li//a"))) ] 
    dep_cat_elements:dict[str,list[list[str]]] = {}
    for a in dep_element_object:
        el: WebElement = WebDriverWait(driver, 30).until(EC.presence_of_element_located(
                    (By.XPATH, f"//a[@href='{a.replace(MAIN_PAGE,'')}']")))
        text = el.text
        ActionChains(driver).move_to_element(el).perform()
        time.sleep(1)
        try:
            dep_cat_elements[text]= [
                [ele.text,ele.get_attribute("href")] for ele in WebDriverWait(driver, 3).until(
            EC.presence_of_all_elements_located((By.XPATH, "//ul[@class='tiendasjumboqaio-jumbo-main-menu-2-x-nav_menu tiendasjumboqaio-jumbo-main-menu-2-x-nav_menu--header-submenu-item tiendasjumboqaio-jumbo-main-menu-2-x-second_level tiendasjumboqaio-jumbo-main-menu-2-x-second_level--header-submenu-item']/li/div/span/a")))] 
        except TimeoutException as _:
            dep_cat_elements[text] = ["",a]
    list_articles = []
    dep_list=cat_list=sub_list  = None
    if not config["Jumbo"]:
        dep_list,cat_list,sub_list = consulta_ultima_peticion()
    for dep,cats in dep_cat_elements.items():
        if dep in dep_list: continue
        for cat in cats:
            if cat[0] in cat_list: continue
            
            current_url_jumbo = cat[1]
            try:
                driver.get(current_url_jumbo)
            except WebDriverException as _:
                crash_refresh_page(driver,current_url_jumbo)
            ready_document(driver,current_url_jumbo)
            list_articles+=get_subcategories(dep,cat[0],cat[1],sub_list)

    return list_articles

def consulta_ultima_peticion():
    fecha = db.consulta_sql_unica("select max(Fecha_resultados) FROM Jumbo;")
    hora = db.consulta_sql_unica(f"select max(Hora_resultados) FROM Jumbo where Fecha_resultados = {fecha!r};")
    ult_dep = db.consulta_sql_unica(f"SELECT Departamento from Jumbo where Hora_resultados = {hora!r} and Fecha_resultados = {fecha!r};")
    ult_cat = db.consulta_sql_unica(f"SELECT Categoria from Jumbo where Hora_resultados = {hora!r} and Fecha_resultados = {fecha!r} and Departamento= {ult_dep!r};")
    ult_sub = db.consulta_sql_unica(f"""SELECT Sub_categoria from Jumbo where Hora_resultados = {hora!r} and Fecha_resultados = {fecha!r} 
            and Departamento= {ult_dep!r} and Categoria = {ult_cat!r};""")
    
    deps = [val[0] for val in db.consulta_sql(f"select DISTINCT Departamento FROM Jumbo where Departamento <> {ult_dep!r} and Fecha_resultados = {fecha!r};")
                if val[0]] 
    cats = [val[0] for val in db.consulta_sql(f"select DISTINCT Categoria FROM Jumbo where Departamento = {ult_dep!r} and Categoria <> {ult_cat!r} and Fecha_resultados = {fecha!r};")
                if val[0]]
    subs = [val[0] for val in db.consulta_sql(f"""select DISTINCT Sub_categoria FROM Jumbo where Departamento = {ult_dep!r} and Categoria = {ult_cat!r}
            and Sub_categoria <> {ult_sub!r} and Fecha_resultados = {fecha!r};""") if val[0]]
    return deps,cats,subs


def get_subcategories(dep,cat,url,sub_list):
    global current_url_jumbo,driver
    ready_document(driver,current_url_jumbo)
    dep_cat = url.replace("https://www.tiendasjumbo.co/","").split("/")
    list_articles = []
    if (len(dep_cat) != 2):
        count = 1
        while True:
            if (url.__contains__("page=")): current_url_jumbo = re.sub("\d+$","",url)+str(count)
            elif (url.__contains__("?")): current_url_jumbo = f"{url}&page={count}"
            else : current_url_jumbo = f"{url}?page={count}"
            
            driver.get(current_url_jumbo)  
            try:
                ready_document(driver,current_url_jumbo)
                WebDriverWait(driver, 25).until(EC.presence_of_element_located(
                    (By.XPATH, "//div[@class='vtex-search-result-3-x-searchNotFoundInfo flex flex-column ph9']")))
                return list_articles
            except TimeoutException:
                list_articles += get_elements(dep, cat, "")
                count+=1
            except WebDriverException as _:
                if tries == 3: exit()
                tries +=1
                driver = crash_refresh_page(driver,current_url_jumbo)
                time.sleep(4)
                continue
        
    sub_categories = get_subcategories_list()
    tries= 0
    for subcat in sub_categories:
        if subcat in sub_list: continue
        count = 1
        while True:
            current_url_jumbo = f"https://www.tiendasjumbo.co/{dep_cat[0]}/{dep_cat[1]}/{subcat}?initialMap=category-1,categoria&initialQuery={dep_cat[0]}/{dep_cat[1]}&map=category-1,category-2,category-3&page={count}"
            try:
                driver.get(current_url_jumbo)   
                ready_document(driver,current_url_jumbo)
                WebDriverWait(driver, 30).until(EC.presence_of_element_located(
                    (By.XPATH, "//div[@class='vtex-search-result-3-x-searchNotFoundInfo flex flex-column ph9']")))
                break
            except TimeoutException as _:             
                list_articles += get_elements(dep, cat, subcat)
                count+=1
                tries = 0
            except WebDriverException as e:
                if tries == 3: e.with_traceback()
                tries +=1
                driver = crash_refresh_page(driver,current_url_jumbo)
                time.sleep(4)
                continue
    return list_articles

def get_subcategories_list():
    global driver
    tries = 0
    while True:
        try:
            subcat_button: WebElement = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@class,'__container--category-3')]")))
            driver.execute_script("arguments[0].scrollIntoView(true);",subcat_button)
            driver.execute_script("arguments[0].click();",subcat_button)
            time.sleep(2)
            scroll_height: WebElement = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@class,'--category-3')]//div[@class='vtex-search-result-3-x-filterContent']")))
            scroll_element: WebElement = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@class,'--category-3')]//div[@data-testid='scrollable-element']")))
            driver.execute_script("arguments[0].scrollIntoView(true);",scroll_element)
            time.sleep(1)
            for i in [1,2,3]:
                driver.execute_script("arguments[0].scrollTop = arguments[1]",scroll_element,scroll_height.size["height"]*(i/3))
                time.sleep(1)
            ready_document(driver,current_url_jumbo)
            time.sleep(2)
            sub_categories_objects: list[WebElement] = WebDriverWait(driver, 30).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//div[contains(@class,'--category-3')]//div[@data-testid='scrollable-element']//label")))
            return [str(val.get_attribute("for")).replace("category-3-","") for val in sub_categories_objects]
        except TimeoutException as e:
            if tries == 3: print(e,e.args);exit()
            tries+=1
            time.sleep(5)
            driver.refresh()
            ready_document(driver,current_url_jumbo)
        except WebDriverException as _:
            if tries == 3: print(e,e.args);exit()
            tries+=1
            driver = crash_refresh_page(driver,current_url_jumbo)
            ready_document(driver,current_url_jumbo)
    

def scroll_down(final,time_sleep=0):
    time.sleep(time_sleep)
    ready_document(driver,current_url_jumbo)
    step = int(final*0.009)
    for val in range(0,final,step):
        driver.execute_script(f"window.scrollTo(0, {val});")

def get_elements(dep, cat, subcat):
    global driver
    list_elements = []
    try:
        container:WebElement = WebDriverWait(
            driver, 50).until(EC.presence_of_element_located((By.ID, "gallery-layout-container")))
        driver.execute_script("arguments[0].scrollIntoView(true);", container)
        final_height: WebElement = WebDriverWait(driver, 30).until(EC.presence_of_element_located(
                (By.XPATH, "//div[@class='vtex-flex-layout-0-x-flexColChild vtex-flex-layout-0-x-flexColChild--filter-content pb0']")))
        scroll_down(final=container.size["height"],time_sleep= 2)
        elements: list[WebElement] = WebDriverWait(driver,10).until(EC.presence_of_all_elements_located(
            (By.XPATH,"//*[@id='gallery-layout-container']/div/section/a/article")
        ))
    except TimeoutException as _:
        driver.refresh()
        ready_document(driver,current_url_jumbo)
        container:WebElement = WebDriverWait(
            driver, 50).until(EC.presence_of_element_located((By.ID, "gallery-layout-container")))
        driver.execute_script("arguments[0].scrollIntoView(true);", container)
        final_height: WebElement = WebDriverWait(driver, 30).until(EC.presence_of_element_located(
                (By.XPATH, "//div[@class='vtex-flex-layout-0-x-flexColChild vtex-flex-layout-0-x-flexColChild--filter-content pb0']")))
        scroll_down(final=container.size["height"],time_sleep= 2)
        elements: list[WebElement] = WebDriverWait(driver,10).until(EC.presence_of_all_elements_located(
            (By.XPATH,"//*[@id='gallery-layout-container']/div/section/a/article")
        ))
    except WebDriverException as e:
        driver= crash_refresh_page(driver,current_url_jumbo)
        time.sleep(5)
        container:WebElement = WebDriverWait(
            driver, 50).until(EC.presence_of_element_located((By.ID, "gallery-layout-container")))
        driver.execute_script("arguments[0].scrollIntoView(true);", container)
        final_height: WebElement = WebDriverWait(driver, 30).until(EC.presence_of_element_located(
                (By.XPATH, "//div[@class='vtex-flex-layout-0-x-flexColChild vtex-flex-layout-0-x-flexColChild--filter-content pb0']")))
        scroll_down(final=final_height.size["height"],time_sleep= 2)
        elements: list[WebElement] = WebDriverWait(driver,10).until(EC.presence_of_all_elements_located(
            (By.XPATH,"//*[@id='gallery-layout-container']/div/section/a/article")
        ))
    for el in elements:
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);",el)
            element = BeautifulSoup(el.get_attribute('innerHTML'),'html5lib')
        except (WebDriverException,TimeoutException) as e:
            print(e,e.args)
            continue
        
        precio = precio_promo(element)
        if not precio: continue
        nombre_cantidad_unidad = nombre_cantidad(select_name(element))
        precio_norm = precio_normal(element)
        date = datetime.now()
        if (len(nombre_cantidad_unidad) == 3):
            list_elements.append(
                (dep, cat, subcat, nombre_cantidad_unidad[0].replace("\n"," "), precio, nombre_cantidad_unidad[1], 
                 nombre_cantidad_unidad[2], precio_norm, date.date(),date.time()))
        else:
            list_elements.append(
                (dep, cat, subcat, nombre_cantidad_unidad[0].replace("\n"," "), precio, nombre_cantidad_unidad[1], "", 
                 precio_norm, date.date(),date.time()))
        # print(list_elements)
    df = pd.DataFrame(list_elements, columns=COLUMNS)
    db.to_data_base(df,'Jumbo')
    print(f"Productos guardados, en la categoría: {cat}, subcategoría: {subcat} a las {datetime.now()}, la cantidad de {len(df)} productos")
    return list_elements


def precio_promo(element: BeautifulSoup):
    try: # div/div/div/div[4]/div[2]/div/span
        return get_price(
            element.find_next(
                "div", {"id":"items-price"}
            ).find_next("div").find_next("div").text)
    except Exception as e:
        print(e,e.args)
    
def get_price(valor: str):
    exp = re.search("\d+[\.\d+]*", valor).group(0)
    return float(exp.replace(".", ""))

def select_name(element: BeautifulSoup):
    try:
        nombre_cantidad_unidad = element.find(
            "span", {"class": "vtex-product-summary-2-x-productBrand vtex-product-summary-2-x-brandName t-body"}).text.strip()
    except:
        print("NO se encontró el nombre")
        return ""
    return nombre_cantidad_unidad

def nombre_cantidad(nom_cant: str):
    nom_cant = nom_cant.replace("  "," ")
    try:
        cant = re.search("((X|X\s| X\s| X)|(x|x\s| x\s| x))(\d+[\.\d]*|\d+[\,\d]*)\s{0,1}[a-zA-Z]+", 
                         nom_cant).group(0).replace(",",".")
    except AttributeError as _:
        try:
            cant = re.search("(\d+[\.\d]*|\d+[,\d]*)\s{0,1}[a-zA-Z]+\.{0,1}", 
                         nom_cant).group(0).replace(",",".")
        except AttributeError as _:
            return [nom_cant]+["1","UN"]
    cant = cant.replace("x","").replace("X","").strip()
        #cant = "1 UN"
    if (len(cant.split()) == 1):
        new_cant = re.search("\d+[\.\d]*", cant).group(0)
        cant = cant.replace(new_cant, "").strip()
        cant = f"{new_cant} {cant}"

    return [nom_cant]+cant.split()


def precio_normal(element: BeautifulSoup):
    try:
        precio_normal = get_price(
            element.find_next("div", {"id":"items-price"}).find_next("div",{"class":"tiendasjumboqaio-jumbo-minicart-2-x-price"}).text)
        return precio_normal
    except Exception as e :
        return ""

with open("config.json","r") as json_path:
    config:dict = json.load(json_path)
current_url_jumbo = MAIN_PAGE
driver,db = init_scraping(current_url_jumbo,"Jumbo")
each_departments_categories()
config["Jumbo"] = True
with open("config.json","w") as writer:
        json.dump(config,writer)