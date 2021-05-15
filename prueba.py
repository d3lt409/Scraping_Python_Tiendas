from os import PRIO_PGRP
import re
from time import process_time

lista = [2,3,4,5,6,3]
val = int(len(lista)/2)
print(val)
lista = lista[:val]
print(lista)