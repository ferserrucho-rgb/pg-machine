"""
Streamlit page: handles email response tokens.
Replaces the Supabase Edge Function handle-response.
URL: /respond?token=xxx
"""
import streamlit as st
from datetime import datetime
from lib import db

st.set_page_config(page_title="PG Machine — Responder", layout="centered")

token = st.query_params.get("token", "")

if not token:
    st.error("No se proporcionó token de respuesta.")
    st.stop()

# Look up activity by response_token
activity = db.fetch_one(
    "SELECT * FROM activities WHERE response_token = %s",
    (token,),
)

if not activity:
    st.error("Token inválido o actividad no encontrada.")
    st.stop()

# Check token expiration
if activity.get("token_expires_at"):
    expires = activity["token_expires_at"]
    if isinstance(expires, str):
        from datetime import timezone
        expires = datetime.fromisoformat(expires.replace("Z", "+00:00"))
    if expires.tzinfo:
        now = datetime.now(expires.tzinfo)
    else:
        now = datetime.now()
    if now > expires:
        st.error("Este enlace ha expirado. Por favor contacta al equipo.")
        st.stop()

# Check if already responded
if activity.get("estado") == "Respondida":
    st.success("Esta actividad ya fue marcada como respondida. Gracias.")
    st.stop()

# Show activity details
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
</style>
""", unsafe_allow_html=True)

st.title("Responder Actividad")
st.markdown(f"**Tipo:** {activity.get('tipo', '')}")
st.markdown(f"**Objetivo:** {activity.get('objetivo', '')}")
st.markdown(f"**Destinatario:** {activity.get('destinatario', '')}")
st.markdown(f"**Fecha:** {activity.get('fecha', '')}")

st.divider()

with st.form("response_form"):
    feedback = st.text_area("Comentario / Feedback (opcional)", key="feedback")
    submitted = st.form_submit_button("Marcar como Respondida", use_container_width=True)

    if submitted:
        db.execute(
            """UPDATE activities SET
                   estado = 'Respondida',
                   respondida_ts = %s,
                   feedback = %s,
                   response_token = NULL,
                   token_expires_at = NULL
               WHERE id = %s""",
            (datetime.now().isoformat(), feedback, str(activity["id"])),
        )
        st.success("Actividad marcada como respondida. Gracias.")
        st.balloons()
