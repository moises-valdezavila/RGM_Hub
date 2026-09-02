import pandas as pd
from pathlib import Path

archivo = Path(__file__).resolve().parent.parent / "data" / "synthetic_data.xlsx"

def sp_vg_MSV(fecha_inicial, fecha_final):
    df = pd.read_excel(archivo, sheet_name="VEN_MSV")
    
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    inicio = pd.to_datetime(fecha_inicial)
    fin = pd.to_datetime(fecha_final)

    mask = df["fecha"].between(inicio, fin, inclusive="both")
    return df.loc[mask].reset_index(drop=True)


def descargar_tabla(nombre_tabla, columns="*"):
    return pd.read_excel(archivo, sheet_name=nombre_tabla)

def sp_inv(parametro, codigo = ''):
    return pd.read_excel(archivo, sheet_name="INV")