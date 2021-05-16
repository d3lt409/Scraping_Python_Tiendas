import re
import time
from bs4 import BeautifulSoup
from bs4.element import PageElement
from selenium import webdriver
import pandas as pd
from datetime import datetime
import sys

sys.path.append(".")
from Apuestas.Utils import *

driver = webdriver.Chrome("./chrome/chromedriver")
PARTIDOS = {"bask":"inplay-tab-BASK","foot":"inplay-tab-FOOT","tenn":"inplay-tab-TENN","tabl":"inplay-tab-TABL"}
CAMPEONATOS = "table-row row-wrap"

def login():
    driver.get("https://apuestas.wplay.co/es")
    """time.sleep(2)
    user_driver = driver.find_element_by_xpath("//input[@name='username']")
    passw_driver = driver.find_element_by_xpath("//input[@name='password']")
    login_driver = driver.find_element_by_class_name("log-in")

    user_driver.send_keys(USER)
    passw_driver.send_keys(PASSWORD)
    login_driver.click()
    while True:
        try:
            accept = driver.find_element_by_class_name("msg-btn")
            accept.click()
            break
        except Exception as _:
            pass"""

def df_to_excel():
    foot = page2Foot()
    bask = page2Bask()
    tenn = page2Tenn()
    tabl = page2Tabl()
    writer = pd.ExcelWriter(f"Apuestas/excel_files/{NAMEFILE.get(2)}",engine="xlsxwriter")
    bask.to_excel(writer,index=False,sheet_name="Basketball")
    foot.to_excel(writer,index=False,sheet_name="Football")
    tenn.to_excel(writer,index=False,sheet_name="Tennis")
    tabl.to_excel(writer,index=False,sheet_name="Table")
    writer.save()
    print(f"Guardado a las {datetime.now()} para {NAMEFILE[2]}")
    driver.refresh()
    
def runPage():
    login()
    df_to_excel()

def page2Foot():
    try:
        driver.find_element_by_xpath("//a[@href='#inplay-tab-FOOT']").click()
    except Exception as _:
        try:
            df_excel = pd.read_excel(f"Apuestas/excel_files/{NAMEFILE.get(2)}",sheet_name=SHEETNAMES[2])
            return df_excel
        except Exception as _:
            return pd.DataFrame(columns=COLUMNAS["empate"])
    time.sleep(1)
    soup = BeautifulSoup(driver.page_source,'html5lib')
    foot = soup.find("div",{"id":PARTIDOS.get("foot")})
    campeonatos = foot.find_all("div",{"class":re.compile(CAMPEONATOS)})
    nameGruop="None"
    values = []
    for cam in campeonatos:
        try:
            typeName=cam.find('div',attrs={"class":"ev-type-header"})
            nameGruop= typeName.text.strip()
        except Exception as _:
            valid = cam.find_all("a",{"class":"multisort-default"})
            if (len(valid)>0):
                continue
            timeClock:PageElement = cam.find("div",{"class":"time"})
            minutes:PageElement = timeClock.find("span",{"class":re.compile("clock")})
            period = timeClock.find("span",{"class":"period"})
            name = list(cam.find_all("div",{"class":"team-score"}))
            prices = list(cam.find_all("span",{"class":"price dec"}))
            score = list(cam.find_all("span" ,{"class":re.compile(r"score")}))#"data-team_prop":"score_a","data-team_prop":"score_b"})
            if (period.text.strip() == "Segunda Mitad"):
                periodo = 2
            else:
                periodo = 1
            values.append(
                [name[0].text.strip()[2:],int(score[0].text),float(prices[0].text),
                name[1].text.strip()[2:],int(score[1].text),float(prices[2].text),
                float(prices[1].text),nameGruop,datetime.now(),minutes.text.strip(),
                periodo,False])

    try:
        df_excel = pd.read_excel(NAMEFILE[2],sheet_name=SHEETNAMES[2])
        df_values = pd.DataFrame(values,columns=COLUMNAS["empate"])
        df = df_excel.append(df_values)
        return df
    except Exception as _:
        df = pd.DataFrame(values,columns=COLUMNAS["empate"])
        print(df)
        return df

def page2Bask():
    try:
        driver.find_element_by_xpath("//a[@href='#inplay-tab-BASK']").click()
    except Exception as _:
        try:
            df_excel = pd.read_excel(f"Apuestas/excel_files/{NAMEFILE.get(2)}",sheet_name=SHEETNAMES[1])
            return df_excel
        except Exception as _:
            return pd.DataFrame(columns=COLUMNAS["no_empate"])
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source,'html5lib')
    bask = soup.find("div",{"id":PARTIDOS.get("bask")})
    try:
        campeonatos = bask.find_all("div",{"class":re.compile(CAMPEONATOS)})
    except Exception as e:
        print(e)
        time.sleep(1)
        campeonatos = bask.find_all("div",{"class":re.compile(CAMPEONATOS)})
        print(type(campeonatos))
        try:
            df_excel = pd.read_excel(f"Apuestas/excel_files/{NAMEFILE.get(2)}",sheet_name=SHEETNAMES[1])
            return df_excel
        except Exception as _:
            return pd.DataFrame(columns=COLUMNAS["no_empate"])
            
    nameGruop="None"
    values = []
    for cam in campeonatos:
        try:
            typeName=cam.find('div',attrs={"class":"ev-type-header"})
            nameGruop= typeName.text.strip()
        except Exception as e:
            valid = cam.find_all("a",{"class":"multisort-default"})
            if (len(valid)>0):
                continue
            timeClock:PageElement = cam.find("div",{"class":"time"})
            minutes:PageElement = timeClock.find("span",{"class":re.compile("clock")})
            period = timeClock.find("span",{"class":"period"})
            name = list(cam.find_all("div",{"class":"team-score"}))
            prices = list(cam.find_all("span",{"class":"price dec"}))
            score = list(cam.find_all("span" ,{"class":re.compile(r"score")}))#"data-team_prop":"score_a","data-team_prop":"score_b"})
            if (period.text.strip() != "1º Cuarto"):
                periodo = 1
            elif (period.text.strip() != "2º Cuarto"):
                periodo = 2
            elif (period.text.strip() != "3º Cuarto"):
                periodo = 3
            elif (period.text.strip() != "4º Cuarto"):
                periodo = 4
            else:
                periodo = 0
            values.append([
                name[0].text.strip()[2:],int(score[0].text),float(prices[0].text),
                name[1].text.strip()[2:],int(score[1].text),float(prices[1].text),
                nameGruop,datetime.now(),minutes.text.strip(),
                periodo,False])

    #print(names,scores,pricesTo)
    try:
        df_excel = pd.read_excel(f"Apuestas/excel_files/{NAMEFILE.get(2)}",sheet_name=SHEETNAMES[1])
        df_values = pd.DataFrame(values,columns=COLUMNAS["no_empate"])
        df = df_excel.append(df_values)
        return df
    except Exception as _:
        df = pd.DataFrame(values,columns=COLUMNAS["no_empate"])
        return df

