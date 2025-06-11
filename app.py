import os
import pandas as pd
import random
import re # Importar el módulo re para expresiones regulares
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
# ¡¡¡IMPORTANTE!!! CAMBIA ESTO POR UNA CLAVE SEGURA Y ÚNICA EN PRODUCCIÓN
app.secret_key = 'super_secret_key_very_unique_12345'
app.config['DEBUG'] = True

# Título personalizado
TITULO = "Mi Propia IA - Mateo Martín Castro" # Se actualiza el título aquí también

# --- Funciones Auxiliares (MOVIDAS AQUÍ PARA SER DEFINIDAS ANTES DE USARSE) ---
def normalizar_formula(formula):
    """
    Normaliza una fórmula química para comparación (elimina espacios, unifica subíndices, etc.).
    Ej: H₂O -> H2O, Nacl -> NaCl
    """
    if pd.isna(formula):
        return ""
    formula = str(formula).strip()
    # Reemplazar subíndices unicode por dígitos ASCII
    subindices_map = {
        '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4',
        '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9'
    }
    for old, new in subindices_map.items():
        formula = formula.replace(old, new)

    # Capitalizar el primer carácter de cada posible elemento (ej. co -> Co, cl -> Cl)
    # Esto es una simplificación. Un parser real de fórmulas sería más complejo.
    # Esta regex busca una letra mayúscula seguida opcionalmente de una minúscula,
    # o una letra minúscula que podría ser el inicio de un nuevo elemento (ej. Fe2O3, no fe2o3)
    def _capitalize_element_symbol(match):
        s = match.group(0)
        if len(s) == 1:
            return s.upper() # Elemento de una letra siempre mayúscula
        return s[0].upper() + s[1:].lower() # Elemento de dos letras: primera mayúscula, segunda minúscula

    # Usar una expresión regular para encontrar posibles símbolos de elementos (A o Aa)
    # y aplicar la capitalización. Esto es heurístico.
    normalized = re.sub(r'([A-Z][a-z]?|[a-z])', _capitalize_element_symbol, formula)

    # Eliminar espacios y números sueltos si no están seguidos de un símbolo de elemento.
    # Esto es una simplificación y puede no ser robusto para todas las fórmulas.
    normalized = re.sub(r'\s+', '', normalized) # Eliminar cualquier espacio remanente

    return normalized

# Definir la ruta correcta para `compuestos_quimicos.xlsx` (ajustado para tu base de datos)
db_path_excel = os.path.join(os.path.dirname(__file__), 'compuestos_quimicos.xlsx')
db_path_csv = os.path.join(os.path.dirname(__file__), 'data', 'Compuestos.csv') # Por si acaso, se mantiene la referencia al CSV

df_compuestos = None

# Intentar cargar desde Excel primero, si no, desde CSV
if os.path.exists(db_path_excel):
    try:
        df_compuestos = pd.read_excel(db_path_excel)
        print(f"✔️ Se cargó 'compuestos_quimicos.xlsx'.")
    except Exception as e:
        print(f"❌ Error al leer el archivo Excel '{db_path_excel}': {str(e)}")
elif os.path.exists(db_path_csv):
    try:
        df_compuestos = pd.read_csv(db_path_csv)
        print(f"✔️ Se cargó 'Compuestos.csv'.")
    except Exception as e:
        print(f"❌ Error al leer el archivo CSV '{db_path_csv}': {str(e)}")
else:
    print(f"⚠️ Error: No se encontró 'compuestos_quimicos.xlsx' ni 'Compuestos.csv'. Verifica que al menos uno esté en la ubicación correcta.")

# Verificar y preparar el DataFrame
if df_compuestos is not None:
    # Añadir 'Caracteristicas' y 'Usos' a las columnas requeridas
    columnas_requeridas = {'Formula', 'Formula2', 'Sistematica', 'Stock', 'Tradicional', 'Caracteristicas', 'Usos'}
    if not columnas_requeridas.issubset(df_compuestos.columns):
        df_compuestos = None
        print(f"⚠️ Error: El archivo de datos no tiene todas las columnas requeridas: {columnas_requeridas}.")
    else:
        # Añadir columna normalizada para fórmulas (para comparación más robusta en el test)
        df_compuestos['Formula2_Normalizada'] = df_compuestos['Formula2'].astype(str).apply(lambda x: normalizar_formula(x) if pd.notna(x) else "")
        # Normalizar columnas de nomenclatura para una comparación precisa
        df_compuestos['Sistematica_Normalizada'] = df_compuestos['Sistematica'].astype(str).str.strip().str.lower()
        df_compuestos['Stock_Normalizada'] = df_compuestos['Stock'].astype(str).str.strip().str.lower()
        df_compuestos['Tradicional_Normalizada'] = df_compuestos['Tradicional'].astype(str).str.strip().str.lower()

else:
    print("El DataFrame de compuestos no se pudo cargar. La funcionalidad de búsqueda y test podría estar limitada.")

