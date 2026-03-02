"""
Internationalization helpers for PG Machine.
Provides t() translation function, language toggle HTML generators,
estado/tipo display↔DB mappers, and auto_translate for user-generated content.
"""
import streamlit as st
from deep_translator import GoogleTranslator
from lib.translations import TRANSLATIONS


# --- Language state helpers ---

def get_lang() -> str:
    """Return current language code ('es' or 'en')."""
    return st.session_state.get("app_lang", "es")


def set_lang(lang: str):
    """Set current language."""
    st.session_state["app_lang"] = lang


# --- Translation function ---

def t(key: str, **kwargs) -> str:
    """Translate key with fallback chain: current lang → es → raw key.
    Supports {placeholder} formatting via kwargs."""
    lang = get_lang()
    text = TRANSLATIONS.get(lang, {}).get(key) or TRANSLATIONS["es"].get(key, key)
    return text.format(**kwargs) if kwargs else text


# --- Estado display ↔ DB mappers ---
# DB values: "Pendiente", "Enviada", "Respondida" (always Spanish)
# Display values depend on current language

_ESTADO_DB_TO_KEY = {
    "Pendiente": "estado.pendiente",
    "Enviada": "estado.enviada",
    "Respondida": "estado.respondida",
}

_ESTADO_KEY_TO_DB = {
    "estado.pendiente": "Pendiente",
    "estado.enviada": "Enviada",
    "estado.respondida": "Respondida",
}


def display_estado(db_val: str) -> str:
    """Convert DB estado value to display string in current language.
    e.g. 'Pendiente' → 'Pending' (in EN)"""
    key = _ESTADO_DB_TO_KEY.get(db_val)
    if key:
        return t(key)
    return db_val


def db_estado(display_val: str) -> str:
    """Convert display estado back to DB value.
    e.g. 'Pending' → 'Pendiente'"""
    lang = get_lang()
    for key, db in _ESTADO_KEY_TO_DB.items():
        translated = TRANSLATIONS.get(lang, {}).get(key, "")
        if translated == display_val:
            return db
    # Fallback: check Spanish
    for key, db in _ESTADO_KEY_TO_DB.items():
        if TRANSLATIONS["es"].get(key) == display_val:
            return db
    return display_val


def estado_selectbox_options() -> list[str]:
    """Return translated estado options for selectboxes."""
    return [t("estado.pendiente"), t("estado.enviada"), t("estado.respondida")]


# --- Tipo display ↔ DB mappers ---
# DB values: "Email", "Llamada", "Reunión", "Asignación" (always Spanish)

_TIPO_DB_TO_KEY = {
    "Email": "tipo.email",
    "Llamada": "tipo.llamada",
    "Reunión": "tipo.reunion",
    "Asignación": "tipo.asignacion",
}

_TIPO_KEY_TO_DB = {v: k for k, v in _TIPO_DB_TO_KEY.items()}


def display_tipo(db_val: str) -> str:
    """Convert DB tipo value to display string in current language.
    e.g. 'Llamada' → 'Call' (in EN)"""
    key = _TIPO_DB_TO_KEY.get(db_val)
    if key:
        return t(key)
    return db_val


def db_tipo(display_val: str) -> str:
    """Convert display tipo back to DB value.
    e.g. 'Call' → 'Llamada'"""
    lang = get_lang()
    for key, db in _TIPO_KEY_TO_DB.items():
        translated = TRANSLATIONS.get(lang, {}).get(key, "")
        if translated == display_val:
            return db
    # Fallback: check Spanish
    for key, db in _TIPO_KEY_TO_DB.items():
        if TRANSLATIONS["es"].get(key) == display_val:
            return db
    return display_val


def tipo_selectbox_options() -> list[str]:
    """Return translated tipo options for selectboxes."""
    return [t("tipo.email"), t("tipo.llamada"), t("tipo.reunion"), t("tipo.asignacion")]


