XPATH_CATEGORY_BUTTON = "//button[@data-fs-menu-container='true']"
XPATH_LIST_CATEGORY_LI = "//section[2]//li[contains(@class,'Link_link-container__C_KEm')]"

XPATH_CATEGORY_CONTAINER = "//li[@class='SubMenu_subsection-item__TD0at']"
#each cat container 
XPATH_NAME_CATEGORY = ".//div//b"
XPATH_SUBCATEGORY_LINKS = ".//ul//a[@class='link_fs-link__6oAwa']"

XPATH_LIST_CATEGORY_LI_VERIFY = "//section[2]//li[contains(@class,'Link_link-container__C_KEm')]"
XPATH_LIST_SUBVCAT_VERIFY = "//p[contains(@id,'Categorías-nivel3-') and text()!='']"

#Elements XPATH
XPATH_LIST_ELEMENTS_VERIFY = "//div[@id='gallery-layout-container']//h3[contains(@class,'-productNameContainer')]/span[text()!='']"
XPATH_LIST_ELEMENTS = "//div[@id='gallery-layout-container']//div[contains(@class,'Content--product-info-element')]"

XPATH_NAME_ELEMENT = ".//h3[contains(@class,'-productNameContainer')]/span[text()!='']/text()"
XPATH_PRICE_ELEMENT = ".//div[contains(@class,'exito-vtex-components-4-x-PricePDP')]/span[text()!='']/text()"

XPATH_FOOTER_PAGE = "//div[contains(@class,'-x-buttonShowMore')]/button[descendant::div[text()!='']]"

XPATH_NOT_FOUND = "//div[@class='exito-search-result-4-x-containerNotFoundExito']"

XPATH_BUTTON_NEXT_ELEMENT = "//div[contains(@class, 'vtex-search-result-3-x-buttonShowMore ')]/button"
XPATH_CLOSE_SPAN = "//span[@class='exito-geolocation-3-x-cursorPointer']"

XPATH_SELECT_LOCATION = "//div[@class='css-yiuvdt']"
XPATH_INPUT_LOCATION = "//div[@class='']/input"
XPATH_BUTTON_CONFIRM = "//button[@class='exito-geolocation-3-x-primaryButtonEnable']"

URL = "https://www.exito.com"
TIME = 20