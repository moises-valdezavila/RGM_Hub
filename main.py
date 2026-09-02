# from tools.VG_reporte_detalle import execute
# from tools.report_params import ReportParams

# params = ReportParams(
#     dias_transcurridos=16,
#     dias_laborales=26,
#     fecha_inicio="2026-08-01",
#     fecha_final="2026-08-19",
#     exportar_trimestre=False,
# )

# res = execute(params)

# print(res)
import sys

from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()