def buscar_compuesto(tipo_busqueda, valor_busqueda, nomenclatura_devolver=None):
    if df_compuestos is None or df_compuestos.empty:
        return None

    if tipo_busqueda == "formula":
        # Normalizar el valor de búsqueda y la columna de fórmulas
        formula_normalizada_buscada = normalizar_formula(valor_busqueda)
        resultados = df_compuestos[df_compuestos['Formula2_Normalizada'] == formula_normalizada_buscada].copy()
        return resultados if not resultados.empty else None
    elif tipo_busqueda == "nomenclatura":
        valor_busqueda_lower_stripped = valor_busqueda.strip().lower() # Normalizar la entrada del usuario

        # Realizar la búsqueda por coincidencia exacta en las columnas normalizadas
        mask = (df_compuestos['Sistematica_Normalizada'] == valor_busqueda_lower_stripped) | \
               (df_compuestos['Stock_Normalizada'] == valor_busqueda_lower_stripped) | \
               (df_compuestos['Tradicional_Normalizada'] == valor_busqueda_lower_stripped)
        
        resultados = df_compuestos[mask].copy()
        return resultados if not resultados.empty else None
    return None

# --- Rutas de la Aplicación ---
@app.route('/')
def index():
    return render_template('index.html', titulo=TITULO)

@app.route('/informacion')
def informacion():
    return render_template('informacion.html', titulo=TITULO)

# Nueva ruta para el informe del proyecto
@app.route('/informe_proyecto')
def informe_proyecto():
    return render_template('informe_proyecto.html', titulo=TITULO)

# Nueva ruta para la página de comentarios
@app.route('/comentarios')
def comentarios():
    return render_template('comentarios.html', titulo=TITULO)

@app.route('/buscar', methods=['POST'])
def buscar_post():
    tipo_busqueda = request.form['tipo_busqueda']
    valor_busqueda = ""
    error = None
    nomenclatura_devolver = request.form.get('nomenclatura_devolver', 'todas')

    if tipo_busqueda == 'formula':
        valor_busqueda = request.form['formula'].strip()
        if not valor_busqueda:
            error = "La fórmula no puede estar vacía."
    elif tipo_busqueda == 'nomenclatura':
        valor_busqueda = request.form['nomenclatura'].strip()
        if not valor_busqueda:
            error = "La nomenclatura no puede estar vacía."
    else:
        error = "Tipo de búsqueda no válido."

    resultados = None
    if not error:
        resultados = buscar_compuesto(tipo_busqueda, valor_busqueda, nomenclatura_devolver)
        if resultados is None or resultados.empty:
            error = f"No se encontraron resultados para '{valor_busqueda}'."

    return render_template('resultados.html',
                           titulo=TITULO,
                           tipo_busqueda=tipo_busqueda,
                           valor_busqueda=valor_busqueda,
                           resultados=resultados,
                           error=error,
                           nomenclatura_devolver=nomenclatura_devolver)

@app.route('/test', methods=['GET'])
def test():
    # Reiniciar el test si se accede a /test directamente
    session.pop('test_preguntas', None)
    session.pop('test_respuestas_usuario', None)
    session.pop('test_indice_actual', None)

    if df_compuestos is None or df_compuestos.empty:
        return render_template('test.html', titulo=TITULO, error="No se pueden generar preguntas: No hay datos de compuestos cargados.")

    # Generar 10 preguntas aleatorias
    # Asegurarse de tener al menos 10 filas para samplear, o tomar todas si hay menos.
    num_preguntas_a_generar = min(10, len(df_compuestos))
    if num_preguntas_a_generar == 0:
        return render_template('test.html', titulo=TITULO, error="No hay compuestos en la base de datos para generar preguntas.")

    preguntas_df_sample = df_compuestos.sample(n=num_preguntas_a_generar).reset_index(drop=True)
    preguntas_para_test = []

    for index, row in preguntas_df_sample.iterrows():
        # Decidir si la pregunta es de fórmula a nombre o de nombre a fórmula
        pregunta_formula_a_nombre = random.choice([True, False])

        if pregunta_formula_a_nombre: # Dar fórmula, pedir nombre
            opciones_nomenclatura = []
            if pd.notna(row['Sistematica']):
                opciones_nomenclatura.append(('Sistemática', row['Sistematica']))
            if pd.notna(row['Stock']):
                opciones_nomenclatura.append(('Stock', row['Stock']))
            if pd.notna(row['Tradicional']):
                opciones_nomenclatura.append(('Tradicional', row['Tradicional']))

            if opciones_nomenclatura:
                tipo_nom_elegida, respuesta_correcta = random.choice(opciones_nomenclatura)
                enunciado = f"¿Cuál es la nomenclatura {tipo_nom_elegida} de la fórmula: <strong>{row['Formula2']}</strong>?"
                preguntas_para_test.append({
                    'enunciado': enunciado,
                    'respuesta': str(respuesta_correcta),
                    'tipo_pregunta': 'formula_a_nombre',
                    'formula_original': row['Formula2'],
                    'tipo_nomenclatura_pedida': tipo_nom_elegida
                })
            else:
                # Si no hay nomenclaturas disponibles, saltar esta fila o generar otro tipo de pregunta
                continue # Saltar esta iteración
        else: # Dar nombre, pedir fórmula
            opciones_nomenclatura_para_pregunta = []
            if pd.notna(row['Sistematica']):
                opciones_nomenclatura_para_pregunta.append(row['Sistematica'])
            if pd.notna(row['Stock']):
                opciones_nomenclatura_para_pregunta.append(row['Stock'])
            if pd.notna(row['Tradicional']):
                opciones_nomenclatura_para_pregunta.append(row['Tradicional'])

            if opciones_nomenclatura_para_pregunta:
                nomenclatura_elegida = random.choice(opciones_nomenclatura_para_pregunta)
                enunciado = f"¿Cuál es la fórmula química de: <strong>{nomenclatura_elegida}</strong>?"
                preguntas_para_test.append({
                    'enunciado': enunciado,
                    'respuesta': str(row['Formula2']), # La respuesta correcta es la fórmula
                    'tipo_pregunta': 'nombre_a_formula',
                    'nomenclatura_original': nomenclatura_elegida
                })
            else:
                # Si no hay nomenclaturas disponibles, saltar esta fila o generar otro tipo de pregunta
                continue # Saltar esta iteración

    # Asegurarse de que tenemos un número razonable de preguntas
    if not preguntas_para_test:
        return render_template('test.html', titulo=TITULO, error="No se pudieron generar preguntas válidas. Verifica el contenido de tu archivo de datos.")

    session['test_preguntas'] = preguntas_para_test
    session['test_respuestas_usuario'] = [None] * len(preguntas_para_test)
    session['test_indice_actual'] = 0

    # Redirigir a la primera pregunta
    return redirect(url_for('mostrar_pregunta', indice=0))


