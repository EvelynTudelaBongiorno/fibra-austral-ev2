"""¿Qué habría mostrado el tablero si se hubiera decidido distinto?

Estas funciones comparan la decisión tomada en limpieza.py con la alternativa
descartada. Se usan para el informe (decisiones éticas e impacto de cada problema)
y se ejecutan con: python manage.py exportar_graficos
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from .limpieza import DURACION_MAXIMA
from .secciones import META_DURACION, _ruta
from .utils import figura_a_imagen, numero, ACENTO, GRIS_OSCURO


def duracion_sin_filtrar(crudo):
    """La duración como número, pero conservando los valores imposibles."""
    sin_dup = crudo.drop_duplicates().reset_index(drop=True)
    return pd.to_numeric(sin_dup["duracion_min"].astype(str)
                         .str.replace("min", "", regex=False).str.strip(), errors="coerce")


def impactos(crudo, df):
    """Cuánto cambiaría cada resultado si el problema no se hubiera corregido."""
    sin_dup = crudo.drop_duplicates()
    resuelto_crudo = (sin_dup["resuelto"] == "Sí").mean() * 100
    canal_crudo = sin_dup["canal"].astype(str).value_counts()
    dur_bruta = duracion_sin_filtrar(crudo)
    sat_cruda = pd.to_numeric(crudo["satisfaccion"], errors="coerce")
    texto_dur = crudo["duracion_min"].apply(lambda v: isinstance(v, str)).sum()
    fechas_texto = crudo["fecha"].astype(str).str.contains("/").sum()
    return {
        "resolucion_limpia": df["es_resuelto"].mean() * 100,
        "resolucion_sin_homologar": resuelto_crudo,
        "telefono_sin_homologar": int(canal_crudo.get("Teléfono", 0)),
        "telefono_limpio": int((df["canal"] == "Teléfono").sum()),
        "categorias_canal_crudo": int(canal_crudo.size),
        "duracion_limpia": df["duracion_min"].mean(),
        "duracion_con_imposibles": dur_bruta.mean(),
        "duracion_maxima_cruda": dur_bruta.max(),
        "duracion_minima_cruda": dur_bruta.min(),
        "satisfaccion_limpia": df["satisfaccion"].mean(),
        "satisfaccion_con_fuera_escala": sat_cruda.mean(),
        "tickets_con_duplicados": len(crudo),
        "tickets_sin_duplicados": len(sin_dup),
        "duraciones_texto_perdidas": int(texto_dur),
        "fechas_texto": int(fechas_texto),
        "sin_respuesta": int(df["satisfaccion"].isna().sum()),
        "sin_respuesta_pct": df["satisfaccion"].isna().mean() * 100,
        "whatsapp_sin_respuesta_pct": df.loc[df["canal"] == "WhatsApp", "satisfaccion"]
                                        .isna().mean() * 100,
        "resolucion_solo_respondieron": df.loc[df["satisfaccion"].notna(), "es_resuelto"]
                                          .mean() * 100,
    }


def grafico_decision_duracion(crudo, df, carpeta=None):
    """Duración promedio por canal y por tipo de problema con las dos decisiones."""
    comparar = df[["canal", "tipo_problema", "duracion_min"]].copy()
    comparar["bruta"] = duracion_sin_filtrar(crudo).values

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.9),
                                 gridspec_kw={"width_ratios": [1, 1.4]})
    for ax, col in [(a1, "canal"), (a2, "tipo_problema")]:
        t = comparar.groupby(col)[["duracion_min", "bruta"]].mean().sort_values("duracion_min")
        y = np.arange(len(t))
        ax.barh(y + 0.19, t["duracion_min"], height=0.36, color=GRIS_OSCURO,
                label="Decisión tomada: imposibles quedan vacíos")
        ax.barh(y - 0.19, t["bruta"], height=0.36, color=ACENTO,
                label=f"Alternativa: conservar 0, negativos y > {DURACION_MAXIMA} min")
        for i, (a, b) in enumerate(zip(t["duracion_min"], t["bruta"])):
            ax.text(a + 0.2, i + 0.19, numero(a, 1), va="center", fontsize=8, color=GRIS_OSCURO)
            ax.text(b + 0.2, i - 0.19, numero(b, 1), va="center", fontsize=8, color=ACENTO)
        ax.set_yticks(y, t.index)
        ax.axvline(META_DURACION, color="#999999", linestyle="--", linewidth=1)
        ax.set_xlim(0, t.max().max() * 1.18)
        ax.set_xticks(range(0, int(t.max().max() * 1.18) + 1, 5))
        ax.set_xlabel("Duración promedio (min)")
        ax.grid(axis="y", visible=False)
    a1.set_title("Por canal", fontsize=10, color=GRIS_OSCURO, fontweight="normal")
    a2.set_title("Por tipo de problema", fontsize=10, color=GRIS_OSCURO, fontweight="normal")
    handles, labels = a1.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, fontsize=9,
               bbox_to_anchor=(0.5, -0.06))
    t_canal = comparar.groupby("canal")[["duracion_min", "bruta"]].mean()
    t_tipo = comparar.groupby("tipo_problema")[["duracion_min", "bruta"]].mean()
    cambia = t_tipo[(t_tipo["duracion_min"] <= META_DURACION) & (t_tipo["bruta"] > META_DURACION)]
    titulo = (f"Con los valores imposibles, {t_canal['bruta'].idxmin()} pasaría a ser el canal "
              f"más rápido y {cambia.index[0] if len(cambia) else 'ningún tipo'} dejaría de "
              f"cumplir la meta")
    fig.suptitle(titulo, x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    return {"titulo": titulo,
            "imagen": figura_a_imagen(fig, _ruta(carpeta, "e_decision_duracion.png")),
            "canal": t_canal, "tipo": t_tipo}
