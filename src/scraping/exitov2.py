import json
import re
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException
import requests

import sys; sys.path.append(".")
from src.utils.util import (
    Engine)
# from mail.send_email import send_email,erorr_msg

def process_browser_log_entry(entry):
    response = json.loads(entry['message'])['message']
    return response



def main():
    engine = Engine("https://www.exito.com/moda-y-accesorios/arkitect-francesca-miranda","Exito")
    engine.ready_document()
    time.sleep(10)
    container = engine.element_wait_searh(20,By.ID, "gallery-layout-container")
    engine.driver.execute_script("arguments[0].scrollIntoView(true);", container)
    engine.elements_wait_searh(10,By.CSS_SELECTOR, "div#gallery-layout-container > div > section > a > article")
    
    requests = engine.driver.get_network_requests()
    # For each network request, get the response
    for request in requests:
        response = request.response

        # Get the content of the response
        content = response.content

        # Check if the content of the response is JSON
        if json.is_json(content):
            # Save the content of the response to a file
            with open('response.json', 'w') as f:
                f.write(content)
    # browser_log = engine.driver.get_log('performance') 
    # network_events = [process_browser_log_entry(entry) for entry in browser_log]
    # # Filtrar solo las respuestas que son de tipo JSON
    # json_responses = []
    # for event in network_events:
    #     if event["params"] and "response" in event["params"] : 
    #         response = event['params']['response']
    #         response_url = response['url']
    #         response_status = response['status']
    #         response_headers = response.get('headers', {})
    #         response_content_type = response_headers.get('content-type', '').lower()

    #         # Verificar si la respuesta es de tipo JSON
    #         if 'https://www.exito.com/_v/public/graphql/v1?workspace' in response_url:
    #             print()
    #             # Acceder a los datos JSON dentro de la respuesta
    #             try:
    #                 response_data = json.loads(response.get('body', ''))
    #             except json.JSONDecodeError:
    #                 response_data = {}

    #             # Agregar la información relevante de la respuesta a la lista
    #             if response_data:
    #                 json_responses.append({
    #                     'url': response_url,
    #                     'status': response_status,
    #                     'data': response_data
    #                 })

    # # Ahora puedes procesar las respuestas JSON como desees
    # for json_response in json_responses:
    #     print(f"URL: {json_response['url']}")
    #     print(f"Status Code: {json_response['status']}")
    #     print(f"Data: {json_response['data']}")
    #     print('---')
    
    engine.close()
