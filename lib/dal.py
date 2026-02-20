"""
Data Access Layer para PG Machine.
Todas las operaciones CRUD contra Supabase.
"""
import streamlit as st
from datetime import datetime, timedelta
import secrets as py_secrets
from lib.auth import get_supabase


# ============================================================
# OPPORTUNITIES
# ============================================================

def get_opportunities(team_id: str) -> list[dict]:
    """Obtiene todas las oportunidades del equipo."""
    sb = get_supabase()
    resp = sb.table("opportunities") \
        .select("*") \
        .eq("team_id", team_id) \
        .order("monto", desc=True) \
        .execute()
    return resp.data or []

def get_opportunities_for_user(team_id: str, user_id: str, role: str) -> list[dict]:
    """Obtiene oportunidades según el rol del usuario.
    Admin/VP ven todas; otros ven las que poseen o tienen actividades asignadas."""
    if role in ("admin", "vp"):
        return get_opportunities(team_id)
    sb = get_supabase()
    # Oportunidades propias
    own_resp = sb.table("opportunities") \
        .select("*") \
        .eq("team_id", team_id) \
        .eq("owner_id", user_id) \
        .order("monto", desc=True) \
        .execute()
    own_opps = own_resp.data or []
    own_ids = {o["id"] for o in own_opps}
    # Oportunidades con actividades asignadas al usuario
    act_resp = sb.table("activities") \
        .select("opportunity_id") \
        .eq("team_id", team_id) \
        .eq("assigned_to", user_id) \
        .execute()
    assigned_opp_ids = {a["opportunity_id"] for a in (act_resp.data or [])} - own_ids
    extra_opps = []
    if assigned_opp_ids:
        extra_resp = sb.table("opportunities") \
            .select("*") \
            .in_("id", list(assigned_opp_ids)) \
            .order("monto", desc=True) \
            .execute()
        extra_opps = extra_resp.data or []
    return own_opps + extra_opps


def get_opportunity_extra_columns(team_id: str) -> list[str]:
    """Descubre columnas dinámicas en opportunities (excluye las del sistema y las manejadas por la UI)."""
    sb = get_supabase()
    resp = sb.table("opportunities").select("*").eq("team_id", team_id).limit(1).execute()
    if not resp.data:
        return []
    SYSTEM_COLS = {"id", "team_id", "owner_id", "created_at", "updated_at"}
    UI_COLS = {"proyecto", "cuenta", "monto", "categoria", "opp_id", "stage", "close_date", "partner"}
    all_cols = set(resp.data[0].keys())
    extra = sorted(all_cols - SYSTEM_COLS - UI_COLS)
    return extra

def get_opportunity(opp_id: str) -> dict | None:
    """Obtiene una oportunidad por ID."""
    sb = get_supabase()
    resp = sb.table("opportunities") \
        .select("*") \
        .eq("id", opp_id) \
        .maybe_single() \
        .execute()
    return resp.data

def create_opportunity(team_id: str, owner_id: str, data: dict) -> dict:
    """Crea una nueva oportunidad. Pasa todos los campos de data dinámicamente."""
    sb = get_supabase()
    # Campos internos fijos
    record = {"team_id": team_id, "owner_id": owner_id}
    # Asegurar monto como float
    if "monto" in data:
        data["monto"] = float(data["monto"] or 0)
    # Merge: data sobrescribe si hay conflicto
    record.update(data)
    resp = sb.table("opportunities").insert(record).execute()
    return resp.data[0] if resp.data else {}

def update_opportunity(opp_id: str, data: dict) -> dict:
    """Actualiza una oportunidad existente. Acepta cualquier campo dinámicamente."""
    sb = get_supabase()
    if "monto" in data:
        data["monto"] = float(data["monto"] or 0)
    resp = sb.table("opportunities") \
        .update(data) \
        .eq("id", opp_id) \
        .execute()
    return resp.data[0] if resp.data else {}

def delete_opportunity(opp_id: str):
    """Elimina una oportunidad (cascade borra actividades asociadas)."""
    sb = get_supabase()
    sb.table("opportunities").delete().eq("id", opp_id).execute()

