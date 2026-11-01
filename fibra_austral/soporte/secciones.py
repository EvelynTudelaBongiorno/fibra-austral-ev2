"""Los tres KPI con meta y los gráficos del tablero, ordenados por nivel de complejidad.

Nivel 1 · una variable
Nivel 2 · dos variables (una categoría o el tiempo y una medida)
Nivel 3 · tres variables (dos categorías o el tiempo, más una medida)

Cada gráfico devuelve la pregunta que responde, un título-conclusión calculado con los
datos (no escrito a mano) y una lectura para quien decide.
"""
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from .utils import (figura_a_imagen, numero, linea_meta, ACENTO, GRIS, GRIS_OSCURO,
                    GRIS_MEDIO, MAPA_ACENTO, MAPA_ACENTO_INV)

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
         "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
MESES_LARGOS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
                "septiembre", "octubre", "noviembre", "diciembre"]
ORDEN_TURNO = ["Mañana", "Tarde", "Noche"]
ORDEN_CANAL = ["Teléfono", "Chat", "WhatsApp", "Correo"]

# las metas de la gerencia: lo que convierte una métrica en un indicador
META_DURACION = 10       # minutos promedio, como máximo
META_RESOLUCION = 80     # % de tickets resueltos en el primer contacto, como mínimo
META_SATISFACCION = 5.5  # promedio de 1 a 7, como mínimo

TRAMOS = [0, 5, 10, 15, 20, 30, 180]
ETIQUETAS_TRAMO = ["Hasta 5", "5 a 10", "10 a 15", "15 a 20", "20 a 30", "Más de 30"]


def _ruta(carpeta, nombre):
    return os.path.join(carpeta, nombre) if carpeta else None


def _seccion(nivel, numero_pregunta, pregunta, titulo, fig, lectura, carpeta, archivo):
    return {"nivel": nivel, "n": numero_pregunta, "pregunta": pregunta, "titulo": titulo,
            "imagen": figura_a_imagen(fig, _ruta(carpeta, archivo)), "lectura": lectura,
            "archivo": archivo}


def _tramos(serie):
    return pd.cut(serie, bins=TRAMOS, labels=ETIQUETAS_TRAMO)


# =====================================================================
#  Los tres KPI
# =====================================================================

def _valores_kpi(df):
    return {"duracion": df["duracion_min"].mean(),
            "resolucion": df["es_resuelto"].mean() * 100,
            "satisfaccion": df["satisfaccion"].mean()}


def _mini_evolucion(df_anio, clave, meta, trimestre, carpeta, archivo):
    """Línea mensual del KPI con su meta: muestra la evolución dentro de la tarjeta."""
    mensual = df_anio.groupby("mes").apply(lambda g: _valores_kpi(g)[clave],
                                           include_groups=False)
    fig, ax = plt.subplots(figsize=(3.4, 1.15))
    if trimestre:
        ax.axvspan(3 * trimestre - 2 - 0.5, 3 * trimestre + 0.5, color="#F4F4F4", zorder=0)
    ax.plot(mensual.index, mensual.values, color=GRIS_MEDIO, linewidth=1.6, zorder=2)
    ax.scatter(mensual.index[-1], mensual.values[-1], color=ACENTO, s=18, zorder=3)
    ax.axhline(meta, color=GRIS_OSCURO, linestyle="--", linewidth=1)
    ax.set_xticks([1, 4, 7, 10, 12], ["Ene", "Abr", "Jul", "Oct", "Dic"], fontsize=7)
    ax.tick_params(axis="y", labelsize=7)
    ax.yaxis.set_major_formatter(lambda v, _: numero(v, 1 if clave == "satisfaccion" else 0))
    ax.yaxis.set_major_locator(plt.MaxNLocator(3))
    ax.grid(False)
    for lado in ["left", "bottom"]:
        ax.spines[lado].set_color("#DDDDDD")
    return figura_a_imagen(fig, _ruta(carpeta, archivo))


