"""Diagnóstico y limpieza del archivo de tickets de Fibra Austral.

Toda corrección se hace aquí, con pandas. El Excel original no se modifica:
cada vez que se arma el tablero, los datos crudos pasan por limpiar() y cada
decisión queda anotada en la bitácora que se muestra en la interfaz.
"""
import pandas as pd

HOJA = "tickets"
COLUMNAS = ["ticket", "fecha", "hora", "canal", "turno", "tipo_problema",
            "ejecutivo", "duracion_min", "resuelto", "satisfaccion"]

# ---------- diccionarios de homologación: variante en minúsculas → nombre oficial ----------
CANALES = {"teléfono": "Teléfono", "telefono": "Teléfono", "fono": "Teléfono",
           "chat": "Chat",
           "whatsapp": "WhatsApp", "wsp": "WhatsApp",
           "correo": "Correo", "e-mail": "Correo", "email": "Correo"}

# AM y PM se validaron contra la columna hora: todos los AM están entre 08 y 13 h
# (turno Mañana) y todos los PM entre 14 y 19 h (turno Tarde).
TURNOS = {"mañana": "Mañana", "am": "Mañana",
          "tarde": "Tarde", "pm": "Tarde",
          "noche": "Noche"}

PROBLEMAS = {"sin conexión": "Sin conexión", "sin conexion": "Sin conexión",
             "internet lento": "Internet lento", "lentitud": "Internet lento",
             "facturación": "Facturación", "facturacion": "Facturación",
             "cambio de plan": "Cambio de plan", "cambio plan": "Cambio de plan",
             "instalación": "Instalación", "instalacion": "Instalación",
             "router": "Router", "módem/router": "Router"}

RESUELTO = {"sí": "Sí", "si": "Sí", "s": "Sí",
            "no": "No", "n": "No"}

HOMOLOGAR = [("canal", CANALES), ("turno", TURNOS),
             ("tipo_problema", PROBLEMAS), ("resuelto", RESUELTO)]

# horas de inicio de cada turno, para validar la columna turno
HORAS_TURNO = {"Mañana": range(8, 14), "Tarde": range(14, 20),
               "Noche": [20, 21, 22, 23, 0, 1]}

DURACION_MAXIMA = 180   # minutos: sobre 3 horas no es una atención, es un error de registro


def diagnosticar(df):
    """Fotografía del archivo tal como llega, antes de tocarlo."""
    return {
        "filas": len(df),
        "columnas": df.shape[1],
        "duplicados": int(df.duplicated().sum()),
        "tickets_repetidos": int(df["ticket"].duplicated().sum()),
        "detalle": [
            {"columna": c,
             "tipo": str(df[c].dtype),
             "nulos": int(df[c].isna().sum()),
             "distintos": int(df[c].nunique())}
            for c in df.columns
        ],
    }


def homologar(serie, diccionario):
    """Quita espacios, pasa a minúsculas y reemplaza por el nombre oficial."""
    return serie.astype(str).str.strip().str.lower().map(diccionario)


def convertir_fechas(serie):
    """Lee fechas en dos formatos: aaaa-mm-dd (fecha de Excel) y dd/mm/aaaa (texto)."""
    texto = serie.astype(str).str[:10]
    con_barra = texto.str.contains("/")
    iso = pd.to_datetime(texto.where(~con_barra), format="%Y-%m-%d", errors="coerce")
    dmy = pd.to_datetime(texto.where(con_barra), format="%d/%m/%Y", errors="coerce")
    return iso.fillna(dmy)