def page2Tenn():
    try:
        driver.find_element_by_xpath("//a[@href='#inplay-tab-TENN']").click()
    except Exception as _:
        try:
            df_excel = pd.read_excel(NAMEFILE[2],sheet_name=SHEETNAMES[3])
            return df_excel
        except Exception as _:
            return pd.DataFrame(columns=COLUMNAS["no_empate"])
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source,'html5lib')
    tenn = soup.find("div",{"id":PARTIDOS.get("tenn")})
    campeonatos = tenn.find_all("div",{"class":re.compile(CAMPEONATOS)})
    nameGruop="None"
    values = []
    for cam in campeonatos:
        try:
            typeName=cam.find('div',attrs={"class":"ev-type-header"})
            nameGruop= typeName.text.strip()
        except Exception:
            valid = cam.find_all("a",{"class":"multisort-default"})
            if (len(valid)>0):
                continue
            timeClock:PageElement = cam.find("div",{"class":"time"})
            minutes:PageElement = timeClock.find("span",{"class":re.compile("clock")})
            period = timeClock.find("span",{"class":"period"})
            name = list(cam.find_all("div",{"class":"team-score"}))
            prices = list(cam.find_all("span",{"class":"price dec"}))
            score = list(cam.find_all("span" ,{"class":re.compile(r"score")}))#"data-team_prop":"score_a","data-team_prop":"score_b"})
            values.append(
                [name[0].text.strip()[2:],int(score[0].text),float(prices[0].text),
                name[1].text.strip()[2:],int(score[1].text),float(prices[1].text),
                nameGruop,datetime.now(),minutes.text.strip(),
                period.text.strip(),False])

    #print(names,scores,pricesTo)

    try:
        df_excel = pd.read_excel(f"Apuestas/excel_files/{NAMEFILE.get(2)}",sheet_name=SHEETNAMES[3])
        df_values = pd.DataFrame(values,columns=COLUMNAS["no_empate"])
        df = df_excel.append(df_values)
        return df
    except Exception as e:
        df = pd.DataFrame(values,columns=COLUMNAS["no_empate"])
        return df

def page2Tabl():
    try:
        driver.find_element_by_xpath("//a[@href='#inplay-tab-TABL']").click()
    except Exception as e:
        try:
            df_excel = pd.read_excel(f"Apuestas/excel_files/{NAMEFILE.get(2)}",sheet_name=SHEETNAMES[4])
            return df_excel
        except Exception as ex:
            return pd.DataFrame(columns=COLUMNAS["no_empate"])
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source,'html5lib')
    tabl = soup.find("div",{"id":PARTIDOS.get("tabl")})
    campeonatos = tabl.find_all("div",{"class":re.compile(CAMPEONATOS)})
    nameGruop="None"
    values = []
    for cam in campeonatos:
        try:
            typeName=cam.find('div',attrs={"class":"ev-type-header"})
            nameGruop= typeName.text.strip()
        except Exception as e:
            valid = cam.find_all("a",{"class":"multisort-default"})
            if (len(valid)>0):
                continue
            timeClock:PageElement = cam.find("div",{"class":"time"})
            minutes:PageElement = timeClock.find("span",{"class":re.compile("clock")})
            period = timeClock.find("span",{"class":"period"})
            name = list(cam.find_all("div",{"class":"team-score"}))
            prices = list(cam.find_all("span",{"class":"price dec"}))
            score = list(cam.find_all("span" ,{"class":re.compile(r"score")}))#"data-team_prop":"score_a","data-team_prop":"score_b"})
            values.append(
                [name[0].text.strip()[2:],int(score[0].text),float(prices[0].text),
                name[1].text.strip()[2:],int(score[1].text),float(prices[1].text),
                nameGruop,datetime.now(),minutes.text.strip(),
                period.text.strip(),False])
     
    #print(names,scores,pricesTo)

    try:
        df_excel = pd.read_excel(f"Apuestas/excel_files/{NAMEFILE.get(2)}",sheet_name=SHEETNAMES[4])
        df_values = pd.DataFrame(values,columns=COLUMNAS["no_empate"])
        df = df_excel.append(df_values)
        return df
    except Exception as e:
        df = pd.DataFrame(values,columns=COLUMNAS["no_empate"])
        return df

