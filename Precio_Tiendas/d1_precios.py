from datetime import datetime                                        # To call when the code runs the webscrapping
import time                                                          # To allow the code to wait a few second between some lines
from bs4 import BeautifulSoup                                        # To do the scrapping
from bs4 import element                                              # To scrolldown help from functions when you type
from bs4.element import PageElement, ResultSet                       # To scrolldown help from functions when you type (pageElement:single outcome, ResultSet: several outcomes)
import pandas as pd                                                  # To define de data frame
import re                                                            # To Use regular expressions
from selenium import webdriver                                       # Module to call the Bot 
from selenium.common.exceptions import TimeoutException              # When the scrapping i running put of time  
from selenium.webdriver.support.ui import WebDriverWait              # Give some second to the bot to wait for the webpage response
from selenium.webdriver.common.by import By                          # To refer Xpath or Css selector in the WebDriverWait
from selenium.webdriver.support import expected_conditions as EC     # To define the expected element to look for in the WebDriverWait
import sqlite3                                                       # Module to call sqlite

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

FILENAME = "d1_precios.xlsx"                                         # String with the name of the excel file

chrome_options = Options()
#chrome_options.add_argument('--headless')
#chrome_options.add_argument("--disable-gpu")
#chrome_options.add_argument('--no-sandbox')
#chrome_options.add_argument('--disable-dev-shm-usage')
#chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--log-level=3")
driver = webdriver.Chrome(ChromeDriverManager().install(),options=chrome_options)                     # Define the driver we are using
driver.get("https://domicilios.tiendasd1.com")                       # Web page 
EMAIL = 'dfzd1984@gmail.com'                                            
PASW = '1234567'
TIME_OUT = 30

def login():
    driver.execute_script("arguments[0].click();",WebDriverWait(driver,TIME_OUT).until(EC.presence_of_element_located((
        By.XPATH,"//span[@class='user__chevron__link']"))))   # Click on the begin session
    time.sleep(2)
    driver.execute_script("arguments[0].click();",WebDriverWait(driver,TIME_OUT).until(EC.presence_of_element_located((
        By.XPATH,"//div[@class='account__menu__radio-group__item__text']/p[text()='Inicio Sesión']"))))  # Click on the log in button
    time.sleep(4)
    
    while True: 
        try:
            email= driver.find_element_by_css_selector('#signup_email')   
            pasw = driver.find_element_by_css_selector('#signup_password')
            break 
        except Exception as _:
            continue
    
 
    email.send_keys(EMAIL)
    pasw.send_keys(PASW)
    
    driver.execute_script("arguments[0].click();",driver.find_element_by_css_selector("#signup > div.ant-row.ant-form-item.submit > div > div > div > button"))  # click on the login
    time.sleep(3)
    driver.execute_script("arguments[0].click();",WebDriverWait(driver,TIME_OUT).until(EC.presence_of_element_located(
                        (By.ID,"card-operation-model-DELIVERY"))))  #clear delivery way
    time.sleep(3)
    driver.execute_script("arguments[0].click();",WebDriverWait(driver,TIME_OUT).until(EC.presence_of_element_located(
        (By.XPATH,"/html/body/div[5]/div/div[2]/div/div[2]/div[2]/div[1]/div/div"))))   # select adress

    
    
def categoires():
    #N=the number of categories the Bot encounter
    driver.execute_script("arguments[0].click();",
            driver.find_element_by_xpath("//div[@class='generalHeader__mainMenuBtn']")) # get into categories
    
    time.sleep(3)
   
    cat_list_object =  WebDriverWait(driver, TIME_OUT).until(EC.presence_of_all_elements_located(
                        (By.XPATH, "//li[@class='categories-menu__item']"))) # categories list
    cat_list:list[str] = [el.text for el in cat_list_object]

    category = cat_list.pop(0) # Function "pop" take out the defined position, in this case the first position. In This case is "alimentos y despensa" when the code was developed
    driver.execute_script("arguments[0].click();",WebDriverWait(driver, TIME_OUT).until(EC.presence_of_element_located(
                        (By.XPATH, f"//li[@class='categories-menu__item'][contains(text(),'{category}')]")))) # Click on the first category 
    driver.execute_script("arguments[0].click();",WebDriverWait(driver, TIME_OUT).until(EC.presence_of_element_located(
                        (By.XPATH, f"//h4[@class='categoriesNav-Header__subtitle'][contains(text(),'{category}')]")))) 
    cat_products = get_elements(category,[]) # function to Download the webpage information in the category into cat_products object
    
    for name in cat_list:
        driver.execute_script("arguments[0].click();",WebDriverWait(driver,TIME_OUT).until(
            EC.presence_of_element_located((By.XPATH,"//div[@class='generalHeader__mainMenuBtn']"))))
        driver.execute_script("arguments[0].click();",WebDriverWait(driver, TIME_OUT).until(EC.presence_of_element_located(
                        (By.XPATH, f"//li[@class='categories-menu__item'][contains(text(),'{name}')]")))) 
        driver.execute_script("arguments[0].click();",WebDriverWait(driver, TIME_OUT).until(EC.presence_of_element_located(
                        (By.XPATH, f"//h4[@class='categoriesNav-Header__subtitle'][contains(text(),'{name}')]")))) 
        cat_products+=get_elements(name,[])
    return cat_products


