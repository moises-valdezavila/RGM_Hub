import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
from datetime import datetime
from services.to_sql import sp_vg_MSV, descargar_tabla, sp_inv
from data.map import map_almacen

def execute(params_u):
    params = assign_parameters(**params_u)
    return logic(**params)


def assign_parameters(**params_u):

    dias_transcurridos = params_u.get("dias_transcurridos")
    dias_laborales = params_u.get("dias_laborales")

    exportar_trimestre = params_u.get("exportar_trimestre", False)

    fecha_inicio = pd.to_datetime(params_u.get("fecha_inicio"))

    fecha_final = pd.to_datetime(params_u.get("fecha_final"))
    

    return {
        "dias_transcurridos": dias_transcurridos,
        "dias_laborales": dias_laborales,
        "exportar_trimestre": exportar_trimestre,
        "fecha_inicio": fecha_inicio,
        "fecha_final": fecha_final,
    }

def logic(
    dias_transcurridos,
    dias_laborales,
    exportar_trimestre,
    fecha_inicio,
    fecha_final
):
    fecha_inicial_aa = fecha_inicio - pd.DateOffset(years=1)
    fecha_final_aa = (fecha_final - pd.DateOffset(years=1) + pd.DateOffset(months=3)).replace(day=1) + pd.offsets.MonthEnd(0)

    df_act = sp_vg_MSV(fecha_inicio, fecha_final) #YY-MM-DD
    df_aa = sp_vg_MSV(fecha_inicial_aa, fecha_final_aa) #YY-MM-DD
    df_inv = sp_inv('TODOS')
    df_inv['basico_moda'] = np.select(
        [df_inv['Minimo'] == 0, df_inv['Minimo'] == 9999],
        ['Moda', 'Basico-Moda'],
        default='Basico'
    )
    df_act = df_act[df_act['target'].isin(['Menudeo', 'Combinado'])]
    df_act['codigo'] = (
        df_act['articulo'].astype(str)
        + df_act['subcuenta'].fillna('').astype(str)
    )

    df_aa = df_aa[df_aa['target'].isin(['Menudeo', 'Combinado'])]
    df_aa['codigo'] = (
        df_aa['articulo'].astype(str)
        + df_aa['subcuenta'].fillna('').astype(str)
    )
    cols = ['mes', 'sucursal', 'categoria', 'rama', 'familia', 'codigo']

    df_aa[cols] = df_aa[cols].fillna('SIN_DATO')
    df_act[cols] = df_act[cols].fillna('SIN_DATO')

    datos_art = pd.concat([
        df_act[['codigo','articulo','subcuenta','descripcion1','Color']]
            .drop_duplicates(subset=['codigo']),
        df_aa[['codigo','articulo','subcuenta','descripcion1','Color']]
            .drop_duplicates(subset=['codigo'])
    ]).drop_duplicates(subset=['codigo'])
        
    df_group = df_act.groupby(['mes','sucursal','categoria','subcategoria','familia','codigo']).agg(
        {'VentaTotal_sin_Monedero': 'sum',
        'costototal': 'sum',
        'cantidadinventario':'sum'}).reset_index()

    df_group_aa = df_aa.groupby(['mes','sucursal','categoria','subcategoria','familia','codigo']).agg(
        {'VentaTotal_sin_Monedero': 'sum',
        'costototal': 'sum',
        'cantidadinventario':'sum'}).reset_index() 
    
    df_group_aa_mes_act = df_group_aa[df_group_aa['mes'].isin(df_group['mes'].unique())]
    df_merge = df_group.merge(
        df_group_aa_mes_act,
        how='outer',
        on=['mes','sucursal','categoria','subcategoria','familia','codigo'],
        suffixes=('_act', '_aa')
    ).fillna(0)
    
    df_merge['margen_act'] = np.where(
        df_merge['VentaTotal_sin_Monedero_act'] != 0,
        (df_merge['VentaTotal_sin_Monedero_act'] - df_merge['costototal_act']) / df_merge['VentaTotal_sin_Monedero_act'],
        0
    )
    df_merge['margen_aa'] = np.where(
        df_merge['VentaTotal_sin_Monedero_aa'] != 0,
        (df_merge['VentaTotal_sin_Monedero_aa'] - df_merge['costototal_aa']) / df_merge['VentaTotal_sin_Monedero_aa'],
        0
    )
    # Columnas calculadas
    df_merge['tendencia_venta'] = df_merge['VentaTotal_sin_Monedero_act'] / dias_transcurridos * dias_laborales
    df_merge['crecimiento_venta'] = ((df_merge['tendencia_venta'] - df_merge['VentaTotal_sin_Monedero_aa']) / df_merge['VentaTotal_sin_Monedero_aa'].replace(0, np.nan)).fillna(0)
    df_merge['diferencia_venta'] = df_merge['tendencia_venta'] - df_merge['VentaTotal_sin_Monedero_aa']
    df_merge['dif_MC'] = df_merge['margen_act'] - df_merge['margen_aa']
    df_merge['tendencia_costo'] = df_merge['costototal_act'] / dias_transcurridos * dias_laborales
    df_merge['margen_act_$'] = df_merge['VentaTotal_sin_Monedero_act'] - df_merge['costototal_act']
    df_merge['margen_tend_$'] = df_merge['tendencia_venta'] - df_merge['tendencia_costo']
    df_merge['margen_aa_$'] = df_merge['VentaTotal_sin_Monedero_aa'] - df_merge['costototal_aa']
    df_merge['dif_utilidad'] = df_merge['margen_act_$'] - df_merge['margen_aa_$']
    
    #Calculo con trimestre siguiente del AA
    df_group_tri_aa = (
        df_aa[df_aa['mes'].isin(df_aa['mes'].unique()[-3:])].groupby(
            ['sucursal','categoria','subcategoria','familia','codigo'], as_index=False)
            .agg({'cantidadinventario': 'sum'})
    )
    df_group_tri_aa['minimov2'] = df_group_tri_aa['cantidadinventario'] / 3
    df_group_tri_aa = df_group_tri_aa.drop(columns='cantidadinventario')

    df_merge_tri_ven = df_merge.merge(df_group_tri_aa, how='left', on=['sucursal','categoria','subcategoria','familia','codigo']).fillna(0)
    # Calculo con mínimo en tabla artalm
    df_artalm = descargar_tabla('artalm')

    df_artalm['Almacen2'] = df_artalm['Almacen'].map(map_almacen)
    df_artalm_group = df_artalm.groupby(['Articulo','SubCuenta','Almacen2']).agg({'Minimo': 'sum'}).reset_index()
    df_artalm_group['codigo'] = (
        df_artalm_group['Articulo'].astype(str)
        + df_artalm_group['SubCuenta'].fillna('').astype(str)
    )
    # Normalizar sucursales
    df_merge_tri_ven['sucursal'] = df_merge_tri_ven['sucursal'].str.upper()
    df_artalm_group['Almacen2'] = df_artalm_group['Almacen2'].str.upper()

    # Agregar la columna Minimo
    df_merge_tri_ven = df_merge_tri_ven.merge(
        df_artalm_group[['codigo', 'Almacen2', 'Minimo']],
        left_on=['codigo', 'sucursal'],
        right_on=['codigo', 'Almacen2'],
        how='left'
    )

    # Sólo reemplazar donde minimov2 sea 0
    mask = df_merge_tri_ven['minimov2'] == 0
    df_merge_tri_ven.loc[mask, 'minimov2'] = (
        df_merge_tri_ven.loc[mask, 'Minimo']
        .fillna(0)
    )

    # Eliminar columnas auxiliares
    df_merge_tri_ven = df_merge_tri_ven.drop(columns=['Almacen2', 'Minimo'])
    # Calculo de venta actual en tendencia
    df_aux_dias_inv = df_act.groupby(['mes','sucursal','categoria','subcategoria','familia','codigo']).agg({'cantidadinventario': 'sum'}).reset_index()
    df_aux_dias_inv['minimov2_aux'] = df_aux_dias_inv['cantidadinventario'] / dias_transcurridos * dias_laborales
    
    # Normalizar sucursales
    df_aux_dias_inv['sucursal'] = df_aux_dias_inv['sucursal'].str.upper()

    # Agregar la columna minimov2 del dataframe auxiliar
    df_merge_tri_ven = df_merge_tri_ven.merge(
        df_aux_dias_inv[['codigo', 'sucursal', 'minimov2_aux']],
        on=['codigo', 'sucursal'],
        how='left'
    )

    # Reemplazar únicamente donde minimov2 sea 0
    mask = df_merge_tri_ven['minimov2'] == 0
    df_merge_tri_ven.loc[mask, 'minimov2'] = (
        df_merge_tri_ven.loc[mask, 'minimov2_aux']
        .fillna(0)
    )

    # Eliminar la columna auxiliar
    df_merge_tri_ven = df_merge_tri_ven.drop(columns='minimov2_aux')
    # Agregar inventarios
    df_inv['Almacen2'] = df_inv['Almacen'].str.strip().map(map_almacen)
    df_inv['codigo'] = (
        df_inv['articulo'].astype(str)
        + df_inv['subcuenta'].fillna('').astype(str)
    )
    df_merge_inv = df_merge_tri_ven.merge(
        df_inv[['codigo', 'Almacen2', 'disponible']],
        left_on=['codigo', 'sucursal'],
        right_on=['codigo', 'Almacen2'],
        how='left'
    )

    df_merge_inv = df_merge_inv.rename(columns={'disponible': 'inv_une'})
    df_merge_inv = df_merge_inv.drop(columns='Almacen2')
    
    df_inv_aldis = (
        df_inv[df_inv['Almacen2'] == 'ALDIS']
        .groupby('codigo', as_index=False)['disponible']
        .sum()
        .rename(columns={'disponible': 'inv_aldis'})
    )

    df_merge_inv = df_merge_inv.merge(
        df_inv_aldis,
        on='codigo',
        how='left'
    )
    df_merge_inv = df_merge_inv.rename(columns={'disponible': 'inv_aldis'}).fillna(0)
    
    df_merge_inv = df_merge_inv[df_merge_inv['sucursal'].isin(['CAMPECHE', 'CENTRO', 'CHARLY', 'KABAH', 'NORTE'])]
    df_merge_inv['dias_inv_une'] = np.where(
        df_merge_inv['minimov2'] > 0,
        (df_merge_inv['inv_une'] / df_merge_inv['minimov2']) * 30,
        0
    )
    minimov2_codigo = (
        df_merge_inv
        .groupby('codigo')['minimov2']
        .sum()
        .rename('minimov2_total_codigo')
    )
    df_merge_inv = df_merge_inv.merge(
        minimov2_codigo,
        on='codigo',
        how='left',
        validate='many_to_one'
    )
    df_merge_inv['dias_inv_aldis'] = np.where(
        df_merge_inv['minimov2_total_codigo'] > 0,
        (df_merge_inv['inv_aldis'] / df_merge_inv['minimov2_total_codigo']) * 30,
        0
    )
    df_merge_info = df_merge_inv.merge(datos_art, how='left', on=['codigo'], validate='many_to_one')
    df_b_m = df_inv[['codigo','Almacen2','basico_moda']].drop_duplicates(subset=['codigo','Almacen2']).rename(columns={'Almacen2': 'sucursal'})
    df_merge_info = df_merge_info.merge(df_b_m, how='left', on=['codigo','sucursal'], validate='many_to_one')
    
    resultado = df_merge_info[['mes','sucursal','categoria','subcategoria','familia','codigo','articulo','subcuenta','descripcion1','Color','basico_moda',
                                   'VentaTotal_sin_Monedero_act','tendencia_venta','VentaTotal_sin_Monedero_aa','crecimiento_venta','diferencia_venta','margen_act',
                                   'dif_MC','margen_aa','costototal_act','costototal_aa','margen_act_$','margen_aa_$','margen_tend_$','dif_utilidad','minimov2',
                                   'inv_une','dias_inv_une','inv_aldis','dias_inv_aldis','cantidadinventario_act','cantidadinventario_aa']]
    
    
    
    # # Estructura diccionario, df por sucursal
    # dfs_por_sucursal = {
    #     sucursal: grupo.copy()
    #     for sucursal, grupo in df_merge_info.groupby('sucursal')
    # }
    # #Exportar a excel
    # # Carpeta de salida
    # ruta_salida = Path(__file__).resolve().parent.parent / "data" / "HUB_Output"
    # ruta_salida.mkdir(parents=True, exist_ok=True)

    # for sucursal, df_sucursal in dfs_por_sucursal.items():
        
    #     archivo_excel = ruta_salida / f"{sucursal}.xlsx"
        
    #     with pd.ExcelWriter(archivo_excel, engine="openpyxl") as writer:
    #         df_sucursal.to_excel(
    #             writer,
    #             sheet_name="Todos",
    #             index=False
    #         )
    #         for categoria, df_categoria in df_sucursal.groupby('categoria'):
                
    #             nombre_hoja = str(categoria)[:30]
                
    #             df_categoria.to_excel(
    #                 writer,
    #                 sheet_name=nombre_hoja,
    #                 index=False
    #             )
    return resultado