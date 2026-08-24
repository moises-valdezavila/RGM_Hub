from tools.report_params import ReportParams
from tools.VG_reporte_detalle import execute

params = ReportParams(
    dias_transcurridos=16,
    dias_laborales=26,
    fecha_inicio="2026-08-01",
    fecha_final="2026-08-19",
    exportar_trimestre=False,
)

res = execute(params)

print(res)
