import os
import time
from flask import Flask, jsonify, render_template_string
import psycopg2

app = Flask(__name__)

# Configuración mediante variables de entorno
APP_NAME = os.getenv("APP_NAME", "Aplicación Flask DevOps")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "devops_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

def get_db_connection():
    """Intenta conectar a la base de datos con reintentos."""
    retries = 5
    while retries > 0:
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            return conn
        except psycopg2.OperationalError:
            retries -= 1
            time.sleep(2)
    return None

def init_db():
    """Crea la tabla e inserta 5 registros iniciales."""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        # Crear tabla
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                precio NUMERIC(10, 2) NOT NULL,
                stock INT NOT NULL
            );
        ''')
        
        # Verificar si ya hay datos para no duplicar
        cursor.execute("SELECT COUNT(*) FROM productos;")
        if cursor.fetchone()[0] == 0:
            productos_iniciales = [
                ('Laptop', 800.00, 10),
                ('Mouse', 20.00, 50),
                ('Teclado', 45.00, 30),
                ('Monitor', 250.00, 15),
                ('Auriculares', 60.00, 25)
            ]
            cursor.executemany(
                "INSERT INTO productos (nombre, precio, stock) VALUES (%s, %s, %s);",
                productos_iniciales
            )
        conn.commit()
        cursor.close()
        conn.close()

# Inicializar la base de datos al arrancar
init_db()

@app.route('/')
def index():
    conn = get_db_connection()
    if conn:
        status = "Conectado exitosamente"
        conn.close()
    else:
        status = "Error de conexión"

    html = f"""
    <h1>{APP_NAME}</h1>
    <p><b>Versión actual:</b> {APP_VERSION}</p>
    <p><b>Estado de conexión con PostgreSQL:</b> {status}</p>
    <p><a href="/productos">Ver Productos</a></p>
    """
    return render_template_string(html)

@app.route('/productos')
def get_productos():
    conn = get_db_connection()
    if not conn:
        return jsonify({{"error": "No se pudo conectar a la base de datos"}}), 500
    
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, precio, stock FROM productos;")
    rows = cursor.fetchall()
    
    productos = []
    for row in rows:
        productos.append({
            "id": row[0],
            "nombre": row[1],
            "precio": float(row[2]),
            "stock": row[3]
        })
    
    cursor.close()
    conn.close()
    return jsonify(productos)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)