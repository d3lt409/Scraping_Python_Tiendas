import time
import json
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

chrome_options = Options()
prefs = {"profile.managed_default_content_settings.images": 2, "stylesheet": 2}
chrome_options.add_experimental_option("prefs", prefs)
chrome_options.add_argument("--log-level=3")
chrome_options.add_argument("--remote-debugging-port=9230")
chrome_options.set_capability('goog:loggingPrefs',{'performance': 'ALL'})


# Create a new instance of the Chrome driver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()) 
                              ,options=chrome_options)    

# Navigate to the desired webpage
driver.get("https://www.exito.com/moda-y-accesorios/arkitect-francesca-miranda")

# Wait for the network traffic to complete
time.sleep(10)
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div#gallery-layout-container > div > section > a > article")))

# Get the performance logs
logs_raw = driver.get_log("performance")
logs = [json.loads(lr["message"])["message"] for lr in logs_raw]

# Filter the logs to find the JSON response
def log_filter(log_):
    return (log_["method"] == "Network.responseReceived"
            and "application/json" in log_["params"]["response"]["mimeType"] 
            and "https://www.exito.com/_v/public/graphql/v1?workspace" in log_["params"]["response"]["url"])

json_logs = filter(log_filter, logs)
json_data = []
# Extract the JSON response
for i,log in enumerate(json_logs):
    request_id = log["params"]["requestId"]
    json_response = driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
    if "body" in json_response:
        body = json.loads(json_response["body"])
        if "data" in body and "productSearch" in body["data"]:
            with open(f"josn{i}.json", "w") as fp:
                fp.write(json.dumps(body["data"]["productSearch"]))
    
driver.close()