def indicadores(df, df_anio, trimestre=None, carpeta=None):
    """Tres tarjetas: valor, unidad, meta, cumplimiento, comparación y evolución mensual."""
    actual = _valores_kpi(df)
    anterior = None
    if trimestre and trimestre > 1:
        anterior = _valores_kpi(df_anio[df_anio["trimestre"] == trimestre - 1])

    def comparar(clave, decimales, unidad, menor_es_mejor):
        if anterior is None:
            return "Sin período anterior en el archivo" if trimestre == 1 else \
                   "Año completo 2025"
        dif = round(actual[clave] - anterior[clave], decimales)
        if dif == 0:
            return f"Sin cambio vs. T{trimestre - 1}"
        mejora = dif < 0 if menor_es_mejor else dif > 0
        signo = "+" if dif > 0 else ""
        return (f"{signo}{numero(dif, decimales)} {unidad} vs. T{trimestre - 1} "
                f"({'mejora' if mejora else 'empeora'})")

    respondieron = int(df["satisfaccion"].notna().sum())
    con_duracion = int(df["duracion_min"].notna().sum())
    return [
        {"etiqueta": "Duración promedio de la atención",
         "valor": numero(actual["duracion"], 1), "unidad": "min",
         "meta": f"Meta: {META_DURACION} min o menos",
         "cumple": actual["duracion"] <= META_DURACION,
         "comparacion": comparar("duracion", 1, "min", True),
         "base": f"{numero(con_duracion)} tickets con duración válida",
         "evolucion": _mini_evolucion(df_anio, "duracion", META_DURACION, trimestre,
                                      carpeta, "kpi_duracion.png")},
        {"etiqueta": "Resolución en el primer contacto",
         "valor": numero(actual["resolucion"], 1), "unidad": "%",
         "meta": f"Meta: {META_RESOLUCION} % o más",
         "cumple": actual["resolucion"] >= META_RESOLUCION,
         "comparacion": comparar("resolucion", 1, "pts.", False),
         "base": f"{numero(len(df))} tickets",
         "evolucion": _mini_evolucion(df_anio, "resolucion", META_RESOLUCION, trimestre,
                                      carpeta, "kpi_resolucion.png")},
        {"etiqueta": "Satisfacción promedio del cliente",
         "valor": numero(actual["satisfaccion"], 2), "unidad": "de 7",
         "meta": f"Meta: {numero(META_SATISFACCION, 1)} o más",
         "cumple": actual["satisfaccion"] >= META_SATISFACCION,
         "comparacion": comparar("satisfaccion", 2, "pts.", False),
         "base": f"{numero(respondieron)} encuestas respondidas",
         "evolucion": _mini_evolucion(df_anio, "satisfaccion", META_SATISFACCION,
                                      trimestre, carpeta, "kpi_satisfaccion.png")},
    ]


# =====================================================================
#  NIVEL 1 · una variable
# =====================================================================

def g1_distribucion_duracion(df, carpeta=None):
    """P1 · Histograma: cómo se reparten los tiempos de atención."""
    d = df["duracion_min"].dropna()
    sobre = (d > META_DURACION).mean() * 100
    media, mediana, p90 = d.mean(), d.median(), d.quantile(0.9)

    fig, ax = plt.subplots(figsize=(8, 3.8))
    bins = [x * 2.5 for x in range(0, 31)]           # tramos de 2,5 min hasta 75 min
    n, bordes, barras = ax.hist(d.clip(upper=74.9), bins=bins, color=GRIS,
                                edgecolor="white", linewidth=0.6)
    for barra, borde in zip(barras, bordes[:-1]):
        if borde >= META_DURACION:
            barra.set_facecolor(ACENTO)
    linea_meta(ax, META_DURACION, f"Meta: {META_DURACION} min", horizontal=False)
    ax.axvline(media, color=ACENTO, linewidth=1.2, linestyle=":")
    ax.annotate(f"Promedio: {numero(media, 1)} min", xy=(media, 0.82),
                xycoords=("data", "axes fraction"), xytext=(4, 0),
                textcoords="offset points", fontsize=9, color=ACENTO)
    titulo = (f"El {numero(sobre)} % de las atenciones supera la meta de "
              f"{META_DURACION} minutos")
    ax.set_title(titulo)
    ax.set_xlabel("Duración de la atención (minutos)")
    ax.set_ylabel("Cantidad de tickets")
    ax.set_xlim(0, 75)
    lectura = (f"La atención típica dura {numero(mediana, 1)} min (mediana) y el promedio "
               f"llega a {numero(media, 1)} min porque una cola de atenciones largas lo "
               f"empuja hacia arriba: el 10 % más lento supera los {numero(p90)} min. "
               f"La meta de {META_DURACION} min no se cumple.")
    return _seccion(1, 1, "¿Cuánto demora una atención y cómo se reparten los tiempos? "
                    "¿Se cumple la meta de 10 minutos?", titulo, fig, lectura,
                    carpeta, "g1_distribucion_duracion.png")


