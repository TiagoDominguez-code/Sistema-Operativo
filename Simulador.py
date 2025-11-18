import csv
from tabulate import tabulate

class Proceso:
    def __init__(self, id, Proceso, tam, arribo, irrupcion):
        self.id = int(id)
        self.Proceso = Proceso
        self.tam = int(tam)
        self.arribo = int(arribo)
        self.irrupcion = int(irrupcion)
        self.restante = int(irrupcion)
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

# Cargar CSV
try:
    with open("Procesos.csv", "r", encoding="utf-8") as archivo_csv:
        reader = csv.DictReader(archivo_csv)
        Procesos_nuevos = list(reader)
except FileNotFoundError:
    print("no se encontro el archivo")
    Procesos_nuevos = []

# Convertir a objetos
procesos = []
for fila in Procesos_nuevos:
    proceso = Proceso(
        id=fila["id"],
        Proceso=fila["Proceso"],
        tam=int(fila["tam"]),
        arribo=int(fila["arribo"]),
        irrupcion=int(fila["irrupcion"])
    )
    procesos.append(proceso)

# Parámetros del sistema
multiprogramacion_max = 5  # activos = en memoria (Listo) + suspendidos
max_en_memoria = 3         # por particiones de usuario
cola_prioridad = []        # Listo + Listo-Suspendido (visualización y orden por restante)

def asignacion_best_fit(proceso, particiones):
    mejor_particion = None
    FI_min = float("inf")
    for particion in particiones:
        if particion.id == 0:
            continue  # saltar partición del SO
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
        proceso.en_memoria = False
        proceso.particion = None
        return False

def liberar_particion(proceso, particiones):
    if proceso.particion is not None:
        for particion in particiones:
            if particion.id == proceso.particion:
                particion.libre = True
                particion.proceso = None
                particion.frag = 0
                break
    proceso.en_memoria = False
    proceso.particion = None

def activos(procesos):
    en_memoria = [p for p in procesos if p.estado == "Listo" and p.en_memoria]
    suspendidos = [p for p in procesos if p.estado == "Listo-Suspendido" and not p.en_memoria]
    return en_memoria, suspendidos

def admitir_nuevos(procesos, tiempo_actual):
    # Admitir procesos que arriban en este tick
    llegados = [p for p in procesos if p.arribo <= tiempo_actual and p.estado == "Nuevo"]
    for p in llegados:
        en_memoria, suspendidos = activos(procesos)
        activos_count = len(en_memoria) + len(suspendidos)
        if activos_count >= multiprogramacion_max:
            continue  # límite alcanzado, permanece en Nuevo

        # Si hay lugar en memoria (< 3), intentar best-fit
        if len(en_memoria) < max_en_memoria:
            asignacion_best_fit(p, particiones)
        else: 
            # Memoria llena, pasa a suspendidos
            p.estado = "Listo-Suspendido"
            p.en_memoria = False
            p.particion = None

def actualizar_cola_prioridad(procesos):
    cola_prioridad.clear()
    for p in procesos:
        if p.estado in ["Listo", "Listo-Suspendido"]:
            cola_prioridad.append(p)
    cola_prioridad.sort(key=lambda x: x.restante)

def swap_in_out(procesos, proceso_en_ejecucion=None):
    actualizar_cola_prioridad(procesos)
    if not cola_prioridad:
        return None

    candidato = cola_prioridad[0]

    # Si ya está en memoria, se ejecuta directamente
    if candidato.estado == "Listo" and candidato.en_memoria:
        return candidato

    if candidato.estado == "Listo-Suspendido":
        en_memoria, _ = activos(procesos)

        # Hay lugar en memoria libre
        if len(en_memoria) < max_en_memoria:
            if asignacion_best_fit(candidato, particiones):
                return candidato

        # Si no hay lugar, intentar swap out
        en_memoria, _ = activos(procesos)

        if en_memoria:
            # Elegir el proceso más largo que además tenga partición suficiente
            proceso_out = None
            for p in sorted(en_memoria, key=lambda x: x.restante, reverse=True):
                # Buscar la partición que ocupa
                for part in particiones:
                    if part.id == p.particion and part.tam >= candidato.tam:
                        proceso_out = p
                        break
                if proceso_out:
                    break

            if proceso_out:
                liberar_particion(proceso_out, particiones)
                proceso_out.estado = "Listo-Suspendido"
                proceso_out.en_memoria = False

                if asignacion_best_fit(candidato, particiones):
                    return candidato
    return None


