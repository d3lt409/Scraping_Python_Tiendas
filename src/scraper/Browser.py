# from seleniumwire import webdriver
from selenium import webdriver

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options


class Browser:

    def __init__(self, headless=False):
        options = self.get_options(headless)
        options.headless = True
        self.driver = webdriver.Chrome(
            ChromeDriverManager().install(),
            options=options
        )

    def get_options(self, headless: bool):
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        # Opciones del navegador Chrome
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
        #
        chrome_options.add_argument("force-device-scale-factor=0.75")
        chrome_options.add_argument("high-dpi-support=0.75")
        # chrome_options.add_argument("--remote-debugging-port=9230")
        chrome_options.set_capability(
            'goog:loggingPrefs', {'performance': 'ALL'})
        chrome_options.add_experimental_option("prefs", {
            "profile.managed_default_content_settings.images": 2,
            "stylesheet": 2
        })

        return chrome_options

    def quit(self):
        self.driver.quit()