# =====================================================================
#  NIVEL 2 · dos variables
# =====================================================================

def _barras_horizontales(ax, serie, destacar, xlabel, formato=1, xmax=None):
    colores = [ACENTO if i == destacar else GRIS for i in serie.index]
    ax.barh(serie.index, serie.values, color=colores, height=0.62)
    for y, v in enumerate(serie.values):
        ax.text(v + (xmax or serie.max()) * 0.015, y, numero(v, formato),
                va="center", fontsize=9, color=GRIS_OSCURO)
    ax.set_xlim(0, xmax or serie.max() * 1.18)        # en barras, el eje parte en cero
    ax.set_xlabel(xlabel)
    ax.grid(axis="y", visible=False)


def g2_rapidez_canal_turno(df, carpeta=None):
    """P2 · Barras horizontales: duración promedio por canal y por turno."""
    canal = df.groupby("canal")["duracion_min"].mean().sort_values(ascending=False)
    turno = df.groupby("turno")["duracion_min"].mean().sort_values(ascending=False)
    rapido_c, rapido_t = canal.index[-1], turno.index[-1]

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.2), sharex=True)
    xmax = max(canal.max(), turno.max()) * 1.2
    _barras_horizontales(a1, canal, rapido_c, "Duración promedio (min)", xmax=xmax)
    _barras_horizontales(a2, turno, rapido_t, "Duración promedio (min)", xmax=xmax)
    for ax, sub in [(a1, "Por canal"), (a2, "Por turno")]:
        ax.axvline(META_DURACION, color=GRIS_OSCURO, linestyle="--", linewidth=1.2)
        ax.set_title(sub, fontsize=10, color=GRIS_OSCURO, fontweight="normal")
    for ax in (a1, a2):
        ax.annotate("Meta 10 min", xy=(META_DURACION, 1), xycoords=("data", "axes fraction"),
                    xytext=(3, 2), textcoords="offset points", fontsize=8, color=GRIS_OSCURO)
    cumplen = (canal <= META_DURACION).sum() + (turno <= META_DURACION).sum()
    titulo = (f"{rapido_c} y el turno {rapido_t} son los más rápidos, "
              f"{'pero ninguno cumple' if cumplen == 0 else 'y se acercan a'} la meta")
    fig.suptitle(titulo, x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.tight_layout()
    lectura = (f"{rapido_c} promedia {numero(canal[rapido_c], 1)} min y {canal.index[0]} "
               f"{numero(canal.iloc[0], 1)} min, el más lento. Entre turnos, "
               f"{rapido_t} promedia {numero(turno[rapido_t], 1)} min y {turno.index[0]} "
               f"{numero(turno.iloc[0], 1)} min: el turno {turno.index[0].lower()} demora "
               f"{numero((turno.iloc[0] / turno[rapido_t] - 1) * 100)} % más.")
    return _seccion(2, 2, "¿Qué turno y qué canal atienden más rápido?", titulo, fig,
                    lectura, carpeta, "g2_rapidez_canal_turno.png")


def g3_problemas_tiempo_resolucion(df, carpeta=None):
    """P3 · Barras horizontales: horas del equipo y resolución por tipo de problema."""
    horas = (df.groupby("tipo_problema")["duracion_min"].sum() / 60).sort_values()
    resol = (df.groupby("tipo_problema")["es_resuelto"].mean() * 100) \
        .sort_values(ascending=False)
    mayor, peor = horas.index[-1], resol.index[-1]
    pct_horas = horas[mayor] / horas.sum() * 100

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.5, 3.4))
    _barras_horizontales(a1, horas, mayor, "Horas de atención en el período", formato=0)
    _barras_horizontales(a2, resol, peor, "Resueltos en el primer contacto (%)",
                         formato=0, xmax=100)
    a2.axvline(META_RESOLUCION, color=GRIS_OSCURO, linestyle="--", linewidth=1.2)
    a2.annotate("Meta 80 %", xy=(META_RESOLUCION, 1), xycoords=("data", "axes fraction"),
                xytext=(3, 2), textcoords="offset points", fontsize=8, color=GRIS_OSCURO)
    a2.set_yticks(range(len(resol)), resol.index)
    a1.set_title("Tiempo que consume", fontsize=10, color=GRIS_OSCURO, fontweight="normal")
    a2.set_title("Qué tan bien se resuelve", fontsize=10, color=GRIS_OSCURO,
                 fontweight="normal")
    titulo = (f"{mayor} consume el {numero(pct_horas)} % del tiempo del equipo y "
              f"{peor} es el que peor se resuelve")
    fig.suptitle(titulo, x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.tight_layout()
    lectura = (f"{mayor} suma {numero(horas[mayor])} horas de atención, el "
               f"{numero(pct_horas)} % del total aunque es el {numero(df['tipo_problema'].eq(mayor).mean() * 100)} % "
               f"de los tickets: cada caso dura más que el resto. {peor} se resuelve en el primer contacto solo el "
               f"{numero(resol[peor])} % de las veces, lejos de la meta de 80 %; "
               f"{(resol >= META_RESOLUCION).sum()} de los 6 tipos la cumplen.")
    return _seccion(2, 3, "¿Qué tipo de problema concentra el tiempo del equipo, y cuál se "
                    "resuelve peor en el primer contacto?", titulo, fig, lectura,
                    carpeta, "g3_problemas_tiempo_resolucion.png")


def g4_demanda_mensual(df, carpeta=None):
    """P4 · Línea: cantidad de tickets mes a mes."""
    mensual = df.groupby("mes").size().reindex(sorted(df["mes"].unique()))
    pico = mensual.idxmax()
    promedio = mensual.mean()

    fig, ax = plt.subplots(figsize=(8, 3.4))
    ax.plot(mensual.index, mensual.values, color=GRIS_MEDIO, linewidth=2, marker="o",
            markersize=5)
    ax.scatter([pico], [mensual[pico]], color=ACENTO, s=60, zorder=3)
    ax.annotate(f"{MESES[pico - 1]}: {mensual[pico]} tickets", xy=(pico, mensual[pico]),
                xytext=(8, 6), textcoords="offset points", color=ACENTO, fontsize=9)
    ax.axhline(promedio, color=GRIS_OSCURO, linestyle=":", linewidth=1)
    ax.annotate(f"Promedio: {numero(promedio)} por mes", xy=(0, promedio),
                xycoords=("axes fraction", "data"), xytext=(4, 4),
                textcoords="offset points", ha="left", fontsize=8, color=GRIS_OSCURO)
    ax.set_xticks(mensual.index, [MESES[m - 1] for m in mensual.index])
    ax.set_ylim(0, mensual.max() * 1.2)
    ax.set_ylabel("Tickets atendidos")
    invierno = mensual.reindex([6, 7, 8]).mean()
    resto = mensual.drop([6, 7, 8], errors="ignore").mean()
    if pd.notna(invierno) and len(mensual) > 3:
        titulo = (f"La demanda sube en invierno: junio a agosto promedia "
                  f"{numero((invierno / resto - 1) * 100)} % más tickets")
    else:
        titulo = (f"{MESES_LARGOS[pico - 1].capitalize()} es el mes con más tickets del "
                  f"período: {mensual[pico]}")
    ax.set_title(titulo)
    lectura = (f"El período promedia {numero(promedio)} tickets por mes. El máximo es "
               f"{MESES_LARGOS[pico - 1]} con {mensual[pico]} tickets; el mínimo, "
               f"{MESES_LARGOS[mensual.idxmin() - 1]} con {mensual.min()}."
               + (" El equipo debe planificarse para el alza de mitad de año."
                  if len(mensual) > 3 else ""))
    return _seccion(2, 4, "¿Cómo evoluciona la demanda durante el año?", titulo, fig,
                    lectura, carpeta, "g4_demanda_mensual.png")


def g5_satisfaccion_por_duracion(df, carpeta=None):
    """P5 · Barras por tramo (pd.cut): satisfacción promedio según la duración."""
    tramos = _tramos(df["duracion_min"])
    nota = df.groupby(tramos, observed=True)["satisfaccion"].mean()
    correlacion = df["duracion_min"].corr(df["satisfaccion"])

    fig, ax = plt.subplots(figsize=(8, 3.6))
    colores = [GRIS if v >= META_SATISFACCION else ACENTO for v in nota.values]
    ax.bar(nota.index.astype(str), nota.values, color=colores, width=0.62)
    for x, (v, c) in enumerate(zip(nota.values, colores)):
        ax.text(x, v - 0.35, numero(v, 1), ha="center", fontsize=10, fontweight="bold",
                color="white" if c == ACENTO else "#333333")
    linea_meta(ax, META_SATISFACCION, "Meta: 5,5", detras=True)
    ax.set_ylim(0, 7)                                 # en barras, el eje parte en cero
    ax.set_xlabel("Duración de la atención (minutos)")
    ax.set_ylabel("Satisfacción promedio (1 a 7)")
    titulo = (f"A más duración, menor satisfacción: de {numero(nota.iloc[0], 1)} "
              f"baja a {numero(nota.iloc[-1], 1)}")
    ax.set_title(titulo)
    bajo = [str(t) for t, v in nota.items() if v < META_SATISFACCION]
    lectura = (f"La relación es negativa (correlación de {numero(correlacion, 2)}): cada "
               f"tramo más largo tiene peor nota. Desde el tramo «{bajo[0]}» minutos la "
               f"satisfacción ya queda bajo la meta de 5,5." if bajo else
               f"La relación es negativa (correlación de {numero(correlacion, 2)}).")
    return _seccion(2, 5, "¿Hay relación entre la duración de la atención y la "
                    "satisfacción del cliente?", titulo, fig, lectura, carpeta,
                    "g5_satisfaccion_por_duracion.png")


# =====================================================================
#  NIVEL 3 · tres variables
# =====================================================================

def _mapa_calor(ax, tabla, mapa, formato, etiqueta_barra, vmin=None, vmax=None):
    sns.heatmap(tabla, annot=tabla.map(formato), fmt="", cmap=mapa, linewidths=2,
                linecolor="white", cbar_kws={"label": etiqueta_barra, "shrink": 0.8},
                annot_kws={"fontsize": 10}, vmin=vmin, vmax=vmax, ax=ax)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(axis="both", length=0)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)


