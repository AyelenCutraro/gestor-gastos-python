import sqlite3
import calendar
from datetime import datetime, date

# ==========================================
# 0. CATÁLOGO DE TARJETAS (Argentina)
# ==========================================
# Pensado para reutilizarse en la futura app Kivy (Spinner, colores, logos).
# Los colores son aproximados: ajustalos a gusto.
# "logo" es la ruta donde guardarías la imagen dentro del proyecto.

TARJETAS_ARGENTINA = {
    "Visa":             {"color": "#1A1F71", "logo": "assets/logos/visa.png"},
    "Mastercard":       {"color": "#EB001B", "logo": "assets/logos/mastercard.png"},
    "American Express": {"color": "#006FCF", "logo": "assets/logos/amex.png"},
    "Naranja X":        {"color": "#FF6600", "logo": "assets/logos/naranja.png"},
    "Mercado Pago":     {"color": "#00B1EA", "logo": "assets/logos/mercadopago.png"},
    "Cabal":            {"color": "#005DAA", "logo": "assets/logos/cabal.png"},
    "Ualá":             {"color": "#3D5AFE", "logo": "assets/logos/uala.png"},
    "Brubank":          {"color": "#6B2FD1", "logo": "assets/logos/brubank.png"},
    "Tarjeta Nevada":   {"color": "#E30613", "logo": "assets/logos/nevada.png"},
    "Carrefour":        {"color": "#004E9F", "logo": "assets/logos/carrefour.png"},
    "Cencosud":         {"color": "#E4002B", "logo": "assets/logos/cencosud.png"},
}

ESTILO_POR_DEFECTO = {"color": "#607D8B", "logo": "assets/logos/generica.png"}


def obtener_estilo_tarjeta(nombre):
    """
    Devuelve {'color':..., 'logo':...} para una tarjeta guardada.
    Como el nombre puede incluir el banco (ej: 'Visa Santander'),
    busca por prefijo. Si no encuentra, devuelve un estilo genérico.
    """
    for base, estilo in TARJETAS_ARGENTINA.items():
        if nombre.lower().startswith(base.lower()):
            return estilo
    return ESTILO_POR_DEFECTO


# ==========================================
# 1. CONEXIÓN Y BASE DE DATOS
# ==========================================

def conectar_db():
    conexion = sqlite3.connect("gastos.db")
    return conexion

def crear_tablas():
    conexion = conectar_db()
    cursor = conexion.cursor()

    # Tabla original de gastos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            categoria TEXT NOT NULL,
            monto REAL NOT NULL,
            fecha TEXT NOT NULL
        )
    """)

    # Tabla de tarjetas de crédito
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tarjetas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            dia_cierre INTEGER NOT NULL,
            dia_vencimiento INTEGER NOT NULL,
            limite REAL DEFAULT 0
        )
    """)

    # Tabla de compras con tarjeta (en cuotas o no)
    # Incluye fecha_ultimo_pago para evitar pagar dos veces la misma cuota
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compras_tarjeta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarjeta_id INTEGER NOT NULL,
            descripcion TEXT NOT NULL,
            monto_total REAL NOT NULL,
            cuotas_totales INTEGER NOT NULL,
            cuotas_pagadas INTEGER DEFAULT 0,
            fecha_compra TEXT NOT NULL,
            fecha_ultimo_pago TEXT DEFAULT NULL,
            FOREIGN KEY (tarjeta_id) REFERENCES tarjetas(id)
        )
    """)

    # Tabla de servicios (luz, gas, internet, etc.)
    # fecha_vencimiento se guarda como AAAA-MM-DD
    # dias_aviso: cuántos días antes del vencimiento empieza a avisar
    # recurrente = 1: al pagarlo, el vencimiento pasa al mes siguiente
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS servicios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            monto REAL DEFAULT 0,
            fecha_vencimiento TEXT NOT NULL,
            dias_aviso INTEGER DEFAULT 3,
            recurrente INTEGER DEFAULT 1,
            pagado INTEGER DEFAULT 0
        )
    """)

    conexion.commit()
    conexion.close()

