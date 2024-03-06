import gc
import os
import sys


from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

from src.database.database import DataBase
from src.scraper.engine.constants import A, CHROME, CLICK

from src.scraper.engine.option import Option
from src.utils.util import internet_on


class Engine:

    profile = None
    proxy = None
    server = None

    def __init__(self, page_url: str, model: A, wire_requests: bool = False,  headless: bool = False, browser=CHROME) -> None:
        self.headless = headless
        self._driver = self.create_driver(wire_requests, browser)
        self._current_url = page_url
        self.init_page()
        self.db = DataBase(model)

    def implicitly_wait(self, time: int):
        self._driver.implicitly_wait(time)

    def create_driver(self, selenium_wire, browser):

        options = Option(browser, selenium_wire, self.headless)
        if browser == CHROME:
            if selenium_wire:
                from seleniumwire import webdriver
                seleniumwire_options = options.create_wire_options()
                driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),
                                          options=options.option, seleniumwire_options=seleniumwire_options)
            else:
                from selenium import webdriver
                driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),
                                          options=options.option)
            return driver
        else:

            if selenium_wire:
                from seleniumwire import webdriver
                seleniumwire_options = options.create_wire_options()
                driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()),
                                           options=options.option, seleniumwire_options=seleniumwire_options)
            else:
                from selenium import webdriver
                from browsermobproxy import Server
                self.server = Server(os.path.join(
                    os.getcwd(), "proxy/browsermob-proxy-2.1.4/bin/browsermob-proxy.bat"), options={"add_opens": "--add-opens=java.base/java.lang=ALL-UNNAMED --add-opens=java.base/java.lang.invoke=ALL-UNNAMED --add-opens=java.base/java.io=ALL-UNNAMED"})
                self.server.start()
                self.proxy = self.server.create_proxy()
                self.profile = webdriver.FirefoxProfile()
                self.profile.set_proxy(self.proxy.selenium_proxy())
                driver = webdriver.Firefox(firefox_profile=self.profile,
                                           options=options.option)
                self.proxy.new_har("file_name", options={
                    'captureHeaders': True, 'captureContent': True})
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
            self.server.stop()
            self._driver.close()
            self._driver.quit()

        except Exception:
            pass
        finally:
            self.db.close()