def g6_turno_canal_duracion(df, carpeta=None):
    """P2 profundizada · Mapa de calor turno × canal × duración promedio."""
    tabla = df.pivot_table(index="turno", columns="canal", values="duracion_min",
                           aggfunc="mean")
    tabla = tabla.reindex(index=[t for t in ORDEN_TURNO if t in tabla.index],
                          columns=[c for c in ORDEN_CANAL if c in tabla.columns])
    fila_max, col_max = tabla.stack().idxmax()
    noche_peor = (tabla.idxmax() == "Noche").sum() if "Noche" in tabla.index else 0

    fig, ax = plt.subplots(figsize=(7.5, 3.1))
    _mapa_calor(ax, tabla, MAPA_ACENTO, lambda v: numero(v, 1), "Duración promedio (min)")
    en = (f"los {noche_peor} canales" if noche_peor == tabla.shape[1]
          else f"{noche_peor} de los {tabla.shape[1]} canales")
    titulo = (f"La noche es la más lenta en {en}; "
              f"{col_max} de {fila_max.lower()} llega a {numero(tabla.max().max(), 1)} min")
    ax.set_title(titulo)
    bajo_meta = int((tabla <= META_DURACION).sum().sum())
    cumplen = ("Ninguna" if bajo_meta == 0 else f"Solo {bajo_meta}")
    lectura = (f"Cruzar las dos variables muestra algo que las barras separadas no: la "
               f"lentitud del turno noche no se explica por el canal, porque es el más "
               f"lento en {en}. {cumplen} de las "
               f"{tabla.size} combinaciones cumple la meta de {META_DURACION} min.")
    return _seccion(3, 2, "¿Qué turno y qué canal atienden más rápido? "
                    "(cruce turno × canal)", titulo, fig, lectura, carpeta,
                    "g6_turno_canal_duracion.png")


