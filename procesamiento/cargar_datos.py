import base64
import io
import re
import unicodedata

import pandas as pd


# ==========================================================
# FORMATO DE LA ENCUESTA (Microsoft Forms)
# Si cambias una pregunta u opción en el formulario, cámbiala aquí también.
# Al comparar se ignoran mayúsculas, tildes, signos y espacios de más.
# ==========================================================

# Columna interna -> encabezados con los que puede venir en el archivo
# exportado (el texto de la pregunta en el formulario)
ENCABEZADOS = {
    "Autorización": [
        "¿Autoriza el tratamiento de sus datos personales "
        "para participar en este estudio académico?"
    ],
    "Nombre completo": ["Nombre completo"],
    # Forms guarda el correo de quien responde en "Correo electrónico"
    # (o "anonymous" si el formulario es anónimo). Si se agrega una
    # pregunta con ese mismo nombre, Excel la deja como "Correo electrónico.1"
    "Correo electrónico": [
        "Correo institucional",
        "Correo electrónico.1",
        "Correo electrónico"
    ],
    "Semestre": ["¿En qué semestre se encuentra actualmente?"],
    "Edad": ["¿Cuál es su edad?"],
    "Género": ["¿Cuál es su género?"],
    "Estrato socioeconómico": ["¿Cuál es su estrato socioeconómico?"],
    "Promedio académico": ["¿Cuál es su promedio académico actual?"],
    "Materias reprobadas": ["¿Cuántas materias reprobó el semestre anterior?"],
    "Dificultad de las materias": [
        "¿Qué tan difícil considera las materias que está cursando actualmente?"
    ],
    "Pago de matrícula": [
        "¿Cuenta actualmente con el plan de matrícula cero o paga su semestre?"
    ],
    "¿Trabaja mientras estudia?": ["¿Actualmente trabaja mientras estudia?"],
    "Horas de trabajo por semana": [
        "¿Cuántas horas trabaja aproximadamente a la semana?"
    ],
    "¿Su familia depende de sus ingresos?": [
        "¿Su familia depende de sus ingresos?"
    ],
    "¿Tiene hijos?": ["¿Tiene hijos?"],
    "¿Ha cambiado de ciudad para estudiar?": [
        "¿Ha tenido que cambiar de ciudad para estudiar Ingeniería de Software?"
    ],
    "¿Vive cerca de sus padres o familiares?": [
        "¿Actualmente vive cerca de sus padres o familiares?"
    ],
    "Municipio": ["¿En qué municipio / ciudad vive?"],
    "¿Le está gustando la carrera de Ingeniería de Software?": [
        "¿Le está gustando la carrera de Ingeniería de Software?"
    ]
}

# El formulario no pide el correo; solo existe si Forms lo registra
COLUMNAS_OPCIONALES = {"Correo electrónico"}

COLUMNAS_TEXTO = ["Nombre completo", "Correo electrónico", "Municipio"]

SI_NO = {"Sí": [], "No": []}

# Respuestas permitidas: valor interno -> textos con que aparece en el formulario.
# El valor interno también se acepta tal cual.
OPCIONES = {
    "Autorización": SI_NO,
    "Semestre": {
        1: ["Primer semestre"],
        2: ["Segundo semestre"],
        3: ["Tercer semestre"],
        4: ["Cuarto semestre"],
        5: ["Quinto semestre"],
        6: ["Sexto semestre"]
    },
    "Género": {
        "Masculino": [],
        "Femenino": [],
        "Otro": ["Otro", "Otro/Prefiero no responder"]
    },
    "Estrato socioeconómico": {1: [], 2: [], 3: [], 4: [], 5: [], 6: []},
    "Materias reprobadas": {
        0: ["Ninguna"],
        1: [],
        2: [],
        3: [],
        4: [],
        5: [],
        # No aplica: queda vacío y no cuenta para la prioridad
        None: ["Estoy en primer semestre"]
    },
    "Dificultad de las materias": {"Fácil": [], "Intermedio": [], "Difícil": []},
    "Pago de matrícula": {
        "Matrícula cero": ["Plan matrícula cero"],
        "Paga la totalidad": ["Pago la totalidad del semestre"],
        "Paga una parte": ["Pago una parte del valor del semestre"]
    },
    "¿Trabaja mientras estudia?": SI_NO,
    "Horas de trabajo por semana": {
        "No trabaja": [],
        "Menos de 10": ["Menos de 10 horas"],
        "10 a 20": ["Entre 10 y 20 horas"],
        "21 a 30": ["Entre 21 y 30 horas"],
        "31 a 40": ["Entre 31 y 40 horas"],
        "Más de 40": ["Más de 40 horas"]
    },
    "¿Su familia depende de sus ingresos?": SI_NO,
    "¿Tiene hijos?": SI_NO,
    "¿Ha cambiado de ciudad para estudiar?": SI_NO,
    "¿Vive cerca de sus padres o familiares?": SI_NO,
    "¿Le está gustando la carrera de Ingeniería de Software?": {
        "Sí": [],
        "Más o menos": [],
        "No": []
    }
}

