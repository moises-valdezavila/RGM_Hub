import pandas as pd
import numpy as np
from pathlib import Path
import logging
import sys
import os
from datetime import datetime
from services.data_source import sp_vg_MSV, descargar_tabla, sp_inv
from data.map import map_almacen
from tools.report_params import ReportParams

logger = logging.getLogger(__name__)
    
# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

TARGETS_VALIDOS = ["Menudeo", "Combinado"]

SUCURSALES_REPORTE = ["CAMPECHE", "CENTRO", "CHARLY", "KABAH", "NORTE"]
ALMACEN_ALDIS = "ALDIS"

COLS_AGRUPACION_MES = ["mes", "sucursal", "categoria", "subcategoria", "familia", "codigo"]
COLS_AGRUPACION_GENERAL = [
    "categoria", "subcategoria", "familia", "codigo",
    "articulo", "subcuenta", "descripcion1", "Color",
]
COLS_LLAVE_TRIMESTRE = ["sucursal", "categoria", "subcategoria", "familia", "codigo"]

COLS_METRICAS_BASE = ["VentaTotal_sin_Monedero", "costototal", "cantidadinventario"]

COLS_SALIDA_DETALLE = [
    "mes", "sucursal", "categoria", "subcategoria", "familia", "codigo", "articulo",
    "subcuenta", "descripcion1", "Color", "basico_moda",
    "VentaTotal_sin_Monedero_act", "tendencia_venta", "VentaTotal_sin_Monedero_aa",
    "crecimiento_venta", "diferencia_venta", "margen_act", "dif_MC", "margen_aa",
    "costototal_act", "costototal_aa", "margen_act_$", "margen_aa_$", "margen_tend_$",
    "dif_utilidad", "minimov2", "inv_une", "dias_inv_une", "inv_aldis", "dias_inv_aldis",
    "cantidadinventario_act", "cantidadinventario_aa",
]

COLS_SALIDA_GENERAL = [c for c in COLS_SALIDA_DETALLE if c not in ("mes", "sucursal")]

PRIORIDAD_BASICO_MODA = {"basico": 1, "basico-moda": 2, "moda": 3}
CLASIFICACION_BASICO_MODA = {v: k for k, v in PRIORIDAD_BASICO_MODA.items()}


# ----------------------------------------------------

def execute(params):
    if not isinstance(params, ReportParams):
        raise TypeError("execute espera una instancia de ReportParams.")
    dfs_por_sucursal, df_general = logic(params)
    return export(dfs_por_sucursal, df_general, params)

# def execute(params_u: dict) -> str:
#     params = assign_parameters(**params_u)
#     dfs_por_sucursal, df_general = logic(
#         dias_transcurridos = params["dias_transcurridos"], 
#         dias_laborales = params["dias_laborales"], 
#         exportar_trimestre = params["exportar_trimestre"], 
#         fecha_inicio = params["fecha_inicio"], 
#         fecha_final = params["fecha_final"]
#     )
#     export(
#         dfs_por_sucursal,
#         df_general,
#         fecha=params["fecha_sufijo"],
#         prefijo=params["nombre_prefijo"],
#         separador=params["separador"],
#         subcarpeta=params["subcarpeta"]
#     )
#     return "Finalizado"



# ---------------------------------------------------------------------------
# Columnas calculadas (margen, tendencia, crecimiento...)
# ---------------------------------------------------------------------------