# ==========================================
# 2. FUNCIONES DE GASTOS GENERALES
# ==========================================

def registrar_gasto(descripcion, categoria, monto):
    conexion = conectar_db()
    cursor = conexion.cursor()
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor.execute(
        "INSERT INTO gastos (descripcion, categoria, monto, fecha) VALUES (?, ?, ?, ?)",
        (descripcion, categoria, monto, fecha_actual)
    )
    conexion.commit()
    conexion.close()

def consultar_gastos():
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM gastos")
    gastos = cursor.fetchall()
    conexion.close()
    return gastos

def buscar_por_categoria(categoria):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM gastos WHERE categoria = ?", (categoria,))
    resultados = cursor.fetchall()
    conexion.close()
    return resultados

def eliminar_gasto(id_gasto):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM gastos WHERE id = ?", (id_gasto,))
    conexion.commit()
    conexion.close()

# ==========================================
# 3. FUNCIONES DE TARJETAS
# ==========================================

def crear_tarjeta(nombre, dia_cierre, dia_vencimiento, limite=0):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute(
        "INSERT INTO tarjetas (nombre, dia_cierre, dia_vencimiento, limite) VALUES (?, ?, ?, ?)",
        (nombre, dia_cierre, dia_vencimiento, limite)
    )
    conexion.commit()
    conexion.close()

def listar_tarjetas():
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM tarjetas")
    tarjetas = cursor.fetchall()
    conexion.close()
    return tarjetas

def eliminar_tarjeta(id_tarjeta):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM compras_tarjeta WHERE tarjeta_id = ?", (id_tarjeta,))
    cursor.execute("DELETE FROM tarjetas WHERE id = ?", (id_tarjeta,))
    conexion.commit()
    conexion.close()

def registrar_compra_tarjeta(tarjeta_id, descripcion, monto_total, cuotas):
    conexion = conectar_db()
    cursor = conexion.cursor()
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        """INSERT INTO compras_tarjeta 
           (tarjeta_id, descripcion, monto_total, cuotas_totales, cuotas_pagadas, fecha_compra, fecha_ultimo_pago) 
           VALUES (?, ?, ?, ?, 0, ?, NULL)""",
        (tarjeta_id, descripcion, monto_total, cuotas, fecha_actual)
    )
    conexion.commit()
    conexion.close()

def listar_compras_tarjeta(tarjeta_id=None):
    conexion = conectar_db()
    cursor = conexion.cursor()
    if tarjeta_id:
        cursor.execute("""
            SELECT c.id, t.nombre, c.descripcion, c.monto_total, 
                   c.cuotas_totales, c.cuotas_pagadas, c.fecha_compra, c.fecha_ultimo_pago
            FROM compras_tarjeta c
            JOIN tarjetas t ON c.tarjeta_id = t.id
            WHERE c.tarjeta_id = ?
        """, (tarjeta_id,))
    else:
        cursor.execute("""
            SELECT c.id, t.nombre, c.descripcion, c.monto_total, 
                   c.cuotas_totales, c.cuotas_pagadas, c.fecha_compra, c.fecha_ultimo_pago
            FROM compras_tarjeta c
            JOIN tarjetas t ON c.tarjeta_id = t.id
        """)
    compras = cursor.fetchall()
    conexion.close()
    return compras

