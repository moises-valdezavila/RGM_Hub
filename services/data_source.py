import os
from services.config import DEMO_MODE

if DEMO_MODE:
    from services.demo_data import (
        sp_vg_MSV,
        descargar_tabla,
        sp_inv,
    )
else:
    from services.to_sql import (
        sp_vg_MSV,
        descargar_tabla,
        sp_inv,
    )