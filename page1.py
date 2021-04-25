from datetime import datetime
from os import close
import time
from bs4 import BeautifulSoup
import bs4
from selenium.webdriver.remote.webelement import WebElement
import pandas as pd
from selenium.webdriver.common.by import By
from Utils import *
import re
from typing import List

driver = webdriver.Chrome('chrome/chromedriver')
driver.get("https://m.codere.com.co/deportescolombia/#/DirectosPage")
time.sleep(4)
while True:
    try:
        driver.find_element_by_xpath("//button[@class='alert-button alert-button-md alert-button-default alert-button-default-md']").click()
        break
    except Exception as _:
        continue


def tennis():
    try:
        driver.find_element_by_xpath("//i[@class='sb-navbar-item--icon codere-icon icon-tennis']").click()
    except Exception as e:
        print(e)
        return
    time.sleep(1)
    soup = BeautifulSoup(driver.page_source,'html5lib')
    tenn:bs4.element.ResultSet = soup.find_all("sb-dropdown",{"class":"sb-dropdown is-collapsable is-open"})
    for ten in tenn:
        nombre_grupo = ten.find("p",{"class":"sb-dropdown--title"})
        tenn = soup.find("div",{"class":"sc-fzoLag frpOCq sc-fznWOq kELbTZ KambiBC-betty-collapsible KambiBC-collapsible-container KambiBC-mod-event-group-container KambiBC-expanded"})

def football():
    time.sleep(2)
    try:
        driver.find_element_by_xpath("//i[@class='sb-navbar-item--icon codere-icon icon-soccer']").click()
    except Exception as e:
        print(e)
        return
    time.sleep(1)
    open_all = List[WebElement]()
    open_all = driver.find_elements_by_xpath("//sb-dropdown[@class='sb-dropdown is-collapsable']")
    for op in open_all:
        op1:WebElement = op
        op1.find_element_by_class("sb-dropdown--header background-color-regular color-dark").click()
    soup = BeautifulSoup(driver.page_source,'html5lib')
    foots:bs4.element.ResultSet = soup.find_all("sb-dropdown",{"class":"sb-dropdown is-collapsable is-open"})
    vs = []
    for foot in foots:
        nombre_grupo = foot.find("p",{"class":"sb-dropdown--title"})
        teams = foot.find_all("div",{"class":"sb-grid-item sb-grid-content--teams"})
        print("\n-------------------------------------------")
        print(nombre_grupo)
        for team in teams:
            nombres = list(team.find_all("p",{"class":"sb-grid-item--title color-dark"}))
            tiempo = team.find("p",{"class":"sb-grid-item--subtitle color-accent"})
            puntajes = team.find_all("p",{"class","sb-grid-item--number color-accent"})
            apuestas = team.find_all("p",{"class","sb-button--subtitle color-dark"})
            print(nombres)
            print("-------------")
            print(tiempo)
            print("-------------")
            print(puntajes)
            print("-------------")
            print(apuestas)
            print("-------------\n")
        
football()