def compute_calculated_columns(df: pd.DataFrame, dias_transcurridos: int, dias_laborales: int) -> pd.DataFrame:
    """Agrega columnas de margen, tendencia y crecimiento a un df que ya
    tiene las columnas *_act / *_aa de venta e inventario."""
    df["margen_act"] = np.where(
        df["VentaTotal_sin_Monedero_act"] != 0,
        (df["VentaTotal_sin_Monedero_act"] - df["costototal_act"]) / df["VentaTotal_sin_Monedero_act"],
        0,
    )
    df["margen_aa"] = np.where(
        df["VentaTotal_sin_Monedero_aa"] != 0,
        (df["VentaTotal_sin_Monedero_aa"] - df["costototal_aa"]) / df["VentaTotal_sin_Monedero_aa"],
        0,
    )
    df["tendencia_venta"] = df["VentaTotal_sin_Monedero_act"] / dias_transcurridos * dias_laborales
    df["crecimiento_venta"] = (
        (df["tendencia_venta"] - df["VentaTotal_sin_Monedero_aa"])
        / df["VentaTotal_sin_Monedero_aa"].replace(0, np.nan)
    ).fillna(0)
    df["diferencia_venta"] = df["tendencia_venta"] - df["VentaTotal_sin_Monedero_aa"]
    df["dif_MC"] = df["margen_act"] - df["margen_aa"]
    df["tendencia_costo"] = df["costototal_act"] / dias_transcurridos * dias_laborales
    df["margen_act_$"] = df["VentaTotal_sin_Monedero_act"] - df["costototal_act"]
    df["margen_tend_$"] = df["tendencia_venta"] - df["tendencia_costo"]
    df["margen_aa_$"] = df["VentaTotal_sin_Monedero_aa"] - df["costototal_aa"]
    df["dif_utilidad"] = df["margen_act_$"] - df["margen_aa_$"]
    return df


# ---------------------------------------------------------------------------
# Carga y preparación de datos base
# ---------------------------------------------------------------------------

def _normalizar_codigo(df: pd.DataFrame, col_articulo: str = "articulo", col_subcuenta: str = "subcuenta") -> pd.Series:
    """Concatena artículo + subcuenta como llave única de producto."""
    return df[col_articulo].astype(str) + df[col_subcuenta].fillna("").astype(str)


def _cargar_ventas_e_inventario(fecha_inicio, fecha_final, fecha_inicial_aa, fecha_final_aa):
    """Descarga venta actual, venta año anterior e inventario, y aplica
    los filtros/columnas base que ambos periodos necesitan."""
    logger.info("Descargando venta actual %s - %s", fecha_inicio, fecha_final)
    df_act = sp_vg_MSV(fecha_inicio, fecha_final)

    logger.info("Descargando venta año anterior %s - %s", fecha_inicial_aa, fecha_final_aa)
    df_aa = sp_vg_MSV(fecha_inicial_aa, fecha_final_aa)

    logger.info("Descargando inventario")
    df_inv = sp_inv("TODOS")
    df_inv["basico_moda"] = np.select(
        [df_inv["Minimo"] == 0, df_inv["Minimo"] == 9999],
        ["Moda", "Basico-Moda"],
        default="Basico",
    )
    # Se calculan aquí (y no sólo dentro de _agregar_inventarios) porque
    # 'codigo' y 'Almacen2' también se usan más adelante en logic() para
    # obtener basico_moda por sucursal.
    df_inv["Almacen2"] = df_inv["Almacen"].str.strip().map(map_almacen)
    df_inv["codigo"] = _normalizar_codigo(df_inv)

    for df in (df_act, df_aa):
        df.query("target in @TARGETS_VALIDOS", inplace=True)
        df["codigo"] = _normalizar_codigo(df)
        df[COLS_AGRUPACION_MES] = df[COLS_AGRUPACION_MES].fillna("SIN_DATO")

    return df_act, df_aa, df_inv


def _catalogo_articulos(df_act: pd.DataFrame, df_aa: pd.DataFrame) -> pd.DataFrame:
    """Catálogo único código -> descripción, tomando de cualquiera de los
    dos periodos (act tiene prioridad por el orden del concat + drop_duplicates)."""
    cols = ["codigo", "articulo", "subcuenta", "descripcion1", "Color"]
    return pd.concat([
        df_act[cols].drop_duplicates(subset=["codigo"]),
        df_aa[cols].drop_duplicates(subset=["codigo"]),
    ]).drop_duplicates(subset=["codigo"])


