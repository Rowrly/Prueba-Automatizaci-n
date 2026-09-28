import csv
import json
import os
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
from urllib.request import urlopen


BASE_URL = "https://west.albion-online-data.com/api/v2/stats/history"

CIUDADES = [
    "Bridgewatch",
    "Fort Sterling",
    "Lymhurst",
    "Martlock",
    "Thetford"
]

ITEMS = [
    # T2
    "T2_ORE",

    # T3
    "T3_ORE",

    # T4
    "T4_ORE",
    "T4_ORE_LEVEL1@1",
    "T4_ORE_LEVEL2@2",
    "T4_ORE_LEVEL3@3",
    "T4_ORE_LEVEL4@4",

    # T5
    "T5_ORE",
    "T5_ORE_LEVEL1@1",
    "T5_ORE_LEVEL2@2",
    "T5_ORE_LEVEL3@3",
    "T5_ORE_LEVEL4@4",

    # T6
    "T6_ORE",
    "T6_ORE_LEVEL1@1",
    "T6_ORE_LEVEL2@2",
    "T6_ORE_LEVEL3@3",
    "T6_ORE_LEVEL4@4",

    # T7
    "T7_ORE",
    "T7_ORE_LEVEL1@1",
    "T7_ORE_LEVEL2@2",
    "T7_ORE_LEVEL3@3",
    "T7_ORE_LEVEL4@4",

    # T8
    "T8_ORE",
    "T8_ORE_LEVEL1@1",
    "T8_ORE_LEVEL2@2",
    "T8_ORE_LEVEL3@3",
    "T8_ORE_LEVEL4@4"
]

ARCHIVO = "minerales_historico.csv"


def obtener_datos(url):
    print(f"Consultando API...")
    with urlopen(url, timeout=60) as respuesta:
        return json.loads(respuesta.read().decode("utf-8"))


def construir_url(items, fecha_inicio=None, fecha_fin=None):
    items_url = ",".join(quote(item, safe="@") for item in items)

    ciudades_url = ",".join(
        quote(ciudad, safe="") for ciudad in CIUDADES
    )

    url = (
        f"{BASE_URL}/{items_url}.json"
        f"?locations={ciudades_url}"
        f"&qualities=1"
        f"&time-scale=24"
    )

    if fecha_inicio:
        url += f"&date={fecha_inicio}"

    if fecha_fin:
        url += f"&end_date={fecha_fin}"

    return url


def convertir_respuesta(datos):
    filas = []

    for bloque in datos:

        item_id = bloque.get("item_id")
        ciudad = bloque.get("location")
        calidad = bloque.get("quality")

        for registro in bloque.get("data", []):

            filas.append({
                "Fecha": registro.get("timestamp"),
                "Ciudad": ciudad,
                "ItemID": item_id,
                "Calidad": calidad,
                "Cantidad": registro.get("item_count"),
                "PrecioPromedio": registro.get("avg_price")
            })

    return filas


def cargar_historico():
    if not os.path.exists(ARCHIVO):
        return []

    with open(ARCHIVO, "r", encoding="utf-8", newline="") as archivo:
        lector = csv.DictReader(archivo)
        return list(lector)


def guardar_historico(filas):
    columnas = [
        "Fecha",
        "Ciudad",
        "ItemID",
        "Calidad",
        "Cantidad",
        "PrecioPromedio"
    ]

    with open(
        ARCHIVO,
        "w",
        encoding="utf-8",
        newline=""
    ) as archivo:

        escritor = csv.DictWriter(
            archivo,
            fieldnames=columnas
        )

        escritor.writeheader()
        escritor.writerows(filas)


def clave_fila(fila):
    return (
        fila["Fecha"],
        fila["Ciudad"],
        fila["ItemID"],
        str(fila["Calidad"])
    )


def main():

    historico = cargar_historico()

    # Primera ejecución:
    # descargamos todo el histórico disponible.
    if not historico:

        print("No existe histórico.")
        print("Descargando histórico inicial completo...")

        url = construir_url(ITEMS)

        datos = obtener_datos(url)

        nuevas_filas = convertir_respuesta(datos)

        print(f"Registros recibidos: {len(nuevas_filas)}")

        guardar_historico(nuevas_filas)

        print(f"Archivo creado: {ARCHIVO}")

        return

    # Ejecuciones siguientes:
    # descargamos los últimos 2 días.
    ahora = datetime.now(timezone.utc)
    fecha_fin = ahora.date()
    fecha_inicio = fecha_fin - timedelta(days=1)

    print(
        f"Actualizando datos desde "
        f"{fecha_inicio} hasta {fecha_fin}..."
    )

    url = construir_url(
        ITEMS,
        fecha_inicio.strftime("%Y-%m-%d"),
        fecha_fin.strftime("%Y-%m-%d")
    )

    datos = obtener_datos(url)

    nuevas_filas = convertir_respuesta(datos)

    print(f"Registros nuevos recibidos: {len(nuevas_filas)}")

    # Convertimos el histórico en diccionario.
    # Si ya existe una fila con la misma clave,
    # la nueva versión reemplaza a la anterior.
    historico_dict = {
        clave_fila(fila): fila
        for fila in historico
    }

    for fila in nuevas_filas:
        historico_dict[clave_fila(fila)] = fila

    resultado = list(historico_dict.values())

    # Orden cronológico
    resultado.sort(
        key=lambda fila: (
            fila["Fecha"],
            fila["Ciudad"],
            fila["ItemID"]
        )
    )

    guardar_historico(resultado)

    print(f"Total histórico: {len(resultado)}")
    print(f"Archivo actualizado: {ARCHIVO}")


if __name__ == "__main__":
    main()