def pagar_cuota(id_compra, forzar=False):
    """
    Registra el pago de una cuota.
    Si ya se pagó una cuota este mes, pide confirmación (a menos que forzar=True).
    Devuelve un mensaje con el resultado.
    """
    conexion = conectar_db()
    cursor = conexion.cursor()

    # 1. Traemos los datos actuales de la compra
    cursor.execute("""
        SELECT descripcion, monto_total, cuotas_totales, cuotas_pagadas, fecha_ultimo_pago
        FROM compras_tarjeta WHERE id = ?
    """, (id_compra,))
    resultado = cursor.fetchone()

    if not resultado:
        conexion.close()
        return "❌ No existe una compra con ese ID."

    descripcion, monto_total, cuotas_totales, cuotas_pagadas, fecha_ultimo_pago = resultado

    # 2. Verificamos si ya está completamente pagada
    if cuotas_pagadas >= cuotas_totales:
        conexion.close()
        return f"⚠️ La compra '{descripcion}' ya tiene todas sus cuotas pagadas ({cuotas_totales}/{cuotas_totales})."

    # 3. Verificamos si ya se pagó una cuota este mes
    if fecha_ultimo_pago and not forzar:
        fecha_ultimo = datetime.strptime(fecha_ultimo_pago, "%Y-%m-%d")
        hoy = datetime.now()

        if fecha_ultimo.year == hoy.year and fecha_ultimo.month == hoy.month:
            conexion.close()
            return (f"⚠️ Ya registraste un pago de esta compra el "
                    f"{fecha_ultimo.strftime('%d/%m/%Y')}. "
                    f"¿Seguro que querés pagar otra cuota este mes?")

    # 4. Registramos el pago con la fecha actual
    fecha_pago = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        UPDATE compras_tarjeta 
        SET cuotas_pagadas = cuotas_pagadas + 1,
            fecha_ultimo_pago = ?
        WHERE id = ?
    """, (fecha_pago, id_compra))

    conexion.commit()
    conexion.close()

    nueva_cuota = cuotas_pagadas + 1
    monto_cuota = monto_total / cuotas_totales
    return (f"✅ Cuota {nueva_cuota}/{cuotas_totales} pagada "
            f"(${monto_cuota:,.2f}) el {datetime.now().strftime('%d/%m/%Y')}.")

def calcular_saldo_pendiente(id_compra):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute("SELECT monto_total, cuotas_totales, cuotas_pagadas FROM compras_tarjeta WHERE id = ?", (id_compra,))
    resultado = cursor.fetchone()
    conexion.close()
    
    if not resultado:
        return 0
    
    monto_total, cuotas_totales, cuotas_pagadas = resultado
    monto_por_cuota = monto_total / cuotas_totales
    cuotas_restantes = cuotas_totales - cuotas_pagadas
    return monto_por_cuota * cuotas_restantes

# ==========================================
# 4. RECORDATORIOS Y CÁLCULOS
# ==========================================

def dias_hasta_proximo_dia(dia_objetivo):
    """Calcula cuántos días faltan para el próximo 'día X' del mes."""
    hoy = date.today()
    
    # Intentamos con este mes
    try:
        proxima_fecha = date(hoy.year, hoy.month, dia_objetivo)
    except ValueError:
        # Si el día no existe en este mes (ej: 31 en febrero), usamos el 28
        proxima_fecha = date(hoy.year, hoy.month, 28)
    
    # Si ya pasó, vamos al mes siguiente
    if proxima_fecha < hoy:
        if hoy.month == 12:
            proxima_fecha = date(hoy.year + 1, 1, dia_objetivo)
        else:
            try:
                proxima_fecha = date(hoy.year, hoy.month + 1, dia_objetivo)
            except ValueError:
                proxima_fecha = date(hoy.year, hoy.month + 1, 28)
    
    return (proxima_fecha - hoy).days, proxima_fecha

def mostrar_recordatorios():
    tarjetas = listar_tarjetas()
    
    if not tarjetas:
        print("\n⚠️ No tenés tarjetas registradas todavía.")
        return
    
    print("\n" + "="*60)
    print("       🔔 RECORDATORIOS DE TARJETAS")
    print("="*60)
    
    for t in tarjetas:
        id_t, nombre, dia_cierre, dia_venc, limite = t
        
        dias_cierre, fecha_cierre = dias_hasta_proximo_dia(dia_cierre)
        # CORREGIDO: antes decía dia_vencimiento (variable inexistente)
        dias_venc, fecha_venc = dias_hasta_proximo_dia(dia_venc)
        
        print(f"\n💳 {nombre} (ID: {id_t})")
        print(f"   📅 Cierre: {fecha_cierre.strftime('%d/%m/%Y')} — faltan {dias_cierre} días")
        print(f"   💰 Vencimiento: {fecha_venc.strftime('%d/%m/%Y')} — faltan {dias_venc} días")
        
        # Calcular saldo pendiente total de esa tarjeta
        compras = listar_compras_tarjeta(id_t)
        saldo_total = 0
        for c in compras:
            # c = (id, nombre, desc, monto_total, cuotas_tot, cuotas_pag, fecha_compra, fecha_ultimo_pago)
            monto_total, cuotas_tot, cuotas_pag = c[3], c[4], c[5]
            if cuotas_pag < cuotas_tot:
                monto_por_cuota = monto_total / cuotas_tot
                saldo_total += monto_por_cuota * (cuotas_tot - cuotas_pag)
        
        print(f"   📊 Saldo pendiente total: ${saldo_total:,.2f}")
        
        # Aviso si el cierre o vencimiento están cerca
        if dias_cierre <= 3:
            print(f"   ⚠️ ¡ATENCIÓN! El cierre es en {dias_cierre} días.")
        if dias_venc <= 3:
            print(f"   🚨 ¡URGENTE! El vencimiento es en {dias_venc} días.")
    
    print("\n" + "="*60)

def mostrar_compras_con_saldo():
    compras = listar_compras_tarjeta()
    
    if not compras:
        print("\n⚠️ No hay compras registradas con tarjeta.")
        return
    
    print("\n" + "="*110)
    print("       📋 COMPRAS CON TARJETA Y CUOTAS PENDIENTES")
    print("="*110)
    print(f"{'ID':<4} | {'Tarjeta':<13} | {'Descripción':<16} | {'Total':<10} | {'Cuotas':<7} | {'Pendiente':<11} | {'Últ. pago':<10}")
    print("-"*110)
    
    for c in compras:
        # c = (id, nombre, desc, monto_total, cuotas_tot, cuotas_pag, fecha_compra, fecha_ultimo_pago)
        id_c, nombre_t, desc, monto_total, cuotas_tot, cuotas_pag, fecha_compra, fecha_ultimo_pago = c
        monto_por_cuota = monto_total / cuotas_tot
        pendiente = monto_por_cuota * (cuotas_tot - cuotas_pag)
        cuotas_str = f"{cuotas_pag}/{cuotas_tot}"
        ultimo_pago_str = fecha_ultimo_pago if fecha_ultimo_pago else "—"
        print(f"{id_c:<4} | {nombre_t:<13} | {desc:<16} | ${monto_total:<9.2f} | {cuotas_str:<7} | ${pendiente:<10.2f} | {ultimo_pago_str:<10}")
    
    print("-"*110)

# ==========================================
# 4B. SERVICIOS, FECHAS Y ALERTAS
# ==========================================

SERVICIOS_COMUNES = [
    "Luz", "Gas", "Agua", "Internet", "Celular", "Cable / TV",
    "Streaming", "Alquiler", "Expensas", "Impuesto municipal",
    "Patente", "Seguro",
]

def pedir_fecha(texto):
    """Pide una fecha DD/MM/AAAA hasta que sea válida. Devuelve 'AAAA-MM-DD'."""
    while True:
        valor = input(texto).strip()
        try:
            return datetime.strptime(valor, "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            print("❌ Formato inválido. Usá DD/MM/AAAA (ej: 25/10/2026).")

def sumar_un_mes(fecha_iso):
    """Suma un mes a una fecha 'AAAA-MM-DD' respetando el largo de cada mes."""
    f = datetime.strptime(fecha_iso, "%Y-%m-%d").date()
    mes = f.month % 12 + 1
    anio = f.year + (1 if f.month == 12 else 0)
    dia = min(f.day, calendar.monthrange(anio, mes)[1])
    return date(anio, mes, dia).strftime("%Y-%m-%d")

def estado_vencimiento(dias):
    if dias < 0:
        return f"🚨 Vencido hace {-dias} d"
    if dias == 0:
        return "🚨 Vence HOY"
    if dias <= 3:
        return f"⚠️ Vence en {dias} d"
    return f"En {dias} días"

def crear_servicio(nombre, monto, fecha_vencimiento, dias_aviso=3, recurrente=1):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute(
        """INSERT INTO servicios (nombre, monto, fecha_vencimiento, dias_aviso, recurrente)
           VALUES (?, ?, ?, ?, ?)""",
        (nombre, monto, fecha_vencimiento, dias_aviso, recurrente)
    )
    conexion.commit()
    conexion.close()

def listar_servicios():
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT id, nombre, monto, fecha_vencimiento, dias_aviso, recurrente, pagado
        FROM servicios ORDER BY pagado, fecha_vencimiento
    """)
    servicios = cursor.fetchall()
    conexion.close()
    return servicios