def _agrupar_ventas(df_act: pd.DataFrame, df_aa: pd.DataFrame) -> pd.DataFrame:
    """Agrupa venta act/aa a nivel mes-sucursal-categoria...-codigo y las
    combina en un solo df con sufijos _act / _aa."""
    df_group = df_act.groupby(COLS_AGRUPACION_MES).agg({c: "sum" for c in COLS_METRICAS_BASE}).reset_index()
    df_group_aa = df_aa.groupby(COLS_AGRUPACION_MES).agg({c: "sum" for c in COLS_METRICAS_BASE}).reset_index()

    # Sólo comparar contra los meses que sí existen en el periodo actual
    df_group_aa_mes_act = df_group_aa[df_group_aa["mes"].isin(df_group["mes"].unique())]

    return df_group.merge(
        df_group_aa_mes_act,
        how="outer",
        on=COLS_AGRUPACION_MES,
        suffixes=("_act", "_aa"),
    ).fillna(0)


# ---------------------------------------------------------------------------
# Cálculo de "mínimo" (minimov2) por sucursal/código, con 3 fuentes en cascada:
# 1) promedio del último trimestre del año anterior
# 2) mínimo configurado en artalm (si el punto 1 dio 0)
# 3) tendencia de inventario del periodo actual (si el punto 2 también dio 0)
# ---------------------------------------------------------------------------

def _calcular_minimo_trimestre_aa(df_aa: pd.DataFrame) -> pd.DataFrame:
    ultimos_3_meses = df_aa["mes"].unique()[-3:]
    df_tri = (
        df_aa[df_aa["mes"].isin(ultimos_3_meses)]
        .groupby(COLS_LLAVE_TRIMESTRE, as_index=False)
        .agg({"cantidadinventario": "sum"})
    )
    df_tri["minimov2"] = df_tri["cantidadinventario"] / 3
    return df_tri.drop(columns="cantidadinventario")


def _calcular_minimo_artalm() -> pd.DataFrame:
    df_artalm = descargar_tabla("artalm")
    df_artalm["Almacen2"] = df_artalm["Almacen"].map(map_almacen)
    df_artalm_group = df_artalm.groupby(["Articulo", "SubCuenta", "Almacen2"]).agg({"Minimo": "sum"}).reset_index()
    df_artalm_group["codigo"] = _normalizar_codigo(df_artalm_group, "Articulo", "SubCuenta")
    df_artalm_group["Almacen2"] = df_artalm_group["Almacen2"].str.upper()
    return df_artalm_group


def _calcular_minimo_tendencia_actual(df_act: pd.DataFrame, dias_transcurridos: int, dias_laborales: int) -> pd.DataFrame:
    df_aux = df_act.groupby(COLS_AGRUPACION_MES).agg({"cantidadinventario": "sum"}).reset_index()
    df_aux["minimov2_aux"] = df_aux["cantidadinventario"] / dias_transcurridos * dias_laborales
    df_aux["sucursal"] = df_aux["sucursal"].str.upper()
    return df_aux[["codigo", "sucursal", "minimov2_aux"]]


def _rellenar_minimo_en_cascada(df_merge: pd.DataFrame, df_act: pd.DataFrame, df_aa: pd.DataFrame,
                                dias_transcurridos: int, dias_laborales: int) -> pd.DataFrame:
    df = df_merge.copy()
    df["sucursal"] = df["sucursal"].str.upper()

    # Fuente 1: trimestre AA
    df = df.merge(_calcular_minimo_trimestre_aa(df_aa), how="left", on=COLS_LLAVE_TRIMESTRE).fillna({"minimov2": 0})

    # Fuente 2: mínimo configurado en artalm, sólo donde la fuente 1 dio 0
    df_artalm_group = _calcular_minimo_artalm()
    df = df.merge(
        df_artalm_group[["codigo", "Almacen2", "Minimo"]],
        left_on=["codigo", "sucursal"], right_on=["codigo", "Almacen2"], how="left",
    )
    mask = df["minimov2"] == 0
    df.loc[mask, "minimov2"] = df.loc[mask, "Minimo"].fillna(0)
    df = df.drop(columns=["Almacen2", "Minimo"])

    # Fuente 3: tendencia de inventario actual, sólo donde sigue en 0
    df_tendencia = _calcular_minimo_tendencia_actual(df_act, dias_transcurridos, dias_laborales)
    df = df.merge(df_tendencia, on=["codigo", "sucursal"], how="left")
    mask = df["minimov2"] == 0
    df.loc[mask, "minimov2"] = df.loc[mask, "minimov2_aux"].fillna(0)
    df = df.drop(columns="minimov2_aux")

    return df


