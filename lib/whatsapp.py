"""
Módulo de notificaciones WhatsApp via CallMeBot (gratuito).
Envía mensajes vía HTTP GET a api.callmebot.com/whatsapp.php.
"""
import re
import logging
import urllib.parse

import requests

from lib.i18n import _notif_t

logger = logging.getLogger(__name__)


def _normalize_phone(phone: str) -> str:
    """Normaliza número de teléfono: quita espacios/guiones, asegura prefijo +."""
    if not phone:
        return ""
    phone = re.sub(r"[\s\-\(\)]+", "", phone.strip())
    if not phone.startswith("+"):
        phone = "+" + phone
    return phone


def _can_send_whatsapp(recipient: dict) -> bool:
    """Verifica que el destinatario tenga phone y whatsapp_apikey configurados."""
    phone = (recipient.get("phone") or "").strip()
    apikey = (recipient.get("whatsapp_apikey") or "").strip()
    return bool(phone and apikey)


def _send_callmebot(phone: str, apikey: str, message: str) -> bool:
    """Envía mensaje via CallMeBot WhatsApp API (HTTP GET)."""
    phone = _normalize_phone(phone)
    if not phone or not apikey:
        return False
    encoded_msg = urllib.parse.quote_plus(message)
    url = (
        f"https://api.callmebot.com/whatsapp.php"
        f"?phone={phone}&text={encoded_msg}&apikey={apikey}"
    )
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            return True
        logger.warning("CallMeBot respondió %s: %s", resp.status_code, resp.text[:200])
        return False
    except Exception as e:
        logger.warning("Error enviando WhatsApp via CallMeBot: %s", e)
        return False


def _build_assignment_message(activity: dict, assignee: dict, opportunity: dict) -> str:
    """Construye mensaje de asignación para WhatsApp con formato bold."""
    lang = assignee.get("lang", "es")
    nt = lambda key, **kw: _notif_t(key, lang=lang, **kw)

    lines = [
        f"*{nt('notif.new_assignment')}*",
        "",
        f"{nt('notif.label_account')}: {opportunity.get('cuenta', '')}",
        f"{nt('notif.label_project')}: {opportunity.get('proyecto', '')}",
        f"{nt('notif.label_type')}: {activity.get('tipo', '')}",
        f"{nt('notif.label_objective')}: {activity.get('objetivo', '')}",
        f"{nt('notif.label_recipient')}: {activity.get('destinatario', '')}",
        f"{nt('notif.label_date')}: {activity.get('fecha', '')}",
        f"SLA: {activity.get('sla_key', '')}",
    ]
    desc = activity.get("descripcion", "")
    if desc:
        lines.append(f"\n{desc}")
    return "\n".join(lines)


def _build_sla_message(notification: dict) -> str:
    """Construye mensaje de SLA para WhatsApp con formato bold."""
    notif_type = notification.get("type", "")
    recipient = notification.get("recipient", {})
    activity = notification.get("activity", {})

    lang = recipient.get("lang", "es")
    nt = lambda key, **kw: _notif_t(key, lang=lang, **kw)

    type_labels = {
        "sla_warning": (nt("notif.sla_warning"), nt("notif.sla_warning_desc")),
        "sla_expired": (nt("notif.sla_expired"), nt("notif.sla_expired_desc")),
        "blocked": (nt("notif.blocked"), nt("notif.blocked_desc")),
        "assignment": (nt("notif.assignment_title"), nt("notif.assignment_desc")),
    }
    title, desc = type_labels.get(notif_type, (nt("notif.default_title"), nt("notif.default_desc")))

    lines = [
        f"*PG Machine — {title}*",
        "",
        desc,
        "",
        f"{nt('notif.label_type')}: {activity.get('tipo', '')}",
        f"{nt('notif.label_objective')}: {activity.get('objetivo', '')}",
        f"{nt('notif.label_recipient')}: {activity.get('destinatario', '')}",
    ]
    return "\n".join(lines)


def send_whatsapp_assignment(activity: dict, assignee: dict, opportunity: dict) -> bool:
    """Envía notificación de asignación por WhatsApp. Retorna True si se envió."""
    if not _can_send_whatsapp(assignee):
        return False
    message = _build_assignment_message(activity, assignee, opportunity)
    return _send_callmebot(
        assignee["phone"],
        assignee["whatsapp_apikey"],
        message,
    )


def send_whatsapp_sla(notification: dict) -> bool:
    """Envía notificación de SLA por WhatsApp. Retorna True si se envió."""
    recipient = notification.get("recipient", {})
    if not _can_send_whatsapp(recipient):
        return False
    message = _build_sla_message(notification)
    return _send_callmebot(
        recipient["phone"],
        recipient["whatsapp_apikey"],
        message,
    )
