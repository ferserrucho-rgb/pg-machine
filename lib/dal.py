"""
Data Access Layer para PG Machine.
Todas las operaciones CRUD contra Neon PostgreSQL via psycopg2.
"""
import streamlit as st
from datetime import datetime, timedelta
import secrets as py_secrets
from lib import db


# ============================================================
# OPPORTUNITIES
# ============================================================

def _ensure_new_cols(rows: list[dict]) -> list[dict]:
    """Ensure new columns exist in each row."""
    for r in rows:
        r.setdefault("urgency", None)
        r.setdefault("gtm_type", None)
        r.setdefault("killed_at", None)
        r.setdefault("kill_reason", None)
    return rows


def get_opportunities(team_id: str, include_killed: bool = False) -> list[dict]:
    """Obtiene oportunidades del equipo (por defecto solo activas)."""
    if include_killed:
        rows = db.fetch_all(
            "SELECT * FROM opportunities WHERE team_id = %s ORDER BY monto DESC",
            (team_id,),
        )
    else:
        rows = db.fetch_all(
            "SELECT * FROM opportunities WHERE team_id = %s AND killed_at IS NULL ORDER BY monto DESC",
            (team_id,),
        )
    return _ensure_new_cols(rows)


def get_opportunities_for_user(team_id: str, user_id: str, role: str, include_killed: bool = False) -> list[dict]:
    """Obtiene oportunidades según el rol del usuario."""
    if role in ("admin", "vp"):
        return get_opportunities(team_id, include_killed=include_killed)

    # Own opportunities
    killed_clause = "" if include_killed else "AND killed_at IS NULL"
    own = db.fetch_all(
        f"SELECT * FROM opportunities WHERE team_id = %s AND owner_id = %s {killed_clause} ORDER BY monto DESC",
        (team_id, user_id),
    )
    own_ids = {o["id"] for o in own}

    # Opportunities with activities assigned to user
    assigned = db.fetch_all(
        "SELECT DISTINCT opportunity_id FROM activities WHERE team_id = %s AND assigned_to = %s",
        (team_id, user_id),
    )
    extra_ids = [a["opportunity_id"] for a in assigned if a["opportunity_id"] not in own_ids]

    extra = []
    if extra_ids:
        placeholders = ",".join(["%s"] * len(extra_ids))
        extra = db.fetch_all(
            f"SELECT * FROM opportunities WHERE id IN ({placeholders}) {killed_clause} ORDER BY monto DESC",
            tuple(extra_ids),
        )
    return _ensure_new_cols(own + extra)


def get_opportunity_extra_columns(team_id: str) -> list[str]:
    """Descubre columnas dinámicas en opportunities."""
    row = db.fetch_one(
        "SELECT * FROM opportunities WHERE team_id = %s LIMIT 1",
        (team_id,),
    )
    if not row:
        return []
    SYSTEM_COLS = {"id", "team_id", "owner_id", "created_at", "updated_at", "killed_at", "kill_reason", "urgency", "gtm_type"}
    UI_COLS = {"proyecto", "cuenta", "monto", "categoria", "opp_id", "stage", "close_date", "partner"}
    all_cols = set(row.keys())
    return sorted(all_cols - SYSTEM_COLS - UI_COLS)


def get_opportunity(opp_id: str) -> dict | None:
    """Obtiene una oportunidad por ID."""
    row = db.fetch_one("SELECT * FROM opportunities WHERE id = %s", (opp_id,))
    if row:
        _ensure_new_cols([row])
    return row


def create_opportunity(team_id: str, owner_id: str, data: dict) -> dict:
    """Crea una nueva oportunidad."""
    record = {"team_id": team_id, "owner_id": owner_id}
    if "monto" in data:
        data["monto"] = float(data["monto"] or 0)
    record.update(data)

    cols = list(record.keys())
    vals = [record[c] for c in cols]
    col_list = ", ".join(f'"{c}"' for c in cols)
    placeholders = ", ".join(["%s"] * len(cols))
    row = db.execute_returning(
        f'INSERT INTO opportunities ({col_list}) VALUES ({placeholders}) RETURNING *',
        tuple(vals),
    )
    return row or {}


