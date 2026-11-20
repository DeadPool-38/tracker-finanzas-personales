import unicodedata
from datetime import date

import pandas as pd

from transaccion import Transaccion


class Cartera:
    def __init__(self, transacciones=None):
        self.transacciones = list(transacciones) if transacciones else []

    def agregar_transaccion(self, transaccion):
        self.transacciones.append(transaccion)

    def agregar_transacciones(self, transacciones):
        self.transacciones.extend(transacciones)

    def borrar_transacciones(self):
        self.transacciones.clear()

    def eliminar_transaccion(self, transaccion_id: int) -> bool:
        for indice, transaccion in enumerate(self.transacciones):
            if transaccion.id == transaccion_id:
                del self.transacciones[indice]
                return True
        return False

    @staticmethod
    def parsear_monto(monto):
        monto_limpio = monto.replace("$", "").replace(",", "").strip()
        return float(monto_limpio)

    @staticmethod
    def monto_es_positivo(monto):
        return monto > 0

    def resumen(self):
        ingresos = sum(
            transaccion.monto
            for transaccion in self.transacciones
            if transaccion.es_ingreso()
        )
        gastos = [
            transaccion.monto
            for transaccion in self.transacciones
            if transaccion.es_gasto()
        ]
        total_gastos = sum(gastos)
        return {
            "ingresos": ingresos,
            "gastos": total_gastos,
            "balance": ingresos - total_gastos,
            "gasto_promedio": total_gastos / len(gastos) if gastos else 0,
        }

    def filtrar(self, categorias, fecha_desde, fecha_hasta):
        return Cartera(
            transaccion
            for transaccion in self.transacciones
            if transaccion.categoria in categorias
            and fecha_desde <= transaccion.fecha <= fecha_hasta
        )

    def rango_fechas(self):
        if not self.transacciones:
            hoy = date.today()
            return hoy, hoy
        fechas = [transaccion.fecha for transaccion in self.transacciones]
        return min(fechas), max(fechas)

    def gastos_por_categoria(self):
        gastos = {}
        for transaccion in self.transacciones:
            if transaccion.es_gasto():
                gastos[transaccion.categoria] = (
                    gastos.get(transaccion.categoria, 0) + transaccion.monto
                )
        return gastos

    def gastos_por_fecha(self):
        gastos = {}
        for transaccion in self.transacciones:
            if transaccion.es_gasto():
                gastos[transaccion.fecha] = (
                    gastos.get(transaccion.fecha, 0) + transaccion.monto
                )
        return gastos

    def a_dataframe(self):
        return pd.DataFrame(
            [transaccion.a_diccionario() for transaccion in self.transacciones]
        )

    def a_csv(self):
        return self.a_dataframe().to_csv(index=False)

    def guardar_csv(self, archivo):
        self.a_dataframe().to_csv(archivo, index=False)

    @classmethod
    def cargar_csv(cls, archivo):
        try:
            df = pd.read_csv(archivo)
            transacciones = [
                Transaccion(
                    descripcion=fila["descripcion"],
                    monto=float(fila["monto"]),
                    fecha=date.fromisoformat(str(fila["fecha"])),
                    categoria=fila["categoria"],
                    tipo=fila["tipo"],
                )
                for _, fila in df.iterrows()
            ]
            return cls(transacciones)
        except (
            OSError,
            pd.errors.ParserError,
            UnicodeDecodeError,
            ValueError,
            KeyError,
            TypeError,
        ):
            return cls()

    @staticmethod
    def _normalizar_columna(columna):
        return "".join(
            caracter
            for caracter in unicodedata.normalize("NFKD", str(columna))
            if not unicodedata.combining(caracter)
        ).casefold()

    def importar_dataframe(self, df):
        columnas_esperadas = ["descripción", "monto", "fecha", "categoria", "tipo"]
        columnas_csv = {
            self._normalizar_columna(columna): columna for columna in df.columns
        }
        columnas_faltantes = [
            columna
            for columna in columnas_esperadas
            if self._normalizar_columna(columna) not in columnas_csv
        ]
        if columnas_faltantes:
            raise KeyError("Faltan columnas esperadas.")

        try:
            transacciones = [
                Transaccion(
                    descripcion=fila[
                        columnas_csv[self._normalizar_columna("descripción")]
                    ],
                    monto=float(fila[columnas_csv[self._normalizar_columna("monto")]]),
                    fecha=date.fromisoformat(
                        str(fila[columnas_csv[self._normalizar_columna("fecha")]])
                    ),
                    categoria=fila[
                        columnas_csv[self._normalizar_columna("categoria")]
                    ],
                    tipo=fila[columnas_csv[self._normalizar_columna("tipo")]],
                )
                for _, fila in df.iterrows()
            ]
        except (TypeError, ValueError):
            raise ValueError("El CSV contiene valores inválidos en monto o fecha.")

        self.agregar_transacciones(transacciones)
        return len(transacciones)