def traer_suspendidos_si_cabe(procesos):
    # Al liberar partición, priorizar suspendidos que quepan (por restante)
    _, suspendidos = activos(procesos)
    if not suspendidos:
        return
    suspendidos_ordenados = sorted(suspendidos, key=lambda p: p.restante)
    for s in suspendidos_ordenados:
        if asignacion_best_fit(s, particiones):
            break  # traer uno por vez

def imprimir_evento(tiempo_actual, procesos, particiones, titulo, proceso_en_ejecucion=None):
    print(f"\n=== Tiempo {tiempo_actual} ===")

    # Tabla general de procesos
    tabla = []
    for p in procesos:
        tabla.append([p.id, p.Proceso, p.estado, p.tam, p.restante, p.en_memoria, p.particion])
    print(tabulate(tabla, headers=["ID", "Nombre", "Estado", "Tamaño", "Restante", "En Memoria", "Partición"]))

    # Mostrar colas
    en_memoria, suspendidos = activos(procesos)

    print("\n--- Cola de Listos ---")
    if en_memoria:
        for p in en_memoria:
            print(f"ID {p.id} → {p.Proceso}")
    else:
        print("Vacía")

    print("\n--- Cola de Listos-Suspendidos ---")
    if suspendidos:
        for p in suspendidos:
            print(f"ID {p.id} → {p.Proceso}")
    else:
        print("Vacía")

    # Mostrar proceso en ejecución
    print("\n--- Proceso en ejecución ---")
    if proceso_en_ejecucion:
        print(f"ID {proceso_en_ejecucion.id} → {proceso_en_ejecucion.Proceso} "
              f"(Restante={proceso_en_ejecucion.restante}, Partición={proceso_en_ejecucion.particion})")
    else:
        print("Ninguno")

    # Tabla de memoria principal
    tabla_part = []
    for part in particiones:
        tabla_part.append([part.id, part.inicio, part.tam, part.libre, part.proceso, part.frag])
    print("\n--- Estado de Memoria Principal ---")
    print(tabulate(tabla_part, headers=["Partición", "Inicio", "Tamaño", "Libre", "Proceso", "Frag"]))


def todos_finalizados(procesos):
    return all(p.estado == "Finalizado" for p in procesos)

# Modo paso a paso: Enter avanza, 'a' auto, 'q' sale
def esperar_entrada(auto_run):
    if auto_run:
        return True, False
    print("\n[Enter] siguiente | a + Enter automatico | q + Enter salir")
    tecla = input().strip().lower()
    if tecla == "a":
        return True, False
    if tecla == "q":
        return False, True
    return False, False

