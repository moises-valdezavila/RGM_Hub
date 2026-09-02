from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class ReportParams:
    dias_transcurridos: int
    dias_laborales: int
    fecha_inicio: str | pd.Timestamp
    fecha_final: str | pd.Timestamp
    fecha_sufijo: str
    nombre_prefijo: str
    separador: str
    subcarpeta: str
    exportar_trimestre: bool = False
    

    def __post_init__(self):
        if self.dias_transcurridos is None or self.dias_laborales is None:
            raise ValueError("dias_transcurridos y dias_laborales son requeridos.")

        if self.dias_transcurridos <= 0:
            raise ValueError("dias_transcurridos debe ser mayor que 0.")

        if self.dias_laborales <= 0:
            raise ValueError("dias_laborales debe ser mayor que 0.")

        if self.dias_transcurridos > self.dias_laborales:
            raise ValueError("dias_transcurridos no puede ser mayor que dias_laborales")
        
        fecha_inicio = pd.to_datetime(self.fecha_inicio)
        fecha_final = pd.to_datetime(self.fecha_final)

        if pd.isna(fecha_inicio):
            raise ValueError("fecha_inicio no es una fecha válida.")

        if pd.isna(fecha_final):
            raise ValueError("fecha_final no es una fecha válida.")

        if fecha_final < fecha_inicio:
            raise ValueError("fecha_inicio debe ser menor o igual a fecha_final.")

        object.__setattr__(self, "fecha_inicio", fecha_inicio)
        object.__setattr__(self, "fecha_final", fecha_final)
