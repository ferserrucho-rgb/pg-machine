"""
Módulo de autenticación para PG Machine.
Login, registro, gestión de sesión con Supabase Auth.
"""
import streamlit as st
from supabase import create_client, Client

# --- Roles del sistema ---
ALL_ROLES = [
    "admin", "vp", "account_manager", "regional_sales_manager",
    "partner_manager", "regional_partner_manager", "presales_manager", "presales",
]

JOINABLE_ROLES = [r for r in ALL_ROLES if r != "admin"]

ROLE_LABELS = {
    "admin": "Admin",
    "vp": "VP",
    "account_manager": "Account Manager",
    "regional_sales_manager": "Regional Sales Manager",
    "partner_manager": "Partner Manager",
    "regional_partner_manager": "Regional Partner Manager",
    "presales_manager": "Presales Manager",
    "presales": "Presales",
}

def _get_supabase() -> Client:
    """Retorna cliente Supabase singleton."""
    if "supabase_client" not in st.session_state:
        st.session_state.supabase_client = create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_KEY"]
        )
    return st.session_state.supabase_client

def get_supabase() -> Client:
    """Público: retorna el cliente Supabase autenticado."""
    return _get_supabase()

def _try_restore_session():
    """Intenta restaurar sesión desde query_params (sobrevive reruns en Streamlit Cloud)."""
    if st.session_state.get("user"):
        return True
    params = st.query_params
    refresh_token = params.get("_rt")
    access_token = params.get("_at")
    if refresh_token and access_token:
        try:
            sb = _get_supabase()
            resp = sb.auth.set_session(access_token, refresh_token)
            if resp and resp.user:
                _store_session(resp)
                return True
        except Exception:
            # Token expirado o inválido — limpiar
            st.query_params.clear()
    return False

def _store_session(auth_response):
    """Almacena datos de sesión en session_state y query_params."""
    user = auth_response.user
    session = auth_response.session

    # Obtener perfil del usuario
    sb = _get_supabase()
    profile_resp = sb.table("profiles").select("*").eq("id", user.id).maybe_single().execute()
    profile = profile_resp.data if profile_resp.data else {}

    st.session_state.user = {
        "id": user.id,
        "email": user.email,
        "full_name": profile.get("full_name", user.email),
        "team_id": profile.get("team_id"),
        "role": profile.get("role", "presales"),
        "specialty": profile.get("specialty", ""),
    }

    # Persistir tokens en query_params para sobrevivir reruns
    if session:
        st.query_params["_rt"] = session.refresh_token
        st.query_params["_at"] = session.access_token

def logout():
    """Cierra sesión del usuario."""
    try:
        sb = _get_supabase()
        sb.auth.sign_out()
    except Exception:
        pass
    for key in ["user", "supabase_client"]:
        st.session_state.pop(key, None)
    st.query_params.clear()
    st.rerun()

def _do_login(email: str, password: str):
    """Ejecuta login con email/password."""
    sb = _get_supabase()
    try:
        resp = sb.auth.sign_in_with_password({"email": email, "password": password})
        _store_session(resp)
        return None
    except Exception as e:
        msg = str(e)
        if "Invalid login" in msg or "invalid" in msg.lower():
            return "Email o contraseña incorrectos."
        return f"Error de autenticación: {msg}"

def _do_register(email: str, password: str, full_name: str, team_name: str):
    """Registra un nuevo usuario + crea equipo y perfil."""
    sb = _get_supabase()
    try:
        # 1. Registrar en Supabase Auth
        resp = sb.auth.sign_up({"email": email, "password": password})
        if not resp.user:
            return "No se pudo crear la cuenta. Intenta de nuevo."

        user_id = resp.user.id

        # 2. Crear equipo (usa service key si está disponible para bypass RLS)
        try:
            admin_sb = create_client(
                st.secrets["SUPABASE_URL"],
                st.secrets["SUPABASE_SERVICE_KEY"]
            )
        except Exception:
            admin_sb = sb

        team_resp = admin_sb.table("teams").insert({"name": team_name}).execute()
        team_id = team_resp.data[0]["id"]

        # 3. Crear perfil
        admin_sb.table("profiles").insert({
            "id": user_id,
            "team_id": team_id,
            "full_name": full_name,
            "email": email,
            "role": "admin",  # Primer usuario del equipo es admin
        }).execute()

        # 4. Iniciar sesión automáticamente
        login_resp = sb.auth.sign_in_with_password({"email": email, "password": password})
        _store_session(login_resp)
        return None

    except Exception as e:
        msg = str(e)
        if "already registered" in msg.lower() or "already exists" in msg.lower():
            return "Este email ya está registrado."
        return f"Error en registro: {msg}"

def _do_join_team(email: str, password: str, full_name: str, team_id: str, role: str = "presales"):
    """Registra un usuario que se une a un equipo existente."""
    # Validar rol: nunca permitir admin, solo roles válidos
    if role not in JOINABLE_ROLES:
        role = "presales"
    sb = _get_supabase()
    try:
        resp = sb.auth.sign_up({"email": email, "password": password})
        if not resp.user:
            return "No se pudo crear la cuenta."

        user_id = resp.user.id

        try:
            admin_sb = create_client(
                st.secrets["SUPABASE_URL"],
                st.secrets["SUPABASE_SERVICE_KEY"]
            )
        except Exception:
            admin_sb = sb

        admin_sb.table("profiles").insert({
            "id": user_id,
            "team_id": team_id,
            "full_name": full_name,
            "email": email,
            "role": role,
        }).execute()

        login_resp = sb.auth.sign_in_with_password({"email": email, "password": password})
        _store_session(login_resp)
        return None

    except Exception as e:
        return f"Error: {str(e)}"