def delete_opportunities_by_account(team_id: str, cuenta: str):
    """Elimina todas las oportunidades de una cuenta."""
    sb = get_supabase()
    sb.table("opportunities").delete().eq("team_id", team_id).eq("cuenta", cuenta).execute()

def bulk_create_opportunities(team_id: str, owner_id: str, items: list[dict]) -> int:
    """Importación masiva de oportunidades. Pasa todos los campos dinámicamente."""
    sb = get_supabase()
    records = []
    for data in items:
        record = {"team_id": team_id, "owner_id": owner_id}
        if "monto" in data:
            data["monto"] = float(data["monto"] or 0)
        record.update(data)
        records.append(record)
    if records:
        sb.table("opportunities").insert(records).execute()
    return len(records)


# ============================================================
# ACTIVITIES
# ============================================================

def get_activities_for_opportunity(opp_id: str) -> list[dict]:
    """Obtiene actividades de una oportunidad, ordenadas por fecha desc."""
    sb = get_supabase()
    resp = sb.table("activities") \
        .select("*, assigned_profile:assigned_to(full_name, specialty), creator_profile:created_by(full_name)") \
        .eq("opportunity_id", opp_id) \
        .order("created_at", desc=True) \
        .execute()
    return resp.data or []

def get_all_activities(team_id: str) -> list[dict]:
    """Obtiene todas las actividades del equipo con datos de oportunidad."""
    sb = get_supabase()
    resp = sb.table("activities") \
        .select("*, opportunity:opportunity_id(proyecto, cuenta, monto, categoria), assigned_profile:assigned_to(full_name, specialty), creator_profile:created_by(full_name)") \
        .eq("team_id", team_id) \
        .order("fecha", desc=True) \
        .execute()
    return resp.data or []

def get_all_activities_for_user(team_id: str, user_id: str, role: str) -> list[dict]:
    """Obtiene actividades según el rol del usuario.
    Admin/VP ven todas; otros ven actividades de oportunidades propias + asignadas/creadas por ellos."""
    if role in ("admin", "vp"):
        return get_all_activities(team_id)
    sb = get_supabase()
    # IDs de oportunidades propias
    own_resp = sb.table("opportunities") \
        .select("id") \
        .eq("team_id", team_id) \
        .eq("owner_id", user_id) \
        .execute()
    own_opp_ids = [o["id"] for o in (own_resp.data or [])]
    # Actividades de oportunidades propias
    own_acts = []
    if own_opp_ids:
        own_acts_resp = sb.table("activities") \
            .select("*, opportunity:opportunity_id(proyecto, cuenta, monto, categoria), assigned_profile:assigned_to(full_name, specialty), creator_profile:created_by(full_name)") \
            .in_("opportunity_id", own_opp_ids) \
            .order("fecha", desc=True) \
            .execute()
        own_acts = own_acts_resp.data or []
    own_act_ids = {a["id"] for a in own_acts}
    # Actividades asignadas a o creadas por el usuario (que no estén ya incluidas)
    assigned_resp = sb.table("activities") \
        .select("*, opportunity:opportunity_id(proyecto, cuenta, monto, categoria), assigned_profile:assigned_to(full_name, specialty), creator_profile:created_by(full_name)") \
        .eq("team_id", team_id) \
        .eq("assigned_to", user_id) \
        .order("fecha", desc=True) \
        .execute()
    created_resp = sb.table("activities") \
        .select("*, opportunity:opportunity_id(proyecto, cuenta, monto, categoria), assigned_profile:assigned_to(full_name, specialty), creator_profile:created_by(full_name)") \
        .eq("team_id", team_id) \
        .eq("created_by", user_id) \
        .order("fecha", desc=True) \
        .execute()
    extra_acts = []
    seen = set(own_act_ids)
    for a in (assigned_resp.data or []) + (created_resp.data or []):
        if a["id"] not in seen:
            extra_acts.append(a)
            seen.add(a["id"])
    return own_acts + extra_acts


