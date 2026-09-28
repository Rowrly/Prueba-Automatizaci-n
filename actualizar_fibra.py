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
    "T2_FIBER",
    "T3_FIBER",
    "T4_FIBER",
    "T4_FIBER_LEVEL1@1",
    "T4_FIBER_LEVEL2@2",
    "T4_FIBER_LEVEL3@3",
    "T4_FIBER_LEVEL4@4",
    "T5_FIBER",
    "T5_FIBER_LEVEL1@1",
    "T5_FIBER_LEVEL2@2",
    "T5_FIBER_LEVEL3@3",
    "T5_FIBER_LEVEL4@4",
    "T6_FIBER",
    "T6_FIBER_LEVEL1@1",
    "T6_FIBER_LEVEL2@2",
    "T6_FIBER_LEVEL3@3",
    "T6_FIBER_LEVEL4@4",
    "T7_FIBER",
    "T7_FIBER_LEVEL1@1",
    "T7_FIBER_LEVEL2@2",
    "T7_FIBER_LEVEL3@3",
    "T7_FIBER_LEVEL4@4",
    "T8_FIBER",
    "T8_FIBER_LEVEL1@1",
    "T8_FIBER_LEVEL2@2",
    "T8_FIBER_LEVEL3@3",
    "T8_FIBER_LEVEL4@4"
]

ARCHIVO = "fibra_historico.csv"


def obtener_datos(url):
    print("Consultando API...")

    with urlopen(url, timeout=60) as respuesta:
        return json.loads(
            respuesta.read().decode("utf-8")
        )


def construir_url(items, fecha_inicio=None, fecha_fin=None):

    items_url = ",".join(
        quote(item, safe="@")
        for item in items
    )

    ciudades_url = ",".join(
        quote(ciudad, safe="")
        for ciudad in CIUDADES
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
                "FechaDescarga": "",
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

    with open(
        ARCHIVO,
        "r",
        encoding="utf-8",
        newline=""
    ) as archivo:

        lector = csv.DictReader(archivo)

        return list(lector)


def guardar_historico(filas):

    columnas = [
        "Fecha",
        "FechaDescarga",
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

    fecha_descarga = (
        datetime.now(timezone.utc)
        - timedelta(hours=5)
    ).strftime("%Y-%m-%d %H:%M:%S")

    print(
        f"Fecha de descarga de esta ejecución: "
        f"{fecha_descarga}"
    )

    historico = cargar_historico()

    if not historico:

        print("No existe histórico.")
        print("Descargando histórico inicial completo...")

        url = construir_url(ITEMS)

        datos = obtener_datos(url)

        nuevas_filas = convertir_respuesta(datos)

        print(
            f"Registros recibidos: "
            f"{len(nuevas_filas)}"
        )

        resultado = nuevas_filas

    else:

        ahora = datetime.now(timezone.utc)

        fecha_fin = ahora.date()

        fecha_inicio = (
            fecha_fin - timedelta(days=1)
        )

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

        print(
            f"Registros nuevos recibidos: "
            f"{len(nuevas_filas)}"
        )

        historico_dict = {
            clave_fila(fila): fila
            for fila in historico
        }

        for fila in nuevas_filas:

            historico_dict[
                clave_fila(fila)
            ] = fila

        resultado = list(
            historico_dict.values()
        )

    resultado.sort(
        key=lambda fila: (
            fila["Fecha"],
            fila["Ciudad"],
            fila["ItemID"]
        )
    )

    for fila in resultado:

        fila["FechaDescarga"] = fecha_descarga

    guardar_historico(resultado)

    print(
        f"Total histórico: "
        f"{len(resultado)}"
    )

    print(
        f"Archivo actualizado: "
        f"{ARCHIVO}"
    )

    print(
        f"FechaDescarga aplicada a todas las filas: "
        f"{fecha_descarga}"
    )


if __name__ == "__main__":
    main()
