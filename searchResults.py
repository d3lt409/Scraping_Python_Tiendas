import pandas as pd
from selenium import webdriver
from bs4 import BeautifulSoup
from bs4.element import PageElement
from Utils import *
import re
import time
import random

driver_google = webdriver.Chrome('./chrome/chromedriver')

def results(type):
    datos:pd.DataFrame = pd.read_excel(NAMEFILE,sheet_name=SHEETNAMES.get(type))
    df_datos = datos.drop_duplicates(subset=SUBSET, keep='last')
    df = pd.DataFrame(columns=COLUMNAS[2])
    for _,row in df_datos.iterrows():
        if (type == 2):
            minutos = row["Tiempo de juego"].split(":")
            if (row["Finalizado"] == False):
                name1:str = row["Nombre 1"]
                val = re.findall("\([\w]\)",name1)
                if (len(val) > 0):
                    name1 = name1.replace(val[0],"").strip()
                name1 = name1.replace(" ","+")
                name2 = row["Nombre 2"]
                val = re.findall("\([\w]\)",name2)
                if (len(val) > 0):
                    name2 = name2.replace(val[0],"").strip()
                name2 = name2.replace(" ","+")
                time.sleep(random.random())
                driver_google.get(f"https://www.google.com/search?client=opera&q={name1}+vs+{name2}&sourceid=opera&ie=UTF-8&oe=UTF-8")
                soup = BeautifulSoup(driver_google.page_source,'html5lib')
                try:
                    fin = soup.find("span",{"class":"imso_mh__ft-mtch imso-medium-font imso_mh__ft-mtchc"})
                    final = fin.text.strip()
                except Exception as _:
                    continue 
                if (final == 'Finalizado'):
                    puntaje1:PageElement = soup.find("div",{"class":"imso_mh__l-tm-sc imso_mh__scr-it imso-light-font"})
                    puntaje2:PageElement = soup.find("div",{"class":"imso_mh__r-tm-sc imso_mh__scr-it imso-light-font"})
                    min = "90:00"
                    if (int(minutos[0]) > 90):
                        min = row["Tiempo de juego"]
                    df=df.append(
                        {'Nombre 1' : row["Nombre 1"] , 'Puntaje 1' : int(puntaje1.text), 
                        'Precio 1':-1,
                        'Nombre 2' : row["Nombre 2"],'Puntaje 2' : int(puntaje2.text), 
                        'Precio 2':-1,
                        "Empate" : -1,"Grupo": row["Grupo"],
                        "Fecha de juego":row["Fecha de juego"],"Tiempo de juego":min,
                        "Periodo":2,"Finalizado": True
                        },ignore_index=True)
                
    datos["Finalizado"].\
        loc[datos["Nombre 1"].isin(df["Nombre 1"]) & datos["Nombre 2"].isin(df["Nombre 2"])\
            & datos["Grupo"].isin(df["Grupo"])] = True
    datos = datos.append(df)
    return datos
  