def update_opportunity(opp_id: str, data: dict) -> dict:
    """Actualiza una oportunidad existente."""
    if "monto" in data:
        data["monto"] = float(data["monto"] or 0)
    if not data:
        return {}

    cols = list(data.keys())
    vals = [data[c] for c in cols]
    set_clause = ", ".join(f'"{c}" = %s' for c in cols)
    vals.append(opp_id)
    row = db.execute_returning(
        f"UPDATE opportunities SET {set_clause} WHERE id = %s RETURNING *",
        tuple(vals),
    )
    return row or {}


def delete_opportunity(opp_id: str):
    """Elimina una oportunidad (cascade borra actividades asociadas)."""
    db.execute("DELETE FROM opportunities WHERE id = %s", (opp_id,))


def delete_opportunities_by_account(team_id: str, cuenta: str):
    """Elimina todas las oportunidades de una cuenta."""
    db.execute(
        "DELETE FROM opportunities WHERE team_id = %s AND cuenta = %s",
        (team_id, cuenta),
    )


def kill_opportunity(opp_id: str, kill_reason: str) -> dict:
    """Cierra (kill) una oportunidad con razón."""
    row = db.execute_returning(
        "UPDATE opportunities SET killed_at = %s, kill_reason = %s WHERE id = %s RETURNING *",
        (datetime.now().isoformat(), kill_reason, opp_id),
    )
    return row or {}


def get_killed_opportunities(team_id: str) -> list[dict]:
    """Obtiene oportunidades cerradas del equipo."""
    rows = db.fetch_all(
        "SELECT * FROM opportunities WHERE team_id = %s AND killed_at IS NOT NULL ORDER BY killed_at DESC",
        (team_id,),
    )
    return _ensure_new_cols(rows)


def get_all_opportunities_for_snapshot(team_id: str) -> list[dict]:
    """Obtiene TODAS las oportunidades para computar snapshots."""
    return get_opportunities(team_id, include_killed=True)


# ============================================================
# PIPELINE SNAPSHOTS
# ============================================================

def get_pipeline_snapshot(team_id: str, week_ending: str) -> dict | None:
    """Obtiene un snapshot de pipeline por semana."""
    return db.fetch_one(
        "SELECT * FROM pipeline_snapshots WHERE team_id = %s AND week_ending = %s",
        (team_id, week_ending),
    )


def upsert_pipeline_snapshot(team_id: str, week_ending: str, data: dict) -> dict:
    """Inserta o actualiza un snapshot semanal de pipeline."""
    import json
    row = db.execute_returning(
        """INSERT INTO pipeline_snapshots (team_id, week_ending, snapshot_data, updated_at)
           VALUES (%s, %s, %s, %s)
           ON CONFLICT (team_id, week_ending) DO UPDATE SET
               snapshot_data = EXCLUDED.snapshot_data,
               updated_at = EXCLUDED.updated_at
           RETURNING *""",
        (team_id, week_ending, json.dumps(data), datetime.now().isoformat()),
    )
    return row or {}


def get_pipeline_snapshots(team_id: str, weeks: int = 12) -> list[dict]:
    """Obtiene los últimos N snapshots semanales de pipeline."""
    return db.fetch_all(
        "SELECT * FROM pipeline_snapshots WHERE team_id = %s ORDER BY week_ending DESC LIMIT %s",
        (team_id, weeks),
    )


def bulk_create_opportunities(team_id: str, owner_id: str, items: list[dict]) -> int:
    """Importación masiva de oportunidades."""
    count = 0
    for data in items:
        record = {"team_id": team_id, "owner_id": owner_id}
        if "monto" in data:
            data["monto"] = float(data["monto"] or 0)
        record.update(data)

        cols = list(record.keys())
        vals = [record[c] for c in cols]
        col_list = ", ".join(f'"{c}"' for c in cols)
        placeholders = ", ".join(["%s"] * len(cols))
        db.execute(
            f'INSERT INTO opportunities ({col_list}) VALUES ({placeholders})',
            tuple(vals),
        )
        count += 1
    return count


# ============================================================
# ACTIVITIES
# ============================================================

