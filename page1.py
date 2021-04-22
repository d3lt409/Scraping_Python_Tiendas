import time
from bs4 import BeautifulSoup
from selenium import webdriver
import pandas as pd

from selenium.webdriver.common.by import By
driver = webdriver.Chrome('chrome/chromedriver')
driver.get("https://betplay.com.co/apuestas#filter/basketball")
time.sleep(2)
expand = driver.find_elements(By.XPATH, value="//div[@class='sc-fzoLag ioxMxx sc-fznWOq kESZxi KambiBC-betty-collapsible KambiBC-collapsible-container KambiBC-mod-event-group-container']")
for ex in expand:
    ex.click()
time.sleep(4)
soup = BeautifulSoup(driver.page_source,'html.parser')
driver.close()
#names = list(soup.find_all('div',attrs={"class":"KambiBC-event-participants__name"}))
#votes = list(soup.find_all('div',attrs={"class":"sc-AxheI kIcofq"}))
boths = list(soup.find_all('div',attrs={"class":"sc-AxirZ bnliBi"}))
main = list(soup.find_all("div",attrs={"class":"sc-fzqARJ grXYBm"}))
vs = []
if (len(boths) > 0):
    j = 0
    for i in range(0,len(boths)-1,2):
        values = boths[i+1].find("div",{"class":"sc-AxiKw bfgHJg"})
        valueslast = boths[i].find("div",{"class":"sc-AxiKw bfgHJg"})
        name2 = values.find("div",{"class":"sc-AxhCb fmbcv"}).text
        name1 = valueslast.find("div",{"class":"sc-AxhCb fmbcv"}).text

        values = boths[i+1].find("div",{"class":"sc-AxgMl eHRTXh"})
        valueslast = boths[i].find("div",{"class":"sc-AxgMl eHRTXh"})
        vote2 = values.find("div",{"class":"sc-AxheI kIcofq"}).text
        vote1 = valueslast.find("div",{"class":"sc-AxheI kIcofq"}).text

        vs.append((name1,vote1,name2,vote2))#,main[j].text))
        j+=1

df = pd.DataFrame(vs)
print(df)


