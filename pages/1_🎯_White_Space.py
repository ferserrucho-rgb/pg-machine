"""
White Space Analysis - Análisis de cobertura de productos por cliente
"""
import streamlit as st
import pandas as pd
from lib import db
from lib.auth import require_auth, get_current_user
from lib.i18n import t
from datetime import datetime

st.set_page_config(page_title="White Space Analysis - PG Machine", layout="wide")

if not require_auth():
    st.stop()

user = get_current_user()
team_id = user["team_id"]

# Estilos
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.ws-card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem; }
.ws-header { font-size: 1.5rem; font-weight: 700; color: #1e293b; margin-bottom: 1rem; }
.ws-product-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 8px; margin-top: 12px; }
.ws-product-badge { padding: 6px 12px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; text-align: center; }
.ws-product-yes { background: #dcfce7; color: #166534; border: 1px solid #86efac; }
.ws-product-no { background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }
.ws-coverage { font-size: 2rem; font-weight: 800; }
.ws-coverage-high { color: #16a34a; }
.ws-coverage-medium { color: #f59e0b; }
.ws-coverage-low { color: #ef4444; }
</style>
""", unsafe_allow_html=True)

st.title("🎯 White Space Analysis")
st.markdown("Análisis de cobertura de productos por cliente - Mercado completo")

# Productos del mercado organizados por categoría
# Basado en líderes con >30% market share en sus categorías (2026)
PRODUCTOS_BMC = [
    # === ITSM (IT Service Management) ===
    "ServiceNow ITSM",
    "BMC Helix ITSM",
    "Jira Service Management",
    "Freshservice",
    "BMC Remedyforce",

    # === ITOM (IT Operations Management) ===
    "ServiceNow ITOM",
    "BMC Helix ITOM",
    "BMC TrueSight",
    "Splunk ITSI",

    # === APM & Observability (Líderes de mercado) ===
    "Datadog",  # 51.82% market share
    "New Relic",  # 24% market share
    "Dynatrace",
    "Grafana",
    "Splunk Observability",
    "AppDynamics (Cisco)",

    # === Monitoring & Infrastructure ===
    "Prometheus",
    "Nagios",
    "Zabbix",
    "SolarWinds",
    "Instana (IBM)",
    "Elastic Observability",

    # === AIOps & Analytics ===
    "BMC Helix AIOps",
    "Moogsoft",
    "BigPanda",

    # === Automation & Orchestration ===
    "BMC Control-M",
    "Ansible (Red Hat)",
    "ServiceNow Automation",

    # === Cloud Management ===
    "BMC Helix Cloud Cost",
    "CloudHealth (VMware)",

    # === Service Desk & Ticketing ===
    "Jira",
    "BMC Helix Digital Workplace",
    "Zendesk",
    "ServiceNow CSM",

    # === Discovery & CMDB ===
    "BMC Helix Discovery",
    "ServiceNow Discovery",
    "Device42",
]

# Tabs principales
tab_vista, tab_gestionar, tab_importar = st.tabs(["📊 Vista General", "✏️ Gestionar Cuentas", "📥 Importar Datos"])

# ====================
# TAB 1: VISTA GENERAL
# ====================
with tab_vista:
    col1, col2, col3 = st.columns(3)

    # KPIs
    total_accounts = db.fetch_one(
        "SELECT COUNT(*) as count FROM accounts WHERE team_id = %s",
        (team_id,)
    )["count"]

    avg_coverage = db.fetch_one("""
        SELECT COALESCE(ROUND(AVG(coverage_pct), 1), 0) as avg_cov
        FROM whitespace_analysis
        WHERE team_id = %s
    """, (team_id,))["avg_cov"]

    total_products = db.fetch_one("""
        SELECT COUNT(*) as count
        FROM account_products ap
        JOIN accounts a ON ap.account_id = a.id
        WHERE a.team_id = %s AND ap.tiene = true
    """, (team_id,))["count"]

    with col1:
        st.metric("Total Cuentas", total_accounts)
    with col2:
        st.metric("Cobertura Promedio", f"{avg_coverage}%")
    with col3:
        st.metric("Productos Activos", total_products)

    st.markdown("---")

    # Filtros
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        verticales = db.fetch_all(
            "SELECT DISTINCT vertical FROM accounts WHERE team_id = %s AND vertical IS NOT NULL ORDER BY vertical",
            (team_id,)
        )
        vertical_options = ["Todas"] + [v["vertical"] for v in verticales]
        filtro_vertical = st.selectbox("Vertical", vertical_options)

    with col_f2:
        filtro_coverage = st.selectbox("Cobertura", ["Todos", "Alta (>70%)", "Media (30-70%)", "Baja (<30%)"])

    with col_f3:
        filtro_busqueda = st.text_input("🔍 Buscar cuenta")

    # Obtener datos
    query = """
        SELECT * FROM whitespace_analysis
        WHERE team_id = %s
    """
    params = [team_id]

    if filtro_vertical != "Todas":
        query += " AND vertical = %s"
        params.append(filtro_vertical)

    if filtro_coverage != "Todos":
        if filtro_coverage == "Alta (>70%)":
            query += " AND coverage_pct > 70"
        elif filtro_coverage == "Media (30-70%)":
            query += " AND coverage_pct BETWEEN 30 AND 70"
        elif filtro_coverage == "Baja (<30%)":
            query += " AND coverage_pct < 30"

    if filtro_busqueda:
        query += " AND LOWER(nombre) LIKE %s"
        params.append(f"%{filtro_busqueda.lower()}%")

    query += " ORDER BY coverage_pct DESC, nombre"

    accounts_data = db.fetch_all(query, tuple(params))

    if not accounts_data:
        st.info("No hay cuentas registradas. Ve a la pestaña 'Gestionar Cuentas' para agregar.")
    else:
        for acc in accounts_data:
            coverage = acc["coverage_pct"] or 0
            coverage_class = "ws-coverage-high" if coverage > 70 else "ws-coverage-medium" if coverage >= 30 else "ws-coverage-low"

            with st.expander(f"**{acc['nombre']}** - {acc['vertical'] or 'Sin vertical'} - {coverage}% cobertura"):
                col_info, col_coverage = st.columns([3, 1])

                with col_info:
                    if acc['descripcion']:
                        st.markdown(f"**Descripción:** {acc['descripcion']}")
                    st.markdown(f"**Productos activos:** {acc['productos_actuales']} de {acc['productos_totales']}")

                    # Grid de productos
                    if acc['productos']:
                        st.markdown("### Productos")
                        productos_html = '<div class="ws-product-grid">'
                        for prod in acc['productos']:
                            badge_class = "ws-product-yes" if prod['tiene'] else "ws-product-no"
                            icon = "✅" if prod['tiene'] else "❌"
                            productos_html += f'<div class="ws-product-badge {badge_class}">{icon} {prod["product"]}</div>'
                        productos_html += '</div>'
                        st.markdown(productos_html, unsafe_allow_html=True)

                        # Detalles de productos con partner
                        st.markdown("### Detalles")
                        for prod in acc['productos']:
                            if prod['tiene']:
                                info_parts = [f"**{prod['product']}**"]
                                if prod['partner']:
                                    info_parts.append(f"Partner: {prod['partner']}")
                                if prod['partner_executive']:
                                    info_parts.append(f"Ejecutivo: {prod['partner_executive']}")
                                if prod['notas']:
                                    info_parts.append(f"Notas: {prod['notas']}")
                                st.markdown(" • ".join(info_parts))

                with col_coverage:
                    st.markdown(f'<div class="ws-coverage {coverage_class}">{coverage}%</div>', unsafe_allow_html=True)
                    st.markdown("Cobertura")

# ========================
# TAB 2: GESTIONAR CUENTAS
# ========================
with tab_gestionar:
    st.subheader("Gestionar Cuentas")

    modo = st.radio("", ["Agregar Nueva Cuenta", "Editar Cuenta Existente"], horizontal=True)

    if modo == "Agregar Nueva Cuenta":
        with st.form("form_nueva_cuenta"):
            st.markdown("### Información de la Cuenta")
            col1, col2 = st.columns(2)
            with col1:
                nuevo_nombre = st.text_input("Nombre de la Cuenta *")
                nuevo_vertical = st.text_input("Vertical (ej: Retail, Banca, Gobierno)")
            with col2:
                nuevo_descripcion = st.text_area("Descripción")

            st.markdown("### Productos")
            st.markdown("Selecciona los productos que el cliente **actualmente tiene**:")

            productos_seleccionados = {}
            for i in range(0, len(PRODUCTOS_BMC), 3):
                cols = st.columns(3)
                for j, col in enumerate(cols):
                    if i + j < len(PRODUCTOS_BMC):
                        producto = PRODUCTOS_BMC[i + j]
                        with col:
                            tiene = st.checkbox(producto, key=f"nuevo_{producto}")
                            if tiene:
                                partner = st.text_input(f"Partner", key=f"partner_nuevo_{producto}")
                                exec_partner = st.text_input(f"Ejecutivo Partner", key=f"exec_nuevo_{producto}")
                                notas = st.text_area(f"Notas", key=f"notas_nuevo_{producto}", height=60)
                                productos_seleccionados[producto] = {
                                    "tiene": True,
                                    "partner": partner,
                                    "executive": exec_partner,
                                    "notas": notas
                                }
                            else:
                                productos_seleccionados[producto] = {"tiene": False}

            submitted = st.form_submit_button("💾 Guardar Cuenta", type="primary")

            if submitted:
                if not nuevo_nombre:
                    st.error("El nombre de la cuenta es requerido")
                else:
                    try:
                        # Crear cuenta
                        account = db.execute_returning("""
                            INSERT INTO accounts (team_id, nombre, descripcion, vertical)
                            VALUES (%s, %s, %s, %s)
                            RETURNING id
                        """, (team_id, nuevo_nombre, nuevo_descripcion, nuevo_vertical))

                        account_id = account["id"]

                        # Insertar productos
                        for producto, data in productos_seleccionados.items():
                            db.execute("""
                                INSERT INTO account_products (account_id, product_name, tiene, partner, partner_executive, notas)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """, (
                                account_id,
                                producto,
                                data["tiene"],
                                data.get("partner"),
                                data.get("executive"),
                                data.get("notas")
                            ))

                        st.success(f"✅ Cuenta '{nuevo_nombre}' creada exitosamente!")
                        st.rerun()
                    except Exception as e:
                        if "unique" in str(e).lower():
                            st.error("Esta cuenta ya existe en el sistema")
                        else:
                            st.error(f"Error al crear cuenta: {str(e)}")

    else:  # Editar cuenta existente
        cuentas = db.fetch_all("""
            SELECT id, nombre, vertical FROM accounts
            WHERE team_id = %s
            ORDER BY nombre
        """, (team_id,))

        if not cuentas:
            st.info("No hay cuentas para editar. Crea una primera.")
        else:
            cuenta_editar = st.selectbox(
                "Selecciona cuenta a editar",
                options=cuentas,
                format_func=lambda x: f"{x['nombre']} ({x['vertical'] or 'Sin vertical'})"
            )

            if cuenta_editar:
                # Obtener datos actuales
                cuenta_data = db.fetch_one("""
                    SELECT * FROM accounts WHERE id = %s
                """, (cuenta_editar["id"],))

                productos_data = db.fetch_all("""
                    SELECT * FROM account_products WHERE account_id = %s
                """, (cuenta_editar["id"],))

                productos_dict = {p["product_name"]: p for p in productos_data}

                with st.form("form_editar_cuenta"):
                    st.markdown("### Información de la Cuenta")
                    col1, col2 = st.columns(2)
                    with col1:
                        edit_nombre = st.text_input("Nombre de la Cuenta *", value=cuenta_data["nombre"])
                        edit_vertical = st.text_input("Vertical", value=cuenta_data["vertical"] or "")
                    with col2:
                        edit_descripcion = st.text_area("Descripción", value=cuenta_data["descripcion"] or "")

                    st.markdown("### Productos")

                    productos_actualizados = {}
                    for i in range(0, len(PRODUCTOS_BMC), 3):
                        cols = st.columns(3)
                        for j, col in enumerate(cols):
                            if i + j < len(PRODUCTOS_BMC):
                                producto = PRODUCTOS_BMC[i + j]
                                prod_actual = productos_dict.get(producto, {})

                                with col:
                                    tiene = st.checkbox(
                                        producto,
                                        value=prod_actual.get("tiene", False),
                                        key=f"edit_{producto}"
                                    )
                                    if tiene:
                                        partner = st.text_input(
                                            f"Partner",
                                            value=prod_actual.get("partner", ""),
                                            key=f"partner_edit_{producto}"
                                        )
                                        exec_partner = st.text_input(
                                            f"Ejecutivo Partner",
                                            value=prod_actual.get("partner_executive", ""),
                                            key=f"exec_edit_{producto}"
                                        )
                                        notas = st.text_area(
                                            f"Notas",
                                            value=prod_actual.get("notas", ""),
                                            key=f"notas_edit_{producto}",
                                            height=60
                                        )
                                        productos_actualizados[producto] = {
                                            "tiene": True,
                                            "partner": partner,
                                            "executive": exec_partner,
                                            "notas": notas
                                        }
                                    else:
                                        productos_actualizados[producto] = {"tiene": False}

                    col_save, col_delete = st.columns([3, 1])
                    with col_save:
                        submitted = st.form_submit_button("💾 Actualizar Cuenta", type="primary")
                    with col_delete:
                        delete = st.form_submit_button("🗑️ Eliminar", type="secondary")

                    if submitted:
                        try:
                            # Actualizar cuenta
                            db.execute("""
                                UPDATE accounts
                                SET nombre = %s, descripcion = %s, vertical = %s, updated_at = NOW()
                                WHERE id = %s
                            """, (edit_nombre, edit_descripcion, edit_vertical, cuenta_editar["id"]))

                            # Actualizar productos
                            for producto, data in productos_actualizados.items():
                                db.execute("""
                                    INSERT INTO account_products (account_id, product_name, tiene, partner, partner_executive, notas)
                                    VALUES (%s, %s, %s, %s, %s, %s)
                                    ON CONFLICT (account_id, product_name)
                                    DO UPDATE SET
                                        tiene = EXCLUDED.tiene,
                                        partner = EXCLUDED.partner,
                                        partner_executive = EXCLUDED.partner_executive,
                                        notas = EXCLUDED.notas,
                                        updated_at = NOW()
                                """, (
                                    cuenta_editar["id"],
                                    producto,
                                    data["tiene"],
                                    data.get("partner"),
                                    data.get("executive"),
                                    data.get("notas")
                                ))

                            st.success("✅ Cuenta actualizada exitosamente!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al actualizar: {str(e)}")

                    if delete:
                        db.execute("DELETE FROM accounts WHERE id = %s", (cuenta_editar["id"],))
                        st.success("Cuenta eliminada")
                        st.rerun()

# =====================
# TAB 3: IMPORTAR DATOS
# =====================
with tab_importar:
    st.subheader("Importar desde Oportunidades")
    st.markdown("""
    Esta función analiza tus oportunidades existentes y crea/actualiza cuentas automáticamente.
    """)

    if st.button("🔄 Sincronizar desde Oportunidades", type="primary"):
        with st.spinner("Sincronizando..."):
            # Obtener cuentas únicas de opportunities
            opps = db.fetch_all("""
                SELECT DISTINCT cuenta, partner, categoria
                FROM opportunities
                WHERE team_id = %s AND cuenta IS NOT NULL
            """, (team_id,))

            cuentas_creadas = 0
            productos_agregados = 0

            for opp in opps:
                cuenta_nombre = opp["cuenta"]

                # Crear o actualizar cuenta
                account = db.execute_returning("""
                    INSERT INTO accounts (team_id, nombre)
                    VALUES (%s, %s)
                    ON CONFLICT (team_id, nombre) DO UPDATE SET updated_at = NOW()
                    RETURNING id
                """, (team_id, cuenta_nombre))

                if account:
                    cuentas_creadas += 1

                    # Mapear categoría a producto
                    categoria = opp["categoria"] or ""
                    if "ITSM" in categoria.upper():
                        producto = "Helix ITSM"
                    elif "ITOM" in categoria.upper():
                        producto = "Helix ITOM"
                    else:
                        producto = None

                    if producto:
                        db.execute("""
                            INSERT INTO account_products (account_id, product_name, tiene, partner)
                            VALUES (%s, %s, true, %s)
                            ON CONFLICT (account_id, product_name)
                            DO UPDATE SET tiene = true, partner = EXCLUDED.partner, updated_at = NOW()
                        """, (account["id"], producto, opp["partner"]))
                        productos_agregados += 1

            st.success(f"✅ Sincronización completa: {cuentas_creadas} cuentas procesadas, {productos_agregados} productos actualizados")
            st.rerun()
