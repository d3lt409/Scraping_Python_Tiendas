from datetime import datetime
import time
from bs4 import BeautifulSoup
from bs4 import element
from bs4.element import PageElement, ResultSet
from numpy import product, source
from selenium import webdriver
import pandas as pd
import re
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait     
from selenium.webdriver.common.by import By     
from selenium.webdriver.support import expected_conditions as EC

FILENAME = "d1_precios.xlsx"

driver = webdriver.Chrome('chrome/chromedriver')
driver.get("https://domicilios.tiendasd1.com")
EMAIL = 'dfzd1984@gmail.com'
PASW = '1234567'

def login():
    driver.execute_script("arguments[0].click();",driver.find_element_by_xpath("//a[@class='user__account__link']"))
    driver.execute_script("arguments[0].click();",driver.find_element_by_xpath("//p[@class='sc-EHOje koQNrs log-out']"))
    time.sleep(1)
    while True:
        try:
            email = driver.find_element_by_css_selector('#signup_email')
            pasw = driver.find_element_by_css_selector('#signup_password')
            break
        except Exception as _:
            continue

    email.send_keys(EMAIL)
    pasw.send_keys(PASW)
    driver.execute_script("arguments[0].click();",driver.find_element_by_css_selector("#signup > div.ant-row.ant-form-item.submit > div > div > div > button"))
    time.sleep(5)
    driver.execute_script("arguments[0].click();",WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,"//*[@id='app']/div/div[1]/div[2]/div/div[1]/div/div/button"))))
    driver.execute_script("arguments[0].click();",WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,"//div[@class='sc-fjdhpX iEzjzd Styled__GenericCardOpModel-sbnrh2-4 dpJFCE']"))))
    driver.execute_script("arguments[0].click();",WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,"//div[@class='sc-jzJRlG krOjOX']"))))

def categoires():
    driver.execute_script("arguments[0].click();",driver.find_element_by_xpath("//*[@id='app']/div/div[1]/div[2]/div/div[1]/div/button[1]"))
    cat_list = []
    time.sleep(2)
    for i in range(1,12):
        cat_list.append(driver.find_element_by_css_selector(f"#app > div > div.Header__StyledHeader-sc-8w91gm-0.encWLd > div.SubHeader__ContainerForTransparency-sc-136tppk-0.ksPlGk > div > div.SubHeader__CategoryContainer-sc-136tppk-2.jNXlfh > div > div > div:nth-child({i}) > div.center.categories__card__txt__container > p").text)
    category = cat_list.pop(0)
    driver.execute_script("arguments[0].click();",driver.find_element_by_xpath(f"//p[@class='categories__card__txt'][contains(text(),'{category}')]"))
    cat_products = get_elements(category,[])
    for name in cat_list:
        driver.execute_script("arguments[0].click();",WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,"//*[@id='app']/div/div[1]/div[2]/div/div[1]/div/button[1]"))))
        driver.execute_script("arguments[0].click();",WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,f"//p[@class='categories__card__txt'][contains(text(),'{name}')]"))))
        cat_products+=get_elements(name,[])
    return cat_products

def get_elements(cat,list_elements):
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source,'html5lib')
    elements:ResultSet = soup.find_all("div",{"class":"product__content"})
    
    for el in elements:
        el:PageElement
        precio = precio_promo(el.find("p",{"class":"sc-EHOje kKHbON product__content__price__current"}).text)
        nombre = el.find("p",{"class":"sc-EHOje iGdYVA"}).text
        cant_uni_prec =  cantidad_uni_prec(el.find("p",{"class":"sc-EHOje ghaFcP"}).text)
        list_elements.append((nombre,cat,float(precio),int(cant_uni_prec[0]),cant_uni_prec[1],float(cant_uni_prec[2]),datetime.now()))
    try:
        driver.execute_script("arguments[0].click();",WebDriverWait(driver,3).until(EC.presence_of_element_located((By.XPATH,"//li[@title='Next Page'][@aria-disabled='false']"))))
        return get_elements(cat,list_elements)
    except TimeoutException as _:
        return list_elements


def precio_promo(valor:str):
    exp = re.search("\d+(\.\d+)*",valor).group(0)
    return float(exp.replace(".",""))

def cantidad_uni_prec(valor:str):
    valor = valor.replace(".","").replace(",",".")
    cant_uni = re.search("^\d+ (ml|l|g|un|m)",valor).group(0)
    valor = valor.replace(cant_uni,"")
    preci_uni = re.search("\d+(\.\d+){0,1}",valor).group(0)
    return cant_uni.split()+[preci_uni]

def main():
    login()
    df = pd.DataFrame(categoires(), columns=["Nombre","Categoria","Precio","Cantidad","Unidad","Precio_unidad","Fecha de lectura"])
    try:
        df_excel = pd.read_excel(f"Precio_Tiendas/excel_files/{FILENAME}")
        df_total = df_excel.append(df)
        df_total.to_excel(f"Precio_Tiendas/excel_files/{FILENAME}",engine = 'xlsxwriter',index=False)
    except Exception as _:
        df.to_excel(f"Precio_Tiendas/excel_files/{FILENAME}",engine = 'xlsxwriter',index=False)

    print(f"Guardado a las {datetime.now()} para {FILENAME}")
    driver.close()

main()