def _enrich_activities_with_profiles(rows: list[dict]) -> list[dict]:
    """Add nested assigned_profile and creator_profile dicts from joined columns."""
    for r in rows:
        # Build nested dicts from flat joined columns
        if "assigned_full_name" in r:
            r["assigned_profile"] = {
                "full_name": r.pop("assigned_full_name", None),
                "specialty": r.pop("assigned_specialty", None),
            } if r.get("assigned_full_name") else None
        if "creator_full_name" in r:
            r["creator_profile"] = {
                "full_name": r.pop("creator_full_name", None),
            } if r.get("creator_full_name") else None
        if "opp_proyecto" in r:
            r["opportunity"] = {
                "proyecto": r.pop("opp_proyecto", None),
                "cuenta": r.pop("opp_cuenta", None),
                "monto": r.pop("opp_monto", None),
                "categoria": r.pop("opp_categoria", None),
            }
    return rows


def get_activities_for_opportunity(opp_id: str) -> list[dict]:
    """Obtiene actividades de una oportunidad, con profiles."""
    rows = db.fetch_all(
        """SELECT a.*,
                  ap.full_name AS assigned_full_name, ap.specialty AS assigned_specialty,
                  cp.full_name AS creator_full_name
           FROM activities a
           LEFT JOIN profiles ap ON a.assigned_to = ap.id
           LEFT JOIN profiles cp ON a.created_by = cp.id
           WHERE a.opportunity_id = %s
           ORDER BY a.created_at DESC""",
        (opp_id,),
    )
    return _enrich_activities_with_profiles(rows)


def get_all_activities(team_id: str) -> list[dict]:
    """Obtiene todas las actividades del equipo con datos de oportunidad."""
    rows = db.fetch_all(
        """SELECT a.*,
                  o.proyecto AS opp_proyecto, o.cuenta AS opp_cuenta,
                  o.monto AS opp_monto, o.categoria AS opp_categoria,
                  ap.full_name AS assigned_full_name, ap.specialty AS assigned_specialty,
                  cp.full_name AS creator_full_name
           FROM activities a
           LEFT JOIN opportunities o ON a.opportunity_id = o.id
           LEFT JOIN profiles ap ON a.assigned_to = ap.id
           LEFT JOIN profiles cp ON a.created_by = cp.id
           WHERE a.team_id = %s
           ORDER BY a.fecha DESC""",
        (team_id,),
    )
    return _enrich_activities_with_profiles(rows)


def get_all_activities_for_user(team_id: str, user_id: str, role: str) -> list[dict]:
    """Obtiene actividades según el rol del usuario."""
    if role in ("admin", "vp"):
        return get_all_activities(team_id)

    # IDs de oportunidades propias
    own_opp_ids = [
        r["id"] for r in db.fetch_all(
            "SELECT id FROM opportunities WHERE team_id = %s AND owner_id = %s",
            (team_id, user_id),
        )
    ]

    # Actividades de oportunidades propias
    own_acts = []
    if own_opp_ids:
        placeholders = ",".join(["%s"] * len(own_opp_ids))
        own_acts = db.fetch_all(
            f"""SELECT a.*,
                       o.proyecto AS opp_proyecto, o.cuenta AS opp_cuenta,
                       o.monto AS opp_monto, o.categoria AS opp_categoria,
                       ap.full_name AS assigned_full_name, ap.specialty AS assigned_specialty,
                       cp.full_name AS creator_full_name
                FROM activities a
                LEFT JOIN opportunities o ON a.opportunity_id = o.id
                LEFT JOIN profiles ap ON a.assigned_to = ap.id
                LEFT JOIN profiles cp ON a.created_by = cp.id
                WHERE a.opportunity_id IN ({placeholders})
                ORDER BY a.fecha DESC""",
            tuple(own_opp_ids),
        )
    own_act_ids = {a["id"] for a in own_acts}

    # Actividades asignadas a o creadas por el usuario
    extra_acts = db.fetch_all(
        """SELECT a.*,
                  o.proyecto AS opp_proyecto, o.cuenta AS opp_cuenta,
                  o.monto AS opp_monto, o.categoria AS opp_categoria,
                  ap.full_name AS assigned_full_name, ap.specialty AS assigned_specialty,
                  cp.full_name AS creator_full_name
           FROM activities a
           LEFT JOIN opportunities o ON a.opportunity_id = o.id
           LEFT JOIN profiles ap ON a.assigned_to = ap.id
           LEFT JOIN profiles cp ON a.created_by = cp.id
           WHERE a.team_id = %s AND (a.assigned_to = %s OR a.created_by = %s)
           ORDER BY a.fecha DESC""",
        (team_id, user_id, user_id),
    )

    # Merge without duplicates
    seen = set(own_act_ids)
    merged_extra = []
    for a in extra_acts:
        if a["id"] not in seen:
            merged_extra.append(a)
            seen.add(a["id"])

    all_acts = own_acts + merged_extra
    return _enrich_activities_with_profiles(all_acts)


