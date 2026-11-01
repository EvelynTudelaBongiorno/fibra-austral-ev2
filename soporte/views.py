from io import StringIO
import pandas as pd
from django.shortcuts import render, redirect
from .limpieza import COLUMNAS, HOJA, diagnosticar, limpiar
from .secciones import indicadores, todos_los_graficos, grafico_homologacion
from .utils import numero

PERIODOS = [("anio", "Año completo"), ("1", "T1 · enero a marzo"),
            ("2", "T2 · abril a junio"), ("3", "T3 · julio a septiembre"),
            ("4", "T4 · octubre a diciembre")]
NIVELES = {1: "Nivel 1 · Una variable",
           2: "Nivel 2 · Dos variables",
           3: "Nivel 3 · Tres variables"}


def tablero(request):
    # 1 · llega un archivo: se lee con pandas directo desde la subida y se guarda en la sesión
    if request.method == "POST":
        archivo = request.FILES.get("archivo")
        if not archivo:
            return render(request, "soporte/subir.html",
                          {"error": "Elija el archivo Excel de tickets.", "columnas": COLUMNAS})
        try:
            crudo = pd.read_excel(archivo, sheet_name=HOJA)   # en memoria, no en disco
        except Exception:
            return render(request, "soporte/subir.html",
                          {"error": f"No se pudo leer la hoja «{HOJA}» del archivo. "
                                    f"Revise que sea el Excel de la mesa de ayuda.",
                           "columnas": COLUMNAS})
        faltan = [c for c in COLUMNAS if c not in crudo.columns]
        if faltan:
            return render(request, "soporte/subir.html",
                          {"error": f"Al archivo le faltan columnas: {', '.join(faltan)}",
                           "columnas": COLUMNAS})
        request.session["datos"] = crudo.to_json(orient="split", date_format="iso")
        request.session["archivo"] = archivo.name
        return redirect("tablero")

    # 2 · todavía no hay datos: se muestra el formulario de carga
    if "datos" not in request.session:
        return render(request, "soporte/subir.html", {"columnas": COLUMNAS})

    # 3 · hay datos: se recuperan crudos, se diagnostican y se limpian en cada visita
    crudo = pd.read_json(StringIO(request.session["datos"]), orient="split", dtype=False,
                         convert_dates=False)
    diagnostico = diagnosticar(crudo)
    df_anio, bitacora, homologacion = limpiar(crudo)

    # 4 · el filtro se aplica después de limpiar: todo el tablero usa los datos filtrados
    periodo = request.GET.get("periodo", "anio")
    if periodo not in dict(PERIODOS):
        periodo = "anio"
    trimestre = None if periodo == "anio" else int(periodo)
    df = df_anio if trimestre is None else df_anio[df_anio["trimestre"] == trimestre]

    # 5 · KPI y gráficos se calculan con los datos ya filtrados, agrupados por nivel
    graficos = todos_los_graficos(df)
    niveles = [{"nombre": NIVELES[n], "graficos": [g for g in graficos if g["nivel"] == n]}
               for n in (1, 2, 3)]

    previa = df[COLUMNAS].head(10).assign(
        fecha=df["fecha"].head(10).dt.strftime("%d/%m/%Y"),
        satisfaccion=df["satisfaccion"].head(10).map(
            lambda v: "" if pd.isna(v) else numero(v)),
        duracion_min=df["duracion_min"].head(10).map(
            lambda v: "" if pd.isna(v) else numero(v, 1)))

    contexto = {
        "archivo": request.session["archivo"],
        "hoja": HOJA,
        "periodo_texto": (f"{df['fecha'].min():%d/%m/%Y} al {df['fecha'].max():%d/%m/%Y}"),
        "periodos": PERIODOS,
        "periodo": periodo,
        "periodo_nombre": dict(PERIODOS)[periodo],
        "kpis": indicadores(df, df_anio, trimestre),
        "niveles": niveles,
        "diagnostico": diagnostico,
        "bitacora": bitacora,
        "homologacion": homologacion,
        "grafico_homologacion": grafico_homologacion(crudo, df_anio),
        "filas_originales": numero(len(crudo)),
        "filas_limpias": numero(len(df_anio)),
        "filas": numero(len(df)),
        "columnas": len(COLUMNAS),
        "vista_previa": previa.to_html(index=False, classes="tabla", na_rep="—", border=0),
    }
    return render(request, "soporte/tablero.html", contexto)


def reiniciar(request):
    """Olvida el archivo cargado para poder subir otro."""
    request.session.pop("datos", None)
    request.session.pop("archivo", None)
    return redirect("tablero")
