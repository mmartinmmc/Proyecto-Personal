import os
import pandas as pd
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
        # Verificar que el archivo tenga las columnas necesarias
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
        return None  # Si no hay base de datos cargada o está vacía, devuelve None
    
    if tipo_busqueda == "formula":
        # Buscar por fórmula (usando Formula)
        resultados = df[df['Formula'].str.lower() == valor_busqueda.lower()]
        
        # Filtrar las columnas de nomenclatura según la selección del usuario
        if nomenclatura_devolver == "sistematica":
            resultados = resultados[['Formula2', 'Sistematica']]  # Mostrar Formula2
        elif nomenclatura_devolver == "stock":
            resultados = resultados[['Formula2', 'Stock']]
        elif nomenclatura_devolver == "tradicional":
            resultados = resultados[['Formula2', 'Tradicional']]
        elif nomenclatura_devolver == "todas":
            resultados = resultados[['Formula2', 'Sistematica', 'Stock', 'Tradicional']]
        else:
            return None  # Opción no válida
    
    elif tipo_busqueda == "nomenclatura":
        # Buscar por nomenclatura (en las tres columnas)
        resultados = df[
            (df['Sistematica'].str.lower() == valor_busqueda.lower()) |
            (df['Stock'].str.lower() == valor_busqueda.lower()) |
            (df['Tradicional'].str.lower() == valor_busqueda.lower())
        ]
        # Devolver solo las columnas necesarias
        resultados = resultados[['Formula2', 'Sistematica', 'Stock', 'Tradicional']]
    else:
        return None  # Tipo de búsqueda no válido
    
    # Verificar si el DataFrame está vacío usando .empty
    return resultados if not resultados.empty else None

# Ruta para la página principal
@app.route('/')
def index():
    return render_template('index.html', titulo=TITULO)

# Ruta para la búsqueda
@app.route('/buscar', methods=['POST'])
def buscar():
    try:
        tipo_busqueda = request.form.get('tipo_busqueda')  # Obtiene el tipo de búsqueda
        formula = request.form.get('formula')  # Obtiene la fórmula (si se seleccionó)
        nomenclatura = request.form.get('nomenclatura')  # Obtiene la nomenclatura (si se seleccionó)
        nomenclatura_devolver = request.form.get('nomenclatura_devolver')  # Obtiene la nomenclatura a devolver

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

        # Realizar la búsqueda
        resultados = buscar_compuesto(tipo_busqueda, valor_busqueda, nomenclatura_devolver)

        # Verificar si hay resultados
        if resultados is None or resultados.empty:
            return render_template('resultados.html', titulo=TITULO, error="No se encontraron resultados.")

        # Pasar el DataFrame y la nomenclatura seleccionada a la plantilla
        return render_template('resultados.html', titulo=TITULO, tipo_busqueda=tipo_busqueda,
                               valor_busqueda=valor_busqueda,
                               resultados=resultados,
                               nomenclatura_devolver=nomenclatura_devolver,  # Pasar la nomenclatura seleccionada
                               error=None)
    except Exception as e:
        return render_template('resultados.html', titulo=TITULO, error=f"❌ Error interno: {str(e)}"), 500

# Ejecutar en local
if __name__ == '__main__':
    app.run(debug=True)
