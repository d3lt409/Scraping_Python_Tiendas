from datetime import datetime
import time
from bs4 import BeautifulSoup
import bs4
from selenium import webdriver
import pandas as pd
import re
from selenium.webdriver.common.by import By

from selenium.webdriver.remote.webelement import WebElement

URL = 'https://aratiendas.com/inicio/centro/'

driver = webdriver.Chrome('chrome/chromedriver')
driver.get("https://aratiendas.com/rebajon/centro/")
val = driver.find_elements_by_xpath("//div[@class='filter-rebajon-checkbox']")
print(val)
for v in val:
    v:WebElement
    element = v.find_element_by_tag_name("label")
    element.click()
    print(element)
    time.sleep(4)
    # elements = w.find_elements_by_css_selector("*")
    # for el in elements:
    #     el:WebElement
    #     try:
    #         el.click()
    #         print(f"fue {el.tag_name}, {el.rect}")
    #     except Exception as e:
    #         print(e)
    #     time.sleep(7)

