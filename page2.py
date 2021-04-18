import re
import time
from bs4 import BeautifulSoup
from selenium import webdriver
import pandas as pd
from datetime import date,datetime
import schedule
from selenium.webdriver.common import by


USER = 'diegofernandozamoradiaz@gmail.com'
PASSWORD = 'Juchipuchi123.'
driver = webdriver.Chrome('chromedriver')
#driver_google = webdriver.Chrome('chromedriver')
PARTIDOS = {"bask":"inplay-tab-BASK","foot":"inplay-tab-FOOT","tenn":"inplay-tab-TENN","tabl":"inplay-tab-TABL"}
CAMPEONATOS = "table-row row-wrap"
NAMEFILE = "wplay.xlsx"

def login():
    driver.get("https://apuestas.wplay.co/es")
    #driver_google.get("https://www.google.com/search?q=real+madrid+vs+liverpool")
    time.sleep(2)
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
            pass

def df_to_excel():
    foot = page2Foot()
    bask = page2Bask()
    tenn = page2Tenn()
    tabl = page2Tabl()
    writer = pd.ExcelWriter(NAMEFILE,engine="xlsxwriter")
    bask.to_excel(writer,index=False,sheet_name="Basketball")
    foot.to_excel(writer,index=False,sheet_name="Football")
    tenn.to_excel(writer,index=False,sheet_name="Tennis")
    tabl.to_excel(writer,index=False,sheet_name="Table")
    writer.save()
    print("Guardado")
    
def results(datos:pd.DataFrame):
    for _,row in datos.iterrows():
        name1 = row["Nombre 1"]
        name2 = row["Nombre 2"]
        driver_google.get(f"https://apuestas.wplay.co/es/search?s={name1}+{name2}")
        time.sleep(2)
        

def page2Foot():
    try:
        driver.find_element_by_xpath("//a[@href='#inplay-tab-FOOT']").click()
    except Exception as _:
        try:
            df_excel = pd.read_excel(NAMEFILE,sheet_name="Football")
            return df_excel
        except Exception as ex:
            return pd.DataFrame()
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
        except Exception as e:
            valid = cam.find_all("a",{"class":"multisort-default"})
            if (len(valid)>0):
                continue
            timeClock = cam.find("div",{"class":"time"})
            minutes = timeClock.find("span",{"class":re.compile("clock")})
            periodo = timeClock.find("span",{"class":"period"})
            print(minutes.text.strip(),periodo.text.strip())
            name = list(cam.find_all("div",{"class":"team-score"}))
            prices = list(cam.find_all("span",{"class":"price dec"}))
            score = list(cam.find_all("span" ,{"class":re.compile(r"score")}))#"data-team_prop":"score_a","data-team_prop":"score_b"})
            values.append([name[0].text.strip()[2:],int(score[0].text),float(prices[0].text),name[1].text.strip()[2:],int(score[1].text),float(prices[2].text),float(prices[1].text),nameGruop,datetime.now()])


    try:
        df_excel = pd.read_excel(NAMEFILE,sheet_name="Football")
        df_values = pd.DataFrame(values,columns=["Nombre 1","Puntaje 1","Precio 1","Nombre 2","Puntaje 2","Precio 2","Empate","Grupo","Fecha de juego"])
        df = df_excel.append(df_values)
        return df

    except:
        df = pd.DataFrame(values,columns=["Nombre 1","Puntaje 1","Precio 1","Nombre 2","Puntaje 2","Precio 2","Empate","Grupo","Fecha de juego"])
        print(df)
        return df

