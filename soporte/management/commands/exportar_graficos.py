"""Exporta con savefig los gráficos del tablero, para usarlos en el informe.

Uso:  python manage.py exportar_graficos datos/soporte_fibra_austral_2025.xlsx
Las imágenes quedan en la carpeta informe/graficos y salen del mismo código que
dibuja el tablero, por lo que siempre corresponden a la aplicación entregada.
"""
import json
import os
import pandas as pd
from django.core.management.base import BaseCommand
from soporte.limpieza import HOJA, diagnosticar, limpiar
from soporte.secciones import indicadores, todos_los_graficos, grafico_homologacion
from soporte.comparaciones import impactos, grafico_decision_duracion


class Command(BaseCommand):
    help = "Exporta los gráficos del tablero como PNG (savefig) en informe/graficos"

    def add_arguments(self, parser):
        parser.add_argument("archivo", help="Ruta del Excel de tickets")
        parser.add_argument("--carpeta", default=os.path.join("informe", "graficos"))

    def handle(self, *args, **opciones):
        carpeta = opciones["carpeta"]
        os.makedirs(carpeta, exist_ok=True)
        crudo = pd.read_excel(opciones["archivo"], sheet_name=HOJA)
        df, bitacora, homologacion = limpiar(crudo)

        kpis = indicadores(df, df, None, carpeta)
        graficos = todos_los_graficos(df, carpeta)
        grafico_homologacion(crudo, df, carpeta)
        etica = grafico_decision_duracion(crudo, df, carpeta)

        resumen = {
            "diagnostico": diagnosticar(crudo),
            "bitacora": bitacora,
            "homologacion": homologacion,
            "kpis": [{k: (bool(v) if k == "cumple" else v) for k, v in kpi.items()
                      if k != "evolucion"} for kpi in kpis],
            "graficos": [{k: v for k, v in g.items() if k != "imagen"} for g in graficos],
            "impactos": {k: float(v) for k, v in impactos(crudo, df).items()},
            "etica_titulo": etica["titulo"],
        }
        with open(os.path.join(carpeta, "resumen.json"), "w", encoding="utf-8") as f:
            json.dump(resumen, f, ensure_ascii=False, indent=2)
        self.stdout.write(self.style.SUCCESS(
            f"{len(graficos) + 5} imágenes y resumen.json exportados en {carpeta}"))
