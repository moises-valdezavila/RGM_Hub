from datetime import date, timedelta
from tools.report_params import ReportParams
from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from tools.VG_reporte_detalle import execute


class ReporteDetalleWindow(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Reporte detalle de ventas")
        self.setMinimumSize(600, 650)
        self.resize(600, 650)

        self.dias_transcurridos_manual = False
        self.dias_laborales_manual = False

        self.crear_interfaz()
        self.aplicar_estilos()
        self.calcular_dias()

    # =========================================================
    # INTERFAZ
    # =========================================================

    def crear_interfaz(self):

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(30, 25, 30, 25)
        layout_principal.setSpacing(15)

        # -----------------------------------------------------
        # Título
        # -----------------------------------------------------

        titulo = QLabel("Reporte detalle de ventas")
        titulo.setObjectName("windowTitle")

        descripcion = QLabel(
            "Configura los parámetros necesarios para generar el reporte."
        )
        descripcion.setObjectName("windowDescription")

        layout_principal.addWidget(titulo)
        layout_principal.addWidget(descripcion)

        # -----------------------------------------------------
        # Parámetros principales
        # -----------------------------------------------------

        grupo_parametros = QGroupBox()
        layout_parametros = QGridLayout(grupo_parametros)

        layout_parametros.setHorizontalSpacing(15)
        layout_parametros.setVerticalSpacing(12)

        # Fecha inicial

        label_fecha_inicio = QLabel("Fecha inicial")

        self.fecha_inicio = QDateEdit()
        self.fecha_inicio.setCalendarPopup(True)
        self.fecha_inicio.setDate(
            self.fecha_inicio.minimumDate()
        )

        # Fecha final

        label_fecha_final = QLabel("Fecha final")

        self.fecha_final = QDateEdit()
        self.fecha_final.setCalendarPopup(True)

        # Usamos la fecha actual como valor inicial
        hoy = date.today()

        self.fecha_inicio.setDate(
            self.fecha_inicio.date().fromString(
                hoy.replace(day=1).strftime("%d/%m/%Y"),
                "dd/MM/yyyy"
            )
        )

        self.fecha_final.setDate(
            self.fecha_final.date().fromString(
                (hoy- timedelta(days=1)).strftime("%d/%m/%Y"),
                "dd/MM/yyyy"
            )
        )

        self.fecha_inicio.dateChanged.connect(self.fecha_cambio)
        self.fecha_final.dateChanged.connect(self.fecha_cambio)

        layout_parametros.addWidget(
            label_fecha_inicio,
            0, 0
        )

        layout_parametros.addWidget(
            self.fecha_inicio,
            0, 1, 1, 2
        )

        layout_parametros.addWidget(
            label_fecha_final,
            1, 0
        )

        layout_parametros.addWidget(
            self.fecha_final,
            1, 1, 1, 2
        )

        # -----------------------------------------------------
        # Días transcurridos
        # -----------------------------------------------------

        label_dias_transcurridos = QLabel(
            "Días transcurridos"
        )

        self.dias_transcurridos = QSpinBox()
        self.dias_transcurridos.setRange(0, 999)
        self.dias_transcurridos.setMinimumWidth(100)

        boton_reset_transcurridos = QPushButton("↻")
        boton_reset_transcurridos.setFixedWidth(35)
        boton_reset_transcurridos.setToolTip(
            "Restaurar cálculo automático"
        )

        boton_reset_transcurridos.clicked.connect(
            self.restaurar_dias_transcurridos
        )

        self.dias_transcurridos.valueChanged.connect(
            self.dias_transcurridos_modificado
        )

        layout_parametros.addWidget(
            label_dias_transcurridos,
            2, 0
        )

        layout_parametros.addWidget(
            self.dias_transcurridos,
            2, 1
        )

        layout_parametros.addWidget(
            boton_reset_transcurridos,
            2, 2
        )

        # -----------------------------------------------------
        # Días laborales
        # -----------------------------------------------------

        label_dias_laborales = QLabel(
            "Días laborales"
        )

        self.dias_laborales = QSpinBox()
        self.dias_laborales.setRange(0, 999)
        self.dias_laborales.setMinimumWidth(100)

        boton_reset_laborales = QPushButton("↻")
        boton_reset_laborales.setFixedWidth(35)
        boton_reset_laborales.setToolTip(
            "Restaurar cálculo automático"
        )

        boton_reset_laborales.clicked.connect(
            self.restaurar_dias_laborales
        )

        self.dias_laborales.valueChanged.connect(
            self.dias_laborales_modificado
        )

        layout_parametros.addWidget(
            label_dias_laborales,
            3, 0
        )

        layout_parametros.addWidget(
            self.dias_laborales,
            3, 1
        )

        layout_parametros.addWidget(
            boton_reset_laborales,
            3, 2
        )

        # -----------------------------------------------------
        # Exportar trimestre
        # -----------------------------------------------------

        self.exportar_trimestre = QCheckBox(
            "Exportar trimestre"
        )

        layout_parametros.addWidget(
            self.exportar_trimestre,
            4, 0, 1, 3
        )

        layout_principal.addWidget(grupo_parametros)

        # -----------------------------------------------------
        # Opciones avanzadas
        # -----------------------------------------------------

        self.crear_opciones_avanzadas(layout_principal)

        layout_principal.addStretch()

        # -----------------------------------------------------
        # Botón generar
        # -----------------------------------------------------

        self.boton_generar = QPushButton(
            "Generar reporte"
        )

        self.boton_generar.setObjectName("generateButton")

        self.boton_generar.clicked.connect(
            self.generar_reporte
        )

        layout_principal.addWidget(
            self.boton_generar
        )

    # =========================================================
    # OPCIONES AVANZADAS
    # =========================================================

    def crear_opciones_avanzadas(self, layout_principal):

        self.boton_avanzadas = QPushButton(
            "⚙  Opciones avanzadas"
        )

        self.boton_avanzadas.setObjectName(
            "advancedButton"
        )

        self.boton_avanzadas.setCheckable(True)

        self.boton_avanzadas.clicked.connect(
            self.toggle_opciones_avanzadas
        )

        layout_principal.addWidget(
            self.boton_avanzadas
        )

        # Contenedor

        self.panel_avanzadas = QFrame()
        self.panel_avanzadas.setObjectName(
            "advancedPanel"
        )

        layout = QGridLayout(
            self.panel_avanzadas
        )

        layout.setHorizontalSpacing(15)
        layout.setVerticalSpacing(10)

        # Fecha sufijo

        layout.addWidget(
            QLabel("Fecha para nombre del archivo"),
            0, 0
        )

        self.fecha_sufijo = QLineEdit()
        self.fecha_sufijo.setText(
            (date.today() - timedelta(days=1)).strftime("%d-%m-%y")
        )

        layout.addWidget(
            self.fecha_sufijo,
            0, 1
        )

        # Nombre prefijo

        layout.addWidget(
            QLabel("Nombre del reporte"),
            1, 0
        )

        self.nombre_prefijo = QLineEdit(
            "VG Det x SKU"
        )

        layout.addWidget(
            self.nombre_prefijo,
            1, 1
        )

        # Separador

        layout.addWidget(
            QLabel("Separador"),
            2, 0
        )

        self.separador = QLineEdit(
            " - "
        )

        layout.addWidget(
            self.separador,
            2, 1
        )

        # Subcarpeta

        layout.addWidget(
            QLabel("Subcarpeta"),
            3, 0
        )

        self.subcarpeta = QLineEdit(
            "HUB_Output"
        )

        layout.addWidget(
            self.subcarpeta,
            3, 1
        )

        # Inicialmente oculto

        self.panel_avanzadas.setVisible(False)

        layout_principal.addWidget(
            self.panel_avanzadas
        )

    def toggle_opciones_avanzadas(self, visible):

        self.panel_avanzadas.setVisible(
            visible
        )

        if visible:
            self.boton_avanzadas.setText(
                "⚙  Ocultar opciones avanzadas"
            )
        else:
            self.boton_avanzadas.setText(
                "⚙  Opciones avanzadas"
            )

    # =========================================================
    # CÁLCULO DE DÍAS
    # =========================================================

    def fecha_cambio(self):

        if not self.dias_transcurridos_manual:
            self.calcular_dias_transcurridos()

        if not self.dias_laborales_manual:
            self.calcular_dias_laborales()

    def calcular_dias(self):

        self.calcular_dias_transcurridos()
        self.calcular_dias_laborales()

    def calcular_dias_transcurridos(self):
        inicio = self.fecha_inicio.date()
        # el reporte es del día anterior, así que no contamos "hoy"
        final = self.fecha_final.date()

        dias_transcurridos = 0
        fecha = inicio

        while fecha <= final:
            # dayOfWeek(): 1=lunes ... 6=sábado, 7=domingo
            if fecha.dayOfWeek() <= 6:
                dias_transcurridos += 1
            fecha = fecha.addDays(1)

        if dias_transcurridos < 0:
            dias_transcurridos = 0

        self.dias_transcurridos.blockSignals(True)
        self.dias_transcurridos.setValue(dias_transcurridos)
        self.dias_transcurridos.blockSignals(False)

    def calcular_dias_laborales(self):
        final = self.fecha_final.date()

        # total de días laborales de todo el mes (lunes a sábado)
        primer_dia = QDate(final.year(), final.month(), 1)
        ultimo_dia = QDate(final.year(), final.month(), primer_dia.daysInMonth())

        dias_laborales = 0
        fecha = primer_dia

        while fecha <= ultimo_dia:
            if fecha.dayOfWeek() <= 6:
                dias_laborales += 1
            fecha = fecha.addDays(1)
        

        self.dias_laborales.blockSignals(True)
        self.dias_laborales.setValue(
            dias_laborales
        )
        self.dias_laborales.blockSignals(False)

    # =========================================================
    # MODIFICACIÓN MANUAL
    # =========================================================

    def dias_transcurridos_modificado(self):

        self.dias_transcurridos_manual = True

    def dias_laborales_modificado(self):

        self.dias_laborales_manual = True

    def restaurar_dias_transcurridos(self):

        self.dias_transcurridos_manual = False
        self.calcular_dias_transcurridos()

    def restaurar_dias_laborales(self):

        self.dias_laborales_manual = False
        self.calcular_dias_laborales()

    # =========================================================
    # GENERAR
    # =========================================================

    def generar_reporte(self):

        params = ReportParams(
            dias_transcurridos=self.dias_transcurridos.value(),
            dias_laborales=self.dias_laborales.value(),
            fecha_inicio=(
                self.fecha_inicio
                .date()
                .toString("yyyy-MM-dd")
            ),
            fecha_final=(
                self.fecha_final
                .date()
                .toString("yyyy-MM-dd")
            ),
            exportar_trimestre=(self.exportar_trimestre.isChecked()),
            fecha_sufijo=self.fecha_sufijo.text(),
            nombre_prefijo=self.nombre_prefijo.text(),
            separador=self.separador.text(),
            subcarpeta=self.subcarpeta.text()
        )

        print("Parámetros enviados:")
        print(params)

        resultado = execute(params)

        print(resultado)

    # =========================================================
    # ESTILOS
    # =========================================================

    def aplicar_estilos(self):

        self.setStyleSheet("""

            QDialog {
                background-color: #f5f6f8;
            }

            #windowTitle {
                font-size: 24px;
                font-weight: bold;
                color: #20242b;
            }

            #windowDescription {
                color: #6b7078;
                font-size: 13px;
            }

            QGroupBox {
                background-color: #222332;
                border: 1px solid #e1e4e8;
                border-radius: 8px;
                margin-top: 12px;
                padding: 15px;
                font-weight: bold;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 5px;
            }

            QDateEdit,
            QSpinBox,
            QLineEdit {
                background-color: #20242b;
                border: 1px solid #cfd3d8;
                border-radius: 5px;
                padding: 7px;
            }

            QDateEdit:focus,
            QSpinBox:focus,
            QLineEdit:focus {
                border: 1px solid #707780;
            }

            #advancedButton {
                text-align: left;
                border: none;
                background-color: transparent;
                color: #4e545c;
                padding: 8px 2px;
            }

            #advancedButton:hover {
                color: #20242b;
            }

            #advancedPanel {
                background-color: #20242b;
                border: 1px solid #e1e4e8;
                border-radius: 8px;
                padding: 10px;
            }

            #generateButton {
                background-color: #20242b;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-weight: bold;
            }

            #generateButton:hover {
                background-color: #343a43;
            }
            
        """)