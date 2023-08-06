import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException

import sys; sys.path.append(".")
from src.utils.util import init_scraping
# from mail.send_email import send_email,erorr_msg

driver,db = init_scraping("https://www.exito.com","Exito")
print(driver.get_network_conditions())
driver.close()
