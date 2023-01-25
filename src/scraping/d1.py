from datetime import datetime                                        # To call when the code runs the webscrapping
import time                                                          # To allow the code to wait a few second between some lines                 # To scrolldown help from functions when you type (pageElement:single outcome, ResultSet: several outcomes)
import pandas as pd                                                  # To define de data frame
import re                                                            # To Use regular expressions

import sys; sys.path.append(".")
from src.utils.util import init_scraping, CLICK

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

FILENAME = "d1_precios.xlsx"                                         # String with the name of the excel file
EMAIL = 'dfzd1984@gmail.com'                                            
PASW = '1234567'
TIME_OUT = 30

def login():
    driver.execute_script(CLICK,WebDriverWait(driver,TIME_OUT).until(EC.presence_of_element_located((
        By.XPATH,"//span[@class='user__chevron__link']"))))   # Click on the begin session
    time.sleep(2)
    driver.execute_script(CLICK,WebDriverWait(driver,TIME_OUT).until(EC.presence_of_element_located((
        By.XPATH,"/html/body/div[3]/div/div/div/button[3]"))))  # Click on the log in button
    time.sleep(4)
    
    while True: 
        try:
            email= driver.find_element(By.CSS_SELECTOR,'#signup_email')   
            pasw = driver.find_element(By.CSS_SELECTOR, '#signup_password')
            break 
        except Exception as _:
            continue
    
 
    email.send_keys(EMAIL)
    pasw.send_keys(PASW)
    
    driver.execute_script(CLICK,driver.find_element(By.XPATH,"//*[@id='signup']/div[3]/div/div/div/div/button"))  # click on the login
    time.sleep(3)
    driver.execute_script(CLICK,WebDriverWait(driver,TIME_OUT).until(EC.presence_of_element_located(
                        (By.ID,"card-operation-model-DELIVERY"))))  #clear delivery way
    time.sleep(3)
    driver.execute_script(CLICK,WebDriverWait(driver,TIME_OUT).until(EC.presence_of_element_located(
        (By.XPATH,"/html/body/div[5]/div/div[2]/div/div[2]/div[2]/div[1]/div/div"))))   # select adress

    
    
def categoires():
    #N=the number of categories the Bot encounter
    driver.execute_script(CLICK,
            driver.find_element(By.XPATH, "//div[@class='generalHeader__mainMenuBtn']")) # get into categories
    
    time.sleep(3)
   
    cat_list_object =  WebDriverWait(driver, TIME_OUT).until(EC.presence_of_all_elements_located(
                        (By.XPATH, "//li[@class='categories-menu__item']"))) # categories list
    cat_list:list[str] = [el.text for el in cat_list_object]

    category = cat_list.pop(0) # Function "pop" take out the defined position, in this case the first position. In This case is "alimentos y despensa" when the code was developed
    driver.execute_script(CLICK,WebDriverWait(driver, TIME_OUT).until(EC.presence_of_element_located(
                        (By.XPATH, f"//li[@class='categories-menu__item'][contains(text(),'{category}')]")))) # Click on the first category 
    driver.execute_script(CLICK,WebDriverWait(driver, TIME_OUT).until(EC.presence_of_element_located(
                        (By.XPATH, f"//h4[@class='categoriesNav-Header__subtitle'][contains(text(),'{category}')]")))) 
    get_elements(category,[]) # function to Download the webpage information in the category into cat_products object
    
    for name in cat_list:
        driver.execute_script(CLICK,WebDriverWait(driver,TIME_OUT).until(
            EC.presence_of_element_located((By.XPATH,"//div[@class='generalHeader__mainMenuBtn']"))))
        driver.execute_script(CLICK,WebDriverWait(driver, TIME_OUT).until(EC.presence_of_element_located(
                        (By.XPATH, f"//li[@class='categories-menu__item'][contains(text(),'{name}')]")))) 
        driver.execute_script(CLICK,WebDriverWait(driver, TIME_OUT).until(EC.presence_of_element_located(
                        (By.XPATH, f"//h4[@class='categoriesNav-Header__subtitle'][contains(text(),'{name}')]")))) 
        get_elements(name,[])



def get_elements(cat,list_elements:list):
    time.sleep(3)
    
    elements = driver.find_elements(By.XPATH, "//div[@class= 'card-product-vertical ']") # Store in elements all the information within the tree of "product__content"

    for el in elements: # Definir un loop sobre los elementos descargados para un producto
        precio = precio_promo(el.find_element(By.XPATH, "//p[contains(@class,'base__price')]").text)
        nombre = el.find_element(By.XPATH, "//p[contains(@class,'prod__name')]").text.strip()
        cant_uni_prec =  cantidad_uni_prec(el.find_element(By.CSS_SELECTOR,"p>span").text)
        list_elements.append((nombre,cat,float(precio),int(cant_uni_prec[0]),cant_uni_prec[1],float(cant_uni_prec[2]),datetime.now().date()))
    try:
        driver.execute_script(CLICK,WebDriverWait(driver,3).until(EC.presence_of_element_located((By.XPATH,"//li[@title='Next Page'][@aria-disabled='false']"))))
        return get_elements(cat,list_elements)
    except TimeoutException as _:
        df = pd.DataFrame(list_elements, columns=["Nombre_producto","Categoria","Precio","Cantidad","Unidad","Precio_unidad","Fecha_resultados"])
        db.to_data_base(df)
        print("se guardan los archivos de la categoría",cat, "la cantidad de ", len(df))
    
def precio_promo(valor:str):  # function to download the prices data . Argumentos: string
    exp = re.search("\d+(\.\d+)*",valor).group(0) # Example: 98.400.  "\d+":98 ;  "(\.\d+)*": .400. Esta última parte al tener asterizco dice que encuentre los números después del punto pero si no existe punto no trae nada . group(0) retorna el objeto que coincide con la búsqueda   
    return float(exp.replace(".","")) # Retorna el número reemplazando el punto por nada

def cantidad_uni_prec(valor:str):
    valor = valor.replace(".","").replace(",",".")
    uni = re.search("(?<=\d )[a-zA-Z]",valor).group(0)
    cant = re.search("^\d+\.\d+|^\d+",valor).group(0)
    preci_uni = re.search("(?<=\$ ).+(?=\))",valor).group(0) # {0,1}:  esto define el rango de la longitud de números que trae dentro de (\.\d+)  
    return cant,uni,preci_uni
    
def main():
    global driver,db
    driver, db = init_scraping("https://domicilios.tiendasd1.com","D1")                    # Web page https://domicilios.tiendasd1.com
    # login()
    db.init_database_d1()
    categoires()
    db.close()
    driver.close()
    driver.quit