# Preguntas de respuesta libre que deben ser números: (mínimo, máximo, entero)
RANGOS = {
    "Edad": (15, 80, True),
    "Promedio académico": (0, 5, False)
}

COLUMNAS_NUMERICAS = [
    "Semestre",
    "Edad",
    "Estrato socioeconómico",
    "Promedio académico",
    "Materias reprobadas"
]

# Cuántos ejemplos mostrar en cada mensaje de error
MAX_EJEMPLOS = 5


class ArchivoInvalido(ValueError):
    """Error con la lista de problemas encontrados en el archivo."""

    def __init__(self, problemas):
        super().__init__("; ".join(problemas))
        self.problemas = problemas


# ==========================================================
# LECTURA
# ==========================================================

def leer_archivo(contenido, nombre_archivo):
    """
    Convierte el archivo subido con dcc.Upload en un DataFrame validado.
    Devuelve (datos, respuestas excluidas por no autorizar el tratamiento).
    """

    # dcc.Upload entrega "data:<tipo>;base64,<contenido>"
    _, contenido_base64 = contenido.split(",", 1)
    binario = base64.b64decode(contenido_base64)

    if not binario.strip():
        raise ValueError("El archivo está vacío")

    extension = nombre_archivo.lower().rsplit(".", 1)[-1]

    if extension not in ("csv", "xlsx"):
        raise ValueError("Formato no soportado. Sube un archivo .csv o .xlsx")

    try:
        if extension == "csv":
            datos = _leer_csv(binario)
        else:
            datos = pd.read_excel(io.BytesIO(binario))

    # pandas lanza errores muy variados (y en inglés) ante archivos dañados
    except Exception:
        raise ValueError(
            "No se pudo leer el archivo. Verifica que sea un "
            f".{extension} válido y que no esté dañado"
        )

    return preparar_datos(datos)


def _leer_csv(binario):

    # Google Forms exporta en UTF-8; Excel en español suele usar latin-1 y ";"
    try:
        texto = binario.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = binario.decode("latin-1")

    # sep=None detecta automáticamente si el separador es "," o ";"
    return pd.read_csv(io.StringIO(texto), sep=None, engine="python")


# ==========================================================
# VALIDACIÓN
# ==========================================================

def normalizar(texto):
    """'¿Cuál es su  GÉNERO? ' -> 'cual es su genero': solo letras y números."""

    # Excel lee 2 como 2.0 cuando la columna tiene celdas vacías
    if isinstance(texto, float) and texto.is_integer():
        texto = int(texto)

    sin_tildes = (
        unicodedata.normalize("NFKD", str(texto))
        .encode("ascii", "ignore")
        .decode()
    )

    return " ".join(re.sub(r"[^a-z0-9]+", " ", sin_tildes.lower()).split())


def _filas(mascara):
    """'en las filas 3, 8' con los números que se ven en Excel (encabezado = fila 1)."""

    filas = [str(indice + 2) for indice in mascara[mascara].index]

    if len(filas) == 1:
        return f"en la fila {filas[0]}"

    texto = "en las filas " + ", ".join(filas[:MAX_EJEMPLOS])

    if len(filas) > MAX_EJEMPLOS:
        texto += f" y {len(filas) - MAX_EJEMPLOS} más"

    return texto


