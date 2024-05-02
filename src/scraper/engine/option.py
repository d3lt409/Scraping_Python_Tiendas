from selenium.webdriver.chrome.options import Options as options_chrome
from selenium.webdriver.firefox.options import Options as options_firefox


class Option:

    def __init__(self, browser, wire=False, headless=False):
        self._wire = wire
        self._headless = headless
        self._option = self.create_options(browser)

    def _get_option(self):
        return self._option

    def _get_headless(self):
        return self._headless

    option = property(fget=_get_option)
    headless = property(fget=_get_headless)

    def create_options(self, browser):
        if browser == "chrome":
            options = options_chrome()
            if self.headless:
                options.add_argument('--headless')
            options.page_load_strategy = 'none'
            options.add_argument('--no-sandbox')
            options.add_argument("--enable-automation")
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument("--disable-proxy-certificate-handler")
            options.add_argument("--disable-content-security-policy")
            options.add_argument("--dns-prefetch-disable")
            options.add_argument('--disable-gpu')
            options.add_argument("--log-level=3")
            options.add_argument("--disable-infobars")
            options.add_argument("--disable-extensions")
            options.add_argument("--ignore-certificate-errors")
            # chrome_options.add_argument("--allow-running-insecure-content")
            # chrome_options.add_argument("--disable-web-security")
            options.add_argument("force-device-scale-factor=0.75")
            options.add_argument("high-dpi-support=0.75")
            options.set_capability(
                'goog:loggingPrefs', {'performance': 'ALL'})
            options.experimental_options["prefs"] = {
                "profile.managed_default_content_settings.images": 2,
                "stylesheet": 2
            }
        else:
            options = options_firefox()
            if self.headless:
                options.add_argument('--headless')
            options.page_load_strategy = 'none'
            options.add_argument('--no-sandbox')
            options.add_argument("--enable-automation")
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument("--dns-prefetch-disable")
            options.add_argument('--disable-gpu')
            options.add_argument("--log-level=3")
            options.add_argument("--disable-infobars")
            options.add_argument("--disable-extensions")
            options.add_argument("--ignore-certificate-errors")
            options.set_preference("log.level", "Trace")
            options.set_preference(
                "profile.managed_default_content_settings.images", 2)
            options.set_preference("stylesheet", 2)

        return options

    def create_wire_options(self):
        if self._wire:
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
            return seleniumwire_options
        else:
            return {}