def create_activity(opp_id: str, team_id: str, created_by: str, data: dict) -> dict:
    """Crea una nueva actividad."""
    sb = get_supabase()

    # Calcular SLA deadline
    sla_key = data.get("sla_key", "")
    sla_hours = data.get("sla_hours")
    sla_deadline = None
    now = datetime.now()

    if sla_hours:
        sla_deadline = (now + timedelta(hours=sla_hours)).isoformat()

    # Generar response token
    token = py_secrets.token_urlsafe(32)
    token_expires = (now + timedelta(hours=48)).isoformat()

    record = {
        "opportunity_id": opp_id,
        "team_id": team_id,
        "created_by": created_by,
        "assigned_to": data.get("assigned_to") or None,
        "tipo": data["tipo"],
        "fecha": data["fecha"],
        "objetivo": data.get("objetivo", ""),
        "descripcion": data.get("descripcion", ""),
        "estado": "Pendiente",
        "sla_key": sla_key,
        "sla_hours": sla_hours,
        "sla_deadline": sla_deadline,
        "sla_respuesta_dias": data.get("sla_respuesta_dias", 7),
        "destinatario": data.get("destinatario", ""),
        "response_token": token,
        "token_expires_at": token_expires,
    }
    resp = sb.table("activities").insert(record).execute()
    return resp.data[0] if resp.data else {}

def update_activity(act_id: str, data: dict) -> dict:
    """Actualiza una actividad existente."""
    sb = get_supabase()

    # Si se marca como Enviada, calcular response_deadline
    if data.get("estado") == "Enviada" and "enviada_ts" not in data:
        now = datetime.now()
        data["enviada_ts"] = now.isoformat()
        sla_dias = data.get("sla_respuesta_dias", 7)
        # Si no viene sla_respuesta_dias, obtener de la actividad actual
        if "sla_respuesta_dias" not in data:
            current = sb.table("activities").select("sla_respuesta_dias").eq("id", act_id).maybe_single().execute()
            if current.data:
                sla_dias = current.data.get("sla_respuesta_dias", 7)
        data["response_deadline"] = (now + timedelta(days=sla_dias)).isoformat()

    resp = sb.table("activities") \
        .update(data) \
        .eq("id", act_id) \
        .execute()
    return resp.data[0] if resp.data else {}

def delete_activity(act_id: str):
    """Elimina una actividad."""
    sb = get_supabase()
    sb.table("activities").delete().eq("id", act_id).execute()


# ============================================================
# TEAM MEMBERS (PROFILES)
# ============================================================

def get_team_members(team_id: str, active_only: bool = True) -> list[dict]:
    """Obtiene miembros del equipo."""
    sb = get_supabase()
    query = sb.table("profiles") \
        .select("*") \
        .eq("team_id", team_id)
    if active_only:
        query = query.eq("active", True)
    resp = query.order("full_name").execute()
    return resp.data or []

def get_team_member(profile_id: str) -> dict | None:
    """Obtiene un perfil por ID."""
    sb = get_supabase()
    resp = sb.table("profiles") \
        .select("*") \
        .eq("id", profile_id) \
        .maybe_single() \
        .execute()
    return resp.data

def update_team_member(profile_id: str, data: dict) -> dict:
    """Actualiza un perfil de miembro del equipo."""
    sb = get_supabase()
    resp = sb.table("profiles") \
        .update(data) \
        .eq("id", profile_id) \
        .execute()
    return resp.data[0] if resp.data else {}

def delete_team_member(profile_id: str):
    """Elimina un miembro del equipo (perfil + usuario auth)."""
    sb = _get_admin_supabase()
    # Eliminar perfil (cascade borra actividades asignadas, notificaciones, etc.)
    sb.table("profiles").delete().eq("id", profile_id).execute()
    # Eliminar usuario de Supabase Auth
    try:
        sb.auth.admin.delete_user(profile_id)
    except Exception:
        pass


# ============================================================
# TEAM CONFIG
# ============================================================

