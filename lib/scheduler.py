"""
SLA scheduler — replaces pg_cron jobs with on-page-load checks.
Throttled to run at most every 15 minutes per session.
"""
import streamlit as st
from datetime import datetime, timedelta
from lib import db


_THROTTLE_MINUTES = 15


def run_sla_checks():
    """Run SLA checks if not run recently (throttled to every 15 min)."""
    last_run = st.session_state.get("_sla_last_run")
    now = datetime.now()
    if last_run and (now - last_run) < timedelta(minutes=_THROTTLE_MINUTES):
        return
    st.session_state["_sla_last_run"] = now

    try:
        _check_sla_expired()
        _check_blocked()
        _check_sla_warning()
    except Exception:
        pass  # Don't break the app if SLA checks fail


def _check_sla_expired():
    """Insert notification for Pendiente activities past sla_deadline."""
    db.execute(
        """INSERT INTO notifications (team_id, activity_id, recipient_id, type)
           SELECT a.team_id, a.id, COALESCE(a.assigned_to, a.created_by), 'sla_expired'
           FROM activities a
           WHERE a.estado = 'Pendiente'
             AND a.sla_deadline IS NOT NULL
             AND a.sla_deadline < now()
             AND NOT EXISTS (
               SELECT 1 FROM notifications n
               WHERE n.activity_id = a.id AND n.type = 'sla_expired'
             )""",
    )


def _check_blocked():
    """Insert notification for Enviada activities past response_deadline."""
    db.execute(
        """INSERT INTO notifications (team_id, activity_id, recipient_id, type)
           SELECT a.team_id, a.id, a.created_by, 'blocked'
           FROM activities a
           WHERE a.estado = 'Enviada'
             AND a.response_deadline IS NOT NULL
             AND a.response_deadline < now()
             AND NOT EXISTS (
               SELECT 1 FROM notifications n
               WHERE n.activity_id = a.id AND n.type = 'blocked'
             )""",
    )


def _check_sla_warning():
    """Insert notification for activities past 50% of SLA window."""
    db.execute(
        """INSERT INTO notifications (team_id, activity_id, recipient_id, type)
           SELECT a.team_id, a.id, COALESCE(a.assigned_to, a.created_by), 'sla_warning'
           FROM activities a
           WHERE a.estado = 'Pendiente'
             AND a.sla_deadline IS NOT NULL
             AND a.sla_deadline > now()
             AND (a.sla_deadline - now()) < (a.sla_deadline - a.created_at) * 0.5
             AND NOT EXISTS (
               SELECT 1 FROM notifications n
               WHERE n.activity_id = a.id AND n.type = 'sla_warning'
             )""",
    )
