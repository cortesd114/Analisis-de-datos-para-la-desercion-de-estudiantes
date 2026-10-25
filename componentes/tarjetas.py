from dash import html


def crear_tarjeta(titulo, id_valor):

    return html.Div(
        [
            html.Div(
                titulo,
                style={
                    "fontSize": "14px",
                    "color": "#5f6b7a"
                }
            ),

            html.Div(
                id=id_valor,
                style={
                    "fontSize": "30px",
                    "fontWeight": "bold"
                }
            )
        ],
        style={
            "backgroundColor": "white",
            "padding": "18px",
            "borderRadius": "12px",
            "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
            "flex": "1",
            "minWidth": "180px"
        }
    )