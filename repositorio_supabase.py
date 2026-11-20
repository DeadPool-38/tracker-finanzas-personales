from datetime import date
from typing import Iterable

from supabase import Client

from transaccion import Transaccion


class RepositorioSupabase:
    def __init__(self, cliente: Client):
        self.cliente = cliente

    def cargar_transacciones(self, user_id: str) -> list[Transaccion]:
        respuesta = (
            self.cliente.table("transacciones")
            .select("id,descripcion,monto,fecha,categoria,tipo")
            .eq("user_id", user_id)
            .order("fecha")
            .execute()
        )
        return [
            Transaccion(
                descripcion=fila["descripcion"],
                monto=float(fila["monto"]),
                fecha=date.fromisoformat(fila["fecha"]),
                categoria=fila["categoria"],
                tipo=fila["tipo"],
                id=fila["id"],
            )
            for fila in respuesta.data
        ]

    def agregar_transacciones(
        self, user_id: str, transacciones: Iterable[Transaccion]
    ):
        transacciones = list(transacciones)
        filas = [
            {
                "user_id": user_id,
                "descripcion": transaccion.descripcion,
                "monto": transaccion.monto,
                "fecha": transaccion.fecha.isoformat(),
                "categoria": transaccion.categoria,
                "tipo": transaccion.tipo,
            }
            for transaccion in transacciones
        ]
        if filas:
            respuesta = (
                self.cliente.table("transacciones")
                .insert(filas)
                .select("id")
                .execute()
            )
            if len(respuesta.data) != len(transacciones):
                raise RuntimeError(
                    "Supabase no devolvió los identificadores de las transacciones."
                )
            for transaccion, fila in zip(transacciones, respuesta.data):
                transaccion.id = fila["id"]

    def borrar_transaccion(self, user_id: str, transaccion_id: int):
        (
            self.cliente.table("transacciones")
            .delete()
            .eq("user_id", user_id)
            .eq("id", transaccion_id)
            .execute()
        )

    def borrar_transacciones(self, user_id: str):
        (
            self.cliente.table("transacciones")
            .delete()
            .eq("user_id", user_id)
            .execute()
        )
