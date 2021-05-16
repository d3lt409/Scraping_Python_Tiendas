from datetime import datetime
import time
from bs4 import BeautifulSoup
import bs4
from selenium import webdriver
import pandas as pd
import re
import sys

sys.path.append(".")
from Apuestas.Utils import *


driver = webdriver.Chrome('chrome/chromedriver')

def relog():
    driver.get("https://m.codere.com.co/deportescolombia/#/DirectosPage")
    time.sleep(5)
    while True:
        try:
            driver.find_element_by_xpath("//button[@class='alert-button alert-button-md alert-button-default alert-button-default-md']").click()
            driver.refresh()
            time.sleep(5)
            break
        except Exception as _:
            return

def df_to_excel():
    try:
        driver.find_element_by_xpath("//button[@class='alert-button alert-button-md alert-button-default alert-button-default-md']").click()
        driver.get("https://m.codere.com.co/deportescolombia/#/DirectosPage")
        time.sleep(4)
    except Exception as _:
        pass
    foot = football()
    bask = basket()
    tenn = tennis()
    tabl = table()
    writer = pd.ExcelWriter(f"Apuestas/excel_files/{NAMEFILE.get(1)}",engine="xlsxwriter")
    bask.to_excel(writer,index=False,sheet_name="Basketball")
    foot.to_excel(writer,index=False,sheet_name="Football")
    tenn.to_excel(writer,index=False,sheet_name="Tennis")
    tabl.to_excel(writer,index=False,sheet_name="Table")
    writer.save()
    print(f"Guardado a las {datetime.now()} para {NAMEFILE[1]}")
    driver.refresh()

def basket():
    try:
        driver.find_element_by_xpath("//i[@class='sb-navbar-item--icon codere-icon icon-basketball']").click()
    except Exception as e:
        try:
            df_excel = pd.read_excel(f"Apuestas/excel_files/{NAMEFILE.get(1)}",sheet_name=SHEETNAMES[1])
            return df_excel
        except Exception as _:
            return pd.DataFrame(columns=COLUMNAS["no_empate"])
    time.sleep(1)
    soup = BeautifulSoup(driver.page_source,'html5lib')
    foots:bs4.element.ResultSet = soup.find_all("sb-dropdown",{"class":re.compile("sb-dropdown is-collapsable")})
    vs = []
    for foot in foots:
        nombre_grupo = foot.find("p",{"class":"sb-dropdown--title"})
        teams = foot.find_all("sb-grid-item",{"class":"sb-grid-item sb-grid-content--teams"})
        for team in teams:
            nombres = list(team.find_all("p",{"class":"sb-grid-item--title color-dark"}))
            tiempo = team.find("p",{"class":re.compile("sb-grid-item--subtitle color-accent")})
            puntajes = list(team.find_all("p",{"class","sb-grid-item--number color-accent"}))
            list_apuestas = team.find("div",{"class":"sb-grid-item--bets-group has-3-groups is-wrap has-two-buttons"})
            try:
                apuestas = list(list_apuestas.find_all("p",{"class","sb-button--subtitle color-dark"}))
            except Exception as _:
                apuestas = []

            periodo,minutos = tiempo.text.split("\n")[1].strip(),tiempo.text.split("\n")[2].strip()
            minutos = minutos.replace("< ","")
            if (len(minutos) == 0): minutos = '00:00'
            if(len(apuestas) == 0):
                vs.append(
                    (nombres[0].text.strip(),puntajes[0].text.strip(),-1000,
                    nombres[1].text.strip(),puntajes[1].text.strip(),-1000,
                    nombre_grupo.text.strip(),datetime.now(),
                    minutos,periodo,False)
                    )
            else:
                vs.append(
                    (nombres[0].text.strip(),puntajes[0].text.strip(),apuestas[0].text.strip(),
                    nombres[1].text.strip(),puntajes[1].text.strip(),apuestas[1].text.strip(),
                    nombre_grupo.text.strip(),datetime.now(),
                    minutos,periodo,False)
                    )
    try:
        df_excel = pd.read_excel(NAMEFILE[1],sheet_name=SHEETNAMES[1])
        df_values = pd.DataFrame(vs,columns=COLUMNAS["no_empate"])
        df = df_excel.append(df_values)
        return df
    except Exception as _:
        df = pd.DataFrame(vs,columns=COLUMNAS["no_empate"])
        print(df)
        return df

