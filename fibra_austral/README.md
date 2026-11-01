# Fibra Austral · Tablero de la mesa de ayuda

Aplicación web en Django que recibe el archivo de tickets de la mesa de ayuda de Fibra Austral,
lo diagnostica y lo limpia con pandas, y presenta un tablero con tres indicadores con meta y
nueve gráficos de seaborn/matplotlib generados en el servidor, ordenados por nivel de complejidad.

Evaluación N°2 · Visualización de Datos · INACAP. Datos ficticios con fines académicos.

## Requisitos

- Python 3.11 o superior
- Las librerías de `requirements.txt` (Django, pandas, numpy, matplotlib, seaborn y openpyxl,
  que pandas necesita para leer archivos Excel)

## Cómo levantar la aplicación

En Windows:

```
cd fibra_austral
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

En Mac o Linux: `python3 -m venv venv` y `source venv/bin/activate`.

Luego:

1. Abrir http://127.0.0.1:8000/ en el navegador.
2. Seleccionar el archivo `datos/soporte_fibra_austral_2025.xlsx` y presionar **Generar tablero**.
3. Usar el selector **Período** para ver el año completo o un trimestre.
4. **Cargar otro archivo** borra los datos de la sesión y vuelve al formulario.

`migrate` es obligatorio: crea la tabla de sesiones en la que se guardan los datos leídos, para
que el filtro funcione sin volver a subir el archivo.

## Cómo funciona

1. El Excel se sube con un formulario POST (`enctype="multipart/form-data"` y `csrf_token`) y se
   lee con `pd.read_excel` directamente desde la subida. `FILE_UPLOAD_HANDLERS` usa solo el
   manejador en memoria, por lo que el archivo nunca se escribe en una carpeta del servidor.
2. Los datos crudos se guardan en la sesión. El Excel original no se corrige a mano: en cada
   visita pasan por `limpiar()`, que corrige los problemas y anota cada decisión en la bitácora.
3. El filtro de período (GET) se aplica **después** de limpiar; KPI, gráficos y vista previa usan
   los datos filtrados.

## Estructura

```
fibra_austral/
├── config/                  # configuración del proyecto Django
├── datos/
│   └── soporte_fibra_austral_2025.xlsx   # archivo original del caso, sin modificar
├── informe/graficos/        # PNG exportados con savefig para el informe
├── soporte/
│   ├── limpieza.py          # diagnosticar() y limpiar(): datos limpios + bitácora + homologación
│   ├── secciones.py         # los 3 KPI con meta y los 9 gráficos (niveles 1, 2 y 3)
│   ├── comparaciones.py     # qué habría mostrado el tablero con otra decisión de limpieza
│   ├── utils.py             # estilo común de los gráficos, figura_a_imagen y numero
│   ├── views.py             # carga, sesión, filtro y armado del tablero
│   ├── urls.py
│   ├── management/commands/exportar_graficos.py
│   └── templates/soporte/   # base.html, subir.html y tablero.html
├── manage.py
└── requirements.txt
```

## Exportar los gráficos para el informe

```
python manage.py exportar_graficos datos/soporte_fibra_austral_2025.xlsx
```

Genera los PNG con `savefig` en `informe/graficos/` usando las mismas funciones que dibujan el
tablero, junto con `resumen.json` (diagnóstico, bitácora y cifras de impacto).

## Metas del caso

| Indicador | Meta |
|---|---|
| Duración promedio de la atención | 10 minutos o menos |
| Resolución en el primer contacto | 80 % o más de los tickets |
| Satisfacción promedio del cliente | 5,5 o más (escala 1 a 7) |