def eliminar_servicio(id_servicio):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM servicios WHERE id = ?", (id_servicio,))
    conexion.commit()
    conexion.close()

def pagar_servicio(id_servicio):
    """
    Marca un servicio como pagado.
    - Recurrente: el vencimiento pasa al mes siguiente.
    - No recurrente: queda marcado como pagado.
    Si tiene monto, además lo registra como gasto (categoría 'Servicios').
    """
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT nombre, monto, fecha_vencimiento, recurrente FROM servicios WHERE id = ?",
        (id_servicio,)
    )
    resultado = cursor.fetchone()

    if not resultado:
        conexion.close()
        return "❌ No existe un servicio con ese ID."

    nombre, monto, fecha_venc, recurrente = resultado

    if recurrente:
        nueva_fecha = sumar_un_mes(fecha_venc)
        cursor.execute(
            "UPDATE servicios SET fecha_vencimiento = ? WHERE id = ?",
            (nueva_fecha, id_servicio)
        )
        mensaje = (f"✅ '{nombre}' pagado. Próximo vencimiento: "
                   f"{datetime.strptime(nueva_fecha, '%Y-%m-%d').strftime('%d/%m/%Y')}.")
    else:
        cursor.execute("UPDATE servicios SET pagado = 1 WHERE id = ?", (id_servicio,))
        mensaje = f"✅ '{nombre}' marcado como pagado."

    conexion.commit()
    conexion.close()

    if monto and monto > 0:
        registrar_gasto(f"Pago {nombre}", "Servicios", monto)

    return mensaje