def create_activity(opp_id: str, team_id: str, created_by: str, data: dict) -> dict:
    """Crea una nueva actividad."""
    sla_key = data.get("sla_key", "")
    sla_hours = data.get("sla_hours")
    sla_deadline = None
    now = datetime.now()

    if sla_hours:
        sla_deadline = (now + timedelta(hours=sla_hours)).isoformat()

    token = py_secrets.token_urlsafe(32)
    token_expires = (now + timedelta(hours=48)).isoformat()

    row = db.execute_returning(
        """INSERT INTO activities
           (opportunity_id, team_id, created_by, assigned_to, tipo, fecha,
            objetivo, descripcion, estado, sla_key, sla_hours, sla_deadline,
            sla_respuesta_dias, destinatario, response_token, token_expires_at)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'Pendiente',%s,%s,%s,%s,%s,%s,%s)
           RETURNING *""",
        (opp_id, team_id, created_by,
         data.get("assigned_to") or None,
         data["tipo"], data["fecha"],
         data.get("objetivo", ""), data.get("descripcion", ""),
         sla_key, sla_hours, sla_deadline,
         data.get("sla_respuesta_dias", 7),
         data.get("destinatario", ""),
         token, token_expires),
    )
    return row or {}


def update_activity(act_id: str, data: dict) -> dict:
    """Actualiza una actividad existente."""
    # Si se marca como Enviada, calcular response_deadline
    if data.get("estado") == "Enviada" and "enviada_ts" not in data:
        now = datetime.now()
        data["enviada_ts"] = now.isoformat()
        sla_dias = data.get("sla_respuesta_dias", 7)
        if "sla_respuesta_dias" not in data:
            current = db.fetch_one(
                "SELECT sla_respuesta_dias FROM activities WHERE id = %s", (act_id,)
            )
            if current:
                sla_dias = current.get("sla_respuesta_dias", 7)
        data["response_deadline"] = (now + timedelta(days=sla_dias)).isoformat()

    if not data:
        return {}

    cols = list(data.keys())
    vals = [data[c] for c in cols]
    set_clause = ", ".join(f'"{c}" = %s' for c in cols)
    vals.append(act_id)
    row = db.execute_returning(
        f"UPDATE activities SET {set_clause} WHERE id = %s RETURNING *",
        tuple(vals),
    )
    return row or {}


def move_activity(act_id: str, new_opp_id: str) -> dict:
    """Mueve una actividad a otra oportunidad."""
    row = db.execute_returning(
        "UPDATE activities SET opportunity_id = %s WHERE id = %s RETURNING *",
        (new_opp_id, act_id),
    )
    return row or {}


def move_all_activities(from_opp_id: str, to_opp_id: str) -> int:
    """Mueve todas las actividades de una oportunidad a otra."""
    rows = db.execute_returning_all(
        "UPDATE activities SET opportunity_id = %s WHERE opportunity_id = %s RETURNING id",
        (to_opp_id, from_opp_id),
    )
    return len(rows)


def bulk_complete_activities(act_ids: list[str]) -> int:
    """Marca múltiples actividades como Respondida."""
    if not act_ids:
        return 0
    placeholders = ",".join(["%s"] * len(act_ids))
    rows = db.execute_returning_all(
        f"""UPDATE activities SET estado = 'Respondida', respondida_ts = %s
            WHERE id IN ({placeholders}) RETURNING id""",
        (datetime.now().isoformat(), *act_ids),
    )
    return len(rows)


def delete_activity(act_id: str):
    """Elimina una actividad."""
    db.execute("DELETE FROM activities WHERE id = %s", (act_id,))


# ============================================================
# TEAM MEMBERS (PROFILES)
# ============================================================

