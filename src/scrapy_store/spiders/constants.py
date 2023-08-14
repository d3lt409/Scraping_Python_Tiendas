
XPATH_CATEGORY_BUTTON = "//*[@id='category-menu']"
XPATH_LIST_CATEGORY_LI = "//div[@class='exito-category-menu-3-x-categoryList']//ul[@class='exito-category-menu-3-x-categoryListD']/li"
XPATH_CATEGORY_CONTAINER = "//div[@class='exito-category-menu-3-x-itemSideMenu']"
#each cat container
XPATH_NAME_CATEGORY = "//*[contains(@id,'Categorías-nivel2-')]/strong"

XPATH_LIST_CATEGORY_LI_VERIFY = "//div[@class='exito-category-menu-3-x-categoryList']//ul[@class='exito-category-menu-3-x-categoryListD']/li/div/p[text()!='']"
XPATH_LIST_SUBVCAT_VERIFY = "//p[contains(@id,'Categorías-nivel3-') and text()!='']"

#Elements XPATH
XPATH_LIST_ELEMENTS_VERIFY = "//div[@id='gallery-layout-container']//h3[contains(@class,'-productNameContainer')]/span[text()!='']"
XPATH_LIST_ELEMENTS = "//div[@id='gallery-layout-container']//div[contains(@class,'Content--product-info-element')]"

XPATH_NAME_ELEMENT = ".//h3[contains(@class,'-productNameContainer')]/span[text()!='']/text()"
XPATH_PRICE_ELEMENT = ".//div[contains(@class,'exito-vtex-components-4-x-PricePDP')]/span[text()!='']/text()"

XPATH_FOOTER_PAGE = "//div[contains(@class,'-x-buttonShowMore')]/button[descendant::div[text()!='']]"

XPATH_NOT_FOUND = "//div[@class='exito-search-result-4-x-containerNotFoundExito']"