def mostrar_servicios():
    servicios = listar_servicios()

    if not servicios:
        print("\n⚠️ No hay servicios registrados.")
        return

    hoy = date.today()
    print("\n" + "="*75)
    print("       🏠 SERVICIOS Y VENCIMIENTOS")
    print("="*75)
    print(f"{'ID':<4} | {'Servicio':<18} | {'Monto':<11} | {'Vence':<10} | Estado")
    print("-"*75)

    for id_s, nombre, monto, fecha_iso, aviso, recurrente, pagado in servicios:
        fecha = datetime.strptime(fecha_iso, "%Y-%m-%d").date()
        dias = (fecha - hoy).days
        estado = "✅ Pagado" if pagado else estado_vencimiento(dias)
        tipo = " 🔁" if recurrente else ""
        print(f"{id_s:<4} | {nombre:<18} | ${monto:<10.2f} | "
              f"{fecha.strftime('%d/%m/%Y'):<10} | {estado}{tipo}")

    print("-"*75)
    print("🔁 = se repite todos los meses")

def obtener_alertas(dias_aviso_tarjeta=3):
    """
    Devuelve una lista de alertas ordenadas por urgencia:
    (tipo, nombre, fecha, dias_restantes)
    Incluye servicios (según su 'dias_aviso') y cierres/vencimientos de tarjetas.
    """
    alertas = []
    hoy = date.today()

    for id_s, nombre, monto, fecha_iso, aviso, recurrente, pagado in listar_servicios():
        if pagado:
            continue
        fecha = datetime.strptime(fecha_iso, "%Y-%m-%d").date()
        dias = (fecha - hoy).days
        if dias <= aviso:
            alertas.append(("Servicio", nombre, fecha, dias))

    for id_t, nombre, dia_cierre, dia_venc, limite in listar_tarjetas():
        dias, fecha = dias_hasta_proximo_dia(dia_venc)
        if dias <= dias_aviso_tarjeta:
            alertas.append(("Vencimiento tarjeta", nombre, fecha, dias))
        dias, fecha = dias_hasta_proximo_dia(dia_cierre)
        if dias <= dias_aviso_tarjeta:
            alertas.append(("Cierre tarjeta", nombre, fecha, dias))

    alertas.sort(key=lambda a: a[3])
    return alertas