@app.route('/pregunta/<int:indice>', methods=['GET'])
def mostrar_pregunta(indice):
    preguntas = session.get('test_preguntas')
    if not preguntas or indice >= len(preguntas) or indice < 0:
        # Si no hay test en progreso o el índice es inválido, redirigir al inicio del test
        return redirect(url_for('test'))

    pregunta_actual = preguntas[indice]
    total_preguntas = len(preguntas)
    
    return render_template('pregunta.html',
                           titulo=TITULO,
                           pregunta=pregunta_actual,
                           indice_actual=indice,
                           total_preguntas=total_preguntas)


@app.route('/responder', methods=['POST'])
def responder_pregunta():
    preguntas = session.get('test_preguntas')
    respuestas_usuario = session.get('test_respuestas_usuario')
    indice_actual = session.get('test_indice_actual')

    if not preguntas or respuestas_usuario is None or indice_actual is None:
        # Si la sesión no es válida (por ejemplo, el usuario cerró el navegador y volvió)
        return redirect(url_for('test'))

    respuesta_dada = request.form['respuesta'].strip()

    # Almacenar la respuesta del usuario
    if indice_actual < len(respuestas_usuario): # Asegurarse de que el índice sea válido
        respuestas_usuario[indice_actual] = respuesta_dada
        session['test_respuestas_usuario'] = respuestas_usuario

    # Incrementar el índice para la próxima pregunta
    session['test_indice_actual'] = indice_actual + 1

    if session['test_indice_actual'] < len(preguntas):
        # Todavía hay preguntas, ir a la siguiente
        return redirect(url_for('mostrar_pregunta', indice=session['test_indice_actual']))
    else:
        # Todas las preguntas respondidas, ir a evaluar
        return redirect(url_for('evaluar_test'))

@app.route('/evaluar_test')
def evaluar_test():
    preguntas = session.get('test_preguntas')
    respuestas_usuario = session.get('test_respuestas_usuario')

    if not preguntas or not respuestas_usuario:
        return redirect(url_for('test')) # Si no hay datos, volver al test

    puntaje = 0
    resultados_test = []

    for i, pregunta in enumerate(preguntas):
        respuesta_correcta = str(pregunta['respuesta']).strip()
        respuesta_dada = str(respuestas_usuario[i]).strip() if respuestas_usuario[i] is not None else ""

        es_correcta = False
        if pregunta['tipo_pregunta'] == 'nombre_a_formula':
            # Para fórmulas, normalizar ambas para comparar
            es_correcta = normalizar_formula(respuesta_dada) == normalizar_formula(respuesta_correcta)
        else: # 'formula_a_nombre'
            # Para nombres, comparar de forma insensible a mayúsculas/minúsculas y espacios extra
            es_correcta = respuesta_dada.lower() == respuesta_correcta.lower()

        if es_correcta:
            puntaje += 1

        resultados_test.append({
            'enunciado': pregunta['enunciado'],
            'respuesta_usuario': respuesta_dada,
            'respuesta_correcta': respuesta_correcta,
            'correcta': es_correcta
        })

    total_preguntas = len(preguntas)

    # Limpiar la sesión del test después de la evaluación para que un nuevo test inicie limpio
    session.pop('test_preguntas', None)
    session.pop('test_respuestas_usuario', None)
    session.pop('test_indice_actual', None)

    return render_template('resultados_test.html',
                           titulo=TITULO,
                           puntaje=puntaje,
                           total=total_preguntas,
                           resultados=resultados_test)

if __name__ == '__main__':
    app.run(debug=True)