def get_team_config(team_id: str, key: str) -> dict | list | None:
    """Obtiene un valor de configuración del equipo."""
    sb = get_supabase()
    resp = sb.table("team_config") \
        .select("value") \
        .eq("team_id", team_id) \
        .eq("key", key) \
        .maybe_single() \
        .execute()
    if resp.data:
        return resp.data["value"]
    return None

def set_team_config(team_id: str, key: str, value) -> None:
    """Establece un valor de configuración del equipo (upsert)."""
    sb = get_supabase()
    sb.table("team_config") \
        .upsert({"team_id": team_id, "key": key, "value": value}, on_conflict="team_id,key") \
        .execute()

def get_sla_options(team_id: str) -> dict:
    """Obtiene opciones de SLA del equipo o las por defecto."""
    config = get_team_config(team_id, "sla_opciones")
    if config:
        return config
    return {
        "🚨 Urgente (2-4h)": {"horas": 4, "color": "#ef4444"},
        "⚠️ Importante (2d)": {"dias": 2, "color": "#f59e0b"},
        "☕ No urgente (7d)": {"dias": 7, "color": "#3b82f6"}
    }

def get_sla_respuesta(team_id: str) -> dict:
    """Obtiene opciones de SLA de respuesta del equipo o las por defecto."""
    config = get_team_config(team_id, "sla_respuesta")
    if config:
        return config
    return {
        "3 días": 3,
        "1 semana": 7,
        "2 semanas": 14,
        "1 mes": 30
    }

def get_categorias(team_id: str) -> list[str]:
    """Obtiene categorías del equipo."""
    config = get_team_config(team_id, "categorias")
    if config:
        return config
    return ["LEADS", "OFFICIAL", "GTM"]


# ============================================================
# NOTIFICATIONS
# ============================================================

def create_notification(team_id: str, activity_id: str, recipient_id: str, notif_type: str) -> dict:
    """Crea una notificación."""
    sb = get_supabase()
    resp = sb.table("notifications").insert({
        "team_id": team_id,
        "activity_id": activity_id,
        "recipient_id": recipient_id,
        "type": notif_type,
    }).execute()
    return resp.data[0] if resp.data else {}

def get_unsent_notifications() -> list[dict]:
    """Obtiene notificaciones no enviadas con datos del destinatario."""
    sb = get_supabase()
    resp = sb.table("notifications") \
        .select("*, recipient:recipient_id(full_name, email), activity:activity_id(tipo, objetivo, destinatario, opportunity_id)") \
        .eq("sent", False) \
        .order("created_at") \
        .execute()
    return resp.data or []

def mark_notification_sent(notif_id: str):
    """Marca notificación como enviada."""
    sb = get_supabase()
    sb.table("notifications") \
        .update({"sent": True, "sent_at": datetime.now().isoformat()}) \
        .eq("id", notif_id) \
        .execute()


# ============================================================
# TEAM INFO
# ============================================================

def _get_admin_supabase():
    """Retorna cliente Supabase con service key para bypass de RLS."""
    from supabase import create_client
    try:
        return create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_SERVICE_KEY"]
        )
    except Exception:
        return get_supabase()

def get_team(team_id: str) -> dict | None:
    """Obtiene info del equipo."""
    sb = get_supabase()
    resp = sb.table("teams") \
        .select("*") \
        .eq("id", team_id) \
        .maybe_single() \
        .execute()
    return resp.data

def get_all_teams() -> list[dict]:
    """Obtiene todos los equipos (requiere service key para bypass RLS)."""
    sb = _get_admin_supabase()
    resp = sb.table("teams") \
        .select("*") \
        .order("name") \
        .execute()
    return resp.data or []

def create_team(name: str) -> dict:
    """Crea un nuevo equipo."""
    sb = _get_admin_supabase()
    resp = sb.table("teams").insert({"name": name}).execute()
    return resp.data[0] if resp.data else {}

def update_team(team_id: str, data: dict) -> dict:
    """Actualiza info de un equipo."""
    sb = _get_admin_supabase()
    resp = sb.table("teams") \
        .update(data) \
        .eq("id", team_id) \
        .execute()
    return resp.data[0] if resp.data else {}