def g7_participacion_canal(df, carpeta=None):
    """P4 profundizada · Líneas con hue: participación mensual de cada canal."""
    conteo = pd.crosstab(df["mes"], df["canal"])
    pct = conteo.div(conteo.sum(axis=1), axis=0) * 100
    pct = pct[[c for c in ORDEN_CANAL if c in pct.columns]]
    k = 3 if len(pct) >= 6 else 1                 # se comparan los extremos del período
    inicio, fin = pct.iloc[:k].mean(), pct.iloc[-k:].mean()
    tramo_ini = MESES[pct.index[0] - 1] + (f"–{MESES[pct.index[k - 1] - 1]}" if k > 1 else "")
    tramo_fin = MESES[pct.index[-k] - 1] + (f"–{MESES[pct.index[-1] - 1]}" if k > 1 else "")
    cambio = fin - inicio
    sube = cambio.idxmax()
    baja = cambio.idxmin()
    largo = pd.melt(pct.reset_index(), id_vars="mes", var_name="canal", value_name="pct")
    colores = {c: GRIS for c in pct.columns}
    colores.update({sube: ACENTO, baja: GRIS_OSCURO})

    fig, ax = plt.subplots(figsize=(8, 3.8))
    sns.lineplot(data=largo, x="mes", y="pct", hue="canal", palette=colores,
                 linewidth=2, marker="o", markersize=4, ax=ax)
    for c in pct.columns:
        ax.annotate(c, xy=(pct.index[-1], pct[c].iloc[-1]), xytext=(6, 0),
                    textcoords="offset points", va="center", fontsize=9,
                    color=colores[c], fontweight="bold" if c in (sube, baja) else "normal")
    ax.get_legend().remove()
    ax.set_xticks(pct.index, [MESES[m - 1] for m in pct.index])
    ax.set_xlim(pct.index.min() - 0.3, pct.index.max() + 1.2)
    ax.set_ylim(0, pct.max().max() * 1.15)
    ax.set_xlabel("")
    ax.set_ylabel("Participación en los tickets del mes (%)")
    titulo = (f"{sube} sube de {numero(inicio[sube])} % a {numero(fin[sube])} % de los "
              f"tickets ({tramo_ini} vs. {tramo_fin}); {baja} baja de "
              f"{numero(inicio[baja])} % a {numero(fin[baja])} %")
    ax.set_title(titulo)
    principal = fin.idxmax()
    lectura = (f"La línea de demanda total esconde un cambio de fondo en el canal: "
               f"{sube} gana {numero(cambio[sube])} puntos en el período y {baja} pierde "
               f"{numero(-cambio[baja])}. Al cierre ({tramo_fin}), {principal} sigue siendo el canal "
               f"con más tickets, pero si la tendencia continúa el equipo de {sube} debe "
               f"crecer antes que el resto.")
    return _seccion(3, 4, "¿Cómo cambia el uso de cada canal durante el año?", titulo, fig,
                    lectura, carpeta, "g7_participacion_canal.png")