def _ubicar_columnas(datos):
    """Renombra las preguntas del formulario a los nombres internos."""

    por_encabezado = {}
    faltantes = []

    for interna, encabezados in ENCABEZADOS.items():

        buscados = [normalizar(texto) for texto in encabezados + [interna]]

        encontrada = next(
            (
                columna
                for buscado in buscados
                for columna in datos.columns
                if normalizar(columna) == buscado
                and columna not in por_encabezado
            ),
            None
        )

        if encontrada is not None:
            por_encabezado[encontrada] = interna

        elif interna not in COLUMNAS_OPCIONALES:
            faltantes.append(f"Falta la pregunta «{encabezados[0]}»")

    if faltantes:
        raise ArchivoInvalido(faltantes)

    datos = datos[list(por_encabezado)].rename(columns=por_encabezado)

    for columna in COLUMNAS_OPCIONALES - set(datos.columns):
        datos[columna] = None

    return datos[list(ENCABEZADOS)]


def _validar_opciones(datos, columna, opciones, problemas):

    por_normalizada = {}

    for valor, textos in opciones.items():

        if valor is not None:
            por_normalizada[normalizar(valor)] = valor

        for texto in textos:
            por_normalizada[normalizar(texto)] = valor

    originales = datos[columna]
    invalidas = originales.notna() & ~originales.map(
        lambda valor: normalizar(valor) in por_normalizada
    )

    if invalidas.any():

        ejemplos = originales[invalidas].astype(str).value_counts()
        listado = ", ".join(
            f"«{valor}» ({cantidad})"
            for valor, cantidad in ejemplos.head(MAX_EJEMPLOS).items()
        )
        permitidas = ", ".join(
            textos[0] if textos else str(valor)
            for valor, textos in opciones.items()
        )

        problemas.append(
            f"«{columna}»: respuestas no reconocidas {listado} "
            f"{_filas(invalidas)}. "
            f"Valores permitidos: {permitidas}"
        )

    datos[columna] = originales.map(
        lambda valor: por_normalizada.get(normalizar(valor))
        if pd.notna(valor) else None
    )


def _validar_numero(datos, columna, minimo, maximo, entero, problemas):

    originales = datos[columna]

    # Respuesta libre: toma el primer número ("19 años" -> 19, "3,8" -> 3.8)
    numeros = originales.map(
        lambda valor: re.search(r"\d+(?:[.,]\d+)?", str(valor))
        if pd.notna(valor) else None
    ).map(
        lambda encontrado: float(encontrado.group().replace(",", "."))
        if encontrado else None
    ).astype(float)

    no_numericos = originales.notna() & numeros.isna()

    if no_numericos.any():
        ejemplos = ", ".join(
            f"«{valor}»"
            for valor in originales[no_numericos].astype(str).unique()[:MAX_EJEMPLOS]
        )
        problemas.append(
            f"«{columna}»: respuestas sin un número válido {ejemplos} "
            f"{_filas(no_numericos)}"
        )

    fuera_de_rango = numeros.notna() & ~numeros.between(minimo, maximo)

    if fuera_de_rango.any():
        problemas.append(
            f"«{columna}»: valores fuera del rango {minimo} a {maximo} "
            f"{_filas(fuera_de_rango)}"
        )

    no_enteros = numeros.notna() & (numeros % 1 != 0)

    if entero and no_enteros.any():
        problemas.append(
            f"«{columna}»: debe ser un número entero "
            f"({_filas(no_enteros)})"
        )

    datos[columna] = numeros