def get_team_members(team_id: str, active_only: bool = True) -> list[dict]:
    """Obtiene miembros del equipo."""
    if active_only:
        return db.fetch_all(
            "SELECT * FROM profiles WHERE team_id = %s AND active = true ORDER BY full_name",
            (team_id,),
        )
    return db.fetch_all(
        "SELECT * FROM profiles WHERE team_id = %s ORDER BY full_name",
        (team_id,),
    )


def get_team_member(profile_id: str) -> dict | None:
    """Obtiene un perfil por ID."""
    return db.fetch_one("SELECT * FROM profiles WHERE id = %s", (profile_id,))


def update_team_member(profile_id: str, data: dict) -> dict:
    """Actualiza un perfil de miembro del equipo."""
    if not data:
        return {}
    cols = list(data.keys())
    vals = [data[c] for c in cols]
    set_clause = ", ".join(f'"{c}" = %s' for c in cols)
    vals.append(profile_id)
    row = db.execute_returning(
        f"UPDATE profiles SET {set_clause} WHERE id = %s RETURNING *",
        tuple(vals),
    )
    return row or {}


def delete_team_member(profile_id: str):
    """Elimina un miembro del equipo."""
    db.execute("DELETE FROM profiles WHERE id = %s", (profile_id,))


# ============================================================
# TEAM CONFIG
# ============================================================

def get_team_config(team_id: str, key: str) -> dict | list | None:
    """Obtiene un valor de configuración del equipo."""
    row = db.fetch_one(
        "SELECT value FROM team_config WHERE team_id = %s AND key = %s",
        (team_id, key),
    )
    return row["value"] if row else None


def set_team_config(team_id: str, key: str, value) -> None:
    """Establece un valor de configuración del equipo (upsert)."""
    import json
    db.execute(
        """INSERT INTO team_config (team_id, key, value) VALUES (%s, %s, %s)
           ON CONFLICT (team_id, key) DO UPDATE SET value = EXCLUDED.value""",
        (team_id, key, json.dumps(value)),
    )


def get_team_config_bulk(team_id: str, keys: list[str]) -> dict:
    """Obtiene múltiples configs del equipo en una sola consulta."""
    if not keys:
        return {}
    placeholders = ",".join(["%s"] * len(keys))
    rows = db.fetch_all(
        f"SELECT key, value FROM team_config WHERE team_id = %s AND key IN ({placeholders})",
        (team_id, *keys),
    )
    return {r["key"]: r["value"] for r in rows}


def get_sla_options(team_id: str) -> dict:
    """Obtiene opciones de SLA del equipo o las por defecto."""
    config = get_team_config(team_id, "sla_opciones")
    if config:
        return config
    return {
        "\ud83d\udea8 Urgente (2-4h)": {"horas": 4, "color": "#ef4444"},
        "\u26a0\ufe0f Importante (2d)": {"dias": 2, "color": "#f59e0b"},
        "\u2615 No urgente (7d)": {"dias": 7, "color": "#3b82f6"},
    }


