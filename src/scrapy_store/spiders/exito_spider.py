import scrapy
from scrapy_splash import SplashRequest
from scrapy_splash.response import SplashResponse
from scrapy.http.response.html import HtmlResponse
import json


class ExitoSpider(scrapy.Spider):
    name = "exito"
    start_urls = [
        "https://www.exito.com/moda-y-accesorios/arkitect-francesca-miranda"]

    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(url, self.parse, endpoint='render.har', args={'wait': 2, 'response_body': 1})

    def parse(self, response: SplashResponse):
        # Extraer información de la pestaña "Network" usando el campo "body"
        print(response)
        # print(network_data)
        # with open("out.json", 'w', encoding='utf-8') as fp:
        #     fp.write(network_data)
        # # Decodificar la información JSON que contiene los datos de la red
        # network_data_json = json.loads(network_data)
        # xhr_and_fetch_data = []
        # for entry in network_data_json['log']['entries']:
        #     request = entry['request']
        #     resp = entry['response']

        #     # Filtrar solo las solicitudes y respuestas XHR y Fetch
        #     if request['method'] in ('GET') and 'xhr' in request['headers'].get('fetch', '').lower():
        #         xhr_and_fetch_data.append({
        #             'url': request['url'],
        #             'method': request['method'],
        #             'status': resp['status'],
        #             'response_body': resp.get('content', {}).get('text', ''),
        #         })
        # for data in xhr_and_fetch_data:
        #     print(data)
        # # Aquí puedes utilizar selectores de Scrapy para extraer información
        # # como lo hacías antes, sin embargo, el contenido será el generado por JavaScript.
        # product_names = response.css(".product-name::text").extract()
        # product_prices = response.css(".product-price::text").extract()

        # # Aquí puedes procesar los datos como desees
        # for name, price in zip(product_names, product_prices):
        #     yield {
        #         'name': name,
        #         'price': price,
        #     }
