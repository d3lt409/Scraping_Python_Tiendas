
USER = 'diegofernandozamoradiaz@gmail.com'
PASSWORD = 'Juchipuchi123.'

N1 = "Nombre 1"
N2 = "Nombre 2"
P1 = "Puntaje 1"
P2 = "Puntaje 2"
PR1 = "Precio 1"
PR2 = "Precio 2"

NAMEFILE = {
    2:"wplay.xlsx",
    1:'codere.xlsx'
    }

SHEETNAMES = {1:"Basketball",2:"Football",3:"Tennis",4:"Table"}

COLUMNAS = {
    "no_empate":[N1,P1,PR1,N2,P2,PR2,"Grupo","Fecha de juego","Tiempo de juego","Periodo","Finalizado"],
    "empate":[N1,P1,PR1,N2,P2,PR2,"Empate","Grupo","Fecha de juego","Tiempo de juego","Periodo","Finalizado"]
    }
    
SUBSET = [N1,N2,"Grupo"]
TIPO = {1:("10:00",10,4),2:("90:00",90,2),3:("120:00",120,0),4:("120:00",120,0)}

