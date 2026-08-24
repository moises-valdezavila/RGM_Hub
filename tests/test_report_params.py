import sys
import types
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

services_module = types.ModuleType("services")
services_module.__path__ = []
services_to_sql = types.ModuleType("services.to_sql")


def _mock_sp_vg_MSV(start, end):
    return pd.DataFrame(
        [
            {
                "mes": "2026-08",
                "sucursal": "CAMPECHE",
                "categoria": "Categoria A",
                "rama": "Rama A",
                "subcategoria": "Subcat A",
                "familia": "Familia A",
                "target": "Menudeo",
                "articulo": 101,
                "subcuenta": 10,
                "descripcion1": "Prod 101",
                "Color": "Rojo",
                "VentaTotal_sin_Monedero": 1000,
                "costototal": 600,
                "cantidadinventario": 25,
            }
        ]
    )


def _mock_sp_inv(_):
    return pd.DataFrame(
        [
            {
                "articulo": 101,
                "subcuenta": 10,
                "Almacen": "CAMPECHE",
                "disponible": 30,
                "Minimo": 0,
            }
        ]
    )


def _mock_descargar_tabla(table_name):
    assert table_name == "artalm"
    return pd.DataFrame(
        [
            {
                "Articulo": 101,
                "SubCuenta": 10,
                "Almacen": "CAMPECHE",
                "Minimo": 15,
            }
        ]
    )


services_to_sql.sp_vg_MSV = _mock_sp_vg_MSV
services_to_sql.sp_inv = _mock_sp_inv
services_to_sql.descargar_tabla = _mock_descargar_tabla
services_module.to_sql = services_to_sql
sys.modules["services"] = services_module
sys.modules["services.to_sql"] = services_to_sql

from tools.VG_reporte_detalle import ReportParams, execute


class ReportParamsTests(unittest.TestCase):
    def test_report_params_normalizes_and_validates_dates(self):
        params = ReportParams(
            dias_transcurridos=16,
            dias_laborales=26,
            fecha_inicio="2026-08-01",
            fecha_final="2026-08-19",
        )

        self.assertEqual(params.dias_transcurridos, 16)
        self.assertEqual(params.dias_laborales, 26)
        self.assertFalse(params.exportar_trimestre)
        self.assertEqual(params.fecha_inicio, pd.Timestamp("2026-08-01"))
        self.assertEqual(params.fecha_final, pd.Timestamp("2026-08-19"))

    def test_report_params_rejects_invalid_range(self):
        with self.assertRaisesRegex(ValueError, "fecha_inicio.*fecha_final"):
            ReportParams(
                dias_transcurridos=16,
                dias_laborales=26,
                fecha_inicio="2026-08-20",
                fecha_final="2026-08-19",
            )

    def test_execute_accepts_report_params_and_returns_dataframe(self):
        params = ReportParams(
            dias_transcurridos=16,
            dias_laborales=26,
            fecha_inicio="2026-08-01",
            fecha_final="2026-08-19",
        )

        result = execute(params)

        self.assertIsInstance(result, pd.DataFrame)
        self.assertTrue({"mes", "sucursal", "categoria", "codigo"}.issubset(result.columns))
        self.assertFalse(result.empty)

    def test_execute_rejects_dict_input(self):
        with self.assertRaisesRegex(TypeError, "ReportParams"):
            execute({
                "dias_transcurridos": 16,
                "dias_laborales": 26,
                "fecha_inicio": "2026-08-01",
                "fecha_final": "2026-08-19",
            })


if __name__ == "__main__":
    unittest.main()