def football():
    time.sleep(2)
    try:
        driver.find_element_by_xpath("//i[@class='sb-navbar-item--icon codere-icon icon-soccer']").click()
    except Exception as _:
        try:
            df_excel = pd.read_excel(f"Apuestas/excel_files/{NAMEFILE.get(1)}",sheet_name=SHEETNAMES[2])
            return df_excel
        except Exception as _:
            return pd.DataFrame(columns=COLUMNAS["empate"])
    time.sleep(1)
    soup = BeautifulSoup(driver.page_source,'html5lib')
    foots:bs4.element.ResultSet = soup.find_all("sb-dropdown",{"class":re.compile("sb-dropdown is-collapsable")})
    vs = []
    for foot in foots:
        nombre_grupo = foot.find("p",{"class":"sb-dropdown--title"})
        teams = foot.find_all("sb-grid-item",{"class":"sb-grid-item sb-grid-content--teams"})
        for team in teams:
            nombres = list(team.find_all("p",{"class":"sb-grid-item--title color-dark"}))
            tiempo = team.find("p",{"class":re.compile("sb-grid-item--subtitle color-accent")})
            puntajes = list(team.find_all("p",{"class","sb-grid-item--number color-accent"}))
            list_apuestas = team.find("div",{"class":"sb-grid-item--bets-group has-2-groups is-wrap has-three-buttons"})
            try:
                apuestas = list(list_apuestas.find_all("p",{"class","sb-button--subtitle color-dark"}))
            except Exception as _:
                apuestas = []
            print(tiempo)
            periodo,minutos = tiempo.text.split("\n")[1].strip(),tiempo.text.split("\n")[2].strip()
            minutos = minutos.replace("'","")
            if(len(minutos) == 0): minutos = "00:00"
            else: minutos = f"{minutos}:00"
            if(len(apuestas) == 0):
                vs.append(
                    (nombres[0].text.strip(),puntajes[0].text.strip(),-1000,
                    nombres[1].text.strip(),puntajes[1].text.strip(),-1000,
                    -1000,nombre_grupo.text.strip(),datetime.now(),
                    minutos,periodo,False)
                    )
            else:
                vs.append(
                    (nombres[0].text.strip(),puntajes[0].text.strip(),apuestas[0].text.strip(),
                    nombres[1].text.strip(),puntajes[1].text.strip(),apuestas[2].text.strip(),
                    apuestas[1].text.strip(),nombre_grupo.text.strip(),datetime.now(),
                    minutos,periodo,False)
                    )
    try:
        df_excel = pd.read_excel(NAMEFILE[1],sheet_name=SHEETNAMES[2])
        df_values = pd.DataFrame(vs,columns=COLUMNAS["empate"])
        df = df_excel.append(df_values)
        return df
    except Exception as _:
        df = pd.DataFrame(vs,columns=COLUMNAS["empate"])
        print(df)
        return df
        
