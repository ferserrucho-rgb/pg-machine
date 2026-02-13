"""
Módulo de notificaciones por email via SendGrid.
"""
import streamlit as st
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from lib import dal


def _get_sendgrid() -> SendGridAPIClient | None:
    """Retorna cliente SendGrid o None si no está configurado."""
    api_key = st.secrets.get("SENDGRID_API_KEY", "")
    if not api_key or api_key.startswith("SG.your"):
        return None
    return SendGridAPIClient(api_key=api_key)

def _from_email() -> Email:
    return Email(
        st.secrets.get("SENDGRID_FROM_EMAIL", "noreply@pgmachine.com"),
        st.secrets.get("SENDGRID_FROM_NAME", "PG Machine")
    )

def _app_url() -> str:
    return st.secrets.get("APP_URL", "https://your-app.streamlit.app")

def _supabase_url() -> str:
    return st.secrets.get("SUPABASE_URL", "")

def send_assignment_notification(activity: dict, assignee: dict, opportunity: dict):
    """
    Envía notificación de asignación a un miembro del equipo.
    activity: dict con datos de la actividad creada
    assignee: dict con datos del perfil asignado (full_name, email)
    opportunity: dict con datos de la oportunidad (proyecto, cuenta)
    """
    sg = _get_sendgrid()
    if not sg:
        return

    response_url = f"{_supabase_url()}/functions/v1/handle-response?token={activity.get('response_token', '')}"

    subject = f"Nueva asignación: {activity.get('tipo', '')} — {opportunity.get('cuenta', '')}"
    html_body = f"""
    <div style="font-family: Inter, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #1e293b; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
            <h2 style="margin: 0;">Nueva Asignación</h2>
        </div>
        <div style="background: white; padding: 20px; border: 1px solid #e2e8f0; border-radius: 0 0 8px 8px;">
            <p>Hola <b>{assignee.get('full_name', '')}</b>,</p>
            <p>Se te ha asignado una nueva actividad:</p>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 8px; color: #64748b;">Cuenta</td><td style="padding: 8px; font-weight: 600;">{opportunity.get('cuenta', '')}</td></tr>
                <tr><td style="padding: 8px; color: #64748b;">Proyecto</td><td style="padding: 8px; font-weight: 600;">{opportunity.get('proyecto', '')}</td></tr>
                <tr><td style="padding: 8px; color: #64748b;">Tipo</td><td style="padding: 8px;">{activity.get('tipo', '')}</td></tr>
                <tr><td style="padding: 8px; color: #64748b;">Objetivo</td><td style="padding: 8px;">{activity.get('objetivo', '')}</td></tr>
                <tr><td style="padding: 8px; color: #64748b;">Destinatario</td><td style="padding: 8px;">{activity.get('destinatario', '')}</td></tr>
                <tr><td style="padding: 8px; color: #64748b;">Fecha</td><td style="padding: 8px;">{activity.get('fecha', '')}</td></tr>
                <tr><td style="padding: 8px; color: #64748b;">SLA</td><td style="padding: 8px;">{activity.get('sla_key', '')}</td></tr>
            </table>
            <p style="margin-top: 16px;">{activity.get('descripcion', '')}</p>
            <div style="margin-top: 20px; text-align: center;">
                <a href="{response_url}" style="background: #1a73e8; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: 600;">
                    Responder desde el celular
                </a>
            </div>
            <p style="margin-top: 20px; font-size: 0.8rem; color: #94a3b8;">
                O ingresa a <a href="{_app_url()}">PG Machine</a> para más detalles.
            </p>
        </div>
    </div>
    """

    message = Mail(
        from_email=_from_email(),
        to_emails=To(assignee.get("email", "")),
        subject=subject,
        html_content=Content("text/html", html_body)
    )
    try:
        sg.send(message)
    except Exception as e:
        st.warning(f"No se pudo enviar email de asignación: {e}")

def send_sla_notification(notification: dict):
    """
    Envía notificación de SLA (warning, expired, blocked).
    notification: dict con datos expandidos (recipient, activity)
    """
    sg = _get_sendgrid()
    if not sg:
        return False

    notif_type = notification.get("type", "")
    recipient = notification.get("recipient", {})
    activity = notification.get("activity", {})

    if not recipient.get("email"):
        return False

    type_labels = {
        "sla_warning": ("Advertencia de SLA", "El SLA de una actividad está por vencer."),
        "sla_expired": ("SLA Vencido", "El SLA de una actividad ha vencido."),
        "blocked": ("Actividad Bloqueada", "Una actividad lleva demasiado tiempo sin respuesta del cliente."),
        "assignment": ("Nueva Asignación", "Se te ha asignado una nueva actividad."),
    }

    title, desc = type_labels.get(notif_type, ("Notificación", "Tienes una notificación pendiente."))

    color_map = {
        "sla_warning": "#f59e0b",
        "sla_expired": "#ef4444",
        "blocked": "#ef4444",
        "assignment": "#1a73e8",
    }
    color = color_map.get(notif_type, "#1e293b")

    subject = f"PG Machine — {title}: {activity.get('tipo', '')} — {activity.get('objetivo', '')}"
    html_body = f"""
    <div style="font-family: Inter, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: {color}; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
            <h2 style="margin: 0;">{title}</h2>
        </div>
        <div style="background: white; padding: 20px; border: 1px solid #e2e8f0; border-radius: 0 0 8px 8px;">
            <p>Hola <b>{recipient.get('full_name', '')}</b>,</p>
            <p>{desc}</p>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 8px; color: #64748b;">Tipo</td><td style="padding: 8px;">{activity.get('tipo', '')}</td></tr>
                <tr><td style="padding: 8px; color: #64748b;">Objetivo</td><td style="padding: 8px;">{activity.get('objetivo', '')}</td></tr>
                <tr><td style="padding: 8px; color: #64748b;">Destinatario</td><td style="padding: 8px;">{activity.get('destinatario', '')}</td></tr>
            </table>
            <div style="margin-top: 20px; text-align: center;">
                <a href="{_app_url()}" style="background: #1e293b; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: 600;">
                    Ver en PG Machine
                </a>
            </div>
        </div>
    </div>
    """

    message = Mail(
        from_email=_from_email(),
        to_emails=To(recipient["email"]),
        subject=subject,
        html_content=Content("text/html", html_body)
    )
    try:
        sg.send(message)
        return True
    except Exception:
        return False

def process_pending_notifications():
    """
    Procesa notificaciones pendientes en la cola.
    Llamado desde la Edge Function o manualmente.
    """
    unsent = dal.get_unsent_notifications()
    sent_count = 0
    for notif in unsent:
        if send_sla_notification(notif):
            dal.mark_notification_sent(notif["id"])
            sent_count += 1
    return sent_count
