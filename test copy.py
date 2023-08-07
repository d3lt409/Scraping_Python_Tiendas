import time
import json
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from browsermobproxy import Server

chrome_options = Options()
prefs = {"profile.managed_default_content_settings.images": 2, "stylesheet": 2}
chrome_options.add_experimental_option("prefs", prefs)
chrome_options.add_argument("--log-level=3")
chrome_options.add_argument("--ignore-certificate-errors")
chrome_options.add_argument("--remote-debugging-port=9230")
chrome_options.set_capability('goog:loggingPrefs',{'performance': 'ALL'})

  
# Main Function
if __name__ == "__main__":
  
    # Enter the path of bin folder by
    # extracting browsermob-proxy-2.1.4-bin
    path_to_browsermobproxy = "C:\\Users\\Manuel Fernandez\\Downloads\\browsermob-proxy-2.1.4\\bin\\"
  
    # Start the server with the path and port 8090
    server = Server(path_to_browsermobproxy
                    + "browsermob-proxy", options={'port': 8090})
    server.start()
  
    # Create the proxy with following parameter as true
    proxy = server.create_proxy(params={"trustAllServers": "true"})
  
    # Create the webdriver object and pass the arguments
    options = webdriver.ChromeOptions()
  
    # Chrome will start in Headless mode
    options.add_argument('headless')
  
    # Ignores any certificate errors if there is any
    options.add_argument("--ignore-certificate-errors")
  
    # Setting up Proxy for chrome
    options.add_argument("--proxy-server={0}".format(proxy.proxy))
  
    # Startup the chrome webdriver with executable path and
    # the chrome options as parameters.
    # Create a new instance of the Chrome driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()) 
                                ,options=chrome_options)    
    
    # Create a new HAR file of the following domain
    # using the proxy.
    proxy.new_har("exito.com/moda-y-accesorios/arkitect-francesca-miranda", {
        "captureContent": True
    })
  
    # Send a request to the website and let it load
    driver.get("https://www.exito.com/moda-y-accesorios/arkitect-francesca-miranda")
  
    # Sleeps for 10 seconds
    time.sleep(10)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div#gallery-layout-container > div > section > a > article")))
  
    # Write it to a HAR file.
    with open("network_log1.har", "w", encoding="utf-8") as f:
        f.write(json.dumps(proxy.har))
  
    print("Quitting Selenium WebDriver")
    driver.quit()
  
    # Read HAR File and parse it using JSON
    # to find the urls containing images.
    har_file_path = "network_log1.har"
    with open(har_file_path, "r", encoding="utf-8") as f:
        logs = json.loads(f.read())
  
    # Store the network logs from 'entries' key and
    # iterate them
    network_logs = logs['log']['entries']
    for log in network_logs:
  
        # Except block will be accessed if any of the
        # following keys are missing
        try:
            # URL is present inside the following keys
            url = log['request']['url']
  
            # Checks if the extension is .png or .jpg
            if url[len(url)-4:] == '.png' or url[len(url)-4:] == '.jpg':
                print(url, end="\n\n")
        except Exception as e:
            # print(e)
            pass