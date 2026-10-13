import sqlite3

def conectar_db():
    conexion = sqlite3.connect("gastos.db")
    return conexion

def crear_tabla():
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            categoria TEXT NOT NULL,
            monto REAL NOT NULL
        )
    """)

    conexion.commit()
    conexion.close()

def registrar_gasto(descripcion, categoria, monto):
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute(
        "INSERT INTO gastos (descripcion, categoria, monto) VALUES (?, ?, ?)",
        (descripcion, categoria, monto)
    )

    conexion.commit()
    conexion.close()

def consultar_gastos():
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("SELECT * FROM gastos")
    gastos = cursor.fetchall()

    for gasto in gastos:
        print(gasto)

    conexion.close()

if __name__ == "__main__":
    crear_tabla()
    registrar_gasto("Compra de supermercado", "Alimentos", 15000)
    print("Gastos registrados:")
    consultar_gastos()