def get_sla_respuesta(team_id: str) -> dict:
    """Obtiene opciones de SLA de respuesta del equipo o las por defecto."""
    config = get_team_config(team_id, "sla_respuesta")
    if config:
        return config
    return {
        "3 d\u00edas": 3,
        "1 semana": 7,
        "2 semanas": 14,
        "1 mes": 30,
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
    row = db.execute_returning(
        """INSERT INTO notifications (team_id, activity_id, recipient_id, type)
           VALUES (%s, %s, %s, %s) RETURNING *""",
        (team_id, activity_id, recipient_id, notif_type),
    )
    return row or {}


def get_unsent_notifications() -> list[dict]:
    """Obtiene notificaciones no enviadas (email o WhatsApp) con datos del destinatario y actividad."""
    rows = db.fetch_all(
        """SELECT n.*,
                  p.full_name AS recipient_full_name, p.email AS recipient_email,
                  p.lang AS recipient_lang, p.phone AS recipient_phone,
                  p.whatsapp_apikey AS recipient_whatsapp_apikey,
                  a.tipo AS act_tipo, a.objetivo AS act_objetivo,
                  a.destinatario AS act_destinatario, a.opportunity_id AS act_opp_id
           FROM notifications n
           LEFT JOIN profiles p ON n.recipient_id = p.id
           LEFT JOIN activities a ON n.activity_id = a.id
           WHERE n.sent = false OR n.whatsapp_sent = false
           ORDER BY n.created_at""",
    )
    # Reshape into nested dicts matching PostgREST format
    result = []
    for r in rows:
        notif = {k: v for k, v in r.items() if not k.startswith("recipient_") and not k.startswith("act_")}
        notif["recipient"] = {
            "full_name": r.get("recipient_full_name"),
            "email": r.get("recipient_email"),
            "lang": r.get("recipient_lang", "es"),
            "phone": r.get("recipient_phone"),
            "whatsapp_apikey": r.get("recipient_whatsapp_apikey"),
        }
        notif["activity"] = {
            "tipo": r.get("act_tipo"),
            "objetivo": r.get("act_objetivo"),
            "destinatario": r.get("act_destinatario"),
            "opportunity_id": r.get("act_opp_id"),
        }
        result.append(notif)
    return result


def mark_notification_sent(notif_id: str):
    """Marca notificación como enviada (email)."""
    db.execute(
        "UPDATE notifications SET sent = true, sent_at = %s WHERE id = %s",
        (datetime.now().isoformat(), notif_id),
    )


def mark_notification_whatsapp_sent(notif_id: str):
    """Marca notificación como enviada por WhatsApp."""
    db.execute(
        "UPDATE notifications SET whatsapp_sent = true, whatsapp_sent_at = %s WHERE id = %s",
        (datetime.now().isoformat(), notif_id),
    )


# ============================================================
# TEAM INFO
# ============================================================

def get_team(team_id: str) -> dict | None:
    """Obtiene info del equipo."""
    return db.fetch_one("SELECT * FROM teams WHERE id = %s", (team_id,))


def get_all_teams() -> list[dict]:
    """Obtiene todos los equipos."""
    return db.fetch_all("SELECT * FROM teams ORDER BY name")


def create_team(name: str) -> dict:
    """Crea un nuevo equipo."""
    row = db.execute_returning(
        "INSERT INTO teams (name) VALUES (%s) RETURNING *",
        (name,),
    )
    return row or {}


def update_team(team_id: str, data: dict) -> dict:
    """Actualiza info de un equipo."""
    if not data:
        return {}
    cols = list(data.keys())
    vals = [data[c] for c in cols]
    set_clause = ", ".join(f'"{c}" = %s' for c in cols)
    vals.append(team_id)
    row = db.execute_returning(
        f"UPDATE teams SET {set_clause} WHERE id = %s RETURNING *",
        tuple(vals),
    )
    return row or {}


def delete_team(team_id: str):
    """Elimina un equipo y todos sus datos (cascade)."""
    db.execute("DELETE FROM teams WHERE id = %s", (team_id,))


def get_all_members_for_team(team_id: str) -> list[dict]:
    """Obtiene todos los miembros de un equipo específico."""
    return db.fetch_all(
        "SELECT * FROM profiles WHERE team_id = %s ORDER BY full_name",
        (team_id,),
    )


def move_member_to_team(profile_id: str, new_team_id: str) -> dict:
    """Mueve un miembro a otro equipo."""
    row = db.execute_returning(
        "UPDATE profiles SET team_id = %s WHERE id = %s RETURNING *",
        (new_team_id, profile_id),
    )
    return row or {}


# ============================================================
# CALENDAR INBOX
# ============================================================

def get_pending_calendar_events(team_id: str) -> list[dict]:
    """Obtiene todos los eventos pendientes del equipo."""
    return db.fetch_all(
        "SELECT * FROM calendar_inbox WHERE team_id = %s AND status = 'pending' ORDER BY start_time ASC",
        (team_id,),
    )


def get_pending_calendar_events_for_user(team_id: str, user_id: str, role: str) -> list[dict]:
    """Obtiene eventos pendientes según el rol."""
    if role in ("admin", "vp"):
        return get_pending_calendar_events(team_id)
    return db.fetch_all(
        "SELECT * FROM calendar_inbox WHERE team_id = %s AND profile_id = %s AND status = 'pending' ORDER BY start_time ASC",
        (team_id, user_id),
    )


def get_pending_calendar_count(team_id: str, user_id: str, role: str) -> int:
    """Cuenta eventos pendientes (optimizado para badge)."""
    if role in ("admin", "vp"):
        row = db.fetch_one(
            "SELECT COUNT(*) AS cnt FROM calendar_inbox WHERE team_id = %s AND status = 'pending'",
            (team_id,),
        )
    else:
        row = db.fetch_one(
            "SELECT COUNT(*) AS cnt FROM calendar_inbox WHERE team_id = %s AND profile_id = %s AND status = 'pending'",
            (team_id, user_id),
        )
    return row["cnt"] if row else 0


def assign_calendar_event(inbox_id: str, opp_id: str, activity_id: str, assigned_by: str) -> dict:
    """Marca un evento como asignado y lo vincula a una actividad."""
    row = db.execute_returning(
        """UPDATE calendar_inbox SET
               status = 'assigned',
               assigned_opportunity_id = %s,
               assigned_activity_id = %s,
               assigned_at = %s,
               assigned_by = %s
           WHERE id = %s RETURNING *""",
        (opp_id, activity_id, datetime.now().isoformat(), assigned_by, inbox_id),
    )
    return row or {}


def dismiss_calendar_event(inbox_id: str) -> dict:
    """Marca un evento como descartado."""
    row = db.execute_returning(
        "UPDATE calendar_inbox SET status = 'dismissed' WHERE id = %s RETURNING *",
        (inbox_id,),
    )
    return row or {}


def create_calendar_event(team_id: str, user_id: str, user_email: str, data: dict) -> dict:
    """Crea un evento de calendario manualmente."""
    import json
    row = db.execute_returning(
        """INSERT INTO calendar_inbox
           (team_id, profile_id, user_email, subject, start_time, end_time,
            organizer, attendees, location, body, status)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'pending') RETURNING *""",
        (team_id, user_id, user_email,
         data.get("subject", ""),
         data.get("start_time"),
         data.get("end_time"),
         data.get("organizer", ""),
         json.dumps(data.get("attendees", [])),
         data.get("location", ""),
         data.get("body", "")),
    )
    return row or {}


# ============================================================
# VIAJES (TRIPS)
# ============================================================

def get_viajes(team_id: str) -> list[dict]:
    """Obtiene todos los viajes del equipo."""
    return db.fetch_all(
        "SELECT * FROM viajes WHERE team_id = %s ORDER BY fecha_inicio DESC",
        (team_id,),
    )


def get_viajes_for_user(team_id: str, user_id: str, role: str) -> list[dict]:
    """Obtiene viajes según el rol."""
    if role in ("admin", "vp"):
        return get_viajes(team_id)
    return db.fetch_all(
        "SELECT * FROM viajes WHERE team_id = %s AND created_by = %s ORDER BY fecha_inicio DESC",
        (team_id, user_id),
    )


def get_viaje(viaje_id: str) -> dict | None:
    """Obtiene un viaje por ID."""
    return db.fetch_one("SELECT * FROM viajes WHERE id = %s", (viaje_id,))


def create_viaje(team_id: str, created_by: str, data: dict) -> dict:
    """Crea un nuevo viaje."""
    import json
    row = db.execute_returning(
        """INSERT INTO viajes (team_id, created_by, destino, fecha_inicio, fecha_fin, notas, visitas)
           VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING *""",
        (team_id, created_by,
         data["destino"], data["fecha_inicio"], data["fecha_fin"],
         data.get("notas", ""),
         json.dumps(data.get("visitas", "[]")) if not isinstance(data.get("visitas"), str) else data.get("visitas", "[]")),
    )
    return row or {}


def update_viaje(viaje_id: str, data: dict) -> dict:
    """Actualiza un viaje existente."""
    data["updated_at"] = datetime.now().isoformat()
    cols = list(data.keys())
    vals = [data[c] for c in cols]
    set_clause = ", ".join(f'"{c}" = %s' for c in cols)
    vals.append(viaje_id)
    row = db.execute_returning(
        f"UPDATE viajes SET {set_clause} WHERE id = %s RETURNING *",
        tuple(vals),
    )
    return row or {}


def delete_viaje(viaje_id: str):
    """Elimina un viaje."""
    db.execute("DELETE FROM viajes WHERE id = %s", (viaje_id,))
