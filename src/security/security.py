import keyring

EMAIL = "manuelfer1996@gmail.com"
PASSWORD:str = keyring.get_password("scraping",EMAIL)