def simular(procesos, particiones, tiempo_max=1000):
    tiempo_actual = 0
    proceso_en_ejecucion = None
    ultimo_ejecucion_id = None  # para detectar cambios de CPU
    auto_run = False
    salir = False

    while not todos_finalizados(procesos) and tiempo_actual <= tiempo_max and not salir:
        evento_titulo = None

        # Snapshot antes de admitir
        estado_antes = [(p.id, p.estado, p.en_memoria, p.particion) for p in procesos]
        admitir_nuevos(procesos, tiempo_actual)
        estado_despues = [(p.id, p.estado, p.en_memoria, p.particion) for p in procesos]

        # Detectar ingreso a memoria
        for (id0, est0, mem0, part0), (id1, est1, mem1, part1) in zip(estado_antes, estado_despues):
            if id0 == id1 and est0 == "Nuevo" and est1 == "Listo" and mem1 and part1 is not None:
                evento_titulo = f"Ingreso a memoria del proceso {id1}"
                break

        # Elegir proceso a ejecutar
        candidato = swap_in_out(procesos, proceso_en_ejecucion)

        if candidato:
            if candidato.t_inicio is None:
                candidato.t_inicio = tiempo_actual

            # Detectar cambio de CPU
            if ultimo_ejecucion_id != candidato.id:
                evento_titulo = evento_titulo or f"Cambio de CPU: entra {candidato.id}"

            proceso_en_ejecucion = candidato
            ultimo_ejecucion_id = candidato.id
            candidato.restante -= 1

            # Actualizar espera de otros
            for p in procesos:
                if p != candidato and p.estado == "Listo" and p.en_memoria:
                    p.t_espera += 1

            # Finalización
            if candidato.restante == 0:
                candidato.t_fin = tiempo_actual + 1
                candidato.t_retorno = candidato.t_fin - candidato.arribo
                candidato.estado = "Finalizado"
                liberar_particion(candidato, particiones)

                # Traer suspendidos
                traer_suspendidos_si_cabe(procesos)

                # Nuevo candidato en el mismo tick
                nuevo_candidato = swap_in_out(procesos, None)
                proceso_en_ejecucion = nuevo_candidato
                ultimo_ejecucion_id = nuevo_candidato.id if nuevo_candidato else None

                if nuevo_candidato:
                    evento_titulo = evento_titulo or f"Cambio de CPU tras finalización: entra {nuevo_candidato.id}"

                # Detectar intercambio de colas
                estado_swap_despues = [(p.id, p.estado, p.en_memoria, p.particion) for p in procesos]
                for (idA, estA, memA, partA), (idB, estB, memB, partB) in zip(estado_despues, estado_swap_despues):
                    if idA == idB and ((estA == "Listo" and estB == "Listo-Suspendido") or (estA == "Listo-Suspendido" and estB == "Listo")):
                        evento_titulo = f"Intercambio de colas: {idB} {estA}→{estB}"
                        break

        else:
            proceso_en_ejecucion = None
            ultimo_ejecucion_id = None

        # SOLO imprimir y esperar entrada si hubo evento
        if evento_titulo:
            imprimir_evento(tiempo_actual, procesos, particiones, evento_titulo, proceso_en_ejecucion)
            auto_run, salir = esperar_entrada(auto_run)
            if salir:
                break

        # Avanzar tiempo siempre
        tiempo_actual += 1

    # Fin de simulación
    print("\n=== Simulación finalizada ===")
    tabla_fin = []
    total_espera = 0
    total_retorno = 0
    total_cpu = 0
    n = len(procesos)

    for p in procesos:
        tabla_fin.append([p.id, p.Proceso, p.irrupcion, p.t_espera, p.t_retorno, p.t_inicio, p.t_fin, p.estado])
        total_espera += p.t_espera
        total_retorno += p.t_retorno
        total_cpu += p.irrupcion

    print(tabulate(tabla_fin, headers=["ID", "Nombre", "CPU", "Espera", "Retorno", "Inicio", "Fin", "Estado"]))

    # Calcular promedios
    prom_espera = total_espera / n if n > 0 else 0
    prom_retorno = total_retorno / n if n > 0 else 0

    # Rendimiento de CPU
    cpu_utilizacion = (total_cpu / tiempo_actual) * 100 if tiempo_actual > 0 else 0

    print("\n--- Resultados globales ---")
    print(f"Tiempo promedio de espera: {prom_espera:.2f}")
    print(f"Tiempo promedio de retorno: {prom_retorno:.2f}")
    print(f"Rendimiento de la CPU: {cpu_utilizacion:.2f}%")


# Ejecutar simulación
if procesos:
    simular(procesos, particiones, tiempo_max=500)
else:
    print("No hay procesos para simular.")
