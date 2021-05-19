from datetime import datetime
import time
from bs4 import BeautifulSoup
from bs4.element import PageElement, ResultSet
from numpy import product
from selenium import webdriver
import pandas as pd
import re
from selenium.webdriver.remote.webelement import WebElement

FILENAME = "justo_y_bueno.xlsx"

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
    time.sleep(2)
    driver.execute_script("arguments[0].click();",driver.find_element_by_xpath("//*[@id='app']/div/div[1]/div[2]/div/div[1]/div/div/button"))
    time.sleep(2)
    driver.execute_script("arguments[0].click();",driver.find_element_by_xpath("//div[@class='sc-fjdhpX iEzjzd Styled__GenericCardOpModel-sbnrh2-4 dpJFCE']"))
    time.sleep(1)
    driver.execute_script("arguments[0].click();",driver.find_element_by_xpath("//div[@class='sc-jzJRlG krOjOX']"))

def categoires():
    driver.execute_script("arguments[0].click();",driver.find_element_by_xpath("//*[@id='app']/div/div[1]/div[2]/div/div[1]/div/button[1]"))
    cat_list = []
    time.sleep(2)
    for i in range(1,12):
        cat_list.append(driver.find_element_by_css_selector(f"#app > div > div.Header__StyledHeader-sc-8w91gm-0.encWLd > div.SubHeader__ContainerForTransparency-sc-136tppk-0.ksPlGk > div > div.SubHeader__CategoryContainer-sc-136tppk-2.jNXlfh > div > div > div:nth-child({i}) > div.center.categories__card__txt__container > p").text)
    
    driver.execute_script("arguments[0].click();",driver.find_element_by_xpath(f"//p[@class='categories__card__txt'][contains(text(),'{cat_list.pop(0)}')]"))

login()
categoires()