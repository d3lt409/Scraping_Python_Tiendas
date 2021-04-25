from datetime import datetime
from os import close
import time
from bs4 import BeautifulSoup
from selenium import webdriver
import pandas as pd
from selenium.webdriver.common.by import By
from Utils import *
import re

driver = webdriver.Chrome('chrome/chromedriver')
driver.get("https://betplay.com.co/live#filter/all/all/all/all/in-play")
time.sleep(1)
soup = BeautifulSoup(driver.page_source,'html.parser')
# driver.close()
# #names = list(soup.find_all('div',attrs={"class":"KambiBC-event-participants__name"}))
# #votes = list(soup.find_all('div',attrs={"class":"sc-AxheI kIcofq"}))
# boths = list(soup.find_all('div',attrs={"class":"sc-AxirZ bnliBi"}))
# main = list(soup.find_all("div",attrs={"class":"sc-fzqARJ grXYBm"}))
# vs = []
# if (len(boths) > 0):
#     j = 0
#     for i in range(0,len(boths)-1,2):
#         values = boths[i+1].find("div",{"class":"sc-AxiKw bfgHJg"})
#         valueslast = boths[i].find("div",{"class":"sc-AxiKw bfgHJg"})
#         name2 = values.find("div",{"class":"sc-AxhCb fmbcv"}).text
#         name1 = valueslast.find("div",{"class":"sc-AxhCb fmbcv"}).text

#         values = boths[i+1].find("div",{"class":"sc-AxgMl eHRTXh"})
#         valueslast = boths[i].find("div",{"class":"sc-AxgMl eHRTXh"})
#         vote2 = values.find("div",{"class":"sc-AxheI kIcofq"}).text
#         vote1 = valueslast.find("div",{"class":"sc-AxheI kIcofq"}).text

#         vs.append((name1,vote1,name2,vote2))#,main[j].text))
#         j+=1

# df = pd.DataFrame(vs)
# print(df)

def page1Tennis():
    try:
        driver.find_element_by_xpath("//span[@class='KambiBC-navicon__sport-icon KambiBC-navicon__sport-icon--small KambiBC-navicon__sport-icon--table_tennis']").click()
    except Exception as e:
        print(e)
        return
    time.sleep(1)
    soup = BeautifulSoup(driver.page_source,'html5lib')
    tenn = soup.find("div",{"class":"sc-fzoLag frpOCq sc-fznWOq kELbTZ KambiBC-betty-collapsible KambiBC-collapsible-container KambiBC-mod-event-group-container KambiBC-expanded"})
    campeonatos = tenn.find_all("div",{"class":"KambiBC-collapsible-content KambiBC-mod-event-group-event-container"})
    namegroup = ""
    vs = []
    for cam in campeonatos:
        typeName=cam.find('div',attrs={"class":"sc-fzqARJ gvnTIZ"})
        namegroup = typeName.text.strip()
        puntos = cam.find_all("span",{"class":"KambiBC-event-result__points"})
        nombres = cam.find_all("div",{"class":"KambiBC-event-participants__name"})
        apuestas = cam.find_all("div",{"class":"sc-AxheI cWjOQp"})
        print(namegroup)
        print(puntos)
        print(nombres)
        print(apuestas)
        vs.append(
            (nombres[0].text,puntos[2].text,apuestas[0].text,
            nombres[1].text,puntos[3].text,apuestas[1].text,
            namegroup,datetime.now(),False))#,main[j].text))
    return vs

def page1Foot():
    try:
        driver.find_element_by_xpath("//span[@class='KambiBC-navicon__sport-icon KambiBC-navicon__sport-icon--small KambiBC-navicon__sport-icon--football']").click()
    except Exception as e:
        print(e)
        return
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source,'html5lib')
    tenn = soup.find_all("div",{"class":"sc-fzoLag frpOCq sc-fznWOq kELbTZ KambiBC-betty-collapsible KambiBC-collapsible-container KambiBC-mod-event-group-container KambiBC-expanded"})
    vs = []
    print(len(tenn))
    for ten in tenn:
        campeonatos = ten.find_all("div",{"class":"KambiBC-collapsible-content KambiBC-mod-event-group-event-container"})
        print(len(campeonatos))
        for cam in campeonatos:
            nombres_grupos = list(cam.find_all("div",{"class":"KambiBC-betoffer-labels KambiBC-betoffer-labels--with-title"}))
            partidos_grupos = list(cam.find_all("ul",{"class":"KambiBC-list-view__column KambiBC-list-view__event-list"}))
            print(len(nombres_grupos),len(partidos_grupos))
            for i in range(len(nombres_grupos)):
                typeName=nombres_grupos[i].find('div',attrs={"class":"sc-fzqARJ gvnTIZ"})
                partidos = partidos_grupos[i].find_all('li',{"class":re.compile("KambiBC-event-item KambiBC-event-item-[\d]+ KambiBC-event-item--sport-FOOTBALL KambiBC-event-item--type-match KambiBC-event-item--live")})
                namegroup = typeName.text.strip()
                print(namegroup)
                print(partidos)
                for par in partidos:
                    puntos = par.find_all("span",{"class":"KambiBC-event-result__points"})
                    nombres = par.find_all("div",{"class":"KambiBC-event-participants__name"})
                    apuestas = par.find_all("div",{"class":"sc-AxheI cWjOQp"})
                    print(namegroup)
                    print(puntos)
                    print(nombres)
                    print(apuestas)
                    vs.append(
                        (nombres[0].text,puntos[0].text,apuestas[0].text,
                        nombres[1].text,puntos[1].text,apuestas[1].text,
                        namegroup,datetime.now(),False))#,main[j].text))
    return vs


# df = pd.DataFrame(page1Tennis(),columns=[N1,"Puntaje 1","Precio 1",N2,"Puntaje 2","Precio 2","Grupo","Fecha de juego","Finalizado"]) 
# print(df)

df1 = pd.DataFrame(page1Foot(),columns=[N1,"Puntaje 1","Precio 1",N2,"Puntaje 2","Precio 2","Grupo","Fecha de juego","Finalizado"]) 
print(df1)

driver.close()