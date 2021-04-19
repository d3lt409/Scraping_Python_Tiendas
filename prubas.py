
nombre = 'Strong Kirchheimer '
newNombre = nombre.split()
print(newNombre[0][0].upper())
if (newNombre[1] in nombre and nombre.startswith(newNombre[0][0].upper())):
    print("He verad")