# ---------------------------------------------------------------------------
# Inventarios (UNE propia + ALDIS) y días de inventario
# ---------------------------------------------------------------------------

def _agregar_inventarios(df_merge: pd.DataFrame, df_inv: pd.DataFrame) -> pd.DataFrame:
    """`df_inv` ya debe traer las columnas 'codigo' y 'Almacen2'
    (se calculan en _cargar_ventas_e_inventario)."""
    df = df_merge.merge(
        df_inv[["codigo", "Almacen2", "disponible"]],
        left_on=["codigo", "sucursal"], right_on=["codigo", "Almacen2"], how="left",
    ).rename(columns={"disponible": "inv_une"}).drop(columns="Almacen2")

    df_inv_aldis = (
        df_inv[df_inv["Almacen2"] == ALMACEN_ALDIS]
        .groupby("codigo", as_index=False)["disponible"]
        .sum()
        .rename(columns={"disponible": "inv_aldis"})
    )
    df = df.merge(df_inv_aldis, on="codigo", how="left").fillna(0)

    df = df[df["sucursal"].isin(SUCURSALES_REPORTE)]

    df["dias_inv_une"] = np.where(df["minimov2"] > 0, (df["inv_une"] / df["minimov2"]) * 30, 0)

    minimov2_codigo = df.groupby("codigo")["minimov2"].sum().rename("minimov2_total_codigo")
    df = df.merge(minimov2_codigo, on="codigo", how="left", validate="many_to_one")
    df["dias_inv_aldis"] = np.where(
        df["minimov2_total_codigo"] > 0,
        (df["inv_aldis"] / df["minimov2_total_codigo"]) * 30,
        0,
    )
    return df


# ---------------------------------------------------------------------------
# Libro general (todas las sucursales combinadas)
# ---------------------------------------------------------------------------

def _construir_libro_general(df_merge_info: pd.DataFrame, dias_transcurridos: int, dias_laborales: int,
                            num_sucursales: int) -> pd.DataFrame:
    df_tmp = df_merge_info.copy()
    df_tmp["prioridad_basico_moda"] = df_tmp["basico_moda"].str.lower().map(PRIORIDAD_BASICO_MODA)
    prioridad_por_codigo = df_tmp.groupby("codigo")["prioridad_basico_moda"].min()

    df_general = df_tmp.groupby(COLS_AGRUPACION_GENERAL, as_index=False, dropna=False).sum(numeric_only=True)
    df_general["basico_moda"] = df_general["codigo"].map(prioridad_por_codigo).map(CLASIFICACION_BASICO_MODA)

    df_general = df_general[COLS_SALIDA_GENERAL]
    df_general = compute_calculated_columns(df_general, dias_transcurridos, dias_laborales)

    # minimov2 / inv_aldis / dias_inv_aldis se sumaron por sucursal al agrupar;
    # se promedian de vuelta a nivel "una sucursal" para que el libro general
    # sea comparable con los libros individuales.
    df_general["minimov2"] = df_general["minimov2"] / num_sucursales
    df_general["inv_aldis"] = df_general["inv_aldis"] / num_sucursales
    df_general["dias_inv_aldis"] = df_general["dias_inv_aldis"] / num_sucursales
    df_general["dias_inv_une"] = np.where(
        df_general["minimov2"] > 0,
        (df_general["inv_une"] / df_general["minimov2"]) * 30,
        0,
    )
    return df_general[COLS_SALIDA_GENERAL]


# ---------------------------------------------------------------------------
# Orquestador principal
# ---------------------------------------------------------------------------

