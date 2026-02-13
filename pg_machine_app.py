import streamlit as st
import pandas as pd
import uuid
from datetime import datetime, date, timedelta

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="PG Machine | v116 Core", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f8fafc; }

    /* Force full width on main container - override inline styles */
    section.main > div[style] { max-width: 100% !important; padding-left: 1rem !important; padding-right: 1rem !important; }
    .block-container { max-width: 100% !important; padding-left: 1rem !important; padding-right: 1rem !important; padding-top: 1.5rem !important; }

    /* Categorías */
    .cat-header { background: #1e293b; color: white; padding: 10px; border-radius: 8px; text-align: center; font-weight: 700; margin-bottom: 15px; }

    /* Scorecard */
    .scorecard { background: white; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .badge { float:right; font-size:0.6rem; font-weight:bold; padding:2px 6px; border-radius:8px; text-transform: uppercase; border: 1.2px solid; }
    .sc-cuenta { color: #64748b; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }
    .sc-proyecto { color: #1e293b; font-size: 0.95rem; font-weight: 700; margin: 4px 0; }
    .sc-monto { color: #16a34a; font-size: 1.1rem; font-weight: 800; display: block; }

    /* Panel Derecho */
    .action-panel { background: white; padding: 25px; border-radius: 12px; border: 1px solid #e2e8f0; border-top: 6px solid #1a73e8; }
    .hist-card { background: #f8fafc; padding: 12px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 10px; }
    .activity-line { font-size: 0.72rem; color: #475569; margin: 2px 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    </style>
    """, unsafe_allow_html=True)

# JS to force remove inline max-width set by Streamlit's runtime
st.markdown("""
    <script>
    const observer = new MutationObserver(() => {
        document.querySelectorAll('section.main > div').forEach(el => {
            if (el.style.maxWidth) {
                el.style.maxWidth = '100%';
                el.style.paddingLeft = '1rem';
                el.style.paddingRight = '1rem';
            }
        });
    });
    observer.observe(document.body, {childList: true, subtree: true, attributes: true});
    document.querySelectorAll('section.main > div').forEach(el => {
        el.style.maxWidth = '100%';
        el.style.paddingLeft = '1rem';
        el.style.paddingRight = '1rem';
    });
    </script>
    """, unsafe_allow_html=True)

# --- 2. LÓGICA DE DATOS ---
if 'db_leads' not in st.session_state: st.session_state.db_leads = []
if 'selected_id' not in st.session_state: st.session_state.selected_id = None

SLA_OPCIONES = {
    "🚨 Urgente (2-4h)": {"horas": 4, "color": "#ef4444"},
    "⚠️ Importante (2d)": {"dias": 2, "color": "#f59e0b"},
    "☕ No urgente (7d)": {"dias": 7, "color": "#3b82f6"}
}

def _traffic_light(act):
    if act["estado"] in ("Completada", "Respondida"):
        return "🟢", "Completada"
    sla_cfg = SLA_OPCIONES.get(act["sla"], {})
    if "horas" in sla_cfg:
        deadline = datetime.strptime(act["fecha"], "%Y-%m-%d") + timedelta(hours=sla_cfg["horas"])
    else:
        deadline = datetime.strptime(act["fecha"], "%Y-%m-%d") + timedelta(days=sla_cfg.get("dias", 7))
    remaining = deadline - datetime.now()
    total = deadline - datetime.strptime(act["fecha"], "%Y-%m-%d")
    if remaining.total_seconds() <= 0:
        return "🔴", "Vencida"
    ratio = remaining / total if total.total_seconds() > 0 else 0
    if ratio > 0.5:
        return "🟢", f"{remaining.days}d rest."
    return "🟡", f"{remaining.days}d rest."

def add_item(p, e, m, cat, extra=None):
    item = {"id": str(uuid.uuid4())[:8], "Proyecto": p, "Cuenta": e, "Monto": float(m), "CategoriaRaiz": cat, "actividades": []}
    if extra: item.update(extra)
    st.session_state.db_leads.append(item)

# --- 3. SIDEBAR: MOTORES DE CARGA (RESTAURADOS) ---
with st.sidebar:
    st.title("🚀 PG Machine v116")
    
    with st.expander("📥 CARGA MASIVA (EXCEL)", expanded=True):
        perfil = st.radio("Formato:", ["Leads Propios", "Forecast BMC"])
        up = st.file_uploader("Subir Archivo", type=["xlsx"])
        if up and st.button("Ejecutar Importación"):
            df = pd.read_excel(up)
            for _, r in df.iterrows():
                if perfil == "Leads Propios":
                    add_item(r.get('Proyecto','S/N'), r.get('Cuenta','S/N'), r.get('Monto',0), "LEADS")
                else:
                    ex = {"ID": r.get('BMC Opportunity Id','-'), "ST": r.get('Stage','-')}
                    add_item(r.get('Opportunity Name','-'), r.get('Account Name','-'), r.get('Amount USD', 0), "OFFICIAL", ex)
            st.success("Importación exitosa"); st.rerun()

    st.divider()
    st.write("✍️ **ALTA MANUAL**")
    with st.form("manual_entry"):
        nc = st.text_input("Cuenta"); np = st.text_input("Proyecto"); nm = st.number_input("Monto USD", value=0)
        ncat = st.selectbox("Categoría", ["LEADS", "OFFICIAL", "GTM"])
        if st.form_submit_button("Añadir Individual"):
            if nc and np: add_item(np, nc, nm, ncat); st.rerun()

# --- 4. LAYOUT ---
if st.session_state.selected_id:
    l_col, r_col = st.columns([0.25, 0.75])
    with l_col:
        o = next((it for it in st.session_state.db_leads if it['id'] == st.session_state.selected_id), None)
        if o:
            st.markdown(f'<div class="cat-header">{o["CategoriaRaiz"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="scorecard"><div class="sc-cuenta">{o["Cuenta"]}</div><div class="sc-proyecto">{o["Proyecto"]}</div><span class="sc-monto">USD {o["Monto"]:,.0f}</span></div>', unsafe_allow_html=True)
            if st.button("⬅️ VOLVER AL TABLERO"): st.session_state.selected_id = None; st.rerun()
    with r_col:
        st.markdown('<div class="action-panel">', unsafe_allow_html=True)
        st.title(f"🎯 {o['Cuenta']}")
        # Gestión de Actividades
        with st.form("act_v116"):
            c1, c2, c3 = st.columns(3)
            tipo = c1.selectbox("Canal", ["Email", "Llamada", "Reunión", "Asignación"])
            sla = c2.selectbox("SLA", list(SLA_OPCIONES.keys()))
            fecha = c3.date_input("Fecha", value=date.today())
            destinatario = st.text_input("Destinatario")
            desc = st.text_area("Descripción / Notas")
            if st.form_submit_button("Guardar Actividad"):
                o['actividades'].append({"id_act": str(uuid.uuid4())[:6], "tipo": tipo, "fecha": str(fecha), "desc": desc, "estado": "Pendiente", "sla": sla, "destinatario": destinatario})
                st.rerun()
        
        st.subheader("📜 Historial e Interacción")
        for a in reversed(o['actividades']):
            with st.container():
                dest_txt = f' → {a["destinatario"]}' if a.get("destinatario") else ""
                st.markdown(f'<div class="hist-card"><b>{a["tipo"]}</b>{dest_txt} ({a["fecha"]}) - <i>{a["estado"]}</i><br>{a["desc"]}</div>', unsafe_allow_html=True)
                b1, b2 = st.columns([1, 4])
                if b1.button("✅ HECHO", key=f"d_{a['id_act']}"): a['estado'] = "Completada"; st.rerun()
                if b1.button("📩 RPTA", key=f"r_{a['id_act']}"): a['estado'] = "Respondida"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # TABLERO COMPLETO
    cats = ["LEADS", "OFFICIAL", "GTM"]
    cols = st.columns(3)
    for i, col in enumerate(cols):
        with col:
            st.markdown(f'<div class="cat-header">{cats[i]}</div>', unsafe_allow_html=True)
            items = [it for it in st.session_state.db_leads if it['CategoriaRaiz'] == cats[i]]
            for o in sorted(items, key=lambda x: x['Monto'], reverse=True):
                act_lines = ""
                for a in o.get("actividades", []):
                    light, label = _traffic_light(a)
                    dest = f' - {a["destinatario"]}' if a.get("destinatario") else ""
                    act_lines += f'<div class="activity-line">{light} {a["tipo"]}{dest} - {label}</div>'
                st.markdown(f'<div class="scorecard"><div class="sc-cuenta">{o["Cuenta"]}</div><div class="sc-proyecto">{o["Proyecto"]}</div><span class="sc-monto">USD {o["Monto"]:,.0f}</span>{act_lines}</div>', unsafe_allow_html=True)
                if st.button("Gestionar", key=f"g_{o['id']}", use_container_width=True):
                    st.session_state.selected_id = o['id']; st.rerun()
