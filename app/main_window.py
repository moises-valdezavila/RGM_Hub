from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
# Ventanas de tools
from app.windows.reporte_detalle import ReporteDetalleWindow



class ToolCard(QFrame):
    """
    Tarjeta que representa una herramienta dentro de RGM Hub.
    """

    def __init__(self, titulo, descripcion, callback):
        super().__init__()

        self.setObjectName("toolCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Icono
        icono = QLabel("📊")
        icono.setObjectName("toolIcon")

        # Título
        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("toolTitle")

        # Descripción
        label_descripcion = QLabel(descripcion)
        label_descripcion.setObjectName("toolDescription")
        label_descripcion.setWordWrap(True)

        # Botón
        boton = QPushButton("Abrir")
        boton.setObjectName("toolButton")
        boton.clicked.connect(callback)

        layout.addWidget(icono)
        layout.addWidget(label_titulo)
        layout.addWidget(label_descripcion)
        layout.addStretch()
        layout.addWidget(boton)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("RGM Hub")
        self.resize(1200, 750)

        self.crear_interfaz()
        self.aplicar_estilos()

    # =========================================================
    # INTERFAZ
    # =========================================================

    def crear_interfaz(self):

        central = QWidget()
        self.setCentralWidget(central)

        layout_principal = QHBoxLayout(central)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # -----------------------------------------------------
        # MENÚ LATERAL
        # -----------------------------------------------------

        self.crear_menu_lateral(layout_principal)

        # -----------------------------------------------------
        # CONTENIDO
        # -----------------------------------------------------

        self.crear_area_contenido(layout_principal)

    # =========================================================
    # MENÚ LATERAL
    # =========================================================

    def crear_menu_lateral(self, layout_principal):

        menu = QFrame()
        menu.setObjectName("sideBar")
        menu.setFixedWidth(220)

        layout = QVBoxLayout(menu)
        layout.setContentsMargins(15, 25, 15, 25)
        layout.setSpacing(8)

        # Logo / nombre
        titulo = QLabel("RGM Hub")
        titulo.setObjectName("appTitle")
        titulo.setAlignment(Qt.AlignCenter)

        layout.addWidget(titulo)
        layout.addSpacing(30)

        # Inicio
        boton_inicio = QPushButton("⌂   Inicio")
        boton_inicio.setObjectName("menuButton")
        boton_inicio.clicked.connect(self.mostrar_inicio)

        layout.addWidget(boton_inicio)

        # Reportes
        boton_reportes = QPushButton("▣   Reportes")
        boton_reportes.setObjectName("menuButton")
        boton_reportes.clicked.connect(self.mostrar_reportes)

        layout.addWidget(boton_reportes)

        # Inventario
        boton_inventario = QPushButton("▣   Datos / Bases")
        boton_inventario.setObjectName("menuButton")
        boton_inventario.clicked.connect(self.mostrar_inventario)

        layout.addWidget(boton_inventario)

        # Análisis
        boton_analisis = QPushButton("▣   Análisis")
        boton_analisis.setObjectName("menuButton")
        boton_analisis.clicked.connect(self.mostrar_analisis)

        layout.addWidget(boton_analisis)

        layout.addStretch()

        layout_principal.addWidget(menu)

    # =========================================================
    # ÁREA DE CONTENIDO
    # =========================================================

    def crear_area_contenido(self, layout_principal):

        contenedor = QWidget()

        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(35, 30, 35, 30)
        layout.setSpacing(20)

        # -----------------------------------------------------
        # Encabezado
        # -----------------------------------------------------

        self.titulo_seccion = QLabel()
        self.titulo_seccion.setObjectName("sectionTitle")

        self.descripcion_seccion = QLabel()
        self.descripcion_seccion.setObjectName("sectionDescription")

        layout.addWidget(self.titulo_seccion)
        layout.addWidget(self.descripcion_seccion)

        # -----------------------------------------------------
        # Área de herramientas
        # -----------------------------------------------------

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.contenedor_cards = QWidget()

        self.grid_cards = QGridLayout(self.contenedor_cards)
        self.grid_cards.setContentsMargins(0, 10, 0, 10)
        self.grid_cards.setHorizontalSpacing(20)
        self.grid_cards.setVerticalSpacing(20)

        self.scroll.setWidget(self.contenedor_cards)

        layout.addWidget(self.scroll)

        layout_principal.addWidget(contenedor)

        # Mostrar inicio al arrancar
        self.mostrar_inicio()

    # =========================================================
    # SECCIONES
    # =========================================================

    def limpiar_cards(self):

        while self.grid_cards.count():

            item = self.grid_cards.takeAt(0)

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def agregar_card(self, titulo, descripcion, callback):

        card = ToolCard(
            titulo=titulo,
            descripcion=descripcion,
            callback=callback,
        )

        # Por ahora colocamos máximo 3 cards por fila.
        cantidad = self.grid_cards.count()

        fila = cantidad // 3
        columna = cantidad % 3

        self.grid_cards.addWidget(card, fila, columna)

    # =========================================================
    # INICIO
    # =========================================================

    def mostrar_inicio(self):

        self.limpiar_cards()

        self.titulo_seccion.setText("Inicio")

        self.descripcion_seccion.setText(
            "Selecciona una herramienta para comenzar."
        )

        self.agregar_card(
            "Reporte detalle de ventas",
            "Genera el reporte detallado de ventas por sucursal.",
            self.abrir_reporte_detalle,
        )

    # =========================================================
    # REPORTES
    # =========================================================

    def mostrar_reportes(self):

        self.limpiar_cards()

        self.titulo_seccion.setText("Reportes")

        self.descripcion_seccion.setText(
            "Herramientas para generar reportes."
        )

        self.agregar_card(
            "Reporte detalle de ventas",
            "Genera el reporte detallado de ventas por sucursal.",
            self.abrir_reporte_detalle,
        )

    # =========================================================
    # INVENTARIO
    # =========================================================

    def mostrar_inventario(self):

        self.limpiar_cards()

        self.titulo_seccion.setText("Inventario")

        self.descripcion_seccion.setText(
            "Herramientas relacionadas con inventario."
        )

        # Todavía no tenemos herramientas aquí.

    # =========================================================
    # ANÁLISIS
    # =========================================================

    def mostrar_analisis(self):

        self.limpiar_cards()

        self.titulo_seccion.setText("Análisis")

        self.descripcion_seccion.setText(
            "Herramientas de análisis y métricas."
        )

        # Todavía no tenemos herramientas aquí.

    # =========================================================
    # HERRAMIENTAS
    # =========================================================

    def abrir_reporte_detalle(self):
        ventana = ReporteDetalleWindow(self)

        ventana.exec()

    # =========================================================
    # ESTILOS
    # =========================================================

    def aplicar_estilos(self):

        self.setStyleSheet("""

            QMainWindow {
                background-color: #f5f6f8;
            }

            #sideBar {
                background-color: #20242b;
            }

            #appTitle {
                color: white;
                font-size: 22px;
                font-weight: bold;
            }

            #menuButton {
                color: #d9dce1;
                background-color: transparent;
                border: none;
                text-align: left;
                padding: 12px;
                font-size: 14px;
                border-radius: 6px;
            }

            #menuButton:hover {
                background-color: #30353e;
                color: white;
            }

            #sectionTitle {
                font-size: 28px;
                font-weight: bold;
                color: #20242b;
            }

            #sectionDescription {
                font-size: 14px;
                color: #6b7078;
            }

            #toolCard {
                background-color: white;
                border: 1px solid #e1e4e8;
                border-radius: 10px;
                min-height: 180px;
            }

            #toolCard:hover {
                border: 1px solid #b9bec7;
            }

            #toolIcon {
                font-size: 30px;
            }

            #toolTitle {
                font-size: 17px;
                font-weight: bold;
                color: #20242b;
            }

            #toolDescription {
                font-size: 13px;
                color: #6b7078;
            }

            #toolButton {
                background-color: #20242b;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 9px;
            }

            #toolButton:hover {
                background-color: #343a43;
            }

            QScrollArea {
                background-color: transparent;
            }

        """)