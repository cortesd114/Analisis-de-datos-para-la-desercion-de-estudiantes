import os

import pandas as pd
from dash import Dash, html, dcc, Input, Output, State, no_update
from dash.exceptions import PreventUpdate

from autenticacion.login import configurar_login
from procesamiento.cargar_datos import (
    ArchivoInvalido,
    crear_plantilla,
    leer_archivo
)
from procesamiento.indicadores import agregar_indicadores

from graficos.graficos import (
    grafica_semestres,
    grafica_promedios,
    grafica_gusto_carrera,
    grafica_prioridad,
    grafica_reprobadas,
    grafica_estrato,
    grafica_horas_trabajo,
    grafica_pago_matricula,
    grafica_dificultad,
    grafica_condiciones_familiares
)

from componentes.tarjetas import crear_tarjeta
from componentes.tabla import crear_tabla, IDS_COLUMNAS


# ==========================================================
# 1. CREAR APLICACIÓN
# ==========================================================

app = Dash(__name__)
app.title = "Seguimiento de estudiantes"

configurar_login(app.server)

# Encuesta de Microsoft Forms con la que se recogen los datos
URL_ENCUESTA = (
    "https://forms.cloud.microsoft/pages/responsepage.aspx"
    "?id=oGfaB0MfjE6Xf1-ItkcO5lOT-5FqchlDi490HjclEsxUN0pQQVM2TEM2RU03MFA0T0tRTDlLSFBNOS4u"
    "&route=shorturl"
)

COLOR_ERROR = "#d64545"
COLOR_EXITO = "#3a9d5d"
COLOR_ENLACE = "#2f6fb3"

ESTILO_GENERAL = {
    "fontFamily": "Arial, sans-serif",
    "backgroundColor": "#f5f7fa",
    "minHeight": "100vh",
    "padding": "25px"
}

# Cada gráfica con su función generadora, en el orden en que se muestran
GRAFICAS = [
    ("grafica-semestre", grafica_semestres),
    ("grafica-promedio", grafica_promedios),
    ("grafica-reprobadas", grafica_reprobadas),
    ("grafica-dificultad", grafica_dificultad),
    ("grafica-estrato", grafica_estrato),
    ("grafica-pago", grafica_pago_matricula),
    ("grafica-horas", grafica_horas_trabajo),
    ("grafica-familia", grafica_condiciones_familiares),
    ("grafica-gusto", grafica_gusto_carrera),
    ("grafica-prioridad", grafica_prioridad)
]


# ==========================================================
# 2. ENCABEZADO
# ==========================================================

encabezado = html.Div(
    [
        html.Div(
            [
                html.H1("Dashboard de seguimiento estudiantil"),
                html.P(
                    "Ingeniería de Software",
                    style={"fontSize": "18px", "color": "#5f6b7a"}
                ),
                html.P(
                    "Análisis de condiciones académicas, económicas y laborales",
                    style={"color": "#6c757d"}
                )
            ]
        ),
        html.A(
            "Cerrar sesión",
            href="/logout",
            style={"color": "#2f6fb3", "fontWeight": "bold"}
        )
    ],
    style={
        "display": "flex",
        "justifyContent": "space-between",
        "alignItems": "flex-start",
        "flexWrap": "wrap",
        "gap": "10px",
        "marginBottom": "25px"
    }
)


# ==========================================================
# 3. CARGA DE ARCHIVO
# ==========================================================