def mostrar_alertas(mostrar_si_vacio=True):
    alertas = obtener_alertas()

    if not alertas:
        if mostrar_si_vacio:
            print("\n✅ No tenés vencimientos próximos. ¡Todo al día!")
        return

    print("\n" + "="*60)
    print("       🔔 PRÓXIMOS VENCIMIENTOS")
    print("="*60)
    for tipo, nombre, fecha, dias in alertas:
        print(f"{estado_vencimiento(dias):<24} | {tipo}: {nombre} ({fecha.strftime('%d/%m/%Y')})")
    print("="*60)

def elegir_servicio_del_menu():
    """Muestra el menú de servicios comunes y devuelve el nombre elegido."""
    print("\n¿Qué servicio querés agregar?")
    for i, nombre in enumerate(SERVICIOS_COMUNES, start=1):
        print(f"{i:>2}. {nombre}")
    otro = len(SERVICIOS_COMUNES) + 1
    print(f"{otro:>2}. Otro (escribir nombre)")

    try:
        eleccion = int(input("Elegí una opción: "))
    except ValueError:
        return None

    if 1 <= eleccion <= len(SERVICIOS_COMUNES):
        return SERVICIOS_COMUNES[eleccion - 1]
    if eleccion == otro:
        return input("Nombre del servicio: ").strip() or None
    return None

def mostrar_menu_servicios():
    print("\n--- SERVICIOS Y VENCIMIENTOS ---")
    print("1. Agregar servicio")
    print("2. Ver servicios")
    print("3. Marcar servicio como pagado")
    print("4. Eliminar servicio")
    print("5. Volver al menú principal")

def menu_servicios():
    while True:
        mostrar_menu_servicios()
        opcion = input("Elige una opción (1-5): ")

        if opcion == "1":
            nombre = elegir_servicio_del_menu()
            if not nombre:
                print("❌ Opción inválida.")
                continue
            try:
                monto_str = input("Monto aproximado (Enter para omitir): ")
                monto = float(monto_str) if monto_str else 0
                fecha_venc = pedir_fecha("Fecha de vencimiento (DD/MM/AAAA): ")
                aviso_str = input("¿Cuántos días antes querés el aviso? (Enter = 3): ")
                aviso = int(aviso_str) if aviso_str else 3
                rec = input("¿Se repite todos los meses? (s/n, Enter = s): ").lower()
                recurrente = 0 if rec == "n" else 1
                crear_servicio(nombre, monto, fecha_venc, aviso, recurrente)
                print(f"✅ Servicio '{nombre}' agregado.")
            except ValueError:
                print("❌ Monto o días inválidos.")

        elif opcion == "2":
            mostrar_servicios()

        elif opcion == "3":
            mostrar_servicios()
            try:
                id_s = int(input("ID del servicio que pagaste: "))
                print(pagar_servicio(id_s))
            except ValueError:
                print("❌ ID inválido.")

        elif opcion == "4":
            mostrar_servicios()
            try:
                id_s = int(input("ID del servicio a eliminar: "))
                confirmar = input("¿Confirmás? (s/n): ")
                if confirmar.lower() == "s":
                    eliminar_servicio(id_s)
                    print("🗑️ Servicio eliminado.")
                else:
                    print("Cancelado.")
            except ValueError:
                print("❌ ID inválido.")

        elif opcion == "5":
            break
        else:
            print("❌ Opción no válida.")

