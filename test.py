
from copy import deepcopy
import json

base = {"Exito": {"Supermercado": {"Mercado": ["Frutas", "Carnes"],"Cocina": ["Olla", "Sarten"]},
                  "Eletro": {"Labadoras": ["algo", "diferente"]},
                  "Celular": {"Samsum": ["x1", "x2"]}}}
base_copy = deepcopy(base)
for dep in base_copy["Exito"].keys():
  cats = base_copy["Exito"][dep]
  for cat in base_copy["Exito"][dep].keys():
    subs = base_copy["Exito"][dep][cat]
    while len(subs) > 0:
      el = subs.pop(0)
    print(base_copy)
    del base["Exito"][dep][cat]
    print(base)
  del base["Exito"][dep]
print(base)