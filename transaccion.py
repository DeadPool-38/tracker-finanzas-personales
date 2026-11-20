from dataclasses import dataclass
from datetime import date


@dataclass
class Transaccion:
    descripcion: str
    monto: float
    fecha: date
    categoria: str
    tipo: str
    id: int | None = None

    def es_gasto(self):
        return self.tipo == "Gasto"

    def es_ingreso(self):
        return self.tipo == "Ingreso"

    def a_diccionario(self):
        return {
            "descripcion": self.descripcion,
            "monto": self.monto,
            "fecha": self.fecha,
            "categoria": self.categoria,
            "tipo": self.tipo,
        }
