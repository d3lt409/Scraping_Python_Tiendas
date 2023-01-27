import re
import scrapy
from scrapy.selector import Selector
from scrapy.http import Response
import time

from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException

from scrapy_selenium import SeleniumRequest
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


XPATH_CATEGORY_BUTTON = "//*[@id='category-menu']"
XPATH_LIST_CATEGORY_LI = "//div[@class='exito-category-menu-3-x-categoryList']//ul[@class='exito-category-menu-3-x-categoryListD']/li"
XPATH_CATEGORY_CONTAINER = "//div[@class='exito-category-menu-3-x-itemSideMenu']"
#each cat container
XPATH_NAME_CATEGORY = "//*[contains(@id,'Categorías-nivel2-')]/strong"

XPATH_LIST_CATEGORY_LI_VERIFY = "//div[@class='exito-category-menu-3-x-categoryList']//ul[@class='exito-category-menu-3-x-categoryListD']/li/div/p[text()!='']"
XPATH_LIST_SUBVCAT_VERIFY = "//p[contains(@id,'Categorías-nivel3-') and text()!='']"

#Elements XPATH
XPATH_LIST_ELEMENTS_VERIFY = "//div[@id='gallery-layout-container']//h3[contains(@class,'-productNameContainer')]/span[text()!='']"
XPATH_LIST_ELEMENTS = "//div[@id='gallery-layout-container']//div[contains(@class,'Content--product-info-element')]"

XPATH_NAME_ELEMENT = ".//h3[contains(@class,'-productNameContainer')]/span[text()!='']/text()"
XPATH_FOOTER_PAGE = "//div[contains(@class,'-x-buttonShowMore')]/button[descendant::div[text()!='']]"

XPATH_NOT_FOUND = "//div[@class='exito-search-result-4-x-containerNotFoundExito']"

URL = "https://www.exito.com"
TIME = 20


class SpiderExito(scrapy.Spider):
    name = "exito"
    custom_settings = {"FEED_URI":"/src/assets/results.json"}
    
    def start_requests(self):
        yield SeleniumRequest(
            url = "https://www.exito.com",
            callback = self.parse_links, 
            wait_time=20,
            wait_until=EC.element_to_be_clickable((By.XPATH, XPATH_CATEGORY_BUTTON))
            )
    
    def parse_links(self,response:Response):
        driver:WebDriver = response.meta["driver"]
        driver.implicitly_wait(10)
        self.action = ActionChains(driver)
        
        driver.find_element(By.XPATH, XPATH_CATEGORY_BUTTON).click()
        WebDriverWait(driver,TIME).until(EC.presence_of_element_located((By.XPATH,XPATH_LIST_CATEGORY_LI_VERIFY)))
        links = {}
        # driver.execute_script("document.body.style.zoom='80%';")
        for el in driver.find_elements(By.XPATH, XPATH_LIST_CATEGORY_LI)[0:1]:
            self.action.move_to_element(el).perform()
            WebDriverWait(driver,TIME).until(EC.presence_of_element_located((By.XPATH,XPATH_LIST_SUBVCAT_VERIFY)))
            sub_categories = el.find_elements(By.XPATH,"//a[contains(@id,'Categorías-nivel3-')]")
            cat_name = driver.find_element(By.XPATH,XPATH_NAME_CATEGORY).text
            sub_links = {}
            for sub in sub_categories[0:1]:
                sub_name = sub.find_element(By.XPATH, XPATH_LIST_SUBVCAT_VERIFY).text
                sub_link = sub.get_attribute("href")
                sub_links[sub_name] = sub_links.get(sub_name,[])+[sub_link]
            links[cat_name] = sub_links
        for cat, sub_dict in links.items():
            for sub, links in sub_dict.items():
                for link in links[0:2]:
                    yield SeleniumRequest(
                        url=link+"?page=1",
                        callback = self.parse, 
                        wait_time=TIME,
                        cb_kwargs = {"sub_name" :sub_name,"cat_name":cat}
                        )
                    

            
    def parse(self,response:Response, **kwargs):
        driver:WebDriver = response.meta["driver"]
        try: 
            WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH,XPATH_NOT_FOUND)))
        except TimeoutException: 
            yield kwargs
        element = WebDriverWait(driver,TIME).until(EC.presence_of_all_elements_located((By.XPATH,XPATH_LIST_ELEMENTS_VERIFY)))
        driver.execute_script("arguments[0].scrollIntoView();", element[-1])
        time.sleep(2)
        footer = WebDriverWait(driver,TIME).until(EC.presence_of_element_located((By.XPATH,XPATH_FOOTER_PAGE)))
        driver.execute_script("arguments[0].scrollIntoView();", footer)

        response_obj = Selector(text = driver.page_source)
        values = response_obj.xpath(XPATH_LIST_ELEMENTS)
        
        for val in values:
            kwargs.update({"name":val.xpath(XPATH_NAME_ELEMENT).get()})
        comp = re.compile("(?<=page=)\d*$")
        page_num = int(comp.search(driver.current_url).group(0)) + 1
        new_url = comp.sub(driver.current_url,str(page_num))
        yield SeleniumRequest(
                        url=new_url,
                        callback = self.parse, 
                        wait_time=TIME,
                        cb_kwargs = kwargs
                        )
