from dash import dash_table
from dash.dash_table.Format import Format, Scheme

from graficos.graficos import COLORES_PRIORIDAD


COLUMNAS = [
    {"name": "Nombre", "id": "Nombre completo"},
    {"name": "Correo", "id": "Correo electrónico"},
    {"name": "Semestre", "id": "Semestre"},
    {"name": "Municipio", "id": "Municipio"},
    {
        "name": "Promedio",
        "id": "Promedio académico",
        "type": "numeric",
        "format": Format(precision=2, scheme=Scheme.fixed)
    },
    {"name": "Reprobadas (sem. anterior)", "id": "Materias reprobadas"},
    {"name": "Trabaja", "id": "¿Trabaja mientras estudia?"},
    {
        "name": "Le gusta la carrera",
        "id": "¿Le está gustando la carrera de Ingeniería de Software?"
    },
    {"name": "Prioridad", "id": "Prioridad de atención"}
]

IDS_COLUMNAS = [columna["id"] for columna in COLUMNAS]


def crear_tabla():

    # Colorea la celda de prioridad según su nivel
    estilos_prioridad = [
        {
            "if": {
                "filter_query": f'{{Prioridad de atención}} = "{prioridad}"',
                "column_id": "Prioridad de atención"
            },
            "backgroundColor": color,
            "color": "white",
            "fontWeight": "bold"
        }
        for prioridad, color in COLORES_PRIORIDAD.items()
    ]

    return dash_table.DataTable(
        id="tabla-estudiantes",
        columns=COLUMNAS,
        data=[],
        page_size=10,
        sort_action="native",
        filter_action="native",
        style_table={"overflowX": "auto"},
        style_cell={
            "padding": "10px",
            "textAlign": "left",
            "minWidth": "120px"
        },
        style_header={"fontWeight": "bold"},
        style_data_conditional=estilos_prioridad
    )
