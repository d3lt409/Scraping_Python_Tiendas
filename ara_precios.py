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

URL = 'https://aratiendas.com/inicio/centro/'

driver = webdriver.Chrome('chrome/chromedriver')
driver.get("https://aratiendas.com/rebajon/centro/")

soup = BeautifulSoup(driver.page_source,'html5lib')
destacados = soup.find_all("article",{"class":re.compile("elementor-post elementor-grid-item ecs-post-loop post-[\d]+ productos_rebajon type-productos_rebajon status-publish format-standard has-post-thumbnail hentry tag-destacado categorias_rebajon-[\w]+(-[\w]+)+ zonas_rebajon-nacional")})
produc_destacados = []
for des in destacados:
    des:PageElement
    item = list(des.find_all("h2",{"class":"elementor-heading-title elementor-size-default"}))
    sep = item[1].text.split(" DE ")
    if (len(sep) <= 1 ):
        sep = item[1].text.split(" X ")
    print(sep)    
    if (len(item) == 6):
        produc_destacados.append((sep[0],sep[1][:len(sep[1])-1],item[2].text.strip(),item[3].text.strip(),item[5].text.strip()))
    elif (len(item) == 5):
        produc_destacados.append((sep[0],sep[1][:len(sep[1])-1],item[2].text.strip(),None,item[4].text.strip()))
    else:
        print(item)

df = pd.DataFrame(produc_destacados,columns=["Nombre producto","Cantidad","Precio promoción","Cantidad por producto","precio normal",])
print(df)
driver.close()
sys.exit()

val = driver.find_elements_by_xpath("//div[@class='filter-rebajon-checkbox']")

for v in val:
    v:WebElement
    element = v.find_element_by_tag_name("label")
    element.click()
    cat = v.find_element_by_xpath("//div").text
    time.sleep(1)
    articles:bs4.element.ResultSet = soup.find_all("",{"class":re.compile("sb-dropdown is-collapsable")})