def limpiar(df):
    """Devuelve los datos limpios, la bitácora y el detalle de la homologación."""
    df = df.copy()
    bitacora = []
    homologacion = []

    def anotar(problema, filas, decision):
        bitacora.append({"paso": len(bitacora) + 1, "problema": problema,
                         "filas": int(filas), "decision": decision})

    # 1 · filas duplicadas: el mismo ticket, con todos sus datos, registrado dos veces
    n = df.duplicated().sum()
    df = df.drop_duplicates().reset_index(drop=True)
    anotar("Filas duplicadas (mismo ticket y mismos datos)", n,
           "Se eliminan: es la misma atención contada dos veces")

    # 2 · homologación de las cuatro columnas de texto
    for columna, diccionario in HOMOLOGAR:
        original = df[columna].copy()
        df[columna] = homologar(original, diccionario)
        cambiadas = original.astype(str) != df[columna].astype(str)
        sin_traduccion = df[columna].isna() & original.notna()
        variantes = (pd.DataFrame({"original": original[cambiadas].astype(str),
                                   "oficial": df.loc[cambiadas, columna]})
                     .value_counts().reset_index(name="filas"))
        for v in variantes.itertuples():
            homologacion.append({"columna": columna, "original": repr(v.original),
                                 "oficial": v.oficial, "filas": int(v.filas)})
        anotar(f"Columna {columna} escrita de {original.nunique()} formas distintas",
               cambiadas.sum() - sin_traduccion.sum(),
               f"Se unifica a los {df[columna].nunique()} nombres oficiales")
        if sin_traduccion.any():
            anotar(f"Valor de {columna} no reconocido", sin_traduccion.sum(),
                   "Queda vacío: no se asigna una categoría inventada")

    # 3 · validación del turno contra la hora de inicio
    hora = pd.to_numeric(df["hora"].astype(str).str[:2], errors="coerce")
    coincide = pd.Series([h in HORAS_TURNO.get(t, []) for t, h in zip(df["turno"], hora)],
                         index=df.index)
    anotar("Turno que no coincide con la hora de inicio", (~coincide).sum(),
           "Se verifica: confirma que AM = Mañana y PM = Tarde")

    # 4 · fechas escritas como texto dd/mm/aaaa
    n = df["fecha"].astype(str).str.contains("/").sum()
    df["fecha"] = convertir_fechas(df["fecha"])
    anotar("Fecha escrita como texto dd/mm/aaaa", n,
           "Se convierte al mismo tipo fecha que el resto")
    fuera = df["fecha"].isna() | (df["fecha"].dt.year != 2025)
    if fuera.any():
        df = df[~fuera]
        anotar("Fecha ilegible o fuera de 2025", fuera.sum(),
               "Se elimina: no se puede ubicar en el período")

    # 5 · duración escrita como texto ("14.9 min")
    es_texto = df["duracion_min"].apply(lambda v: isinstance(v, str))
    df["duracion_min"] = pd.to_numeric(
        df["duracion_min"].astype(str).str.replace("min", "", regex=False).str.strip(),
        errors="coerce")
    anotar("Duración escrita como texto con la unidad «min»", es_texto.sum(),
           "Se quita la unidad y se convierte a número")
    vacias = df["duracion_min"].isna().sum()

    # 6 · duraciones imposibles: cero, negativas o de más de 3 horas
    imposible = (df["duracion_min"] <= 0) | (df["duracion_min"] > DURACION_MAXIMA)
    df.loc[imposible, "duracion_min"] = None
    anotar(f"Duración imposible: cero, negativa o mayor a {DURACION_MAXIMA} min",
           imposible.sum(),
           "Se deja vacía: el ticket existió y cuenta para demanda y resolución, "
           "pero no para el tiempo")

    # 7 · duración vacía en el archivo original
    anotar("Duración vacía en el archivo", vacias,
           "No se rellena: inventar un tiempo movería el promedio; la fila se conserva")

    # 8 · satisfacción fuera de la escala 1 a 7
    df["satisfaccion"] = pd.to_numeric(df["satisfaccion"], errors="coerce")
    sin_respuesta = df["satisfaccion"].isna().sum()
    fuera_escala = df["satisfaccion"].notna() & ~df["satisfaccion"].between(1, 7)
    df.loc[fuera_escala, "satisfaccion"] = None
    anotar("Satisfacción fuera de la escala 1 a 7 (0, 8 o 10)", fuera_escala.sum(),
           "Se deja vacía: no se sabe qué nota quiso poner el cliente")
    anotar("Satisfacción vacía: el cliente no respondió la encuesta", sin_respuesta,
           "No es un error: la fila se conserva y solo se excluye del promedio")

    # columnas de trabajo que usan los gráficos
    df["mes"] = df["fecha"].dt.month
    df["trimestre"] = df["fecha"].dt.quarter
    df["hora_num"] = pd.to_numeric(df["hora"].astype(str).str[:2], errors="coerce")
    df["es_resuelto"] = df["resuelto"] == "Sí"

    return df.reset_index(drop=True), bitacora, homologacion