# ==========================================
# 5. MENÚS
# ==========================================

def mostrar_menu_principal():
    print("\n" + "="*40)
    print("       GESTOR DE GASTOS PERSONALES")
    print("="*40)
    print("1. Gastos generales")
    print("2. Tarjetas de crédito")
    print("3. Servicios (luz, gas, internet...)")
    print("4. 🔔 Ver próximos vencimientos")
    print("5. Salir")
    print("="*40)

def mostrar_menu_gastos():
    print("\n--- GASTOS GENERALES ---")
    print("1. Registrar nuevo gasto")
    print("2. Ver todos los gastos")
    print("3. Buscar por categoría")
    print("4. Eliminar un gasto")
    print("5. Volver al menú principal")

def mostrar_menu_tarjetas():
    print("\n--- TARJETAS DE CRÉDITO ---")
    print("1. Agregar tarjeta")
    print("2. Ver mis tarjetas")
    print("3. Registrar compra con tarjeta")
    print("4. Ver compras y cuotas pendientes")
    print("5. Pagar una cuota")
    print("6. 🔔 Ver recordatorios y saldos")
    print("7. Eliminar tarjeta")
    print("8. Volver al menú principal")

def elegir_tarjeta_del_menu():
    """Muestra el menú de tarjetas argentinas y devuelve el nombre elegido."""
    nombres = list(TARJETAS_ARGENTINA.keys())

    print("\n¿Qué tarjeta querés agregar?")
    for i, nombre in enumerate(nombres, start=1):
        print(f"{i:>2}. {nombre}")
    otra = len(nombres) + 1
    print(f"{otra:>2}. Otra (escribir nombre)")

    try:
        eleccion = int(input("Elegí una opción: "))
    except ValueError:
        return None

    if 1 <= eleccion <= len(nombres):
        base = nombres[eleccion - 1]
    elif eleccion == otra:
        return input("Nombre de la tarjeta: ").strip() or None
    else:
        return None

    # Opcional: banco emisor (útil para Visa/Mastercard/Amex)
    banco = input(f"Banco emisor de tu {base} (Enter para omitir): ").strip()
    return f"{base} {banco}" if banco else base

# ==========================================
# 6. LÓGICA DE LOS MENÚS
# ==========================================

def menu_gastos():
    while True:
        mostrar_menu_gastos()
        opcion = input("Elige una opción (1-5): ")

        if opcion == "1":
            desc = input("Descripción: ")
            cat = input("Categoría: ")
            try:
                monto = float(input("Monto: "))
                registrar_gasto(desc, cat, monto)
                print("✅ Gasto registrado.")
            except ValueError:
                print("❌ Monto inválido.")

        elif opcion == "2":
            gastos = consultar_gastos()
            if not gastos:
                print("No hay gastos registrados.")
            else:
                print("\n" + "-"*70)
                for g in gastos:
                    print(f"ID {g[0]:<4} | {g[4]:<16} | {g[1]:<18} | {g[2]:<12} | ${g[3]:.2f}")
                print("-"*70)

        elif opcion == "3":
            cat = input("Categoría a buscar: ")
            resultados = buscar_por_categoria(cat)
            if resultados:
                for r in resultados:
                    print(f"  - {r[4]} | {r[1]} | ${r[3]}")
            else:
                print(f"No se encontraron gastos en '{cat}'.")

        elif opcion == "4":
            try:
                id_eliminar = int(input("ID a eliminar: "))
                eliminar_gasto(id_eliminar)
                print("🗑️ Eliminado.")
            except ValueError:
                print("❌ ID inválido.")

        elif opcion == "5":
            break
        else:
            print("❌ Opción no válida.")

