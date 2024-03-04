import gc
import os
import sys
import time
from typing import TypeVar

from seleniumwire.undetected_chromedriver import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from src.database.database import DataBase
from src.models.models import Base
from src.utils.util import internet_on

A = TypeVar('A', bound=Base)
CLICK = "arguments[0].click();"


class Engine:

    def __init__(self, page_url: str, model: A, headless: bool = False) -> None:
        self.headless = headless
        self._driver = self.create_driver()
        self._current_url = page_url
        self.init_page()
        self.db = DataBase(model)

    def implicitly_wait(self, time: int):
        self._driver.implicitly_wait(time)

    def create_driver(self):
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.page_load_strategy = 'none'
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument("--enable-automation")
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument("--dns-prefetch-disable")
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--ignore-certificate-errors")
        # chrome_options.add_argument("--allow-running-insecure-content")
        # chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("force-device-scale-factor=0.75")
        chrome_options.add_argument("high-dpi-support=0.75")
        chrome_options.set_capability(
            'goog:loggingPrefs', {'performance': 'ALL'})
        # chrome_options.experimental_options["prefs"] = {
        #     "profile.managed_default_content_settings.images": 2,
        #     "stylesheet": 2
        # }
        PROXY = 'http://61.28.233.217:3128'

        seleniumwire_options = {
            'disable_encoding': True,
            'images': False,
            'stylesheet': False,
            'request_block_rules': [
                {
                    'resource_type': 'image'
                },
                {
                    'resource_type': 'stylesheet'
                }
            ]

        }
        options = {

        }
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),
                                  options=chrome_options, seleniumwire_options=seleniumwire_options)
        return driver

    def _get_driver(self):
        return self._driver

    def _get_current_url(self):
        return self._current_url

    def _set_current_url(self, url):
        self._current_url = url

    current_url = property(fget=_get_current_url, fset=_set_current_url)
    driver = property(fget=_get_driver)

    def init_page(self):
        while not internet_on():
            continue
        self._driver.maximize_window()
        self._driver.get(self._current_url)

    def ready_document(self):
        WebDriverWait(self._driver, 60).until(
            lambda driver: driver.execute_script('return document.readyState') == 'complete')

    def crash_refresh_page(self):
        while not internet_on():
            continue
        try:
            self._driver.close()
            self._driver.quit()
            gc.collect(2)
        except WebDriverException:
            pass
        self._driver = self.create_driver()
        self.init_page()
        self.ready_document()

    def element_wait_search(self, time: int, by, value: str) -> WebElement:
        return WebDriverWait(self._driver, time).until(EC.presence_of_element_located((by, value)))

    def element_wait_click(self, time: int, by, value: str):
        element = self.element_wait_search(time, by, value)
        self.click(element)

    def click(self, element: WebElement):
        self._driver.execute_script(CLICK, element)

    def elements_wait_search(self, time: int, by, value: str):
        return WebDriverWait(self._driver, time).until(EC.presence_of_all_elements_located((by, value)))

    def close(self):
        try:
            self._driver.stop_client()
            self._driver.close()
            self._driver.quit()
        except Exception:
            pass
        finally:
            self.db.close()