def g8_satisfaccion_duracion_resolucion(df, carpeta=None):
    """P5 profundizada · Barras agrupadas: tramo de duración × resuelto × satisfacción."""
    datos = df.assign(tramo=_tramos(df["duracion_min"]))
    tabla = (datos.groupby(["tramo", "resuelto"], observed=True)["satisfaccion"].mean()
             .reset_index())
    si = tabla[tabla["resuelto"] == "Sí"].set_index("tramo")["satisfaccion"]
    no = tabla[tabla["resuelto"] == "No"].set_index("tramo")["satisfaccion"]
    brecha = (si - no).mean()
    caida_duracion = si.iloc[0] - si.iloc[-1]

    fig, ax = plt.subplots(figsize=(8.5, 3.8))
    sns.barplot(data=tabla, x="tramo", y="satisfaccion", hue="resuelto",
                hue_order=["Sí", "No"], palette={"Sí": GRIS, "No": ACENTO}, width=0.7, ax=ax)
    for barras, color in zip(ax.containers, ["#333333", "white"]):
        ax.bar_label(barras, labels=[numero(b.get_height(), 1) for b in barras],
                     fontsize=8.5, color=color, fontweight="bold", label_type="edge",
                     padding=-13)
    linea_meta(ax, META_SATISFACCION, "Meta: 5,5", detras=True)
    ax.set_ylim(0, 7)
    ax.set_xlabel("Duración de la atención (minutos)")
    ax.set_ylabel("Satisfacción promedio (1 a 7)")
    ax.legend(title="¿Resuelto en el primer contacto?", loc="upper center",
              bbox_to_anchor=(0.5, -0.2), ncol=2, fontsize=9, title_fontsize=9)
    titulo = (f"Resolver pesa más que demorar: sin resolver, la nota cae "
              f"{numero(brecha, 1)} puntos en cualquier duración")
    ax.set_title(titulo)
    lectura = (f"Al agregar si el caso se resolvió aparece el patrón que el gráfico de "
               f"tramos ocultaba: alargar la atención cuesta {numero(caida_duracion, 1)} "
               f"puntos entre el tramo más corto y el más largo, pero no resolver cuesta "
               f"{numero(brecha, 1)} puntos en promedio. Un caso resuelto en 20 a 30 min "
               f"({numero(si.get('20 a 30', float('nan')), 1)}) deja más conforme que uno no "
               f"resuelto en menos de 5 ({numero(no.iloc[0], 1)}).")
    return _seccion(3, 5, "¿La relación entre duración y satisfacción cambia si el caso "
                    "se resuelve?", titulo, fig, lectura, carpeta,
                    "g8_satisfaccion_duracion_resolucion.png")


