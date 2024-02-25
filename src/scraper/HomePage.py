from src.scraper.BasePage import BasePage


from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement

from selenium.webdriver.common.devtools.v113.network import get_response_body

import sys

from src.models.models import Base


class HomePage(BasePage):

    url = ''

    def load(self):
        self.driver.get(self.url)

    def element_wait_searh(self, time: int, by, value: str) -> WebElement:
        return WebDriverWait(self._driver, time).until(EC.presence_of_element_located((by, value)))

    def element_wait_click(self, time: int, by, value: str):
        self.driver.execute_script(
            "arguments[0].click();", self.element_wait_searh(time, by, value))

    def click(self, element: WebElement):
        self.driver.execute_script("arguments[0].click();", element)

    def elements_wait_searh(self, time: int, by, value: str) -> list[WebElement]:
        return WebDriverWait(self._driver, time).until(EC.presence_of_all_elements_located((by, value)))
