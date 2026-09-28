import csv
import json
import os
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
from urllib.request import urlopen
from urllib.error import HTTPError


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

    try:

        with urlopen(url, timeout=120) as respuesta:

            contenido = respuesta.read().decode("utf-8")

            return json.loads(contenido)

    except HTTPError as error:

        print(
            f"ERROR HTTP {error.code}: {error.reason}"
        )

        raise


def construir_url():

    items = ",".join(ITEMS)

    ciudades = ",".join(CIUDADES)

    return (
        f"{BASE_URL}/"
        f"{quote(items, safe='@,')}.json"
        f"?locations={quote(ciudades, safe=',')}"
        f"&qualities=1"
        f"&time-scale=24"
    )


def convertir_respuesta(datos, fecha_descarga):

    filas = []

    # -------------------------------------------------
    # ESTRUCTURA HISTÓRICA AGRUPADA
    #
    # [
    #   {
    #       "location": "...",
    #       "item_id": "...",
    #       "quality": 1,
    #       "data": [
    #           {
    #               "timestamp": "...",
    #               "item_count": ...,
    #               "avg_price": ...
    #           }
    #       ]
    #   }
    # ]
    # -------------------------------------------------

    for registro in datos:

        ciudad = registro.get("location")
        item_id = registro.get("item_id")
        calidad = registro.get("quality")

        data = registro.get("data")

        if isinstance(data, list):

            for punto in data:

                timestamp = punto.get("timestamp")

                cantidad = punto.get("item_count")
                precio = punto.get("avg_price")

                if timestamp is None:
                    continue

                if ciudad is None:
                    continue

                if item_id is None:
                    continue

                if calidad is None:
                    continue

                filas.append({
                    "Fecha": timestamp,
                    "FechaDescarga": fecha_descarga,
                    "Ciudad": ciudad,
                    "ItemID": item_id,
                    "Calidad": calidad,
                    "Cantidad": cantidad,
                    "PrecioPromedio": precio
                })

        # -------------------------------------------------
        # ESTRUCTURA PLANA
        #
        # Se mantiene por seguridad, por si la API devuelve
        # registros directamente.
        # -------------------------------------------------

        else:

            timestamp = registro.get("timestamp")

            if timestamp is None:
                continue

            ciudad = registro.get("location")
            item_id = registro.get("item_id")
            calidad = registro.get("quality")

            if ciudad is None:
                continue

            if item_id is None:
                continue

            if calidad is None:
                continue

            filas.append({
                "Fecha": timestamp,
                "FechaDescarga": fecha_descarga,
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
        fila.get("Fecha"),
        fila.get("Ciudad"),
        fila.get("ItemID"),
        str(fila.get("Calidad"))
    )


def main():

    fecha_descarga = (
        datetime.now(timezone.utc)
        - timedelta(hours=5)
    ).strftime("%Y-%m-%d %H:%M:%S")


    print("========================================")
    print("ACTUALIZANDO HISTÓRICO DE PIEL")
    print("========================================")

    print(
        f"Ciudades: {len(CIUDADES)}"
    )

    print(
        f"Ítems: {len(ITEMS)}"
    )

    print(
        f"Combinaciones: "
        f"{len(CIUDADES) * len(ITEMS)}"
    )

    print("")
    print("Consultando API en una sola solicitud...")
    print("")


    # -----------------------------------------------
    # UNA SOLA PETICIÓN PARA TODOS LOS ÍTEMS
    # Y TODAS LAS CIUDADES
    # -----------------------------------------------

    url = construir_url()

    print(
        f"Longitud de URL: {len(url)} caracteres"
    )

    if len(url) > 4096:

        raise Exception(
            "La URL supera el límite de 4096 caracteres."
        )


    try:

        datos = obtener_datos(url)

    except Exception as error:

        print("")
        print("ERROR AL CONSULTAR LA API:")
        print(error)

        raise


    print("API consultada correctamente.")


    nuevas_filas = convertir_respuesta(
        datos,
        fecha_descarga
    )


    print(
        f"Registros nuevos obtenidos: "
        f"{len(nuevas_filas)}"
    )


    # -----------------------------------------------
    # CARGAR HISTÓRICO EXISTENTE
    # -----------------------------------------------

    historico = cargar_historico()

    print(
        f"Registros existentes: "
        f"{len(historico)}"
    )


    # -----------------------------------------------
    # COMBINAR
    # -----------------------------------------------

    combinadas = historico + nuevas_filas

    diccionario = {}


    for fila in combinadas:

        fecha = fila.get("Fecha")

        if fecha is None or fecha == "":

            continue

        diccionario[clave_fila(fila)] = fila


    resultado = list(
        diccionario.values()
    )


    # -----------------------------------------------
    # ORDENAR
    # -----------------------------------------------

    resultado.sort(
        key=lambda fila: (
            fila.get("Fecha") or "",
            fila.get("Ciudad") or "",
            fila.get("ItemID") or "",
            str(fila.get("Calidad") or "")
        )
    )


    # -----------------------------------------------
    # GUARDAR
    # -----------------------------------------------

    guardar_historico(resultado)


    print("")
    print("========================================")
    print("HISTÓRICO DE PIEL ACTUALIZADO")
    print("========================================")

    print(
        f"Filas totales: {len(resultado)}"
    )

    print(
        f"Fecha de descarga: {fecha_descarga}"
    )


if __name__ == "__main__":

    main()