def preparar_datos(datos):
    """Devuelve (datos validados, respuestas excluidas por no autorizar)."""

    # Se conserva el índice original para reportar la fila exacta del Excel
    datos = _ubicar_columnas(datos).dropna(how="all")

    if datos.empty:
        raise ValueError("El archivo no tiene respuestas")

    # Ley 1581 de 2012: solo se usan las respuestas que autorizaron el tratamiento
    autorizadas = datos["Autorización"].map(normalizar) == "si"
    excluidas = int((~autorizadas).sum())
    datos = datos[autorizadas].drop(columns="Autorización")

    if datos.empty:
        raise ValueError(
            "Ninguna respuesta autorizó el tratamiento de datos personales"
        )

    problemas = []

    for columna in COLUMNAS_TEXTO:
        datos[columna] = datos[columna].map(
            lambda valor: " ".join(str(valor).split()) if pd.notna(valor) else None
        )

    # Forms registra "anonymous" cuando el formulario no pide iniciar sesión
    datos.loc[datos["Correo electrónico"] == "anonymous", "Correo electrónico"] = None

    for columna, opciones in OPCIONES.items():
        if columna in datos.columns:
            _validar_opciones(datos, columna, opciones, problemas)

    for columna, (minimo, maximo, entero) in RANGOS.items():
        _validar_numero(datos, columna, minimo, maximo, entero, problemas)

    if problemas:
        raise ArchivoInvalido(problemas)

    # Quien no trabaja se salta la sección laboral del formulario
    no_trabaja = datos["¿Trabaja mientras estudia?"] == "No"

    datos.loc[
        no_trabaja & datos["Horas de trabajo por semana"].isna(),
        "Horas de trabajo por semana"
    ] = "No trabaja"

    datos.loc[
        no_trabaja & datos["¿Su familia depende de sus ingresos?"].isna(),
        "¿Su familia depende de sus ingresos?"
    ] = "No"

    for columna in COLUMNAS_NUMERICAS:
        datos[columna] = pd.to_numeric(datos[columna])

    datos["Promedio académico"] = datos["Promedio académico"].round(2)

    return datos, excluidas


# ==========================================================
# PLANTILLA
# ==========================================================

def crear_plantilla():
    """Archivo de ejemplo con las preguntas y respuestas tal como las exporta Forms."""

    filas = [
        {
            "Autorización": "Sí",
            "Nombre completo": "Ana María Pérez Gómez",
            "Correo electrónico": "ana.perez@ucundinamarca.edu.co",
            "Semestre": "Segundo semestre",
            "Edad": "18",
            "Género": "Femenino",
            "Estrato socioeconómico": "2",
            "Promedio académico": "3,8",
            "Materias reprobadas": "Ninguna",
            "Dificultad de las materias": "Intermedio",
            "Pago de matrícula": "Plan matrícula cero",
            "¿Trabaja mientras estudia?": "No",
            "Horas de trabajo por semana": "",
            "¿Su familia depende de sus ingresos?": "",
            "¿Tiene hijos?": "No",
            "¿Ha cambiado de ciudad para estudiar?": "No",
            "¿Vive cerca de sus padres o familiares?": "Sí",
            "Municipio": "Girardot",
            "¿Le está gustando la carrera de Ingeniería de Software?": "Sí"
        },
        {
            "Autorización": "Sí",
            "Nombre completo": "Carlos Andrés Ruiz Díaz",
            "Correo electrónico": "carlos.ruiz@ucundinamarca.edu.co",
            "Semestre": "Cuarto semestre",
            "Edad": "22",
            "Género": "Masculino",
            "Estrato socioeconómico": "1",
            "Promedio académico": "2,9",
            "Materias reprobadas": "3",
            "Dificultad de las materias": "Difícil",
            "Pago de matrícula": "Pago la totalidad del semestre",
            "¿Trabaja mientras estudia?": "Sí",
            "Horas de trabajo por semana": "Entre 31 y 40 horas",
            "¿Su familia depende de sus ingresos?": "Sí",
            "¿Tiene hijos?": "Sí",
            "¿Ha cambiado de ciudad para estudiar?": "Sí",
            "¿Vive cerca de sus padres o familiares?": "No",
            "Municipio": "Flandes",
            "¿Le está gustando la carrera de Ingeniería de Software?": "Más o menos"
        }
    ]

    # Encabezados = texto de cada pregunta en el formulario
    return pd.DataFrame(filas).rename(
        columns={interna: textos[-1] if interna == "Correo electrónico" else textos[0]
                 for interna, textos in ENCABEZADOS.items()}
    )