def page2Bask():
    try:
        driver.find_element_by_xpath("//a[@href='#inplay-tab-BASK']").click()
    except Exception as _:
        try:
            df_excel = pd.read_excel(NAMEFILE,sheet_name="Basketball")
            return df_excel
        except Exception as _:
            return pd.DataFrame()
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source,'html5lib')
    bask = soup.find("div",{"id":PARTIDOS.get("bask")})
    campeonatos = bask.find_all("div",{"class":re.compile(CAMPEONATOS)})
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
            name = list(cam.find_all("div",{"class":"team-score"}))
            prices = list(cam.find_all("span",{"class":"price dec"}))
            score = list(cam.find_all("span" ,{"class":re.compile(r"score")}))#"data-team_prop":"score_a","data-team_prop":"score_b"})
            values.append([name[0].text.strip()[2:],int(score[0].text),float(prices[0].text),name[1].text.strip()[2:],int(score[1].text),float(prices[1].text),nameGruop,datetime.now()])

    #print(names,scores,pricesTo)
    try:
        df_excel = pd.read_excel(NAMEFILE,sheet_name="Basketball")
        df_values = pd.DataFrame(values,columns=["Nombre 1","Puntaje 1","Precio 1","Nombre 2","Puntaje 2","Precio 2","Grupo","Fecha de juego"])
        df = df_excel.append(df_values)
        return df
    except Exception as e:
        df = pd.DataFrame(values,columns=["Nombre 1","Puntaje 1","Precio 1","Nombre 2","Puntaje 2","Precio 2","Grupo","Fecha de juego"])
        return df

def page2Tenn():
    try:
        driver.find_element_by_xpath("//a[@href='#inplay-tab-TENN']").click()
    except Exception as e:
        try:
            df_excel = pd.read_excel(NAMEFILE,sheet_name="Tennis")
            return df_excel
        except Exception as ex:
            return pd.DataFrame()
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
            name = list(cam.find_all("div",{"class":"team-score"}))
            prices = list(cam.find_all("span",{"class":"price dec"}))
            score = list(cam.find_all("span" ,{"class":re.compile(r"score")}))#"data-team_prop":"score_a","data-team_prop":"score_b"})
            values.append([name[0].text.strip()[2:],int(score[0].text),float(prices[0].text),name[1].text.strip()[2:],int(score[1].text),float(prices[1].text),nameGruop,datetime.now()])

    #print(names,scores,pricesTo)

    try:
        df_excel = pd.read_excel(NAMEFILE,sheet_name="Tennis")
        df_values = pd.DataFrame(values,columns=["Nombre 1","Puntaje 1","Precio 1","Nombre 2","Puntaje 2","Precio 2","Grupo","Fecha de juego"])
        df = df_excel.append(df_values)
        return df
    except Exception as e:
        df = pd.DataFrame(values,columns=["Nombre 1","Puntaje 1","Precio 1","Nombre 2","Puntaje 2","Precio 2","Grupo","Fecha de juego"])
        return df

def page2Tabl():
    try:
        driver.find_element_by_xpath("//a[@href='#inplay-tab-TABL']").click()
    except Exception as e:
        try:
            df_excel = pd.read_excel(NAMEFILE,sheet_name="Table")
            return df_excel
        except Exception as ex:
            return pd.DataFrame()
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
            name = list(cam.find_all("div",{"class":"team-score"}))
            prices = list(cam.find_all("span",{"class":"price dec"}))
            score = list(cam.find_all("span" ,{"class":re.compile(r"score")}))#"data-team_prop":"score_a","data-team_prop":"score_b"})
            values.append([name[0].text.strip()[2:],int(score[0].text),float(prices[0].text),name[1].text.strip()[2:],int(score[1].text),float(prices[1].text),nameGruop,datetime.now()])
     
    #print(names,scores,pricesTo)

    try:
        df_excel = pd.read_excel(NAMEFILE,sheet_name="Table")
        df_values = pd.DataFrame(values,columns=["Nombre 1","Puntaje 1","Precio 1","Nombre 2","Puntaje 2","Precio 2","Grupo","Fecha de juego"])
        df = df_excel.append(df_values)
        return df
    except Exception as e:
        df = pd.DataFrame(values,columns=["Nombre 1","Puntaje 1","Precio 1","Nombre 2","Puntaje 2","Precio 2","Grupo","Fecha de juego"])
        return df


login()
schedule.every(3).minutes.do(df_to_excel)
df_to_excel()
while True:
    schedule.run_pending()