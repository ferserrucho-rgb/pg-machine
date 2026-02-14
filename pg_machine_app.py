import streamlit as st
import pandas as pd
import json
from collections import OrderedDict
from datetime import datetime, date, timedelta

# --- AUTH GATE (must be before any other UI) ---
from lib.auth import require_auth, get_current_user, is_admin, is_manager_or_admin, logout, get_supabase
from lib import dal
from lib import notifications

st.set_page_config(page_title="PG Machine", layout="wide", initial_sidebar_state="expanded")

if not require_auth():
    st.stop()

# --- Usuario autenticado ---
user = get_current_user()
team_id = user["team_id"]
user_id = user["id"]

# --- 1. ESTILOS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f8fafc; }
    section.main > div[style] { max-width: 100% !important; padding-left: 1rem !important; padding-right: 1rem !important; }
    .block-container { max-width: 100% !important; padding-left: 1rem !important; padding-right: 1rem !important; padding-top: 1.5rem !important; }
    .cat-header { background: #1e293b; color: white; padding: 10px; border-radius: 8px; text-align: center; font-weight: 700; margin-bottom: 15px; }
    .scorecard { background: white; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .badge { float:right; font-size:0.6rem; font-weight:bold; padding:2px 6px; border-radius:8px; text-transform: uppercase; border: 1.2px solid; }
    .sc-cuenta { color: #64748b; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }
    .sc-proyecto { color: #1e293b; font-size: 0.95rem; font-weight: 700; margin: 4px 0; }
    .sc-monto { color: #16a34a; font-size: 1.1rem; font-weight: 800; display: block; }
    .action-panel { background: white; padding: 25px; border-radius: 12px; border: 1px solid #e2e8f0; border-top: 6px solid #1a73e8; }
    .hist-card { background: #f8fafc; padding: 12px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 10px; border-left: 4px solid #94a3b8; }
    .hist-card.tipo-email { border-left-color: #3b82f6; }
    .hist-card.tipo-llamada { border-left-color: #f59e0b; }
    .hist-card.tipo-reunion { border-left-color: #10b981; }
    .hist-card.tipo-asignacion { border-left-color: #8b5cf6; }
    .hist-card.enviada { background: #f5f3ff; border-left-color: #8b5cf6; }
    .hist-card.bloqueada { background: #fef2f2; border-left-color: #ef4444; }
    .hist-card.respondida { background: #f0fdf4; border-left-color: #16a34a; }
    .estado-enviada { color: #8b5cf6; font-weight: 600; }
    .estado-bloqueada { color: #ef4444; font-weight: 700; }
    .activity-line { font-size: 0.72rem; color: #475569; margin: 2px 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .account-group { background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 10px; padding: 10px; margin-bottom: 12px; }
    .account-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
    .account-name { color: #1e293b; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; }
    .account-total { color: #16a34a; font-size: 0.8rem; font-weight: 800; }
    .account-badge { background: #e2e8f0; color: #475569; font-size: 0.65rem; font-weight: 600; padding: 2px 6px; border-radius: 6px; }
    /* Clickable card — rendered as HTML + invisible button overlay */
    .pgm-card-wrap { position: relative; background: white; border: 1px solid #e2e8f0; border-radius: 8px 8px 0 0; padding: 10px 12px; margin-bottom: 0; box-shadow: 0 1px 3px rgba(0,0,0,0.04); transition: all 0.2s; }
    .pgm-card-wrap:hover { border-color: #1a73e8; border-width: 2px; box-shadow: 0 3px 12px rgba(26,115,232,0.18); }
    /* Card open button — styled via JS class .pgm-open-btn */
    .pgm-open-btn { font-size: 0.55rem !important; padding: 2px 0 !important; min-height: 0 !important; height: auto !important; color: #94a3b8 !important; border: 1px solid #e2e8f0 !important; border-top: none !important; border-radius: 0 0 8px 8px !important; background: #fafbfc !important; margin-top: -4px !important; margin-bottom: 6px !important; }
    .pgm-open-btn:hover { color: #1a73e8 !important; background: #eff6ff !important; }
    .pgm-card-wrap .opp-header { font-size: 0.85rem; font-weight: 600; color: #1e293b; margin-bottom: 3px; }
    .pgm-card-wrap .stage-badge { color: white; font-size: 0.58rem; font-weight: 600; font-style: normal; background: #8b5cf6; padding: 2px 7px; border-radius: 10px; font-family: Georgia, serif; letter-spacing: 0.03em; vertical-align: middle; }
    .pgm-card-wrap .amount { color: #16a34a; font-size: 0.93rem; font-weight: 800; }
    .pgm-card-wrap .opp-meta { font-size: 0.62rem; color: #64748b; margin: 4px 0 0 0; }
    .pgm-card-wrap .opp-id-box { font-family: 'Courier New', monospace; font-size: 0.6rem; font-weight: 700; color: #334155; background: #f1f5f9; border: 1px solid #cbd5e1; padding: 2px 6px; border-radius: 4px; }
    .pgm-card-wrap .act-sep { border-top: 1px dashed #e2e8f0; margin: 6px 0 4px 0; }
    .pgm-card-wrap .act-line { font-size: 0.6rem; color: #475569; font-style: italic; line-height: 1.4; padding: 1px 0 1px 8px; border-left: 2px solid #cbd5e1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    /* User identity bar */
    .user-bar { background: #1e293b; color: white; padding: 6px 14px; border-radius: 6px; font-size: 0.78rem; font-weight: 600; display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
    .user-bar .user-avatar { background: #3b82f6; color: white; width: 28px; height: 28px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: 700; }
    .user-bar .user-role { background: rgba(255,255,255,0.15); padding: 2px 8px; border-radius: 4px; font-size: 0.65rem; text-transform: uppercase; }
    /* Initials avatar badge */
    .avatar-badge { display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 50%; background: #3b82f6; color: white; font-size: 0.6rem; font-weight: 700; margin: 0 2px; vertical-align: middle; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("""
    <script>
    function pgmFixLayout() {
        // Full-width layout
        document.querySelectorAll('section.main > div').forEach(el => {
            if (el.style.maxWidth) { el.style.maxWidth = '100%'; el.style.paddingLeft = '1rem'; el.style.paddingRight = '1rem'; }
        });
        // Style card buttons that follow card HTML
        document.querySelectorAll('button').forEach(btn => {
            const txt = (btn.textContent || '').trim();
            if (txt === '▸' && !btn.classList.contains('pgm-open-btn')) {
                btn.classList.add('pgm-open-btn');
            }
        });
    }
    const observer = new MutationObserver(pgmFixLayout);
    observer.observe(document.body, {childList: true, subtree: true, attributes: true});
    pgmFixLayout();
    </script>
    """, unsafe_allow_html=True)

def _get_initials(full_name: str) -> str:
    """Extrae iniciales: primera letra del nombre + primera del apellido."""
    parts = (full_name or "").strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    elif parts:
        return parts[0][:2].upper()
    return "??"

user_initials = _get_initials(user["full_name"])
user_bar_html = f'<div class="user-bar"><span class="user-avatar">{user_initials}</span> {user["full_name"]} <span class="user-role">{user["role"]}</span></div>'

# --- 2. DATOS DESDE SUPABASE ---
if 'selected_id' not in st.session_state:
    st.session_state.selected_id = None
if 'focused_cat' not in st.session_state:
    st.session_state.focused_cat = None

# Cargar configuración del equipo
SLA_OPCIONES = dal.get_sla_options(team_id)
SLA_RESPUESTA = dal.get_sla_respuesta(team_id)
CATEGORIAS = dal.get_categorias(team_id)

# Cargar miembros del equipo para asignaciones
team_members = dal.get_team_members(team_id)
RECURSOS_PRESALES = {m["id"]: f'{m["full_name"]} ({m["specialty"]})' if m.get("specialty") else m["full_name"] for m in team_members}

def _parse_date(val):
    if not val or str(val).strip() in ("", "NaT", "nan", "None"):
        return None
    s = str(val).strip()
    for fmt in ("%Y-%m-%d", "%b %d, %Y", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    try:
        return pd.to_datetime(s).date()
    except Exception:
        return None

def _sla_to_hours(sla_key: str) -> int | None:
    """Convierte clave SLA a horas totales."""
    cfg = SLA_OPCIONES.get(sla_key, {})
    if "horas" in cfg:
        return cfg["horas"]
    if "dias" in cfg:
        return cfg["dias"] * 24
    return None

def _naive(dt):
    """Strip timezone info to make datetime naive (for safe arithmetic)."""
    if dt and hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt

def _traffic_light(act):
    """Calcula semáforo para una actividad (formato Supabase)."""
    estado = act.get("estado", "Pendiente")
    now = datetime.now()

    if estado == "Respondida":
        return "🟩", "Respondida"

    if estado == "Enviada":
        enviada_ts = _naive(datetime.fromisoformat(act["enviada_ts"])) if act.get("enviada_ts") else now
        sla_dias = act.get("sla_respuesta_dias", 7)
        deadline = enviada_ts + timedelta(days=sla_dias)
        remaining = deadline - now
        if remaining.total_seconds() <= 0:
            return "🟥", "Bloqueada"
        return "🟪", f"Esp. rpta {remaining.days}d"

    # Pendiente
    fecha_str = act.get("fecha", "")
    if isinstance(fecha_str, date):
        fecha = fecha_str
    else:
        fecha = _parse_date(fecha_str) or date.today()

    hoy = date.today()
    if fecha > hoy:
        return "🟨", f"Pendiente {fecha.strftime('%d/%m')}"
    if fecha == hoy:
        return "🟨", "Hoy"

    # SLA check
    sla_deadline_str = act.get("sla_deadline")
    if sla_deadline_str:
        deadline = _naive(datetime.fromisoformat(sla_deadline_str)) if isinstance(sla_deadline_str, str) else _naive(sla_deadline_str)
        created = _naive(datetime.fromisoformat(act["created_at"])) if isinstance(act.get("created_at"), str) else (_naive(act.get("created_at")) or now)
        remaining = deadline - now
        if remaining.total_seconds() <= 0:
            return "🟥", "Vencida"
        total = deadline - created
        ratio = remaining / total if total.total_seconds() > 0 else 0
        hours_left = remaining.total_seconds() / 3600
        if ratio > 0.5:
            return ("🟩", f"{hours_left:.0f}h rest.") if hours_left < 24 else ("🟩", f"{remaining.days}d rest.")
        return ("🟨", f"{hours_left:.0f}h rest.") if hours_left < 24 else ("🟨", f"{remaining.days}d rest.")

    # Fallback from sla_key
    sla_cfg = SLA_OPCIONES.get(act.get("sla_key", ""), {})
    created = _naive(datetime.fromisoformat(act["created_at"])) if act.get("created_at") else now
    if "horas" in sla_cfg:
        deadline = created + timedelta(hours=sla_cfg["horas"])
    else:
        deadline = created + timedelta(days=sla_cfg.get("dias", 7))
    remaining = deadline - now
    if remaining.total_seconds() <= 0:
        return "🟥", "Vencida"
    total = deadline - created
    ratio = remaining / total if total.total_seconds() > 0 else 0
    hours_left = remaining.total_seconds() / 3600
    if ratio > 0.5:
        return ("🟩", f"{hours_left:.0f}h rest.") if hours_left < 24 else ("🟩", f"{remaining.days}d rest.")
    return ("🟨", f"{hours_left:.0f}h rest.") if hours_left < 24 else ("🟨", f"{remaining.days}d rest.")


# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("🚀 PG Machine")
    st.caption(f"👤 {user['full_name']} ({user['role']})")
    if st.button("Cerrar Sesión", key="logout_btn"):
        logout()

    st.divider()

    with st.expander("📥 CARGA MASIVA (EXCEL)", expanded=True):
        perfil = st.radio("Formato:", ["Leads Propios", "Forecast BMC"])
        up = st.file_uploader("Subir Archivo", type=["xlsx"])
        if up and st.button("Ejecutar Importación"):
            df = pd.read_excel(up)
            items = []
            for _, r in df.iterrows():
                if perfil == "Leads Propios":
                    parsed = _parse_date(r.get('Close Date', None))
                    items.append({
                        "proyecto": r.get('Proyecto', 'S/N'),
                        "cuenta": r.get('Empresa', r.get('Cuenta', 'S/N')),
                        "monto": r.get('Valor', r.get('Monto', 0)),
                        "categoria": "LEADS",
                        "close_date": str(parsed) if parsed else None,
                    })
                else:
                    parsed = _parse_date(r.get('Close Date', None))
                    items.append({
                        "proyecto": r.get('Opportunity Name', '-'),
                        "cuenta": r.get('Account Name', '-'),
                        "monto": r.get('Amount USD', 0),
                        "categoria": "OFFICIAL",
                        "opp_id": str(r.get('BMC Opportunity Id', '')),
                        "stage": str(r.get('Stage', '')),
                        "close_date": str(parsed) if parsed else None,
                    })
            count = dal.bulk_create_opportunities(team_id, user_id, items)
            st.success(f"Importación exitosa: {count} oportunidades")
            st.rerun()

    st.divider()
    st.write("✍️ **ALTA MANUAL**")
    with st.form("manual_entry"):
        nc = st.text_input("Cuenta")
        np = st.text_input("Proyecto")
        nm = st.number_input("Monto USD", value=0)
        ncat = st.selectbox("Categoría", CATEGORIAS)
        n_opp_id = st.text_input("Opportunity ID")
        n_stage = st.text_input("Stage")
        n_close = st.date_input("Close Date", value=None)
        if st.form_submit_button("Añadir Individual"):
            if nc and np:
                parsed = _parse_date(n_close)
                dal.create_opportunity(team_id, user_id, {
                    "proyecto": np, "cuenta": nc, "monto": nm,
                    "categoria": ncat, "opp_id": n_opp_id,
                    "stage": n_stage,
                    "close_date": str(parsed) if parsed else None,
                })
                st.rerun()


# --- 4. LAYOUT ---
if st.session_state.selected_id:
    # --- VISTA DETALLE ---
    st.markdown(user_bar_html, unsafe_allow_html=True)
    opp = dal.get_opportunity(st.session_state.selected_id)
    if not opp:
        st.error("Oportunidad no encontrada.")
        st.session_state.selected_id = None
        st.rerun()

    l_col, r_col = st.columns([0.25, 0.75])
    with l_col:
        opp_id_html = f'<span class="opp-id">ID: {opp.get("opp_id","")}</span>' if opp.get("opp_id") else ""
        close_html = f'<span class="opp-id">Cierre: {opp.get("close_date","")}</span>' if opp.get("close_date") else ""
        stage_html = f' <span class="opp-stage">{opp.get("stage","")}</span>' if opp.get("stage") else ""
        st.markdown(f'<div class="cat-header">{opp["categoria"]}{stage_html}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="scorecard"><div class="sc-cuenta">{opp["cuenta"]}</div><div class="sc-proyecto">{opp["proyecto"]}</div><span class="sc-monto">USD {float(opp.get("monto") or 0):,.0f}</span>{opp_id_html}{close_html}</div>', unsafe_allow_html=True)
        btn_c1, btn_c2 = st.columns(2)
        if btn_c1.button("⬅️ VOLVER", use_container_width=True):
            st.session_state.selected_id = None
            st.rerun()
        if btn_c2.button("🗑️ ELIMINAR", key="del_opp", use_container_width=True):
            st.session_state[f"confirm_del_opp_{opp['id']}"] = True
        if st.session_state.get(f"confirm_del_opp_{opp['id']}"):
            st.warning(f"Eliminar **{opp['proyecto']}** y todas sus actividades?")
            dc1, dc2 = st.columns(2)
            if dc1.button("Confirmar", key="confirm_del_opp_yes", use_container_width=True):
                dal.delete_opportunity(opp["id"])
                st.session_state.selected_id = None
                st.session_state.pop(f"confirm_del_opp_{opp['id']}", None)
                st.rerun()
            if dc2.button("Cancelar", key="confirm_del_opp_no", use_container_width=True):
                st.session_state.pop(f"confirm_del_opp_{opp['id']}", None)
                st.rerun()

    with r_col:
        st.markdown(f'<div style="font-size:1.3rem; font-weight:700; color:#1e293b; padding:8px 0 4px 0;">🎯 {opp["cuenta"]}</div>', unsafe_allow_html=True)
        st.caption("📜 Historial e Interacción")
        activities = dal.get_activities_for_opportunity(opp["id"])
        for a in activities:
            with st.container():
                dest_txt = f' → {a["destinatario"]}' if a.get("destinatario") else ""
                # Mostrar nombre del asignado
                assigned_name = ""
                if a.get("assigned_profile") and a["assigned_profile"].get("full_name"):
                    assigned_name = a["assigned_profile"]["full_name"]
                elif a.get("assigned_to"):
                    assigned_name = RECURSOS_PRESALES.get(a["assigned_to"], "")

                light, label = _traffic_light(a)
                tipo_class = f'tipo-{a.get("tipo", "").lower().replace("ó", "o")}' if a.get("tipo") else ""
                if a["estado"] == "Enviada" and label == "Bloqueada":
                    card_class = f"hist-card bloqueada"
                    estado_html = '<span class="estado-bloqueada">🟥 BLOQUEADA</span>'
                elif a["estado"] == "Enviada":
                    card_class = f"hist-card enviada"
                    estado_html = f'<span class="estado-enviada">🟪 {a["estado"]} — {label}</span>'
                elif a["estado"] == "Respondida":
                    card_class = f"hist-card respondida"
                    estado_html = f'<span style="color:#16a34a; font-weight:600;">🟩 Respondida</span>'
                else:
                    card_class = f"hist-card {tipo_class}"
                    estado_html = f'<i>{a["estado"]}</i>'

                obj_txt = f' {a["objetivo"]}' if a.get("objetivo") else ""
                asig_initials = _get_initials(assigned_name) if assigned_name else ""
                asig_txt = f' <span class="avatar-badge">{asig_initials}</span> <b>{assigned_name}</b>' if assigned_name else ""
                feedback_html = f'<br><b>Feedback:</b> {a["feedback"]}' if a.get("feedback") else ""
                fecha_display = str(a.get("fecha", ""))
                tipo_icons = {"Email": "📧", "Llamada": "📞", "Reunión": "🤝", "Asignación": "👤"}
                tipo_icon = tipo_icons.get(a.get("tipo", ""), "📋")

                st.markdown(f'<div class="{card_class}"><b>{tipo_icon} {a["tipo"]}{obj_txt}</b>{dest_txt}{asig_txt} <span style="color:#94a3b8; font-size:0.8rem;">({fecha_display})</span> {estado_html}<br><span style="color:#64748b; font-size:0.85rem;">{a.get("descripcion", "")}</span>{feedback_html}</div>', unsafe_allow_html=True)

                aid = a['id']
                if a["estado"] == "Pendiente":
                    b1, b2 = st.columns(2)
                    if b1.button("✅ ENVIADO", key=f"d_{aid}", use_container_width=True):
                        dal.update_activity(aid, {"estado": "Enviada"})
                        st.rerun()
                    if b2.button("✏️ Editar", key=f"toggle_edit_{aid}", use_container_width=True):
                        st.session_state[f"show_edit_{aid}"] = not st.session_state.get(f"show_edit_{aid}", False)
                        st.rerun()
                elif a["estado"] == "Enviada":
                    if st.session_state.get(f"show_fb_{aid}"):
                        with st.form(f"fb_form_{aid}"):
                            feedback = st.text_area("Feedback del cliente")
                            st.divider()
                            crear_seguimiento = st.checkbox("🔁 Crear actividad de seguimiento", value=False, key=f"seg_{aid}")
                            seg_fecha = st.date_input("Fecha seguimiento", value=date.today() + timedelta(days=7), key=f"segf_{aid}")
                            if st.form_submit_button("Confirmar Respuesta"):
                                dal.update_activity(aid, {"estado": "Respondida", "feedback": feedback})
                                if crear_seguimiento:
                                    dal.create_activity(a["opportunity_id"], a["team_id"], user_id, {
                                        "tipo": a.get("tipo", "Email"),
                                        "fecha": str(seg_fecha),
                                        "objetivo": a.get("objetivo", ""),
                                        "descripcion": f'Seguimiento: {feedback}' if feedback else a.get("descripcion", ""),
                                        "sla_key": a.get("sla_key", ""),
                                        "sla_hours": a.get("sla_hours"),
                                        "sla_respuesta_dias": a.get("sla_respuesta_dias", 7),
                                        "destinatario": a.get("destinatario", ""),
                                        "assigned_to": a.get("assigned_to"),
                                    })
                                st.session_state.pop(f"show_fb_{aid}", None)
                                st.rerun()
                    else:
                        b1, b2, b3 = st.columns(3)
                        if b1.button("📩 RESPONDIDA", key=f"r_{aid}", use_container_width=True):
                            st.session_state[f"show_fb_{aid}"] = True
                            st.rerun()
                        if b2.button("✏️ Editar", key=f"toggle_edit_{aid}", use_container_width=True):
                            st.session_state[f"show_edit_{aid}"] = not st.session_state.get(f"show_edit_{aid}", False)
                            st.rerun()
                        if b3.button("🔄 REENVIAR", key=f"re_{aid}", use_container_width=True):
                            dal.update_activity(aid, {"estado": "Pendiente", "enviada_ts": None, "response_deadline": None})
                            st.rerun()
                else:
                    if st.button("✏️ Editar", key=f"toggle_edit_{aid}"):
                        st.session_state[f"show_edit_{aid}"] = not st.session_state.get(f"show_edit_{aid}", False)
                        st.rerun()

                # Inline edit form (toggled)
                if st.session_state.get(f"show_edit_{aid}"):
                    with st.form(f"edit_act_{aid}"):
                        ea_c1, ea_c2, ea_c3 = st.columns(3)
                        ea_tipo = ea_c1.selectbox("Canal", ["Email", "Llamada", "Reunión", "Asignación"],
                            index=["Email", "Llamada", "Reunión", "Asignación"].index(a.get("tipo", "Email")) if a.get("tipo", "Email") in ["Email", "Llamada", "Reunión", "Asignación"] else 0,
                            key=f"et_{aid}")
                        sla_keys = list(SLA_OPCIONES.keys())
                        ea_sla = ea_c2.selectbox("SLA", sla_keys,
                            index=sla_keys.index(a["sla_key"]) if a.get("sla_key") in sla_keys else 0,
                            key=f"es_{aid}")
                        ea_fecha = ea_c3.date_input("Fecha", value=_parse_date(a.get("fecha", "")) or date.today(), key=f"ef_{aid}")
                        ea_c4, ea_c5 = st.columns(2)
                        ea_objetivo = ea_c4.text_input("Objetivo", value=a.get("objetivo", ""), key=f"eo_{aid}")
                        ea_dest = ea_c5.text_input("Destinatario", value=a.get("destinatario", ""), key=f"ed_{aid}")
                        sla_rpta_keys = list(SLA_RESPUESTA.keys())
                        sla_rpta_vals = list(SLA_RESPUESTA.values())
                        cur_sla_idx = sla_rpta_vals.index(a.get("sla_respuesta_dias", 7)) if a.get("sla_respuesta_dias", 7) in sla_rpta_vals else 1
                        ea_sla_rpta = st.selectbox("SLA Respuesta", sla_rpta_keys, index=cur_sla_idx, key=f"esr_{aid}")
                        ea_desc = st.text_area("Descripción", value=a.get("descripcion", ""), height=60, key=f"edc_{aid}")
                        fc1, fc2 = st.columns(2)
                        if fc1.form_submit_button("💾 Guardar"):
                            new_sla_hours = _sla_to_hours(ea_sla)
                            dal.update_activity(aid, {
                                "tipo": ea_tipo, "sla_key": ea_sla, "sla_hours": new_sla_hours,
                                "fecha": str(ea_fecha), "objetivo": ea_objetivo,
                                "destinatario": ea_dest, "sla_respuesta_dias": SLA_RESPUESTA[ea_sla_rpta],
                                "descripcion": ea_desc,
                            })
                            st.session_state.pop(f"show_edit_{aid}", None)
                            st.rerun()
                    if st.button("🗑️ Eliminar actividad", key=f"del_act_{aid}"):
                        st.session_state[f"confirm_del_act_{aid}"] = True
                    if st.session_state.get(f"confirm_del_act_{aid}"):
                        st.warning("Eliminar esta actividad?")
                        da1, da2 = st.columns(2)
                        if da1.button("Confirmar", key=f"cdel_act_y_{aid}", use_container_width=True):
                            dal.delete_activity(aid)
                            st.session_state.pop(f"confirm_del_act_{aid}", None)
                            st.rerun()
                        if da2.button("Cancelar", key=f"cdel_act_n_{aid}", use_container_width=True):
                            st.session_state.pop(f"confirm_del_act_{aid}", None)
                            st.rerun()

        if not activities:
            st.info("No hay actividades registradas aún.")

        st.divider()

        # --- EDITING SECTION (compressed in expanders) ---
        with st.expander("✏️ Editar Oportunidad", expanded=False):
            with st.form("edit_opp"):
                ed_c1, ed_c2, ed_c3 = st.columns(3)
                ed_cuenta = ed_c1.text_input("Cuenta", value=opp["cuenta"])
                ed_proyecto = ed_c2.text_input("Proyecto", value=opp["proyecto"])
                ed_monto = ed_c3.number_input("Monto USD", value=float(opp.get("monto") or 0))
                ed_c4, ed_c5, ed_c6 = st.columns(3)
                ed_cat = ed_c4.selectbox("Categoría", CATEGORIAS, index=CATEGORIAS.index(opp["categoria"]) if opp["categoria"] in CATEGORIAS else 0)
                ed_opp_id = ed_c5.text_input("Opportunity ID", value=opp.get("opp_id", ""))
                ed_stage = ed_c6.text_input("Stage", value=opp.get("stage", ""))
                close_val = _parse_date(opp.get("close_date", ""))
                ed_close = st.date_input("Close Date", value=close_val)
                if st.form_submit_button("💾 Guardar Cambios"):
                    dal.update_opportunity(opp["id"], {
                        "cuenta": ed_cuenta, "proyecto": ed_proyecto,
                        "monto": float(ed_monto), "categoria": ed_cat,
                        "opp_id": ed_opp_id, "stage": ed_stage,
                        "close_date": str(ed_close) if ed_close else None,
                    })
                    st.rerun()

        with st.expander("➕ Nueva Actividad", expanded=False):
            tipo = st.selectbox("Canal", ["Email", "Llamada", "Reunión", "Asignación"])
            with st.form("act_form"):
                c1, c2, c3 = st.columns(3)
                sla_key = c1.selectbox("SLA", list(SLA_OPCIONES.keys()))
                fecha = c2.date_input("Fecha", value=date.today())
                objetivo = c3.text_input("Objetivo")
                asignado_a_id = None
                if tipo == "Asignación":
                    c4, c5, c6 = st.columns(3)
                    destinatario = c4.text_input("Destinatario")
                    recurso_opciones = [""] + list(RECURSOS_PRESALES.values())
                    recurso_ids = [""] + list(RECURSOS_PRESALES.keys())
                    sel_idx = c5.selectbox("Asignado a", range(len(recurso_opciones)), format_func=lambda i: recurso_opciones[i])
                    if sel_idx > 0:
                        asignado_a_id = recurso_ids[sel_idx]
                    sla_rpta = c6.selectbox("SLA Respuesta", list(SLA_RESPUESTA.keys()), index=1)
                else:
                    c4, c5 = st.columns(2)
                    destinatario = c4.text_input("Destinatario")
                    sla_rpta = c5.selectbox("SLA Respuesta", list(SLA_RESPUESTA.keys()), index=1)
                desc = st.text_area("Descripción / Notas", height=80)
                if st.form_submit_button("Guardar Actividad"):
                    sla_hours = _sla_to_hours(sla_key)
                    new_act = dal.create_activity(opp["id"], team_id, user_id, {
                        "tipo": tipo, "fecha": str(fecha), "objetivo": objetivo,
                        "descripcion": desc, "sla_key": sla_key, "sla_hours": sla_hours,
                        "sla_respuesta_dias": SLA_RESPUESTA[sla_rpta],
                        "destinatario": destinatario, "assigned_to": asignado_a_id,
                    })
                    if asignado_a_id and new_act:
                        assignee = dal.get_team_member(asignado_a_id)
                        if assignee:
                            notifications.send_assignment_notification(new_act, assignee, opp)
                            dal.create_notification(team_id, new_act["id"], asignado_a_id, "assignment")
                    st.rerun()

else:
    # --- VISTAS PRINCIPALES ---
    tabs = ["📊 Tablero", "📋 Actividades"]
    if is_manager_or_admin():
        tabs.append("📈 Control")
    tabs.append("👥 Equipo")

    selected_tabs = st.tabs(tabs)

    # --- TAB: TABLERO ---
    with selected_tabs[0]:
        st.markdown(user_bar_html, unsafe_allow_html=True)
        all_opps = dal.get_opportunities(team_id)
        # Precargar actividades para todas las oportunidades
        all_acts_by_opp = {}
        all_activities = dal.get_all_activities(team_id)
        for act in all_activities:
            all_acts_by_opp.setdefault(act["opportunity_id"], []).append(act)

        # Category focus: show buttons to toggle
        focused = st.session_state.focused_cat
        if focused:
            visible_cats = [focused]
        else:
            visible_cats = CATEGORIAS

        # Category selector buttons
        btn_cols = st.columns(len(CATEGORIAS))
        for i, bc in enumerate(btn_cols):
            cat = CATEGORIAS[i]
            if focused == cat:
                if bc.button(f"✕ {cat} — Ver todas", key=f"unfocus_{cat}", use_container_width=True):
                    st.session_state.focused_cat = None
                    st.rerun()
            else:
                if bc.button(cat, key=f"focus_{cat}", use_container_width=True):
                    st.session_state.focused_cat = cat
                    st.rerun()

        def _render_account_group(cuenta, opps, all_acts_by_opp):
            """Renders one account group with its opportunity cards."""
            total = sum(float(o.get('monto') or 0) for o in opps)
            badge = f'<span class="account-badge">{len(opps)} opp{"s" if len(opps) > 1 else ""}</span>' if len(opps) > 1 else ""
            import re
            safe_cuenta = re.sub(r'[^a-zA-Z0-9]', '_', cuenta)
            st.markdown(f'<div class="account-group"><div class="account-header"><span class="account-name">{cuenta}</span><span class="account-total">USD {total:,.0f}</span>{badge}</div>', unsafe_allow_html=True)
            for o in opps:
                opp_acts = all_acts_by_opp.get(o["id"], [])
                monto_val = float(o.get("monto") or 0)
                # Build HTML card
                stage_html = f' <span class="stage-badge">{o["stage"]}</span>' if o.get("stage") else ""
                header_html = f'<div class="opp-header">{o["proyecto"]}{stage_html} <span class="amount">USD {monto_val:,.0f}</span></div>'
                meta_parts = []
                if o.get("opp_id"):
                    meta_parts.append(f'<span class="opp-id-box">{o["opp_id"]}</span>')
                if o.get("close_date"):
                    meta_parts.append(f'Cierre: {o["close_date"]}')
                meta_html = f'<div class="opp-meta">{" &nbsp; ".join(meta_parts)}</div>' if meta_parts else ""
                # Activities
                act_lines = []
                for a in opp_acts:
                    light, label = _traffic_light(a)
                    obj = f' {a["objetivo"]}' if a.get("objetivo") else ""
                    dest = f' - {a["destinatario"]}' if a.get("destinatario") else ""
                    asig_name = ""
                    if a.get("assigned_profile") and a["assigned_profile"].get("full_name"):
                        asig_name = a["assigned_profile"]["full_name"]
                    asig_init = _get_initials(asig_name) if asig_name else ""
                    asig = f' [{asig_init}]' if asig_init else ""
                    act_lines.append(f'<div class="act-line">{light}{obj}{dest}{asig} — {label}</div>')
                acts_html = ""
                if act_lines:
                    acts_html = '<div class="act-sep"></div>' + "".join(act_lines)
                card_html = f'<div class="pgm-card-wrap">{header_html}{meta_html}{acts_html}</div>'
                st.markdown(card_html, unsafe_allow_html=True)
                if st.button("▸", key=f"g_{o['id']}", use_container_width=True):
                    st.session_state.selected_id = o['id']
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        if focused:
            # Focused mode: single category in 2 columns
            cat = visible_cats[0]
            items = [o for o in all_opps if o['categoria'] == cat]
            accounts = OrderedDict()
            for o in sorted(items, key=lambda x: float(x.get('monto') or 0), reverse=True):
                accounts.setdefault(o['cuenta'], []).append(o)
            account_list = list(accounts.items())
            col_left, col_right = st.columns(2)
            for idx, (cuenta, opps) in enumerate(account_list):
                with col_left if idx % 2 == 0 else col_right:
                    _render_account_group(cuenta, opps, all_acts_by_opp)
        else:
            # Normal mode: one column per category
            cols = st.columns(len(visible_cats))
            for i, col in enumerate(cols):
                with col:
                    cat = visible_cats[i]
                    items = [o for o in all_opps if o['categoria'] == cat]
                    accounts = OrderedDict()
                    for o in sorted(items, key=lambda x: float(x.get('monto') or 0), reverse=True):
                        accounts.setdefault(o['cuenta'], []).append(o)
                    for cuenta, opps in accounts.items():
                        _render_account_group(cuenta, opps, all_acts_by_opp)

    # --- TAB: ACTIVIDADES ---
    with selected_tabs[1]:
        st.markdown(user_bar_html, unsafe_allow_html=True)

        ALL_COLUMNS = ["Semáforo", "Estado", "Categoría", "Cuenta", "Proyecto", "Monto USD", "Canal", "Objetivo", "Destinatario", "Asignado a", "Fecha", "SLA", "SLA Respuesta (días)", "Estado Interno", "Feedback", "Descripción"]
        DEFAULT_COLUMNS = ["Semáforo", "Estado", "Categoría", "Cuenta", "Proyecto", "Canal", "Objetivo", "Destinatario", "Fecha", "Estado Interno"]

        # Filter: my tasks vs team tasks
        scope_options = ["📋 Mis tareas", "👥 Tareas del equipo", "🌐 Todas"]
        act_scope = st.radio("Vista", scope_options, horizontal=True, key="act_scope", index=2)

        all_activities_full = dal.get_all_activities(team_id)

        # Apply scope filter
        if act_scope == "📋 Mis tareas":
            all_activities_full = [a for a in all_activities_full if a.get("assigned_to") == user_id or a.get("created_by") == user_id]
        elif act_scope == "👥 Tareas del equipo":
            all_activities_full = [a for a in all_activities_full if a.get("assigned_to") != user_id and a.get("created_by") != user_id]

        all_acts_display = []
        act_refs = []
        for a in all_activities_full:
            opp_data = a.get("opportunity", {}) or {}
            light, label = _traffic_light(a)
            assigned_name = ""
            if a.get("assigned_profile") and a["assigned_profile"].get("full_name"):
                assigned_name = a["assigned_profile"]["full_name"]

            all_acts_display.append({
                "Semáforo": light,
                "Estado": label,
                "Categoría": opp_data.get("categoria", ""),
                "Cuenta": opp_data.get("cuenta", ""),
                "Proyecto": opp_data.get("proyecto", ""),
                "Monto USD": opp_data.get("monto", 0),
                "Canal": a.get("tipo", ""),
                "Objetivo": a.get("objetivo", ""),
                "Destinatario": a.get("destinatario", ""),
                "Asignado a": assigned_name,
                "Fecha": str(a.get("fecha", "")),
                "SLA": a.get("sla_key", ""),
                "SLA Respuesta (días)": a.get("sla_respuesta_dias", ""),
                "Estado Interno": a.get("estado", ""),
                "Feedback": a.get("feedback", ""),
                "Descripción": a.get("descripcion", ""),
            })
            act_refs.append(a)

        if not all_acts_display:
            st.info("No hay actividades registradas aún.")
        else:
            if 'act_columns' not in st.session_state:
                st.session_state.act_columns = DEFAULT_COLUMNS
            selected_cols = st.multiselect("Columnas visibles", ALL_COLUMNS, default=st.session_state.act_columns, key="col_selector")
            st.session_state.act_columns = selected_cols

            fc1, fc2, fc3, fc4 = st.columns(4)
            cats_disponibles = sorted(set(r["Categoría"] for r in all_acts_display))
            fil_cat = fc1.multiselect("Categoría", cats_disponibles, default=cats_disponibles)
            estados_disponibles = sorted(set(r["Estado Interno"] for r in all_acts_display))
            fil_estado = fc2.multiselect("Estado", estados_disponibles, default=estados_disponibles)
            canales_disponibles = sorted(set(r["Canal"] for r in all_acts_display))
            fil_canal = fc3.multiselect("Canal", canales_disponibles, default=canales_disponibles)
            cuentas_disponibles = sorted(set(r["Cuenta"] for r in all_acts_display))
            fil_cuenta = fc4.multiselect("Cuenta", cuentas_disponibles, default=cuentas_disponibles)

            df_acts = pd.DataFrame(all_acts_display)
            mask = (
                (df_acts["Categoría"].isin(fil_cat)) &
                (df_acts["Estado Interno"].isin(fil_estado)) &
                (df_acts["Canal"].isin(fil_canal)) &
                (df_acts["Cuenta"].isin(fil_cuenta))
            )
            df_filtered = df_acts[mask]

            st.divider()
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Total", len(df_filtered))
            m2.metric("Pendientes", len(df_filtered[df_filtered["Estado Interno"] == "Pendiente"]))
            m3.metric("Enviadas", len(df_filtered[df_filtered["Estado Interno"] == "Enviada"]))
            m4.metric("Respondidas", len(df_filtered[df_filtered["Estado Interno"] == "Respondida"]))
            m5.metric("🟥 Bloqueadas/Vencidas", len(df_filtered[df_filtered["Estado"].isin(["Bloqueada", "Vencida"])]))

            st.divider()
            sorted_indices = df_filtered.sort_values("Fecha", ascending=False).index.tolist() if "Fecha" in df_filtered.columns else df_filtered.index.tolist()
            display_cols = [c for c in selected_cols if c in df_filtered.columns]

            n_cols = len(display_cols)
            widths = [1.0 / n_cols] * n_cols + [0.04] if n_cols else [1, 0.04]
            hdr_cols = st.columns(widths)
            for j, c in enumerate(display_cols):
                hdr_cols[j].markdown(f'<div style="font-size:0.7rem; font-weight:700; color:#64748b; text-transform:uppercase;">{c}</div>', unsafe_allow_html=True)

            for row_idx in sorted_indices:
                row = all_acts_display[row_idx]
                a_ref = act_refs[row_idx]
                row_cols = st.columns(widths)
                for j, c in enumerate(display_cols):
                    row_cols[j].markdown(f'<div style="font-size:0.8rem; padding:4px 0; border-bottom:1px solid #e2e8f0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{row.get(c, "")}</div>', unsafe_allow_html=True)
                if row_cols[-1].button("✏️", key=f"eab_{row_idx}"):
                    st.session_state["edit_act_tab_idx"] = row_idx

                if st.session_state.get("edit_act_tab_idx") == row_idx:
                    with st.form(f"edit_act_tab_{row_idx}"):
                        ea_c1, ea_c2, ea_c3 = st.columns(3)
                        ea_tipo = ea_c1.selectbox("Canal", ["Email", "Llamada", "Reunión", "Asignación"],
                            index=["Email", "Llamada", "Reunión", "Asignación"].index(a_ref.get("tipo", "Email")) if a_ref.get("tipo") in ["Email", "Llamada", "Reunión", "Asignación"] else 0)
                        sla_keys = list(SLA_OPCIONES.keys())
                        ea_sla = ea_c2.selectbox("SLA", sla_keys,
                            index=sla_keys.index(a_ref["sla_key"]) if a_ref.get("sla_key") in sla_keys else 0)
                        ea_fecha = ea_c3.date_input("Fecha", value=_parse_date(a_ref.get("fecha", "")) or date.today())
                        ea_objetivo = st.text_input("Objetivo", value=a_ref.get("objetivo", ""))
                        ea_c4, ea_c5, ea_c6 = st.columns(3)
                        ea_dest = ea_c4.text_input("Destinatario", value=a_ref.get("destinatario", ""))
                        # Asignado selector
                        recurso_opciones_tab = [""] + list(RECURSOS_PRESALES.values())
                        recurso_ids_tab = [""] + list(RECURSOS_PRESALES.keys())
                        current_assigned = a_ref.get("assigned_to", "")
                        assigned_idx = 0
                        if current_assigned and current_assigned in recurso_ids_tab:
                            assigned_idx = recurso_ids_tab.index(current_assigned)
                        ea_asig_idx = ea_c5.selectbox("Asignado a", range(len(recurso_opciones_tab)), format_func=lambda i: recurso_opciones_tab[i], index=assigned_idx)
                        sla_rpta_keys = list(SLA_RESPUESTA.keys())
                        sla_rpta_vals = list(SLA_RESPUESTA.values())
                        cur_sla_idx = sla_rpta_vals.index(a_ref.get("sla_respuesta_dias", 7)) if a_ref.get("sla_respuesta_dias", 7) in sla_rpta_vals else 1
                        ea_sla_rpta = ea_c6.selectbox("SLA Respuesta", sla_rpta_keys, index=cur_sla_idx)
                        ea_estado = st.selectbox("Estado", ["Pendiente", "Enviada", "Respondida"],
                            index=["Pendiente", "Enviada", "Respondida"].index(a_ref.get("estado", "Pendiente")) if a_ref.get("estado") in ["Pendiente", "Enviada", "Respondida"] else 0)
                        ea_feedback = st.text_area("Feedback", value=a_ref.get("feedback", ""))
                        ea_desc = st.text_area("Descripción", value=a_ref.get("descripcion", ""))
                        if st.form_submit_button("💾 Guardar"):
                            new_assigned = recurso_ids_tab[ea_asig_idx] if ea_asig_idx > 0 else None
                            new_sla_hours = _sla_to_hours(ea_sla)
                            dal.update_activity(a_ref["id"], {
                                "tipo": ea_tipo, "sla_key": ea_sla, "sla_hours": new_sla_hours,
                                "fecha": str(ea_fecha), "objetivo": ea_objetivo,
                                "destinatario": ea_dest, "assigned_to": new_assigned,
                                "sla_respuesta_dias": SLA_RESPUESTA[ea_sla_rpta],
                                "estado": ea_estado, "feedback": ea_feedback,
                                "descripcion": ea_desc,
                            })
                            st.session_state.pop("edit_act_tab_idx", None)
                            st.rerun()
                    if st.button("❌ Cerrar", key=f"close_eab_{row_idx}"):
                        st.session_state.pop("edit_act_tab_idx", None)
                        st.rerun()

    # --- TAB: CONTROL (managers y admins) ---
    if is_manager_or_admin():
        with selected_tabs[2]:
            st.markdown(user_bar_html, unsafe_allow_html=True)
            st.markdown("### 📈 Panel de Control — RSM")

            # Fetch all activities for the team
            ctrl_activities = dal.get_all_activities(team_id)
            today = date.today()
            now = datetime.now()

            # --- Helpers ---
            def _act_date(a):
                """Parse activity date to date object."""
                f = a.get("fecha")
                if isinstance(f, date):
                    return f
                return _parse_date(f) or today

            def _completed_ts(a):
                """Get the timestamp when activity was marked Respondida (updated_at)."""
                ts = a.get("updated_at") or a.get("created_at")
                if isinstance(ts, str):
                    try:
                        return datetime.fromisoformat(ts).date()
                    except Exception:
                        return None
                if isinstance(ts, datetime):
                    return ts.date()
                return None

            # Classify activities
            pendientes = [a for a in ctrl_activities if a.get("estado") == "Pendiente"]
            enviadas = [a for a in ctrl_activities if a.get("estado") == "Enviada"]
            respondidas = [a for a in ctrl_activities if a.get("estado") == "Respondida"]
            bloqueadas = [a for a in ctrl_activities if a.get("estado") == "Enviada" and _traffic_light(a)[1] == "Bloqueada"]

            # --- Section 1: Overview Metrics ---
            st.markdown("#### Resumen General")
            ov1, ov2, ov3, ov4 = st.columns(4)
            ov1.metric("Total Actividades", len(ctrl_activities))
            ov2.metric("Pendientes", len(pendientes))
            ov3.metric("Enviadas (Esp. rpta)", len(enviadas))
            ov4.metric("Respondidas", len(respondidas))

            if bloqueadas:
                st.error(f"🟥 **{len(bloqueadas)} actividades BLOQUEADAS** — respuesta vencida")

            st.divider()

            # --- Section 2: Activity by Day ---
            st.markdown("#### Actividad por Día")

            # Group activities by fecha for recent days
            day_range = [today - timedelta(days=i) for i in range(7)]
            day_labels = []
            day_created = []
            day_completed = []
            day_enviadas = []

            for d in reversed(day_range):
                day_labels.append(d.strftime("%a %d/%m"))
                day_created.append(len([a for a in ctrl_activities if _act_date(a) == d]))
                day_completed.append(len([a for a in respondidas if _completed_ts(a) == d]))
                day_enviadas.append(len([a for a in enviadas if _act_date(a) == d]))

            df_daily = pd.DataFrame({
                "Día": day_labels,
                "Programadas": day_created,
                "Enviadas": day_enviadas,
                "Respondidas": day_completed,
            })
            st.bar_chart(df_daily.set_index("Día"), color=["#f59e0b", "#8b5cf6", "#16a34a"])

            # Day metrics
            acts_today = [a for a in ctrl_activities if _act_date(a) == today]
            acts_yesterday = [a for a in ctrl_activities if _act_date(a) == today - timedelta(days=1)]
            d1, d2, d3, d4 = st.columns(4)
            d1.metric("Hoy — Programadas", len(acts_today))
            d2.metric("Hoy — Respondidas", len([a for a in respondidas if _completed_ts(a) == today]))
            d3.metric("Ayer — Programadas", len(acts_yesterday))
            d4.metric("Ayer — Respondidas", len([a for a in respondidas if _completed_ts(a) == today - timedelta(days=1)]))

            st.divider()

            # --- Section 3: Weekly Summary ---
            st.markdown("#### Resumen Semanal")

            # Current week (Mon-Sun)
            week_start = today - timedelta(days=today.weekday())
            last_week_start = week_start - timedelta(days=7)

            this_week = [a for a in ctrl_activities if week_start <= _act_date(a) <= today]
            last_week = [a for a in ctrl_activities if last_week_start <= _act_date(a) < week_start]
            this_week_resp = [a for a in respondidas if _completed_ts(a) and week_start <= _completed_ts(a) <= today]
            last_week_resp = [a for a in respondidas if _completed_ts(a) and last_week_start <= _completed_ts(a) < week_start]

            w1, w2, w3, w4 = st.columns(4)
            w1.metric("Esta semana — Programadas", len(this_week),
                       delta=f"{len(this_week) - len(last_week):+d} vs semana anterior")
            w2.metric("Esta semana — Respondidas", len(this_week_resp),
                       delta=f"{len(this_week_resp) - len(last_week_resp):+d} vs semana anterior")
            w3.metric("Semana anterior — Programadas", len(last_week))
            w4.metric("Semana anterior — Respondidas", len(last_week_resp))

            # Completion rate
            if this_week:
                this_rate = len(this_week_resp) / len(this_week) * 100
                st.progress(min(this_rate / 100, 1.0), text=f"Tasa de cierre esta semana: **{this_rate:.0f}%** ({len(this_week_resp)}/{len(this_week)})")

            st.divider()

            # --- Section 4: Upcoming Schedule ---
            st.markdown("#### Próximas Actividades Programadas")

            upcoming_7 = [a for a in pendientes if today < _act_date(a) <= today + timedelta(days=7)]
            upcoming_14 = [a for a in pendientes if today < _act_date(a) <= today + timedelta(days=14)]
            upcoming_30 = [a for a in pendientes if today < _act_date(a) <= today + timedelta(days=30)]
            overdue = [a for a in pendientes if _act_date(a) < today]

            u1, u2, u3, u4 = st.columns(4)
            u1.metric("Próx. 7 días", len(upcoming_7))
            u2.metric("Próx. 14 días", len(upcoming_14))
            u3.metric("Próx. 30 días", len(upcoming_30))
            u4.metric("⚠️ Vencidas (sin enviar)", len(overdue), delta=f"-{len(overdue)}" if overdue else "0", delta_color="inverse")

            st.divider()

            # --- Section 5: Team Member Breakdown ---
            st.markdown("#### Rendimiento por Miembro")

            member_stats = {}
            for m in team_members:
                mid = m["id"]
                mname = m["full_name"]
                m_acts = [a for a in ctrl_activities if a.get("assigned_to") == mid or a.get("created_by") == mid]
                m_pend = len([a for a in m_acts if a.get("estado") == "Pendiente"])
                m_env = len([a for a in m_acts if a.get("estado") == "Enviada"])
                m_resp = len([a for a in m_acts if a.get("estado") == "Respondida"])
                m_bloq = len([a for a in m_acts if a.get("estado") == "Enviada" and _traffic_light(a)[1] == "Bloqueada"])
                m_overdue = len([a for a in m_acts if a.get("estado") == "Pendiente" and _act_date(a) < today])
                m_upcoming = len([a for a in m_acts if a.get("estado") == "Pendiente" and today <= _act_date(a) <= today + timedelta(days=7)])
                total = len(m_acts)
                rate = (m_resp / total * 100) if total > 0 else 0
                member_stats[mname] = {
                    "Total": total,
                    "Pendientes": m_pend,
                    "Enviadas": m_env,
                    "Respondidas": m_resp,
                    "Bloqueadas": m_bloq,
                    "Vencidas": m_overdue,
                    "Próx. 7d": m_upcoming,
                    "% Cierre": f"{rate:.0f}%",
                }

            if member_stats:
                df_members = pd.DataFrame(member_stats).T
                df_members.index.name = "Miembro"
                st.dataframe(df_members, use_container_width=True)

                # Bar chart: respondidas by member
                resp_by_member = {name: stats["Respondidas"] for name, stats in member_stats.items() if stats["Total"] > 0}
                if resp_by_member:
                    st.markdown("##### Actividades Respondidas por Miembro")
                    df_resp_chart = pd.DataFrame({"Miembro": list(resp_by_member.keys()), "Respondidas": list(resp_by_member.values())})
                    st.bar_chart(df_resp_chart.set_index("Miembro"), color=["#16a34a"])

    # --- TAB: EQUIPO (todos los roles) ---
    equipo_tab_idx = 3 if is_manager_or_admin() else 2
    with selected_tabs[equipo_tab_idx]:
        st.markdown(user_bar_html, unsafe_allow_html=True)
        team_info = dal.get_team(team_id)

        # Sub-tabs según rol
        if is_admin():
            equipo_subtabs = st.tabs(["👥 Miembros", "⚙️ Configuración", "📨 Invitaciones"])
        elif is_manager_or_admin():  # manager
            equipo_subtabs = st.tabs(["👥 Miembros", "📨 Invitaciones"])
        else:  # presales
            equipo_subtabs = st.tabs(["👥 Miembros", "📨 Invitaciones"])

        # --- MIEMBROS ---
        with equipo_subtabs[0]:
            st.subheader("Miembros del Equipo")
            members = dal.get_team_members(team_id, active_only=False)

            if team_info:
                st.caption(f"Equipo: **{team_info['name']}** — ID: `{team_id}`")

            if is_manager_or_admin():
                # Admin y Manager: edición completa
                for m in members:
                    with st.expander(f"{'🟢' if m['active'] else '🔴'} {m['full_name']} — {m['role']} {'(' + m['specialty'] + ')' if m.get('specialty') else ''}"):
                        with st.form(f"edit_member_{m['id']}"):
                            mc1, mc2 = st.columns(2)
                            m_name = mc1.text_input("Nombre", value=m["full_name"], key=f"mn_{m['id']}")
                            m_email = mc2.text_input("Email", value=m["email"], key=f"me_{m['id']}")
                            mc3, mc4, mc5 = st.columns(3)
                            m_role = mc3.selectbox("Rol", ["admin", "manager", "presales"],
                                index=["admin", "manager", "presales"].index(m["role"]) if m["role"] in ["admin", "manager", "presales"] else 2,
                                key=f"mr_{m['id']}")
                            m_specialty = mc4.text_input("Especialidad", value=m.get("specialty", ""), key=f"ms_{m['id']}")
                            m_phone = mc5.text_input("Teléfono", value=m.get("phone", ""), key=f"mp_{m['id']}")
                            m_active = st.checkbox("Activo", value=m["active"], key=f"ma_{m['id']}")
                            if st.form_submit_button("💾 Guardar"):
                                dal.update_team_member(m["id"], {
                                    "full_name": m_name, "role": m_role,
                                    "specialty": m_specialty, "phone": m_phone,
                                    "active": m_active,
                                })
                                st.success("Miembro actualizado.")
                                st.rerun()
            else:
                # Presales: vista de solo lectura
                active_members = [m for m in members if m["active"]]
                for m in active_members:
                    role_emoji = {"admin": "🔑", "manager": "📊", "presales": "💼"}.get(m["role"], "👤")
                    specialty_txt = f" · {m['specialty']}" if m.get("specialty") else ""
                    st.markdown(f"{role_emoji} **{m['full_name']}** — {m['role']}{specialty_txt}")

        # --- CONFIGURACIÓN (solo admin) ---
        if is_admin():
            with equipo_subtabs[1]:
                st.subheader("Configuración del Equipo")

                # SLA Opciones
                st.write("**Opciones de SLA**")
                sla_config = dal.get_sla_options(team_id)
                sla_json = st.text_area("SLA (JSON)", value=json.dumps(sla_config, ensure_ascii=False, indent=2), height=200, key="sla_config_edit")
                if st.button("Guardar SLA", key="save_sla"):
                    try:
                        parsed = json.loads(sla_json)
                        dal.set_team_config(team_id, "sla_opciones", parsed)
                        st.success("SLA actualizado.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"JSON inválido: {e}")

                st.divider()

                # SLA Respuesta
                st.write("**SLA de Respuesta**")
                sla_rpta_config = dal.get_sla_respuesta(team_id)
                sla_rpta_json = st.text_area("SLA Respuesta (JSON)", value=json.dumps(sla_rpta_config, ensure_ascii=False, indent=2), height=150, key="sla_rpta_config_edit")
                if st.button("Guardar SLA Respuesta", key="save_sla_rpta"):
                    try:
                        parsed = json.loads(sla_rpta_json)
                        dal.set_team_config(team_id, "sla_respuesta", parsed)
                        st.success("SLA Respuesta actualizado.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"JSON inválido: {e}")

                st.divider()

                # Categorías
                st.write("**Categorías**")
                cats_config = dal.get_categorias(team_id)
                cats_json = st.text_area("Categorías (JSON array)", value=json.dumps(cats_config, ensure_ascii=False, indent=2), height=100, key="cats_config_edit")
                if st.button("Guardar Categorías", key="save_cats"):
                    try:
                        parsed = json.loads(cats_json)
                        if isinstance(parsed, list):
                            dal.set_team_config(team_id, "categorias", parsed)
                            st.success("Categorías actualizadas.")
                            st.rerun()
                        else:
                            st.error("Debe ser un array JSON.")
                    except Exception as e:
                        st.error(f"JSON inválido: {e}")

        # --- INVITACIONES ---
        inv_subtab_idx = 2 if is_admin() else 1
        with equipo_subtabs[inv_subtab_idx]:
            st.subheader("Invitar Miembros")

            app_url = st.secrets.get("APP_URL", "https://your-app.streamlit.app")
            team_name = team_info['name'] if team_info else 'Equipo'

            if not is_manager_or_admin():
                st.info("Puedes invitar a otros miembros presales a unirse al equipo.")

            st.markdown(f"""
**Pasos para invitar a un nuevo miembro:**
1. Comparte el siguiente enlace y datos con el invitado
2. El invitado abre el enlace, selecciona **"Unirse a Equipo"** y se registra con el ID de equipo
""")
            inv_c1, inv_c2 = st.columns(2)
            inv_c1.text_input("Enlace de la app", value=app_url, disabled=True, key="invite_url")
            inv_c2.text_input("ID de equipo", value=team_id, disabled=True, key="invite_tid")

            st.divider()

            # SendGrid email (optional) — real keys are 69+ chars like SG.xxx.yyy
            sg_key = st.secrets.get("SENDGRID_API_KEY", "")
            sg_configured = sg_key and len(sg_key) > 50 and sg_key.startswith("SG.")

            with st.expander("📨 Enviar invitación por email (opcional)"):
                if not sg_configured:
                    st.warning("SendGrid no está configurado. Para habilitar invitaciones por email, crea una cuenta gratuita en [sendgrid.com](https://sendgrid.com) y agrega tu API key en los secrets de la app.")
                else:
                    with st.form("invite_form"):
                        inv_email = st.text_input("Email del invitado")
                        inv_name = st.text_input("Nombre (opcional)")
                        if st.form_submit_button("📨 Enviar Invitación"):
                            if inv_email:
                                from sendgrid import SendGridAPIClient
                                from sendgrid.helpers.mail import Mail, Email, To, Content
                                try:
                                    sg = SendGridAPIClient(api_key=sg_key)
                                    message = Mail(
                                        from_email=Email(st.secrets.get("SENDGRID_FROM_EMAIL", "noreply@pgmachine.com"), st.secrets.get("SENDGRID_FROM_NAME", "PG Machine")),
                                        to_emails=To(inv_email),
                                        subject=f"Invitación a PG Machine — {team_name}",
                                        html_content=Content("text/html", f'<div style="font-family:Inter,sans-serif;max-width:500px;margin:0 auto;"><div style="background:#1e293b;color:white;padding:20px;border-radius:8px 8px 0 0;text-align:center;"><h2>Invitación a PG Machine</h2></div><div style="background:white;padding:20px;border:1px solid #e2e8f0;border-radius:0 0 8px 8px;"><p>Hola{" " + inv_name if inv_name else ""},</p><p>Te han invitado a unirte al equipo <b>{team_name}</b> en PG Machine.</p><p>Para registrarte, abre la app y selecciona "Unirse a Equipo":</p><p><b>ID del equipo:</b> <code>{team_id}</code></p><div style="text-align:center;margin:20px 0;"><a href="{app_url}" style="background:#1a73e8;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600;">Ir a PG Machine</a></div></div></div>')
                                    )
                                    sg.send(message)
                                    st.success(f"Invitación enviada a {inv_email}")
                                except Exception as e:
                                    st.error(f"Error enviando email: {e}")
                            else:
                                st.error("Ingresa un email.")
