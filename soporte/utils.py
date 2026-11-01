"""Estilo común de los gráficos y funciones de apoyo."""
import io
import base64
import logging
import matplotlib
matplotlib.use("Agg")      # dibuja sin abrir ventanas: obligatorio en un servidor
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns

# evita avisos repetidos si el equipo no tiene alguna de las fuentes de la lista
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

# Paleta: un solo color de acento para lo relevante y grises para el resto
ACENTO = "#D9480F"         # naranjo: lo que la gerencia debe mirar
GRIS = "#BDBDBD"           # el resto de las marcas
GRIS_OSCURO = "#5C5C5C"    # líneas de meta, textos secundarios
GRIS_MEDIO = "#8E8E8E"
ROJO_NO_CUMPLE = "#C62828"

# mapas de color para los mapas de calor: de casi blanco al acento
MAPA_ACENTO = LinearSegmentedColormap.from_list("acento", ["#F7F7F7", "#F2B494", ACENTO])
MAPA_ACENTO_INV = LinearSegmentedColormap.from_list("acento_inv", [ACENTO, "#F2B494", "#F7F7F7"])

sns.set_theme(style="whitegrid")
plt.rcParams.update({
    "font.family": ["Calibri", "Carlito", "Arial", "DejaVu Sans"],
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",     # el título-conclusión, alineado a la izquierda
    "axes.titlepad": 10,
    "axes.labelsize": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": "#CFCFCF",
    "axes.labelcolor": GRIS_OSCURO,
    "grid.color": "#ECECEC",
    "xtick.color": GRIS_OSCURO,
    "ytick.color": GRIS_OSCURO,
    "legend.frameon": False,
    "figure.dpi": 100,
})


def figura_a_imagen(fig, guardar_en=None):
    """Convierte la figura en texto base64 para el HTML.

    Si se indica guardar_en, también la exporta como PNG con savefig
    (así se generan las imágenes del informe, desde el mismo código del tablero).
    """
    if guardar_en:
        fig.savefig(guardar_en, format="png", dpi=200, bbox_inches="tight")
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buffer.getvalue()).decode()


def numero(valor, decimales=0):
    """Escribe un número al estilo chileno: 1.234,5"""
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def linea_meta(ax, valor, texto, horizontal=True, detras=False):
    """Dibuja la meta como línea discontinua gris oscura, con su rótulo.

    detras=True la deja detrás de las barras, para no tapar las etiquetas de valor."""
    if horizontal:
        ax.axhline(valor, color=GRIS_OSCURO, linestyle="--", linewidth=1.3,
                   zorder=0.9 if detras else 3)
        ax.annotate(texto, xy=(1, valor), xycoords=("axes fraction", "data"),
                    xytext=(0, 3), textcoords="offset points", ha="right", va="bottom",
                    fontsize=9, color=GRIS_OSCURO)
    else:
        ax.axvline(valor, color=GRIS_OSCURO, linestyle="--", linewidth=1.3, zorder=3)
        ax.annotate(texto, xy=(valor, 1), xycoords=("data", "axes fraction"),
                    xytext=(-4, -2), textcoords="offset points", ha="right", va="top",
                    fontsize=9, color=GRIS_OSCURO)
