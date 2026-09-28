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
    "T2_HIDE",
    "T3_HIDE",
    "T4_HIDE",
    "T4_HIDE_LEVEL1@1",
    "T4_HIDE_LEVEL2@2",
    "T4_HIDE_LEVEL3@3",
    "T4_HIDE_LEVEL4@4",
    "T5_HIDE",
    "T5_HIDE_LEVEL1@1",
    "T5_HIDE_LEVEL2@2",
    "T5_HIDE_LEVEL3@3",
    "T5_HIDE_LEVEL4@4",
    "T6_HIDE",
    "T6_HIDE_LEVEL1@1",
    "T6_HIDE_LEVEL2@2",
    "T6_HIDE_LEVEL3@3",
    "T6_HIDE_LEVEL4@4",
    "T7_HIDE",
    "T7_HIDE_LEVEL1@1",
    "T7_HIDE_LEVEL2@2",
    "T7_HIDE_LEVEL3@3",
    "T7_HIDE_LEVEL4@4",
    "T8_HIDE",
    "T8_HIDE_LEVEL1@1",
    "T8_HIDE_LEVEL2@2",
    "T8_HIDE_LEVEL3@3",
    "T8_HIDE_LEVEL4@4"
]

ARCHIVO = "piel_historico.csv"


def obtener_datos(url):
    with urlopen(url, timeout=60) as respuesta:
        return json.loads(
            respuesta.read().decode("utf-8")
        )


def construir_url(item, ciudad):
    return (
        f"{BASE_URL}/"
        f"{quote(item, safe='@')}.json"
        f"?locations={quote(ciudad)}"
        f"&qualities=1"
        f"&time-scale=24"
    )


def convertir_respuesta(datos, fecha_descarga):
    filas = []

    for registro in datos:

        filas.append({
            "Fecha": registro.get("timestamp"),
            "FechaDescarga": fecha_descarga,
            "Ciudad": registro.get("location"),
            "ItemID": registro.get("item_id"),
            "Calidad": registro.get("quality"),
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
        datetime.now(timezone.utc) - timedelta(hours=5)
    ).strftime("%Y-%m-%d %H:%M:%S")

    historico = cargar_historico()

    nuevas_filas = []

    for ciudad in CIUDADES:

        for item in ITEMS:

            url = construir_url(
                item,
                ciudad
            )

            try:

                datos = obtener_datos(url)

                filas = convertir_respuesta(
                    datos,
                    fecha_descarga
                )

                nuevas_filas.extend(filas)

                print(
                    f"OK: {ciudad} - {item} - "
                    f"{len(filas)} registros"
                )

            except Exception as error:

                print(
                    f"ERROR: {ciudad} - {item} - {error}"
                )

    combinadas = historico + nuevas_filas

    diccionario = {}

    for fila in combinadas:
        diccionario[clave_fila(fila)] = fila

    resultado = list(diccionario.values())

    resultado.sort(
        key=lambda fila: (
            fila["Fecha"],
            fila["Ciudad"],
            fila["ItemID"]
        )
    )

    guardar_historico(resultado)

    print(
        f"\nHistórico de piel actualizado."
        f"\nFilas totales: {len(resultado)}"
    )


if __name__ == "__main__":
    main()
