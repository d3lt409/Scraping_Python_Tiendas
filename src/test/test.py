from requests import get
resp = get("https://www.exito.com/mercado/lacteos-huevos-y-refrigerados/arepas-y-tortillas?fuzzy=0&initialMap=c,c&initialQuery=mercado/lacteos-huevos-y-refrigerados&map=category-1,category-2,category-3&operator=and")
print(resp.headers)