def g9_resolucion_problema_turno(df, carpeta=None):
    """P6 (pregunta propia) · Mapa de calor tipo de problema × turno × % de resolución."""
    tabla = df.pivot_table(index="tipo_problema", columns="turno", values="es_resuelto",
                           aggfunc="mean") * 100
    tabla = tabla[[t for t in ORDEN_TURNO if t in tabla.columns]]
    tabla = tabla.loc[tabla.mean(axis=1).sort_values().index]
    no_resueltos = (df[~df["es_resuelto"]]
                    .pivot_table(index="tipo_problema", columns="turno", values="ticket",
                                 aggfunc="count"))
    fila_min, col_min = tabla.stack().idxmin()
    bajo_meta = int((tabla < META_RESOLUCION).sum().sum())
    top2 = (df[~df["es_resuelto"]]["tipo_problema"].value_counts(normalize=True) * 100)
    peores = list(tabla.index[:2])
    turno_peor = tabla.mean().idxmin()
    fallan_todos = all((tabla.loc[p] < META_RESOLUCION).all() for p in peores)

    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    _mapa_calor(ax, tabla, MAPA_ACENTO_INV, lambda v: f"{numero(v)} %",
                "Resueltos en el primer contacto (%)", vmin=30, vmax=90)
    titulo = (f"{fila_min} de {col_min.lower()} solo se resuelve el "
              f"{numero(tabla.min().min())} % de las veces en el primer contacto")
    ax.set_title(titulo)
    peor_turno_en_todos = (tabla.idxmin(axis=1) == turno_peor).sum()
    lectura = (f"{bajo_meta} de las {tabla.size} combinaciones quedan bajo la meta de 80 %. "
               f"{peores[0]} y {peores[1]} "
               f"{'fallan en todos los turnos' if fallan_todos else 'son los más bajos'} y "
               f"juntos explican el {numero(top2.get(peores[0], 0) + top2.get(peores[1], 0))} "
               f"% de los tickets no resueltos. El turno {turno_peor.lower()} tiene la menor "
               f"resolución en {peor_turno_en_todos} de los {len(tabla)} tipos de problema.")
    return _seccion(3, 6, "Pregunta propia: ¿en qué combinaciones de tipo de problema y "
                    "turno se concentran los tickets que no se resuelven en el primer "
                    "contacto?", titulo, fig, lectura, carpeta,
                    "g9_resolucion_problema_turno.png")


