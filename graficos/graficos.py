import pandas as pd
import plotly.express as px


COLORES_PRIORIDAD = {
    "Prioridad alta": "#d64545",
    "Atención": "#e8a33d",
    "Seguimiento": "#3a9d5d"
}


def _conteo(datos, columna, etiqueta, orden=None):
    """Cantidad de estudiantes por respuesta; con orden, incluye las que tienen 0."""

    conteo = datos[columna].value_counts()

    if orden is None:
        conteo = conteo.sort_index()
    else:
        conteo = conteo.reindex(orden, fill_value=0)

    return conteo.rename_axis(etiqueta).reset_index(name="Estudiantes")


def _barras(tabla, x, titulo, entero=False):

    figura = px.bar(tabla, x=x, y="Estudiantes", title=titulo)

    if entero:
        figura.update_xaxes(dtick=1)

    return figura


def grafica_semestres(datos):

    return _barras(
        _conteo(datos, "Semestre", "Semestre"),
        "Semestre",
        "Distribución de estudiantes por semestre",
        entero=True
    )


def grafica_promedios(datos):

    return px.histogram(
        datos,
        x="Promedio académico",
        nbins=10,
        title="Distribución del promedio académico",
        labels={
            "Promedio académico": "Promedio académico",
            "count": "Estudiantes"
        }
    )


def grafica_gusto_carrera(datos):

    return _barras(
        _conteo(
            datos,
            "¿Le está gustando la carrera de Ingeniería de Software?",
            "Respuesta",
            orden=["Sí", "Más o menos", "No"]
        ),
        "Respuesta",
        "¿A los estudiantes les está gustando la carrera?"
    )


def grafica_prioridad(datos):

    prioridades = _conteo(
        datos,
        "Prioridad de atención",
        "Prioridad",
        orden=list(COLORES_PRIORIDAD)
    )

    figura = px.bar(
        prioridades,
        x="Prioridad",
        y="Estudiantes",
        color="Prioridad",
        color_discrete_map=COLORES_PRIORIDAD,
        title="Prioridad de acompañamiento"
    )

    figura.update_layout(showlegend=False)

    return figura


def grafica_reprobadas(datos):

    # Los estudiantes de primer semestre no aplican y quedan por fuera
    return _barras(
        _conteo(datos, "Materias reprobadas", "Materias reprobadas"),
        "Materias reprobadas",
        "Materias reprobadas el semestre anterior",
        entero=True
    )


def grafica_estrato(datos):

    return _barras(
        _conteo(datos, "Estrato socioeconómico", "Estrato"),
        "Estrato",
        "Distribución por estrato socioeconómico",
        entero=True
    )


def grafica_horas_trabajo(datos):

    return _barras(
        _conteo(
            datos,
            "Horas de trabajo por semana",
            "Horas",
            orden=[
                "No trabaja",
                "Menos de 10",
                "10 a 20",
                "21 a 30",
                "31 a 40",
                "Más de 40"
            ]
        ),
        "Horas",
        "Horas de trabajo por semana"
    )


def grafica_pago_matricula(datos):

    return _barras(
        _conteo(
            datos,
            "Pago de matrícula",
            "Forma de pago",
            orden=["Matrícula cero", "Paga una parte", "Paga la totalidad"]
        ),
        "Forma de pago",
        "¿Cómo paga el semestre?"
    )


def grafica_dificultad(datos):

    return _barras(
        _conteo(
            datos,
            "Dificultad de las materias",
            "Dificultad",
            orden=["Fácil", "Intermedio", "Difícil"]
        ),
        "Dificultad",
        "Dificultad percibida de las materias actuales"
    )


def grafica_condiciones_familiares(datos):

    # Condición -> (columna, respuesta que la cumple)
    condiciones = {
        "Tiene hijos": ("¿Tiene hijos?", "Sí"),
        "Su familia depende de sus ingresos": (
            "¿Su familia depende de sus ingresos?", "Sí"
        ),
        "Cambió de ciudad para estudiar": (
            "¿Ha cambiado de ciudad para estudiar?", "Sí"
        ),
        "No vive cerca de su familia": (
            "¿Vive cerca de sus padres o familiares?", "No"
        )
    }

    tabla = pd.DataFrame(
        {
            "Condición": list(condiciones),
            "Estudiantes": [
                (datos[columna] == respuesta).sum()
                for columna, respuesta in condiciones.values()
            ]
        }
    )

    return px.bar(
        tabla,
        x="Estudiantes",
        y="Condición",
        orientation="h",
        title="Condiciones familiares y de vivienda"
    )
