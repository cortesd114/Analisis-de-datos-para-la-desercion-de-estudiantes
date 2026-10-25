import pandas as pd


def calcular_prioridad(fila):

    puntos = 0

    promedio = fila["Promedio académico"]
    reprobadas = fila["Materias reprobadas"]
    gusto = fila[
        "¿Le está gustando la carrera de Ingeniería de Software?"
    ]

    # Rendimiento académico (Tinto, 2017)
    if pd.notna(promedio):

        if promedio < 3.0:
            puntos += 3

        elif promedio < 3.5:
            puntos += 1

    # Materias reprobadas el semestre anterior (vacío en primer semestre)
    if pd.notna(reprobadas):

        if reprobadas >= 3:
            puntos += 3

        elif reprobadas >= 1:
            puntos += 1

    # Carga laboral
    if fila["¿Trabaja mientras estudia?"] == "Sí":
        puntos += 1

    if fila["Horas de trabajo por semana"] in ["31 a 40", "Más de 40"]:
        puntos += 1

    # Situación económica (Quintero Velasco, 2016; Ramírez, 2020)
    if fila["Pago de matrícula"] == "Paga la totalidad":
        puntos += 1

    if fila["¿Su familia depende de sus ingresos?"] == "Sí":
        puntos += 1

    # Responsabilidades familiares
    if fila["¿Tiene hijos?"] == "Sí":
        puntos += 1

    # Lejos de su red de apoyo familiar (Quintero Velasco, 2016)
    if (
        fila["¿Ha cambiado de ciudad para estudiar?"] == "Sí"
        and fila["¿Vive cerca de sus padres o familiares?"] == "No"
    ):
        puntos += 1

    # Gusto por la carrera
    if gusto == "No":
        puntos += 2

    elif gusto == "Más o menos":
        puntos += 1

    # Clasificación
    if puntos >= 5:
        return "Prioridad alta"

    elif puntos >= 3:
        return "Atención"

    else:
        return "Seguimiento"


def agregar_indicadores(datos):

    datos = datos.copy()

    datos["Prioridad de atención"] = datos.apply(
        calcular_prioridad,
        axis=1
    )

    return datos