def get_elements(cat,list_elements):
    time.sleep(3)
    
    soup = BeautifulSoup(driver.page_source,'html5lib') # get thw webpage source code in this moment
    elements:ResultSet = soup.find_all("div",{"class":"prod--default__content"}) # Store in elements all the information within the tree of "product__content"
    
    for el in elements: # Definir un loop sobre los elementos descargados para un producto
        el:PageElement  # tipar o asignar a "el" como un elemento de la pagina
        precio = precio_promo(el.find("p",{"class":re.compile("prod--default__price__current")}).text) # se ejecuta la función precio_promo. El argumento es: encuentre dentro de la clase "p", una expresión regular llamada "product__content__price__current". text: trae le precio (<p> precio </p>)
        nombre = el.find("p",{"class":re.compile("prod__name")}).text.strip() #find_next es el padre, y .find busca el hijo sobre el padre. Strip quita espacios al final y no en el medio
        cant_uni_prec =  cantidad_uni_prec(el.find("p",{"class":re.compile("prod__pum")}).text)
        list_elements.append((nombre,cat,float(precio),int(cant_uni_prec[0]),cant_uni_prec[1],float(cant_uni_prec[2]),datetime.now()))
        #print(list_elements)
    try:
        driver.execute_script("arguments[0].click();",WebDriverWait(driver,3).until(EC.presence_of_element_located((By.XPATH,"//li[@title='Next Page'][@aria-disabled='false']"))))
        return get_elements(cat,list_elements)
    except TimeoutException as _:
        return list_elements



def to_data_base(data:pd.DataFrame):
    
    conn = sqlite3.connect("./Precio_Tiendas/base_de_datos/Precios.sqlite")
    cur = conn.cursor()
    query = f"""
    CREATE TABLE IF NOT EXISTS D1 (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        Nombre_producto text,
        Categoria text,
        Precio REAL,
        Cantidad int,
        Unidad text,
        Precio_unidad REAL,
        Fecha_resultados TEXT
    );
    """
    cur.executescript(query)
    data = data.astype("str")
    values = data.values
    q = "INSERT INTO D1 (Nombre_producto,Categoria,Precio,Cantidad,Unidad ,Precio_unidad,Fecha_resultados) VALUES (?,?,?,?,?,?,?)"
    cur.executemany(q,values)
    conn.commit()
    cur.close()
    conn.close()
    
    
def precio_promo(valor:str):  # function to download the prices data . Argumentos: string
    exp = re.search("\d+(\.\d+)*",valor).group(0) # Example: 98.400.  "\d+":98 ;  "(\.\d+)*": .400. Esta última parte al tener asterizco dice que encuentre los números después del punto pero si no existe punto no trae nada . group(0) retorna el objeto que coincide con la búsqueda   
    return float(exp.replace(".","")) # Retorna el número reemplazando el punto por nada

def cantidad_uni_prec(valor:str):
    valor = valor.replace(".","").replace(",",".")
    cant_uni = re.search("^\d+ (ml|l|g|un|m)",valor).group(0)  # ^: dice que comienza con un número; " ": este espacio extrae; "ml|l|g|un|m": son las diferentes uniandes de medida
    valor = valor.replace(cant_uni,"")
    preci_uni = re.search("\d+(\.\d+){0,1}",valor).group(0) # {0,1}:  esto define el rango de la longitud de números que trae dentro de (\.\d+)  
    return cant_uni.split()+[preci_uni]


    
def main():
    login()
    df = pd.DataFrame(categoires(), columns=["Nombre","Categoria","Precio","Cantidad","Unidad","Precio_unidad","Fecha de lectura"])
    #print(df)
    to_data_base(df)
    driver.close()

    
main()