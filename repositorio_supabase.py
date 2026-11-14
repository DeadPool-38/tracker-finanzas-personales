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
            .select("descripcion,monto,fecha,categoria,tipo")
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
            )
            for fila in respuesta.data
        ]

    def agregar_transacciones(
        self, user_id: str, transacciones: Iterable[Transaccion]
    ):
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
            self.cliente.table("transacciones").insert(filas).execute()

    def borrar_transacciones(self, user_id: str):
        (
            self.cliente.table("transacciones")
            .delete()
            .eq("user_id", user_id)
            .execute()
        )