def logic(params: ReportParams):
    dias_transcurridos = params.dias_transcurridos
    dias_laborales = params.dias_laborales
    exportar_trimestre = params.exportar_trimestre
    fecha_inicio = params.fecha_inicio
    fecha_final = params.fecha_final

    fecha_inicial_aa = fecha_inicio - pd.DateOffset(years=1)
    fecha_final_aa = (fecha_final - pd.DateOffset(years=1) + pd.DateOffset(months=3)).replace(day=1) + pd.offsets.MonthEnd(0)

    df_act = sp_vg_MSV(fecha_inicio, fecha_final) #YY-MM-DD

    df_aa = sp_vg_MSV(fecha_inicial_aa, fecha_final_aa) #YY-MM-DD

    df_act, df_aa, df_inv = _cargar_ventas_e_inventario(fecha_inicio, fecha_final, fecha_inicial_aa, fecha_final_aa)
    datos_art = _catalogo_articulos(df_act, df_aa)

    df_merge = _agrupar_ventas(df_act, df_aa)
    df_merge = compute_calculated_columns(df_merge, dias_transcurridos, dias_laborales)
    df_merge = _rellenar_minimo_en_cascada(df_merge, df_act, df_aa, dias_transcurridos, dias_laborales)

    df_merge_inv = _agregar_inventarios(df_merge, df_inv)

    df_merge_info = df_merge_inv.merge(datos_art, how="left", on="codigo", validate="many_to_one")

    df_basico_moda = (
        df_inv[["codigo", "Almacen2", "basico_moda"]]
        .drop_duplicates(subset=["codigo", "Almacen2"])
        .rename(columns={"Almacen2": "sucursal"})
    )

    df_merge_info = df_merge_info.merge(df_basico_moda, how="left", on=["codigo", "sucursal"], validate="many_to_one")
    df_merge_info = df_merge_info[COLS_SALIDA_DETALLE]

    dfs_por_sucursal = {sucursal: grupo.copy().drop(columns=["mes", "sucursal"]) for sucursal, grupo in df_merge_info.groupby("sucursal")}

    df_general = _construir_libro_general(
        df_merge_info, dias_transcurridos, dias_laborales, num_sucursales=len(dfs_por_sucursal)
    )

    return dfs_por_sucursal, df_general

# ---------------------------------------------------------------------------
# Exportación a Excel
# ---------------------------------------------------------------------------
 
def exportar_excel(df: pd.DataFrame, archivo_excel: Path) -> None:
    with pd.ExcelWriter(archivo_excel, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Todos", index=False)
        for categoria, df_categoria in df.groupby("categoria"):
            nombre_hoja = str(categoria)[:30]
            df_categoria.to_excel(writer, sheet_name=nombre_hoja, index=False)
 
 
# def export(dfs: dict, df_g: pd.DataFrame, subcarpeta: str, fecha: str, prefijo: str, separador: str) -> None:
def export(dfs: dict, df_g: pd.DataFrame, params: ReportParams) -> None:
    """Exporta un Excel por sucursal + un Excel GENERAL.
 
    `fecha` es el sufijo que se usa en el nombre de archivo (formato DD-MM-AA).
    Si no se especifica, se usa la fecha de hoy para no sobrescribir corridas
    de días distintos con el mismo nombre.
    """
    prefijo = params.nombre_prefijo
    separador = params.separador
    fecha = params.fecha_sufijo
    subcarpeta = params.subcarpeta
    ruta_salida = Path(__file__).resolve().parent.parent / "data" / subcarpeta
    ruta_salida.mkdir(parents=True, exist_ok=True)

    for sucursal, df_sucursal in dfs.items():
        archivo_excel = ruta_salida / f"{prefijo}{separador}{fecha}{separador}{sucursal}.xlsx"
        exportar_excel(df_sucursal, archivo_excel)
 
    archivo_general = ruta_salida / f"{prefijo}{separador}{fecha}{separador}GENERAL.xlsx"
    exportar_excel(df_g, archivo_general)