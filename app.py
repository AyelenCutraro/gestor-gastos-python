"""
Interfaz web (Streamlit) del gestor de gastos - versión con diseño.
Reutiliza la lógica de gestor_gastos.py.

Ejecutar:
    pip install streamlit
    streamlit run app.py
"""
import html
from datetime import date

import pandas as pd
import streamlit as st

import main as g 

st.set_page_config(page_title="Gestor de gastos", page_icon="💸", layout="wide")
g.crear_tablas()

CATEGORIAS_GASTO = ["Comida", "Transporte", "Hogar", "Salud", "Ocio",
                    "Ropa", "Educación", "Servicios", "Otros"]
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
         "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

# ==========================================
# ESTILO
# ==========================================

CSS = """
<style>
.hero{background:linear-gradient(135deg,#6C5CE7 0%,#00B894 100%);padding:24px 28px;
      border-radius:20px;color:#fff;margin-bottom:20px;box-shadow:0 6px 18px rgba(0,0,0,.18)}
.hero h1{margin:0;font-size:1.8rem;color:#fff;padding:0}
.hero p{margin:6px 0 0;opacity:.92}
.kpi{border-radius:16px;padding:16px 18px;color:#fff;box-shadow:0 4px 14px rgba(0,0,0,.18);
     margin-bottom:12px}
.kpi .l{font-size:.78rem;opacity:.92;text-transform:uppercase;letter-spacing:.06em}
.kpi .v{font-size:1.6rem;font-weight:800;line-height:1.25}
.card{border-radius:16px;padding:16px 18px;margin-bottom:12px;
      background:rgba(128,128,128,.10);border:1px solid rgba(128,128,128,.25)}
.card h4{margin:0 0 6px 0;padding:0}
.small{font-size:.85rem;opacity:.85}
.bar{background:rgba(128,128,128,.28);border-radius:999px;height:12px;overflow:hidden;margin:6px 0}
.bar-fill{height:100%;border-radius:999px}
.pill{display:inline-block;padding:2px 10px;border-radius:999px;font-size:.78rem;
      font-weight:700;color:#fff}
.row{display:flex;align-items:center;gap:10px;margin:6px 0}
.row .m{width:74px;font-size:.85rem}
.row .b{flex:1}
.row .a{width:96px;text-align:right;font-size:.85rem;font-weight:600}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def pesos(n):
    """Formato argentino: $1.234.567"""
    return "$" + f"{n:,.0f}".replace(",", ".")


def barra(pct, color):
    pct = max(0, min(100, pct))
    return (f'<div class="bar"><div class="bar-fill" '
            f'style="width:{pct:.0f}%;background:{color}"></div></div>')


def kpi(etiqueta, valor, color):
    return (f'<div class="kpi" style="background:{color}">'
            f'<div class="l">{etiqueta}</div><div class="v">{valor}</div></div>')


def hero(titulo, subtitulo):
    st.markdown(f'<div class="hero"><h1>{titulo}</h1><p>{subtitulo}</p></div>',
                unsafe_allow_html=True)


def color_estado(dias, pagado=False):
    if pagado:
        return "#00B894"
    if dias < 0:
        return "#D63031"
    if dias <= 3:
        return "#E17055"
    if dias <= 7:
        return "#F39C12"
    return "#0984E3"


# ==========================================
# CÁLCULOS
# ==========================================

def proyeccion_cuotas(tarjeta_id=None, meses=6):
    """
    Cuánto vas a pagar de cuotas cada mes (este mes + los siguientes).
    Si ya pagaste una cuota de una compra este mes, su próxima cuota cuenta desde el mes que viene.
    Devuelve [(etiqueta_mes, monto), ...]
    """
    hoy = date.today()
    mes_actual = hoy.strftime("%Y-%m")
    totales = [0.0] * meses

    for c in g.listar_compras_tarjeta(tarjeta_id):
        total, c_tot, c_pag, f_ult = c[3], c[4], c[5], c[7]
        cuota = total / c_tot
        inicio = 1 if (f_ult and f_ult[:7] == mes_actual) else 0
        for k in range(c_tot - c_pag):
            if inicio + k < meses:
                totales[inicio + k] += cuota

    resultado = []
    for i in range(meses):
        m = (hoy.month - 1 + i) % 12
        a = hoy.year + (hoy.month - 1 + i) // 12
        resultado.append((f"{MESES[m]} {a}", totales[i]))
    return resultado


def panel_proyeccion(proy, color="#6C5CE7"):
    """Estilo Mercado Pago: lo que debés el mes que viene y barras por mes."""
    este_mes, proximo = proy[0][1], proy[1][1]
    maximo = max(m for _, m in proy) or 1

    st.markdown(
        f'<div class="card"><div class="small">Cuotas de este mes</div>'
        f'<div style="font-size:1.5rem;font-weight:800">{pesos(este_mes)}</div>'
        f'<div class="small" style="margin-top:8px">El mes que viene pagás</div>'
        f'<div style="font-size:1.9rem;font-weight:800;color:{color}">{pesos(proximo)}</div></div>',
        unsafe_allow_html=True,
    )

    filas = ""
    for i, (mes, monto) in enumerate(proy):
        c = color if i == 1 else "rgba(128,128,128,.55)"
        if i == 0:
            c = "#00B894"
        filas += (f'<div class="row"><div class="m">{mes}</div>'
                  f'<div class="b">{barra(monto / maximo * 100, c)}</div>'
                  f'<div class="a">{pesos(monto)}</div></div>')
    st.markdown(f'<div class="card">{filas}</div>', unsafe_allow_html=True)


# ==========================================
# INICIO
# ==========================================

def pagina_inicio():
    hero("💸 Gestor de gastos", f"Hoy es {date.today():%d/%m/%Y} · tus finanzas de un vistazo")

    mes = date.today().strftime("%Y-%m")
    gastos_mes = sum(x[3] for x in g.consultar_gastos() if x[4].startswith(mes))
    deuda_cuotas = sum(g.calcular_saldo_pendiente(c[0]) for c in g.listar_compras_tarjeta())
    proy = proyeccion_cuotas()
    hoy = date.today()
    serv_30 = sum(s[2] for s in g.listar_servicios()
                  if not s[6] and (date.fromisoformat(s[3]) - hoy).days <= 30)

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi("Gastos del mes", pesos(gastos_mes), "#6C5CE7"), unsafe_allow_html=True)
    c2.markdown(kpi("Deuda total en cuotas", pesos(deuda_cuotas), "#E17055"), unsafe_allow_html=True)
    c3.markdown(kpi("Cuotas mes que viene", pesos(proy[1][1]), "#0984E3"), unsafe_allow_html=True)
    c4.markdown(kpi("Servicios (30 días)", pesos(serv_30), "#00B894"), unsafe_allow_html=True)

    izq, der = st.columns([1, 1])
    with izq:
        st.subheader("🔔 Próximos vencimientos")
        alertas = g.obtener_alertas()
        if not alertas:
            st.success("No tenés vencimientos próximos. ¡Todo al día!")
        for tipo, nombre, fecha, dias in alertas:
            col = color_estado(dias)
            st.markdown(
                f'<div class="card" style="border-left:6px solid {col}">'
                f'<span class="pill" style="background:{col}">{g.estado_vencimiento(dias)}</span> '
                f'<b>{html.escape(nombre)}</b>'
                f'<div class="small">{tipo} · {fecha:%d/%m/%Y}</div></div>',
                unsafe_allow_html=True,
            )
    with der:
        st.subheader("📅 Lo que viene en cuotas")
        panel_proyeccion(proy)


# ==========================================
# GASTOS
# ==========================================

def pagina_gastos():
    hero("🧾 Gastos generales", "Registrá y analizá en qué se va tu plata")

    with st.expander("➕ Registrar gasto", expanded=True):
        with st.form("form_gasto", clear_on_submit=True):
            c1, c2, c3 = st.columns([3, 2, 2])
            desc = c1.text_input("Descripción")
            cat = c2.selectbox("Categoría", CATEGORIAS_GASTO)
            monto = c3.number_input("Monto", min_value=0.0, step=100.0)
            if st.form_submit_button("Guardar gasto"):
                if not desc.strip() or monto <= 0:
                    st.error("Completá la descripción y un monto mayor a 0.")
                else:
                    g.registrar_gasto(desc.strip(), cat, monto)
                    st.success("Gasto registrado.")

    with st.expander("🗑️ Eliminar gasto"):
        gastos_tmp = g.consultar_gastos()
        if gastos_tmp:
            ids = {x[0]: f"#{x[0]} · {x[1]} · {pesos(x[3])}" for x in gastos_tmp}
            id_sel = st.selectbox("Gasto", list(ids), format_func=lambda i: ids[i])
            if st.button("Eliminar gasto"):
                g.eliminar_gasto(id_sel)
                st.success("Gasto eliminado.")
        else:
            st.info("No hay gastos para eliminar.")

    gastos = g.consultar_gastos()
    if not gastos:
        st.info("Todavía no registraste gastos.")
        return

    df = pd.DataFrame(gastos, columns=["ID", "Descripción", "Categoría", "Monto", "Fecha"])
    filtro = st.multiselect("Filtrar por categoría", sorted(df["Categoría"].unique()))
    if filtro:
        df = df[df["Categoría"].isin(filtro)]

    por_cat = df.groupby("Categoría")["Monto"].sum().sort_values(ascending=False)
    k1, k2, k3 = st.columns(3)
    k1.markdown(kpi("Total", pesos(df["Monto"].sum()), "#6C5CE7"), unsafe_allow_html=True)
    k2.markdown(kpi("Categoría principal", por_cat.index[0], "#E17055"), unsafe_allow_html=True)
    k3.markdown(kpi("Cantidad de gastos", str(len(df)), "#0984E3"), unsafe_allow_html=True)

    col_tabla, col_grafico = st.columns([3, 2])
    with col_tabla:
        st.dataframe(df, hide_index=True)
    with col_grafico:
        st.bar_chart(por_cat, color="#6C5CE7")


# ==========================================
# TARJETAS
# ==========================================

def pagina_tarjetas():
    hero("💳 Tarjetas de crédito", "Cuotas, cierres, vencimientos y lo que te queda por pagar")

    with st.expander("➕ Agregar tarjeta"):
        base = st.selectbox("Tarjeta", list(g.TARJETAS_ARGENTINA.keys()) + ["Otra"])
        otra = st.text_input("Nombre de la tarjeta") if base == "Otra" else ""
        with st.form("form_tarjeta", clear_on_submit=True):
            banco = st.text_input("Banco emisor (opcional)")
            c1, c2, c3 = st.columns(3)
            dia_cierre = c1.number_input("Día de cierre", 1, 31, 1)
            dia_venc = c2.number_input("Día de vencimiento", 1, 31, 10)
            limite = c3.number_input("Límite (opcional)", min_value=0.0, value=0.0, step=1000.0)
            if st.form_submit_button("Guardar tarjeta"):
                nombre_base = otra.strip() if base == "Otra" else base
                if not nombre_base:
                    st.error("Escribí el nombre de la tarjeta.")
                else:
                    nombre = f"{nombre_base} {banco.strip()}".strip()
                    g.crear_tarjeta(nombre, int(dia_cierre), int(dia_venc), limite)
                    st.success(f"Tarjeta '{nombre}' agregada.")

    tarjetas = g.listar_tarjetas()
    nombres = {t[0]: t[1] for t in tarjetas}

    with st.expander("🛍️ Registrar compra con tarjeta"):
        if not tarjetas:
            st.info("Primero agregá una tarjeta.")
        else:
            with st.form("form_compra", clear_on_submit=True):
                id_t = st.selectbox("Tarjeta", list(nombres), format_func=lambda i: nombres[i])
                desc = st.text_input("Descripción de la compra")
                c1, c2 = st.columns(2)
                monto = c1.number_input("Monto total", min_value=0.0, step=1000.0)
                cuotas = c2.number_input("Cuotas (1 = pago único)", 1, 60, 1)
                if st.form_submit_button("Registrar compra"):
                    if not desc.strip() or monto <= 0:
                        st.error("Completá la descripción y un monto mayor a 0.")
                    else:
                        g.registrar_compra_tarjeta(id_t, desc.strip(), monto, int(cuotas))
                        st.success(f"Compra registrada: {int(cuotas)} cuota(s) de {pesos(monto / cuotas)}.")

    with st.expander("✅ Pagar una cuota"):
        pendientes = [c for c in g.listar_compras_tarjeta() if c[5] < c[4]]
        if not pendientes:
            st.info("No hay cuotas pendientes.")
        else:
            opciones = {c[0]: f"{c[1]} · {c[2]} ({c[5]}/{c[4]})" for c in pendientes}
            id_c = st.selectbox("Compra", list(opciones), format_func=lambda i: opciones[i])
            forzar = st.checkbox("Pagar otra cuota aunque ya haya pagado una este mes")
            if st.button("Registrar pago de cuota"):
                msg = g.pagar_cuota(id_c, forzar=forzar)
                if msg.startswith("✅"):
                    st.success(msg)
                    st.balloons()
                else:
                    st.warning(msg)

    with st.expander("🗑️ Eliminar tarjeta"):
        if tarjetas:
            id_del = st.selectbox("Tarjeta a eliminar", list(nombres),
                                  format_func=lambda i: nombres[i], key="del_tarjeta")
            ok = st.checkbox("Entiendo que también se borran sus compras")
            if st.button("Eliminar tarjeta") and ok:
                g.eliminar_tarjeta(id_del)
                st.success("Tarjeta eliminada.")
        else:
            st.info("No hay tarjetas.")

    # --- Vista (se lee después de las acciones, así siempre está actualizada) ---
    tarjetas = g.listar_tarjetas()
    if not tarjetas:
        st.info("Todavía no agregaste tarjetas.")
        return

    cols = st.columns(min(len(tarjetas), 3))
    for i, (id_t, nombre, dia_cierre, dia_venc, limite) in enumerate(tarjetas):
        estilo = g.obtener_estilo_tarjeta(nombre)
        d_cierre, f_cierre = g.dias_hasta_proximo_dia(dia_cierre)
        d_venc, f_venc = g.dias_hasta_proximo_dia(dia_venc)
        compras_t = g.listar_compras_tarjeta(id_t)
        saldo = sum(g.calcular_saldo_pendiente(c[0]) for c in compras_t)

        uso = ""
        if limite and limite > 0:
            pct = saldo / limite * 100
            uso = (f'<div style="margin-top:8px;font-size:.85rem">Límite usado: '
                   f'{pesos(saldo)} de {pesos(limite)} ({pct:.0f}%)</div>'
                   f'<div class="bar" style="background:rgba(255,255,255,.3)">'
                   f'<div class="bar-fill" style="width:{min(pct, 100):.0f}%;background:#fff"></div></div>')

        with cols[i % len(cols)]:
            st.markdown(
                f"""
                <div style="background:linear-gradient(135deg,{estilo['color']},{estilo['color']}bb);
                            padding:18px;border-radius:18px;color:white;margin-bottom:14px;
                            box-shadow:0 6px 16px rgba(0,0,0,.22);line-height:1.55">
                  <div style="font-size:1.2rem;font-weight:800">💳 {html.escape(nombre)}</div>
                  <div>📅 Cierre: {f_cierre:%d/%m/%Y} (en {d_cierre} d)</div>
                  <div>💰 Vence: {f_venc:%d/%m/%Y} (en {d_venc} d)</div>
                  <div style="margin-top:6px;font-size:1.25rem;font-weight:800">
                      Debés {pesos(saldo)}</div>
                  {uso}
                </div>
                """,
                unsafe_allow_html=True,
            )

    # --- Proyección mensual ---
    st.subheader("📅 Lo que vas a pagar en los próximos meses")
    opciones_proy = {0: "Todas las tarjetas", **nombres}
    sel = st.selectbox("Ver", list(opciones_proy), format_func=lambda i: opciones_proy[i])
    color = "#6C5CE7" if sel == 0 else g.obtener_estilo_tarjeta(nombres[sel])["color"]
    panel_proyeccion(proyeccion_cuotas(sel or None, meses=8), color)

    # --- Compras con barras que van bajando ---
    compras = g.listar_compras_tarjeta()
    if compras:
        st.subheader("🛍️ Tus compras en cuotas")
        for c_id, tarj, desc, total, c_tot, c_pag, f_compra, f_ult in compras:
            cuota = total / c_tot
            pagado = cuota * c_pag
            pendiente = total - pagado
            pct_pend = pendiente / total * 100 if total else 0
            completa = c_pag >= c_tot
            col = "#00B894" if completa else ("#F39C12" if pct_pend < 50 else
                                              g.obtener_estilo_tarjeta(tarj)["color"])
            etiqueta = "✅ Terminada" if completa else f"Cuota {c_pag}/{c_tot}"
            st.markdown(
                f'<div class="card"><div style="display:flex;justify-content:space-between">'
                f'<b>{html.escape(desc)}</b><span class="pill" style="background:{col}">{etiqueta}</span></div>'
                f'<div class="small">{html.escape(tarj)} · cuota de {pesos(cuota)}</div>'
                f'{barra(pct_pend, col)}'
                f'<div class="small">Pagaste {pesos(pagado)} · '
                f'<b>Quedan {pesos(pendiente)}</b> de {pesos(total)}</div></div>',
                unsafe_allow_html=True,
            )


# ==========================================
# SERVICIOS
# ==========================================

def pagina_servicios():
    hero("🔌 Servicios y vencimientos", "Que no se te pase ninguna fecha")

    with st.expander("➕ Agregar servicio"):
        base = st.selectbox("Servicio", g.SERVICIOS_COMUNES + ["Otro"])
        otro = st.text_input("Nombre del servicio") if base == "Otro" else ""
        with st.form("form_servicio", clear_on_submit=True):
            c1, c2 = st.columns(2)
            monto = c1.number_input("Monto aproximado (opcional)", min_value=0.0, step=1000.0)
            fecha = c2.date_input("Fecha de vencimiento", value=date.today(), format="DD/MM/YYYY")
            c3, c4 = st.columns(2)
            aviso = c3.number_input("Avisar con cuántos días de anticipación", 0, 60, 3)
            recurrente = c4.checkbox("Se repite todos los meses", value=True)
            if st.form_submit_button("Guardar servicio"):
                nombre = otro.strip() if base == "Otro" else base
                if not nombre:
                    st.error("Escribí el nombre del servicio.")
                else:
                    g.crear_servicio(nombre, monto, fecha.strftime("%Y-%m-%d"),
                                     int(aviso), 1 if recurrente else 0)
                    st.success(f"Servicio '{nombre}' agregado.")

    with st.expander("✅ Marcar como pagado / 🗑️ Eliminar"):
        activos = g.listar_servicios()
        if not activos:
            st.info("No hay servicios.")
        else:
            opciones = {s[0]: f"{s[1]} · vence {date.fromisoformat(s[3]):%d/%m/%Y}" for s in activos}
            id_s = st.selectbox("Servicio", list(opciones), format_func=lambda i: opciones[i])
            c1, c2 = st.columns(2)
            if c1.button("Marcar como pagado"):
                st.success(g.pagar_servicio(id_s))
            if c2.button("Eliminar servicio"):
                g.eliminar_servicio(id_s)
                st.success("Servicio eliminado.")

    servicios = g.listar_servicios()
    if not servicios:
        st.info("Todavía no agregaste servicios.")
        return

    hoy = date.today()
    cols = st.columns(3)
    for i, (id_s, nombre, monto, fecha_iso, aviso, recurrente, pagado) in enumerate(servicios):
        f = date.fromisoformat(fecha_iso)
        dias = (f - hoy).days
        col = color_estado(dias, pagado)
        estado = "✅ Pagado" if pagado else g.estado_vencimiento(dias)
        cercania = 100 if pagado else max(0, min(100, (30 - dias) / 30 * 100))
        monto_txt = pesos(monto) if monto else "Sin monto"
        repite = " · 🔁 mensual" if recurrente else ""
        with cols[i % 3]:
            st.markdown(
                f'<div class="card" style="border-left:6px solid {col}">'
                f'<h4>{html.escape(nombre)}</h4>'
                f'<span class="pill" style="background:{col}">{estado}</span>'
                f'<div style="font-size:1.3rem;font-weight:800;margin-top:6px">{monto_txt}</div>'
                f'{barra(cercania, col)}'
                f'<div class="small">Vence {f:%d/%m/%Y}{repite}</div></div>',
                unsafe_allow_html=True,
            )


# ==========================================
# NAVEGACIÓN
# ==========================================

PAGINAS = {
    "🏠 Inicio": pagina_inicio,
    "🧾 Gastos": pagina_gastos,
    "💳 Tarjetas": pagina_tarjetas,
    "🔌 Servicios": pagina_servicios,
}

st.sidebar.title("💸 Menú")
seleccion = st.sidebar.radio("Ir a", list(PAGINAS), label_visibility="collapsed")
PAGINAS[seleccion]()


