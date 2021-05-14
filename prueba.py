import re

valor = re.search("( (X|DE) (\d)+ (G|ML|M|CM|UN)(.*))|( (DE|X) \d+ X \d+ (G|ML|M|CM|UN)(.*))|(\(\d+ (G|ML|M|CM|UN)\))","MANGUERA ESPIRAL DE 10 M.")
if (valor):
    print(valor.group(0).strip())