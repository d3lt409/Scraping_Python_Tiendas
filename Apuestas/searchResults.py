import pandas as pd
from selenium import webdriver
from bs4 import BeautifulSoup
from bs4.element import PageElement
from selenium.webdriver.chrome.webdriver import WebDriver
from datetime import datetime
import re
import time
import random
import sys

sys.path.append(".")
from Apuestas.Utils import *


driver_google = None
FINAL = {2:"imso_mh__ft-mtch imso-medium-font imso_mh__ft-mtchc",1:"imso_mh__ft-mtch imso-medium-font imso_mh__ft-mtchc",3:"tsp-fm"}

def iniciarDriver() -> WebDriver:
    global driver_google
    driver_google = webdriver.Chrome('./chrome/chromedriver')

def results(page,type,empate = "empate"):
    datos:pd.DataFrame = pd.read_excel(f"Apuestas/excel_files/{NAMEFILE[page]}",sheet_name=SHEETNAMES.get(type))
    df_datos = datos.drop_duplicates(subset=SUBSET, keep='last')
    df = search(df_datos,type,empate)             
    datos["Finalizado"].\
        loc[datos[N1].isin(df[N1]) & datos[N2].isin(df[N2])\
            & datos["Grupo"].isin(df["Grupo"])] = True
    datos = datos.append(df)
    return datos

def htmlSearch(name:str):
    val = re.findall("\([\w]\)",name)
    if (len(val) > 0):
        name = name.replace(val[0],"").strip()
    name = name.replace(" ","+")
    return name

def puntajesGoogle(type,soup,nombre1=""):
    newNombre1 = nombre1.split()
    if type in (1,2):
        puntaje1:PageElement = soup.find("div",{"class":"imso_mh__l-tm-sc imso_mh__scr-it imso-light-font"})
        puntaje2:PageElement = soup.find("div",{"class":"imso_mh__r-tm-sc imso_mh__scr-it imso-light-font"})
        return int(puntaje1.text.strip()),int(puntaje2.text.strip())
    elif (type == 3):
        ganador:str = soup.find("span",{"class":"tsp-nd tsp-db tsp-el"}).text.strip()
        if (len(newNombre1) > 1):
            if (newNombre1[1] in ganador and ganador.startswith(newNombre1[0][0].upper())):
                puntaje1 = 1
                puntaje2 = 0
            else:
                puntaje2 = 1
                puntaje1 = 0
            return puntaje1,puntaje2
        else:
            if (nombre1 == ganador):
                puntaje1 = 1
                puntaje2 = 0
            else:
                puntaje2 = 1
                puntaje1 = 0
            return puntaje1,puntaje2

def search(df_datos:pd.DataFrame,type,empate:str):
    values = []
    for _,row in df_datos.iterrows():
        if (row["Finalizado"] == False):
            minutos = row["Tiempo de juego"].split(":")
            name1 = htmlSearch(row[N1])
            name2 = htmlSearch(row[N2])
            time.sleep(random.uniform(1,2))
            driver_google.get(f"https://www.google.com/search?client=opera&q={name1}+-+{name2}&sourceid=opera&ie=UTF-8&oe=UTF-8")
            soup = BeautifulSoup(driver_google.page_source,'html5lib')
            try:
                if (type == 3):
                    ten_fin = soup.find("div",{"class":"tsp-sts tsp-pr"})
                    fin = ten_fin.find("span",{"class":FINAL[type]})
                else:
                    fin = soup.find("span",{"class":FINAL[type]})
                final = fin.text.strip()
            except Exception as _:
                time.sleep(random.uniform(1,2))
                try:
                    driver_google.get(f"https://www.google.com/search?client=opera&q={name1}+vs+{name2}&sourceid=opera&ie=UTF-8&oe=UTF-8") 
                    soup = BeautifulSoup(driver_google.page_source,'html5lib')
                    if (type == 3):
                        ten_fin = soup.find("div",{"class":"tsp-sts tsp-pr"})
                        fin = ten_fin.find("span",{"class":FINAL[type]})
                    else:
                        fin = soup.find("span",{"class":FINAL[type]})
                    final = fin.text.strip()
                except Exception as _:
                    continue
            if (final == 'Finalizado'):
                try:
                    puntaje1,puntaje2 = puntajesGoogle(type,soup,row[N1])
                except Exception as _:
                    continue
                min = TIPO[type][0]
                if (int(minutos[0]) > TIPO[type][1]):
                    min = row["Tiempo de juego"]
                if(empate == "empate"):
                    values.append(
                        (row[N1] ,puntaje1,-1,row["Nombre 2"],puntaje2, 
                        -1,-1,row["Grupo"],row["Fecha de juego"],min,TIPO[type][2],True))
                else:
                    values.append(
                        (row[N1] ,puntaje1,-1,row["Nombre 2"],puntaje2, 
                        -1,row["Grupo"],row["Fecha de juego"],min,TIPO[type][2],True))
    df = pd.DataFrame(values,columns=COLUMNAS[empate])
    return df

def searhEverySesult():
    iniciarDriver()
    for page in NAMEFILE.keys():
        dfs = []
        for sheet in SHEETNAMES.keys():
            if(sheet != 2):
                dfs.append((results(page,sheet,empate="no_empate"),sheet))
            else:
                dfs.append((results(page,sheet),sheet))
        writer = pd.ExcelWriter(f"Apuestas/excel_files/{NAMEFILE.get(page)}",engine="xlsxwriter")
        for df,sheet in dfs:
            df.to_excel(writer,index=False,sheet_name=SHEETNAMES[sheet])
        writer.save()
        print(f"Guardado a las {datetime.now()} para {NAMEFILE[page]}")
searhEverySesult()