carga_archivo = html.Div(
    [
        dcc.Upload(
            id="cargar-archivo",
            children=html.Div(
                [
                    "Arrastra aquí el archivo de la encuesta o ",
                    html.A("selecciónalo", style={"color": "#2f6fb3"}),
                    " (.csv o .xlsx)"
                ]
            ),
            multiple=False,
            style={
                "border": "2px dashed #b5bfcc",
                "borderRadius": "12px",
                "backgroundColor": "white",
                "padding": "25px",
                "textAlign": "center",
                "cursor": "pointer"
            }
        ),
        html.Div(
            [
                html.Button(
                    "Descargar plantilla",
                    id="boton-plantilla",
                    style={
                        "padding": "8px 14px",
                        "border": f"1px solid {COLOR_ENLACE}",
                        "borderRadius": "6px",
                        "backgroundColor": "white",
                        "color": COLOR_ENLACE,
                        "fontWeight": "bold",
                        "cursor": "pointer"
                    }
                ),
                dcc.Download(id="descargar-plantilla"),
                html.A(
                    "Ver encuesta de ejemplo ↗",
                    href=URL_ENCUESTA,
                    target="_blank",
                    rel="noopener noreferrer",
                    style={"color": COLOR_ENLACE, "fontWeight": "bold"}
                )
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "flexWrap": "wrap",
                "gap": "15px",
                "marginTop": "12px"
            }
        ),
        html.P(
            "Exporta las respuestas de la encuesta (en Microsoft Forms: "
            "Respuestas → Abrir en Excel) y súbelas aquí. "
            "La plantilla muestra las columnas y respuestas exactas que se esperan.",
            style={"fontSize": "13px", "color": "#687385", "marginTop": "10px"}
        ),
        html.Div(id="mensaje-carga", style={"marginTop": "10px"})
    ],
    style={"marginBottom": "25px"}
)


# ==========================================================
# 4. FILTRO
# ==========================================================

filtro_semestre = html.Div(
    [
        html.Label("Filtrar por semestre", style={"fontWeight": "bold"}),
        dcc.Dropdown(
            id="filtro-semestre",
            options=[],
            value="Todos",
            clearable=False
        )
    ],
    style={"width": "250px", "maxWidth": "100%", "marginBottom": "25px"}
)


# ==========================================================
# 5. TARJETAS
# ==========================================================

tarjetas = html.Div(
    [
        crear_tarjeta("Total de estudiantes", "kpi-estudiantes"),
        crear_tarjeta("Promedio general", "kpi-promedio"),
        crear_tarjeta("Reprobaron el semestre anterior", "kpi-reprobadas"),
        crear_tarjeta("Estudiantes que trabajan", "kpi-trabajan"),
        crear_tarjeta("Prioridad alta", "kpi-alta")
    ],
    style={
        "display": "flex",
        "gap": "15px",
        "flexWrap": "wrap",
        "marginBottom": "25px"
    }
)


# ==========================================================
# 6. GRÁFICAS
# ==========================================================

# auto-fit: dos columnas en pantallas anchas, una en pantallas pequeñas
graficas = html.Div(
    [dcc.Graph(id=id_grafica) for id_grafica, _ in GRAFICAS],
    style={
        "display": "grid",
        "gridTemplateColumns": "repeat(auto-fit, minmax(min(450px, 100%), 1fr))",
        "gap": "15px"
    }
)


# ==========================================================
# 7. TABLA
# ==========================================================

seccion_tabla = html.Div(
    [
        html.H2("Estudiantes para seguimiento"),
        html.P("La tabla permite ordenar y filtrar los estudiantes."),
        crear_tabla(),
        html.P(
            "La prioridad de atención es un indicador de "
            "acompañamiento basado en las respuestas de la encuesta. "
            "No representa una predicción de deserción.",
            style={"fontSize": "12px", "color": "#687385", "marginTop": "15px"}
        )
    ],
    style={"marginTop": "30px"}
)


# ==========================================================
# 8. LAYOUT
# ==========================================================

# El contenido se muestra solo cuando hay un archivo cargado
contenido = html.Div(
    [filtro_semestre, tarjetas, graficas, seccion_tabla],
    id="contenido-dashboard",
    style={"display": "none"}
)

app.layout = html.Div(
    [
        # "session": los datos viven solo en esta pestaña del navegador
        dcc.Store(id="datos-cargados", storage_type="session"),
        encabezado,
        carga_archivo,
        contenido
    ],
    style=ESTILO_GENERAL
)


# ==========================================================
# 9. CALLBACKS
# ==========================================================