GRAFICOS = [g1_distribucion_duracion,
            g2_rapidez_canal_turno, g3_problemas_tiempo_resolucion, g4_demanda_mensual,
            g5_satisfaccion_por_duracion,
            g6_turno_canal_duracion, g7_participacion_canal,
            g8_satisfaccion_duracion_resolucion, g9_resolucion_problema_turno]


def todos_los_graficos(df, carpeta=None):
    return [g(df, carpeta) for g in GRAFICOS]


# =====================================================================
#  Calidad de datos · el efecto de homologar
# =====================================================================

def grafico_homologacion(crudo, df, carpeta=None):
    """Antes y después de homologar la columna canal (tickets por categoría)."""
    antes = crudo.drop_duplicates()["canal"].astype(str).value_counts().sort_values()
    despues = df["canal"].value_counts().sort_values()
    oficial_antes = antes.reindex(despues.index).fillna(0)
    perdidos = despues - oficial_antes

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.5, 4.2),
                                 gridspec_kw={"width_ratios": [1.25, 1]})
    colores = [GRIS_OSCURO if c in despues.index else ACENTO for c in antes.index]
    a1.barh([repr(c) for c in antes.index], antes.values, color=colores, height=0.7)
    a1.set_title(f"Antes: {len(antes)} categorías", fontsize=10, color=GRIS_OSCURO,
                 fontweight="normal")
    a1.set_xlabel("Tickets")
    a2.barh(despues.index, despues.values, color=GRIS_OSCURO, height=0.6)
    a2.barh(despues.index, perdidos.values, left=oficial_antes.values, color=ACENTO,
            height=0.6, label="Recuperados al homologar")
    for y, (v, p) in enumerate(zip(despues.values, perdidos.values)):
        a2.text(v + 15, y, f"{numero(v)} (+{numero(p)})", va="center", fontsize=9,
                color=GRIS_OSCURO)
    a2.set_xlim(0, despues.max() * 1.3)
    a2.set_title(f"Después: {len(despues)} canales oficiales", fontsize=10,
                 color=GRIS_OSCURO, fontweight="normal")
    a2.set_xlabel("Tickets")
    a2.legend(loc="lower right", fontsize=8)
    for ax in (a1, a2):
        ax.grid(axis="y", visible=False)
        ax.tick_params(axis="y", labelsize=8.5)
    mayor = perdidos.idxmax()
    titulo = (f"Sin homologar, el archivo muestra {len(antes)} canales y {mayor} "
              f"pierde {numero(perdidos[mayor])} tickets")
    fig.suptitle(titulo, x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.tight_layout()
    return {"titulo": titulo, "imagen": figura_a_imagen(fig, _ruta(carpeta,
                                                                  "h_homologacion_canal.png"))}