def delete_team(team_id: str):
    """Elimina un equipo y todos sus datos (cascade)."""
    sb = _get_admin_supabase()
    sb.table("teams").delete().eq("id", team_id).execute()

def get_all_members_for_team(team_id: str) -> list[dict]:
    """Obtiene todos los miembros de un equipo específico (bypass RLS)."""
    sb = _get_admin_supabase()
    resp = sb.table("profiles") \
        .select("*") \
        .eq("team_id", team_id) \
        .order("full_name") \
        .execute()
    return resp.data or []

def move_member_to_team(profile_id: str, new_team_id: str) -> dict:
    """Mueve un miembro a otro equipo."""
    sb = _get_admin_supabase()
    resp = sb.table("profiles") \
        .update({"team_id": new_team_id}) \
        .eq("id", profile_id) \
        .execute()
    return resp.data[0] if resp.data else {}


# ============================================================
# CALENDAR INBOX
# ============================================================

def get_pending_calendar_events(team_id: str) -> list[dict]:
    """Obtiene todos los eventos pendientes del equipo."""
    sb = get_supabase()
    resp = sb.table("calendar_inbox") \
        .select("*") \
        .eq("team_id", team_id) \
        .eq("status", "pending") \
        .order("start_time", desc=False) \
        .execute()
    return resp.data or []

def get_pending_calendar_events_for_user(team_id: str, user_id: str, role: str) -> list[dict]:
    """Obtiene eventos pendientes según el rol.
    Admin/VP ven todos; otros ven solo los propios."""
    if role in ("admin", "vp"):
        return get_pending_calendar_events(team_id)
    sb = get_supabase()
    resp = sb.table("calendar_inbox") \
        .select("*") \
        .eq("team_id", team_id) \
        .eq("profile_id", user_id) \
        .eq("status", "pending") \
        .order("start_time", desc=False) \
        .execute()
    return resp.data or []

def get_pending_calendar_count(team_id: str, user_id: str, role: str) -> int:
    """Cuenta eventos pendientes (optimizado para badge)."""
    sb = get_supabase()
    query = sb.table("calendar_inbox") \
        .select("id") \
        .eq("team_id", team_id) \
        .eq("status", "pending")
    if role not in ("admin", "vp"):
        query = query.eq("profile_id", user_id)
    resp = query.execute()
    return len(resp.data) if resp.data else 0

def assign_calendar_event(inbox_id: str, opp_id: str, activity_id: str, assigned_by: str) -> dict:
    """Marca un evento como asignado y lo vincula a una actividad."""
    sb = get_supabase()
    resp = sb.table("calendar_inbox") \
        .update({
            "status": "assigned",
            "assigned_opportunity_id": opp_id,
            "assigned_activity_id": activity_id,
            "assigned_at": datetime.now().isoformat(),
            "assigned_by": assigned_by,
        }) \
        .eq("id", inbox_id) \
        .execute()
    return resp.data[0] if resp.data else {}

def dismiss_calendar_event(inbox_id: str) -> dict:
    """Marca un evento como descartado."""
    sb = get_supabase()
    resp = sb.table("calendar_inbox") \
        .update({"status": "dismissed"}) \
        .eq("id", inbox_id) \
        .execute()
    return resp.data[0] if resp.data else {}

def create_calendar_event(team_id: str, user_id: str, user_email: str, data: dict) -> dict:
    """Crea un evento de calendario manualmente."""
    sb = get_supabase()
    record = {
        "team_id": team_id,
        "profile_id": user_id,
        "user_email": user_email,
        "subject": data.get("subject", ""),
        "start_time": data.get("start_time"),
        "end_time": data.get("end_time"),
        "organizer": data.get("organizer", ""),
        "attendees": data.get("attendees", []),
        "location": data.get("location", ""),
        "body": data.get("body", ""),
        "status": "pending",
    }
    resp = sb.table("calendar_inbox").insert(record).execute()
    return resp.data[0] if resp.data else {}