def menu_tarjetas():
    while True:
        mostrar_menu_tarjetas()
        opcion = input("Elige una opción (1-8): ")

        if opcion == "1":
            nombre = elegir_tarjeta_del_menu()
            if not nombre:
                print("❌ Opción inválida.")
                continue
            try:
                dia_cierre = int(input("Día de cierre (1-31): "))
                dia_venc = int(input("Día de vencimiento (1-31): "))
                limite_str = input("Límite (opcional, Enter para omitir): ")
                limite = float(limite_str) if limite_str else 0
                crear_tarjeta(nombre, dia_cierre, dia_venc, limite)
                print(f"✅ Tarjeta '{nombre}' agregada.")
            except ValueError:
                print("❌ Días o límite inválidos.")

        elif opcion == "2":
            tarjetas = listar_tarjetas()
            if not tarjetas:
                print("No hay tarjetas registradas.")
            else:
                for t in tarjetas:
                    print(f"  ID {t[0]} | {t[1]} | Cierre día {t[2]} | Venc. día {t[3]} | Límite: ${t[4]:.2f}")

        elif opcion == "3":
            tarjetas = listar_tarjetas()
            if not tarjetas:
                print("Primero agregá una tarjeta.")
                continue
            for t in tarjetas:
                print(f"  ID {t[0]} | {t[1]}")
            try:
                id_t = int(input("ID de la tarjeta: "))
                desc = input("Descripción de la compra: ")
                monto = float(input("Monto total: "))
                cuotas = int(input("¿En cuántas cuotas? (1 = pago único): "))
                registrar_compra_tarjeta(id_t, desc, monto, cuotas)
                print(f"✅ Compra registrada. {cuotas} cuota(s) de ${monto/cuotas:.2f} cada una.")
            except ValueError:
                print("❌ Datos inválidos.")

        elif opcion == "4":
            mostrar_compras_con_saldo()

        elif opcion == "5":
            try:
                id_c = int(input("ID de la compra a la que le pagaste una cuota: "))
                resultado = pagar_cuota(id_c)

                # Si el sistema pide confirmación, le preguntamos al usuario
                if resultado.startswith("⚠️ Ya registraste"):
                    print(resultado)
                    confirmar = input("¿Confirmás que querés pagar otra cuota? (s/n): ")
                    if confirmar.lower() == "s":
                        resultado = pagar_cuota(id_c, forzar=True)
                        print(resultado)
                    else:
                        print("Cancelado. No se registró el pago.")
                else:
                    print(resultado)

            except ValueError:
                print("❌ ID inválido.")

        elif opcion == "6":
            mostrar_recordatorios()

        elif opcion == "7":
            try:
                id_t = int(input("ID de la tarjeta a eliminar: "))
                confirmar = input("⚠️ Esto también borra sus compras. ¿Confirmás? (s/n): ")
                if confirmar.lower() == "s":
                    eliminar_tarjeta(id_t)
                    print("🗑️ Tarjeta eliminada.")
                else:
                    print("Cancelado.")
            except ValueError:
                print("❌ ID inválido.")

        elif opcion == "8":
            break
        else:
            print("❌ Opción no válida.")

# ==========================================
# 7. PUNTO DE ENTRADA
# ==========================================

def main():
    crear_tablas()
    mostrar_alertas(mostrar_si_vacio=False)  # avisa al abrir si hay algo por vencer
    
    while True:
        mostrar_menu_principal()
        opcion = input("Elige una opción (1-5): ")
        
        if opcion == "1":
            menu_gastos()
        elif opcion == "2":
            menu_tarjetas()
        elif opcion == "3":
            menu_servicios()
        elif opcion == "4":
            mostrar_alertas()
        elif opcion == "5":
            print("\n¡Hasta luego! 👋")
            break
        else:
            print("❌ Opción no válida.")

if __name__ == "__main__":
    main()

