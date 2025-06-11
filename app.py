import os
import pandas as pd
import random
from flask import Flask, render_template, request

app = Flask(__name__)
app.config['DEBUG'] = True  # Modo depuración activado

# Título personalizado
TITULO = "PROYECTO PERSONAL"

# Definir la ruta correcta para `Compuestos.csv`
db_path = os.path.join(os.path.dirname(__file__), 'data', 'Compuestos.csv')

# Verificar si el archivo existe antes de cargarlo
if os.path.exists(db_path):
    try:
        df = pd.read_csv(db_path)
        columnas_requeridas = {'Formula', 'Formula2', 'Sistematica', 'Stock', 'Tradicional'}
        if not columnas_requeridas.issubset(df.columns):
            df = None
            print(f"⚠️ Error: El archivo '{db_path}' no tiene las columnas requeridas: {columnas_requeridas}.")
    except Exception as e:
        df = None
        print(f"⚠️ Error al leer el archivo CSV: {str(e)}")
else:
    df = None
    print(f"⚠️ Error: No se encontró '{db_path}'. Verifica que el archivo esté en la carpeta 'data/'.")

# Función para buscar compuestos
def buscar_compuesto(tipo_busqueda, valor_busqueda, nomenclatura_devolver=None):
    if df is None or df.empty:
        return None

    if tipo_busqueda == "formula":
        resultados = df[df['Formula'].str.lower() == valor_busqueda.lower()]
        if nomenclatura_devolver == "sistematica":
            resultados = resultados[['Formula2', 'Sistematica']]
        elif nomenclatura_devolver == "stock":
            resultados = resultados[['Formula2', 'Stock']]
        elif nomenclatura_devolver == "tradicional":
            resultados = resultados[['Formula2', 'Tradicional']]
        elif nomenclatura_devolver == "todas":
            resultados = resultados[['Formula2', 'Sistematica', 'Stock', 'Tradicional']]
        else:
            return None

    elif tipo_busqueda == "nomenclatura":
        resultados = df[
            (df['Sistematica'].str.lower() == valor_busqueda.lower()) |
            (df['Stock'].str.lower() == valor_busqueda.lower()) |
            (df['Tradicional'].str.lower() == valor_busqueda.lower())
        ]
        resultados = resultados[['Formula2', 'Sistematica', 'Stock', 'Tradicional']]
    else:
        return None

    return resultados if not resultados.empty else None

@app.route('/')
def index():
    return render_template('index.html', titulo=TITULO)

@app.route('/informacion')
def informacion():
    return render_template('informacion.html', titulo="Guía de Nomenclatura")

@app.route('/buscar', methods=['POST'])
def buscar():
    try:
        tipo_busqueda = request.form.get('tipo_busqueda')
        formula = request.form.get('formula')
        nomenclatura = request.form.get('nomenclatura')
        nomenclatura_devolver = request.form.get('nomenclatura_devolver')

        if tipo_busqueda == "formula":
            if not formula:
                return render_template('resultados.html', titulo=TITULO, error="⚠️ Debes ingresar una fórmula.")
            valor_busqueda = formula
        elif tipo_busqueda == "nomenclatura":
            if not nomenclatura:
                return render_template('resultados.html', titulo=TITULO, error="⚠️ Debes ingresar una nomenclatura.")
            valor_busqueda = nomenclatura
        else:
            return render_template('resultados.html', titulo=TITULO, error="⚠️ Tipo de búsqueda no válido.")

        resultados = buscar_compuesto(tipo_busqueda, valor_busqueda, nomenclatura_devolver)

        if resultados is None or resultados.empty:
            return render_template('resultados.html', titulo=TITULO, error="No se encontraron resultados.")

        return render_template('resultados.html', titulo=TITULO, tipo_busqueda=tipo_busqueda,
                               valor_busqueda=valor_busqueda,
                               resultados=resultados,
                               nomenclatura_devolver=nomenclatura_devolver,
                               error=None)
    except Exception as e:
        return render_template('resultados.html', titulo=TITULO, error=f"❌ Error interno: {str(e)}"), 500

# Ruta del test interactivo con manejo de errores para depuración
@app.route("/test")
def test():
    try:
        preguntas = cargar_preguntas()
        return render_template("test.html", titulo="Test de Formulación Química", preguntas=preguntas)
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        # Mostrar el error detallado en HTML para facilitar la depuración
        return f"<h1>Error al cargar test</h1><pre>{tb}</pre>", 500

@app.route("/evaluar_test", methods=["POST"])
def evaluar_test():
    resultados = []
    puntaje = 0
    total = 0

    for i in range(10):
        respuesta_usuario = request.form.get(f"respuesta_{i}")
        respuesta_correcta = request.form.get(f"correcta_{i}")
        if respuesta_usuario is None or respuesta_correcta is None:
            continue
        total += 1
        correcta = respuesta_usuario.strip().lower() == respuesta_correcta.strip().lower()
        resultados.append({
            "pregunta": i + 1,
            "respuesta_usuario": respuesta_usuario,
            "respuesta_correcta": respuesta_correcta,
            "correcta": correcta
        })
        if correcta:
            puntaje += 1

    # *** CAMBIO: usar un template específico para resultados del test ***
    return render_template("resultados_test.html", titulo="Resultados del Test", resultados=resultados, puntaje=puntaje, total=total)

# Función para cargar preguntas del DataFrame de forma segura
def cargar_preguntas():
    preguntas = []
    if df is None or df.empty:
        return preguntas

    # Aseguramos que existan columnas necesarias
    columnas_necesarias = {'Formula2', 'Sistematica', 'Stock', 'Tradicional'}
    if not columnas_necesarias.issubset(df.columns):
        return preguntas

    # Seleccionar hasta 10 compuestos al azar
    seleccionadas = df.sample(n=min(10, len(df)))

    for _, fila in seleccionadas.iterrows():
        # Elegir tipo de pregunta al azar
        tipo = random.choice(["formula_a_nombre", "nombre_a_formula"])

        if tipo == "formula_a_nombre":
            nombre = fila.get("Tradicional") or fila.get("Stock") or fila.get("Sistematica") or ""
            preguntas.append({
                "enunciado": f"¿Cuál es el nombre del compuesto {fila['Formula2']}?",
                "respuesta": nombre,
            })
        else:
            nombre = fila.get("Tradicional") or fila.get("Stock") or fila.get("Sistematica")
            if nombre:
                preguntas.append({
                    "enunciado": f"¿Cuál es la fórmula del compuesto {nombre}?",
                    "respuesta": fila['Formula2']
                })
    return preguntas

if __name__ == '__main__':
    app.run(debug=True)
