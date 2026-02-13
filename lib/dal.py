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
    """Crea una nueva oportunidad."""
    sb = get_supabase()
    record = {
        "team_id": team_id,
        "owner_id": owner_id,
        "proyecto": data["proyecto"],
        "cuenta": data["cuenta"],
        "monto": float(data.get("monto", 0)),
        "categoria": data.get("categoria", "LEADS"),
        "opp_id": data.get("opp_id", ""),
        "stage": data.get("stage", ""),
        "close_date": data.get("close_date"),
    }
    resp = sb.table("opportunities").insert(record).execute()
    return resp.data[0] if resp.data else {}

def update_opportunity(opp_id: str, data: dict) -> dict:
    """Actualiza una oportunidad existente."""
    sb = get_supabase()
    resp = sb.table("opportunities") \
        .update(data) \
        .eq("id", opp_id) \
        .execute()
    return resp.data[0] if resp.data else {}

def delete_opportunity(opp_id: str):
    """Elimina una oportunidad."""
    sb = get_supabase()
    sb.table("opportunities").delete().eq("id", opp_id).execute()

def bulk_create_opportunities(team_id: str, owner_id: str, items: list[dict]) -> int:
    """Importación masiva de oportunidades. Retorna cantidad creada."""
    sb = get_supabase()
    records = []
    for data in items:
        records.append({
            "team_id": team_id,
            "owner_id": owner_id,
            "proyecto": data["proyecto"],
            "cuenta": data["cuenta"],
            "monto": float(data.get("monto", 0)),
            "categoria": data.get("categoria", "LEADS"),
            "opp_id": data.get("opp_id", ""),
            "stage": data.get("stage", ""),
            "close_date": data.get("close_date"),
        })
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
        .select("*, assigned_profile:assigned_to(full_name, specialty)") \
        .eq("opportunity_id", opp_id) \
        .order("created_at", desc=True) \
        .execute()
    return resp.data or []

def get_all_activities(team_id: str) -> list[dict]:
    """Obtiene todas las actividades del equipo con datos de oportunidad."""
    sb = get_supabase()
    resp = sb.table("activities") \
        .select("*, opportunity:opportunity_id(proyecto, cuenta, monto, categoria), assigned_profile:assigned_to(full_name, specialty)") \
        .eq("team_id", team_id) \
        .order("fecha", desc=True) \
        .execute()
    return resp.data or []

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

def get_team(team_id: str) -> dict | None:
    """Obtiene info del equipo."""
    sb = get_supabase()
    resp = sb.table("teams") \
        .select("*") \
        .eq("id", team_id) \
        .maybe_single() \
        .execute()
    return resp.data
