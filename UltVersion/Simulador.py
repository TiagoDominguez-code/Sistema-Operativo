import csv 
from tabulate import tabulate

class Proceso:
    def __init__(self, id, Proceso, tam, arribo, irrupcion):
        self.id = id
        self.Proceso = Proceso
        self.tam = tam
        self.arribo = arribo
        self.irrupcion = irrupcion
        self.restante = irrupcion
        self.estado = "Nuevo"
        self.en_memoria = False
        self.particion = None
        self.t_espera = 0
        self.t_retorno = 0
        self.t_inicio = None
        self.t_fin = None

class Particion:
    def __init__(self, id, inicio, tam, reservado=False):
        self.id = id
        self.inicio = inicio
        self.tam = tam
        self.libre = not reservado
        self.proceso = "SO" if reservado else None
        self.frag = 0

particiones = [
    Particion(0, 0, 100, reservado=True),     # SO
    Particion(1, 100, 250),
    Particion(2, 350, 150),
    Particion(3, 500, 50),
]


#procesos = cargar_procesos("procesos.csv")
try:
    with open("Procesos.csv", "r", encoding="utf-8") as archivo_csv:
        reader = csv.DictReader(archivo_csv) #se usa DictReader para que cada fila sea un diccionario
    
        Procesos_nuevos = list(reader) #Matriz con todos los procesos
except FileNotFoundError:
    print ("no se encontro el archivo")

#Convertir a Objetos
procesos = []
for fila in Procesos_nuevos:
    proceso = Proceso(
    id=fila["id"],
    Proceso=fila["Proceso"],
    tam=int(fila["tam"]),
    arribo=int(fila["arribo"]),
    irrupcion=int(fila["irrupcion"])
)
    #cola con todos los procesos del Archivo.csv
    procesos.append(proceso)

def asignacion_best_fit(proceso, particiones):
    mejor_particion = None
    FI_min = float("inf")

    for particion in particiones:
        if particion.libre and particion.tam >= proceso.tam:
            FI = particion.tam - proceso.tam
            if FI < FI_min:
                FI_min = FI
                mejor_particion = particion

    if mejor_particion:
        mejor_particion.libre = False
        mejor_particion.proceso = proceso.id
        mejor_particion.frag = FI_min

        proceso.en_memoria = True
        proceso.particion = mejor_particion.id
        proceso.estado = "Listo"
        return True
    else:
        proceso.estado = "Listo-Suspendido"
        return False
    
cola_prioridad = []  # Cola única para Listo y Listo-Suspendido
multiprogramacion = 5

for proceso in procesos:
    if proceso.arribo == 0 and proceso.estado == "Nuevo":
        # Contar procesos activos en memoria
        activos_en_memoria = [p for p in procesos if p.en_memoria]
        suspendidos_actuales = [p for p in procesos if p.estado == "Listo-Suspendido"]

        if len(activos_en_memoria) + len(suspendidos_actuales) <= multiprogramacion:
            asignacion_best_fit(proceso, particiones)
        else:
            proceso.estado = "Nuevo"


        # Agregar a la cola si está en Listo o Listo-Suspendido
        if proceso.estado in ["Listo", "Listo-Suspendido"]:
            cola_prioridad.append(proceso)

# Ordenar la cola por tiempo restante
cola_prioridad.sort(key=lambda p: p.restante)



tabla = []
for p in cola_prioridad:
    tabla.append([p.id, p.Proceso, p.estado, p.tam, p.restante, p.en_memoria, p.particion])

print(tabulate(tabla, headers=["ID", "Nombre", "Estado", "Tamaño", "Restante", "En Memoria", "Partición"]))