def tipo_selectbox_index(db_val: str) -> int:
    """Return the index of db_val in tipo selectbox options."""
    db_list = ["Email", "Llamada", "Reunión", "Asignación"]
    return db_list.index(db_val) if db_val in db_list else 0


def estado_selectbox_index(db_val: str) -> int:
    """Return the index of db_val in estado selectbox options."""
    db_list = ["Pendiente", "Enviada", "Respondida"]
    return db_list.index(db_val) if db_val in db_list else 0


# --- Notification translation (no session state — uses explicit lang) ---

def _notif_t(key: str, lang: str = "es", **kwargs) -> str:
    """Translate for notifications using explicit language (not session state).
    Used in email templates where recipient's language may differ."""
    text = TRANSLATIONS.get(lang, {}).get(key) or TRANSLATIONS["es"].get(key, key)
    return text.format(**kwargs) if kwargs else text


# --- Toggle HTML generators ---

def lang_toggle_html() -> str:
    """Generate language toggle HTML for the user bar (light text on dark background).
    Reuses the scope-toggle CSS pattern."""
    lang = get_lang()
    is_en = lang == "en"
    cls = "lang-en" if is_en else ""
    sp_active = "" if is_en else "active"
    en_active = "active" if is_en else ""
    return (
        f'<span class="scope-toggle pgm-toggle-lang {cls}">'
        f'<span class="scope-label {sp_active}">SP</span>'
        f'<span class="scope-track"><span class="scope-knob"></span></span>'
        f'<span class="scope-label {en_active}">EN</span>'
        f'</span>'
    )


def auth_lang_toggle_html() -> str:
    """Generate language toggle HTML for the auth page (dark text on light background)."""
    lang = get_lang()
    is_en = lang == "en"
    sp_active = "" if is_en else "font-weight:700;color:#1e293b;"
    en_active = "font-weight:700;color:#1e293b;" if is_en else ""
    sp_inactive = "color:#94a3b8;" if is_en else ""
    en_inactive = "" if is_en else "color:#94a3b8;"
    knob_transform = "transform:translateX(14px);" if is_en else ""
    track_bg = "background:#0ea5e9;" if is_en else "background:#cbd5e1;"
    return (
        f'<div style="display:flex;justify-content:center;margin-bottom:1rem;">'
        f'<span class="pgm-toggle-lang" style="display:inline-flex;align-items:center;gap:6px;cursor:pointer;user-select:none;font-size:0.75rem;font-weight:600;">'
        f'<span style="{sp_inactive}{sp_active}">SP</span>'
        f'<span style="width:28px;height:14px;{track_bg}border-radius:7px;position:relative;transition:background 0.2s;">'
        f'<span style="position:absolute;top:2px;left:2px;width:10px;height:10px;background:white;border-radius:50%;transition:transform 0.2s;{knob_transform}"></span>'
        f'</span>'
        f'<span style="{en_inactive}{en_active}">EN</span>'
        f'</span>'
        f'</div>'
    )


# --- Auto-translate user-generated content ---

@st.cache_data(ttl=3600, max_entries=500)
def _cached_translate(text: str, target: str) -> str:
    """Translate text to target language. Cached for 1 hour."""
    try:
        return GoogleTranslator(source="auto", target=target).translate(text)
    except Exception:
        return text  # fail silently, show original


def auto_translate(text: str, target_lang: str = None) -> str:
    """Translate user content if viewer's language differs.
    Returns original text if empty, too short, or same language."""
    if not text or len(text.strip()) < 3:
        return text
    target = target_lang or get_lang()
    if target == "es":
        return text  # content is already in Spanish (default)
    return _cached_translate(text, target)


def _at(text: str) -> str:
    """Auto-translate and wrap with indicator if translated."""
    if not text or get_lang() == "es":
        return text
    translated = auto_translate(text)
    if translated != text:
        return f'<span class="auto-translated">{translated}</span>'
    return text