@app.callback(
    Output("datos-cargados", "data"),
    Output("mensaje-carga", "children"),
    Input("cargar-archivo", "contents"),
    State("cargar-archivo", "filename"),
    prevent_initial_call=True
)
def cargar_archivo(contenido, nombre_archivo):

    try:
        datos, excluidas = leer_archivo(contenido, nombre_archivo)
        datos = agregar_indicadores(datos)

    except ArchivoInvalido as error:
        return no_update, html.Div(
            [
                html.Strong(
                    f"No se pudo cargar «{nombre_archivo}». "
                    "Corrige lo siguiente y vuelve a subirlo:"
                ),
                html.Ul([html.Li(problema) for problema in error.problemas])
            ],
            style={"color": COLOR_ERROR}
        )

    except ValueError as error:
        return no_update, html.Span(
            f"No se pudo cargar «{nombre_archivo}»: {error}",
            style={"color": COLOR_ERROR}
        )

    mensaje = f"✓ {nombre_archivo}: {len(datos):,} estudiantes cargados"

    if excluidas:
        mensaje += (
            f" ({excluidas} respuesta(s) excluida(s) por no autorizar "
            "el tratamiento de datos personales)"
        )

    return datos.to_dict("records"), html.Span(
        mensaje,
        style={"color": COLOR_EXITO, "fontWeight": "bold"}
    )


@app.callback(
    Output("descargar-plantilla", "data"),
    Input("boton-plantilla", "n_clicks"),
    prevent_initial_call=True
)
def descargar_plantilla(_):

    return dcc.send_data_frame(
        crear_plantilla().to_excel,
        "plantilla_encuesta.xlsx",
        index=False,
        sheet_name="Respuestas"
    )


def hay_datos_validos(registros):
    """Descarta datos guardados en el navegador por una versión anterior de la app."""

    return bool(registros) and set(IDS_COLUMNAS) <= set(registros[0])


@app.callback(
    Output("contenido-dashboard", "style"),
    Output("filtro-semestre", "options"),
    Output("filtro-semestre", "value"),
    Input("datos-cargados", "data")
)
def preparar_dashboard(registros):

    if not hay_datos_validos(registros):
        return {"display": "none"}, [], "Todos"

    semestres = sorted(pd.DataFrame(registros)["Semestre"].dropna().unique())

    opciones = [{"label": "Todos los semestres", "value": "Todos"}] + [
        {"label": f"Semestre {int(semestre)}", "value": int(semestre)}
        for semestre in semestres
    ]

    return {"display": "block"}, opciones, "Todos"


@app.callback(
    Output("kpi-estudiantes", "children"),
    Output("kpi-promedio", "children"),
    Output("kpi-reprobadas", "children"),
    Output("kpi-trabajan", "children"),
    Output("kpi-alta", "children"),
    [Output(id_grafica, "figure") for id_grafica, _ in GRAFICAS],
    Output("tabla-estudiantes", "data"),
    Input("datos-cargados", "data"),
    Input("filtro-semestre", "value")
)
def actualizar_dashboard(registros, semestre):

    if not hay_datos_validos(registros):
        raise PreventUpdate

    datos = pd.DataFrame(registros)

    if semestre != "Todos":
        datos = datos[datos["Semestre"] == int(semestre)]

    # Indicadores
    total = len(datos)
    promedio = datos["Promedio académico"].mean()
    reprobados = (datos["Materias reprobadas"] > 0).sum()
    trabajan = (datos["¿Trabaja mientras estudia?"] == "Sí").sum()
    alta = (datos["Prioridad de atención"] == "Prioridad alta").sum()

    figuras = [funcion(datos) for _, funcion in GRAFICAS]

    tabla = datos[IDS_COLUMNAS].to_dict("records")

    return (
        f"{total:,}",
        f"{promedio:.2f}" if total > 0 else "0.00",
        f"{reprobados:,}",
        f"{trabajan:,}",
        f"{alta:,}",
        *figuras,
        tabla
    )


# ==========================================================
# 10. EJECUTAR
# ==========================================================

if __name__ == "__main__":

    # Modo debug solo si se activa explícitamente: DASH_DEBUG=1
    app.run(debug=os.environ.get("DASH_DEBUG") == "1")
