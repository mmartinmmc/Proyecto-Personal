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

# Función para buscar compuestos (versión corregida)
def buscar_compuesto(tipo_busqueda, valor_busqueda, nomenclatura_devolver=None):
    if df is None or df.empty:
        return None

    # Normalización del input
    valor_busqueda = str(valor_busqueda).strip().lower()

    if tipo_busqueda == "formula":
        # Búsqueda exacta por fórmula
        resultados = df[df['Formula'].astype(str).str.lower().str.strip() == valor_busqueda]
        
        # Filtrar columnas según nomenclatura
        if nomenclatura_devolver == "sistematica":
            resultados = resultados[['Formula2', 'Sistematica']]
        elif nomenclatura_devolver == "stock":
            resultados = resultados[['Formula2', 'Stock']]
        elif nomenclatura_devolver == "tradicional":
            resultados = resultados[['Formula2', 'Tradicional']]
        elif nomenclatura_devolver == "todas":
            resultados = resultados[['Formula2', 'Sistematica', 'Stock', 'Tradicional']]
    
    elif tipo_busqueda == "nomenclatura":
        # Búsqueda flexible en nomenclaturas
        mask = (
            df['Sistematica'].astype(str).str.lower().str.strip().str.contains(valor_busqueda, regex=False, na=False) |
            df['Stock'].astype(str).str.lower().str.strip().str.contains(valor_busqueda, regex=False, na=False) |
            df['Tradicional'].astype(str).str.lower().str.strip().str.contains(valor_busqueda, regex=False, na=False)
        )
        resultados = df[mask]
        
        # Filtrar columnas para mostrar
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
    
    return resultados if not resultados.empty else None

# Ruta para la página principal
@app.route('/')
def index():
    return render_template('index.html', titulo=TITULO)

# Ruta para la búsqueda
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

        return render_template('resultados.html',
                            titulo=TITULO,
                            tipo_busqueda=tipo_busqueda,
                            valor_busqueda=valor_busqueda,
                            resultados=resultados.to_dict('records'),
                            nomenclatura_devolver=nomenclatura_devolver,
                            error=None)
    except Exception as e:
        return render_template('resultados.html', titulo=TITULO, error=f"❌ Error interno: {str(e)}"), 500

if __name__ == '__main__':
    app.run(debug=True)