def show_auth_page():
    """Muestra la página de login/registro (pantalla completa, sin sidebar)."""

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .auth-header { text-align: center; margin-bottom: 2rem; }
    .auth-header h1 { font-size: 2.5rem; font-weight: 800; color: #1e293b; }
    .auth-header p { color: #64748b; font-size: 1rem; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div class="auth-header"><h1>PG Machine</h1><p>Plataforma de gestión de oportunidades</p></div>', unsafe_allow_html=True)

        tab_login, tab_register, tab_join = st.tabs(["Iniciar Sesión", "Crear Equipo", "Unirse a Equipo"])

        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Contraseña", type="password", key="login_password")
                submitted = st.form_submit_button("Iniciar Sesión", use_container_width=True)
                if submitted:
                    if not email or not password:
                        st.error("Completa todos los campos.")
                    else:
                        err = _do_login(email, password)
                        if err:
                            st.error(err)
                        else:
                            st.rerun()
            if st.button("¿Olvidaste tu contraseña?", key="forgot_pw"):
                st.session_state["_show_forgot_pw"] = True
            if st.session_state.get("_show_forgot_pw"):
                forgot_email = st.text_input("Ingresa tu email para restablecer la contraseña", key="forgot_email")
                if st.button("Enviar enlace de restablecimiento", key="send_reset"):
                    if not forgot_email:
                        st.error("Ingresa tu email.")
                    else:
                        try:
                            sb = _get_supabase()
                            sb.auth.reset_password_email(forgot_email)
                            st.success("Se envió un enlace de restablecimiento a tu email. Revisa tu bandeja de entrada.")
                            st.session_state.pop("_show_forgot_pw", None)
                        except Exception as e:
                            st.error(f"Error al enviar el enlace: {str(e)}")

        with tab_register:
            with st.form("register_form"):
                r_name = st.text_input("Nombre completo", key="reg_name")
                r_email = st.text_input("Email", key="reg_email")
                r_password = st.text_input("Contraseña", type="password", key="reg_password")
                r_team = st.text_input("Nombre del equipo", key="reg_team")
                submitted = st.form_submit_button("Crear Cuenta y Equipo", use_container_width=True)
                if submitted:
                    if not all([r_name, r_email, r_password, r_team]):
                        st.error("Completa todos los campos.")
                    elif len(r_password) < 6:
                        st.error("La contraseña debe tener al menos 6 caracteres.")
                    else:
                        err = _do_register(r_email, r_password, r_name, r_team)
                        if err:
                            st.error(err)
                        else:
                            st.rerun()

        with tab_join:
            st.info("Usa el ID de equipo que te compartió tu administrador.")
            with st.form("join_form"):
                j_name = st.text_input("Nombre completo", key="join_name")
                j_email = st.text_input("Email", key="join_email")
                j_password = st.text_input("Contraseña", type="password", key="join_password")
                j_team_id = st.text_input("ID del equipo", key="join_team_id")
                j_role = st.selectbox(
                    "Rol",
                    JOINABLE_ROLES,
                    format_func=lambda r: ROLE_LABELS.get(r, r),
                    index=JOINABLE_ROLES.index("presales"),
                    key="join_role",
                )
                submitted = st.form_submit_button("Unirse al Equipo", use_container_width=True)
                if submitted:
                    if not all([j_name, j_email, j_password, j_team_id]):
                        st.error("Completa todos los campos.")
                    else:
                        err = _do_join_team(j_email, j_password, j_name, j_team_id, j_role)
                        if err:
                            st.error(err)
                        else:
                            st.rerun()

def require_auth():
    """
    Auth gate: retorna True si el usuario está autenticado.
    Si no, muestra la página de login y retorna False.
    """
    if _try_restore_session():
        return True
    if st.session_state.get("user"):
        return True
    show_auth_page()
    return False

def get_current_user() -> dict:
    """Retorna el usuario actual o dict vacío."""
    return st.session_state.get("user", {})

def is_admin() -> bool:
    """Retorna True si el usuario actual es admin."""
    return get_current_user().get("role") == "admin"

def is_manager_or_admin() -> bool:
    """Retorna True si el usuario actual es admin o manager (legacy)."""
    return get_current_user().get("role") in ("admin", "manager", "account_manager")

def has_control_access() -> bool:
    """Retorna True si el usuario tiene acceso al Panel de Control."""
    return get_current_user().get("role") in (
        "admin", "vp", "account_manager", "regional_sales_manager",
        "partner_manager", "regional_partner_manager", "presales_manager",
    )

def can_see_all_opportunities() -> bool:
    """Retorna True si el usuario puede ver todas las oportunidades del equipo."""
    return get_current_user().get("role") in ("admin", "vp")
