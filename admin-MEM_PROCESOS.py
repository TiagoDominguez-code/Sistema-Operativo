from tabulate import tabulate
import csv
import math


def inicializar_particiones():
    particion_1 = {"PID": 0, "Proceso": " ", "tamaño": 250, "mem": 0, "FI": 0, "TR": 0, "disp": "si"}
    particion_2 = {"PID": 0, "Proceso": " ", "tamaño": 150, "mem": 0, "FI": 0, "TR": 0, "disp": "si"}
    particion_3 = {"PID": 0, "Proceso": " ", "tamaño": 50, "mem": 0, "FI": 0, "TR": 0, "disp": "si"}
    particion_SO = {"PID": 0, "Proceso": "SO","tamaño": 100,  "mem": 100, "FI": 0, "TR": "--", "disp": "NO"}

    particiones_inicial= [particion_1, particion_2, particion_3, particion_SO]

    return particiones_inicial


def asignacion_best_fit(proceso, particiones):
    global Procesos_residentes, listos, listos_y_suspendidos

    mejor_particion = -1
    FI_min = math.inf 

    try:
        mem_proceso = int(proceso["mem"])
        ti_proceso = int(proceso.get("TI", 0))
    except ValueError:
        print(f"Error: El proceso {proceso['Proceso']} tiene un valor de 'mem' no numérico.")
        return
    except KeyError:
        print(f"Error: El proceso {proceso['Proceso']} no tiene 'mem' o 'TI' en el CSV.")
        return
    
    for i in range(len(particiones)): #i es el indice de cada particion
        
        particion = particiones[i] 

        if particion["disp"] == "si":
            if particion["tamaño"] >= mem_proceso:
                FI = particion["tamaño"] - mem_proceso
                if FI < FI_min :
                    FI_min = FI
                    mejor_particion = i
    if mejor_particion != -1:
        p = particiones[mejor_particion]

        p["PID"] = proceso["PID"]
        p["Proceso"] = proceso["Proceso"]
        p["mem"] = proceso["mem"]
        p["FI"] = FI_min
        p["disp"] = "NO"

    else:
        proceso["estado"] = "listo y suspendido"
        listos_y_suspendidos.append(proceso)
        listos_y_suspendidos.sort(key=lambda x: int(x["TI"]))

    Procesos_residentes = Procesos_residentes + 1 
    



#=======PROCESO=======================================================================================================================
particiones = inicializar_particiones()
print(tabulate(particiones, headers="keys", tablefmt="heavy_grid"))
T_global = 0

Procesos_entrantes = [] #Matriz con todos los procesos
listos_y_suspendidos = [0] #cola de listos


#===============================================================================================================================

#===============================================================================================================================
try:
    with open("Procesos.csv", "r", encoding="utf-8") as archivo_csv:
        reader = csv.DictReader(archivo_csv) # se usa DictReader para que cada fila sea un diccionario
    
        Procesos_entrantes = list(reader) #Matriz con todos los procesos
except FileNotFoundError:
    print ("no se encontro el archivo")
#===============================================================================================================================

#=============================CICLO PRINCIPAL===================================================================================
for i in range(len(Procesos_entrantes)):
    print("vefificando archivo .csv")
if (i<11):
    if Procesos_entrantes or listos:
        Procesos_residentes = range(len(listos))
        if Procesos_residentes < 5:
            for proc in Procesos_entrantes:
                asignacion_best_fit(proc, particiones)



        print("\n--- ESTADO FINAL DE LA MEMORIA ---")
        print(tabulate(particiones, headers="keys", tablefmt="heavy_grid"))
    else:
        print("Archivo 'Procesos.csv' está vacío. No hay nada que asignar")
else:
    print("El archivo .csv tiene más de 10 procesos")