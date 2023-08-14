import re
import os
import scrapy
from scrapy.http.response import Response
from scrapy.selector import Selector
from scrapy.http import Response
import time

from scrapy_splash import SplashRequest
from .constants import *

URL = "https://www.exito.com"
TIME = 20


class MySpider(scrapy.Spider):
    name = 'exito-spider'
    start_urls = ["https://www.exito.com/mercado/lacteos-huevos-y-refrigerados/huevos?page=3"]

    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(url, self.parse, args={'wait': 10})

    def parse(self, response:Response):
        # Aquí puedes usar expresiones XPath o CSS para extraer datos de la página
        # Ejemplo: obtener el título de la página
        # elements = engine.elements_wait_searh(10,By.CSS_SELECTOR, "div#gallery-layout-container > div > section > a > article")
        scroll_script = """
        function main(splash)
            splash:scroll_position(0, splash:jsfunc("function() { return document.body.scrollHeight / 2; }"))
            splash:wait(3)
            splash:scroll_position(0, document.body.scrollHeight)
            splash:wait(2)
            return splash:html()
        end
        """
        yield SplashRequest(response.url, self.parse_result,
                            args={'lua_source': scroll_script},  # Esperar 2 segundos después del scroll
                            endpoint='execute')
        
    def parse_result(self, response:Response):
        elements = response.css("div#gallery-layout-container > div > section > a > article")
        for element in elements:
            print(element)