def table():
    try:
        driver.find_element_by_xpath("//i[@class='sb-navbar-item--icon codere-icon icon-table_tennis']").click()
    except Exception as _:
        try:
            df_excel = pd.read_excel(f"Apuestas/excel_files/{NAMEFILE.get(1)}",sheet_name=SHEETNAMES[4])
            return df_excel
        except Exception as e:
            print(e)
            return pd.DataFrame(columns=COLUMNAS["no_empate"])
    time.sleep(1)
    soup = BeautifulSoup(driver.page_source,'html5lib')
    foots:bs4.element.ResultSet = soup.find_all("sb-dropdown",{"class":re.compile("sb-dropdown is-collapsable")})
    vs = []
    for foot in foots:
        nombre_grupo = foot.find("p",{"class":"sb-dropdown--title"})
        teams = foot.find_all("sb-grid-item",{"class":"sb-grid-item sb-grid-content--teams"})
        for team in teams:
            nombres = list(team.find_all("p",{"class":"sb-grid-item--title color-dark"}))
            tiempo = team.find("p",{"class":re.compile("sb-grid-item--subtitle color-accent")})
            puntajes = list(team.find_all("p",{"class","sb-grid-item--number color-accent"}))
            list_apuestas = team.find("div",{"class":"sb-grid-item--bets-group has-2-groups is-wrap has-two-buttons"})
            try:
                apuestas = list(list_apuestas.find_all("p",{"class","sb-button--subtitle color-dark"}))
            except Exception as _:
                apuestas = []

            periodo = tiempo.text.split("\n")[1].strip()
            minutos = '00:00'

            if(len(apuestas) == 0):
                vs.append(
                    (nombres[0].text.strip(),puntajes[0].text.strip(),-1000,
                    nombres[1].text.strip(),puntajes[1].text.strip(),-1000,
                    nombre_grupo.text.strip(),datetime.now(),
                    minutos,periodo,False)
                    )
            else:
                vs.append(
                    (nombres[0].text.strip(),puntajes[0].text.strip(),apuestas[0].text.strip(),
                    nombres[1].text.strip(),puntajes[1].text.strip(),apuestas[1].text.strip(),
                    nombre_grupo.text.strip(),datetime.now(),
                    minutos,periodo,False)
                    )
    try:
        df_excel = pd.read_excel(NAMEFILE[1],sheet_name=SHEETNAMES[4])
        df_values = pd.DataFrame(vs,columns=COLUMNAS["no_empate"])
        df = df_excel.append(df_values)
        return df
    except Exception as _:
        df = pd.DataFrame(vs,columns=COLUMNAS["no_empate"])
        print(df)
        return df

def tennis():
    try:
        driver.find_element_by_xpath("//i[@class='sb-navbar-item--icon codere-icon icon-tennis']").click()
    except Exception as _:
        try:
            df_excel = pd.read_excel(f"Apuestas/excel_files/{NAMEFILE.get(1)}",sheet_name=SHEETNAMES[3])
            return df_excel
        except Exception as e:
            print(e)
            return pd.DataFrame(columns=COLUMNAS["no_empate"])
    time.sleep(1)
    soup = BeautifulSoup(driver.page_source,'html5lib')
    foots:bs4.element.ResultSet = soup.find_all("sb-dropdown",{"class":re.compile("sb-dropdown is-collapsable")})
    vs = []
    for foot in foots:
        nombre_grupo = foot.find("p",{"class":"sb-dropdown--title"})
        teams = foot.find_all("sb-grid-item",{"class":"sb-grid-item sb-grid-content--teams"})
        for team in teams:
            nombres = list(team.find_all("p",{"class":"sb-grid-item--title color-dark"}))
            tiempo = team.find("p",{"class":re.compile("sb-grid-item--subtitle color-accent")})
            puntajes = list(team.find_all("p",{"class","sb-grid-item--number color-accent"}))
            list_apuestas = team.find("div",{"class":"sb-grid-item--bets-group has-2-groups is-wrap has-two-buttons"})
            try:
                apuestas = list(list_apuestas.find_all("p",{"class","sb-button--subtitle color-dark"}))
            except Exception as _:
                apuestas = []
            periodo = tiempo.text.strip()

            if(len(apuestas) == 0):
                vs.append(
                    (nombres[0].text.strip(),puntajes[0].text.strip(),-1000,
                    nombres[1].text.strip(),puntajes[1].text.strip(),-1000,
                    nombre_grupo.text.strip(),datetime.now(),
                    '00:00',periodo,False)
                    )
            else:
                vs.append(
                    (nombres[0].text.strip(),puntajes[0].text.strip(),apuestas[0].text.strip(),
                    nombres[1].text.strip(),puntajes[1].text.strip(),apuestas[1].text.strip(),
                    nombre_grupo.text.strip(),datetime.now(),
                    "00:00",periodo,False)
                    )
    try:
        df_excel = pd.read_excel(NAMEFILE[1],sheet_name=SHEETNAMES[3])
        df_values = pd.DataFrame(vs,columns=COLUMNAS["no_empate"])
        df = df_excel.append(df_values)
        return df
    except Exception as _:
        df = pd.DataFrame(vs,columns=COLUMNAS["no_empate"])
        print(df)
        return df

def runPage():
    relog()
    df_to_excel()

runPage()