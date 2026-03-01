"""
Módulo de autenticación para PG Machine.
Login, registro, gestión de sesión con Supabase Auth.
"""
import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
from lib.i18n import t, get_lang, set_lang, auth_lang_toggle_html

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
            return t("auth.invalid_login")
        return t("auth.auth_error", msg=msg)

def _do_register(email: str, password: str, full_name: str, team_name: str):
    """Registra un nuevo usuario + crea equipo y perfil."""
    sb = _get_supabase()
    try:
        # 1. Registrar en Supabase Auth
        resp = sb.auth.sign_up({"email": email, "password": password})
        if not resp.user:
            return t("auth.register_fail")

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
            return t("auth.email_exists")
        return t("auth.register_error", msg=msg)

def _do_join_team(email: str, password: str, full_name: str, team_id: str, role: str = "presales"):
    """Registra un usuario que se une a un equipo existente."""
    # Validar rol: nunca permitir admin, solo roles válidos
    if role not in JOINABLE_ROLES:
        role = "presales"
    sb = _get_supabase()
    try:
        resp = sb.auth.sign_up({"email": email, "password": password})
        if not resp.user:
            return t("auth.account_fail")

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
        return t("auth.join_error", msg=str(e))

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
        # Language toggle for auth page
        st.markdown(auth_lang_toggle_html(), unsafe_allow_html=True)
        components.html("""
        <script>
        (function() {
            function findBtn(label) {
                var btns = window.parent.document.querySelectorAll('button');
                for (var i = 0; i < btns.length; i++) {
                    if (btns[i].textContent.trim() === label) return btns[i];
                }
                return null;
            }
            // Hide the trigger button
            function hideBtn() {
                var btn = findBtn('AUTH_TOGGLE_LANG');
                if (btn) { var el = btn.closest('[data-testid="stButton"]') || btn; el.style.display = 'none'; }
            }
            hideBtn();
            new MutationObserver(hideBtn).observe(window.parent.document.body, {childList: true, subtree: true});
            // Toggle click handler
            window.parent.document.addEventListener('click', function(e) {
                if (e.target.closest('.pgm-toggle-lang')) {
                    var btn = findBtn('AUTH_TOGGLE_LANG');
                    if (btn) btn.click();
                }
            });
        })();
        </script>
        """, height=0)

        st.markdown(f'<div class="auth-header"><h1>{t("auth.title")}</h1><p>{t("auth.subtitle")}</p></div>', unsafe_allow_html=True)

        tab_login, tab_register, tab_join = st.tabs([t("auth.tab_login"), t("auth.tab_register"), t("auth.tab_join")])

        with tab_login:
            with st.form("login_form"):
                email = st.text_input(t("auth.email"), key="login_email")
                password = st.text_input(t("auth.password"), type="password", key="login_password")
                submitted = st.form_submit_button(t("auth.login_btn"), use_container_width=True)
                if submitted:
                    if not email or not password:
                        st.error(t("auth.fill_all"))
                    else:
                        err = _do_login(email, password)
                        if err:
                            st.error(err)
                        else:
                            st.rerun()
            if st.button(t("auth.forgot_pw"), key="forgot_pw"):
                st.session_state["_show_forgot_pw"] = True
            if st.session_state.get("_show_forgot_pw"):
                forgot_email = st.text_input(t("auth.forgot_email_prompt"), key="forgot_email")
                if st.button(t("auth.send_reset"), key="send_reset"):
                    if not forgot_email:
                        st.error(t("auth.enter_email"))
                    else:
                        try:
                            sb = _get_supabase()
                            app_url = st.secrets.get("APP_URL", "http://localhost:8501")
                            sb.auth.reset_password_email(forgot_email, {"redirect_to": app_url})
                            st.success(t("auth.reset_sent"))
                            st.session_state.pop("_show_forgot_pw", None)
                        except Exception as e:
                            st.error(t("auth.reset_error", msg=str(e)))

        with tab_register:
            with st.form("register_form"):
                r_name = st.text_input(t("auth.full_name"), key="reg_name")
                r_email = st.text_input(t("auth.email"), key="reg_email")
                r_password = st.text_input(t("auth.password"), type="password", key="reg_password")
                r_team = st.text_input(t("auth.team_name"), key="reg_team")
                submitted = st.form_submit_button(t("auth.register_btn"), use_container_width=True)
                if submitted:
                    if not all([r_name, r_email, r_password, r_team]):
                        st.error(t("auth.fill_all"))
                    elif len(r_password) < 6:
                        st.error(t("auth.pw_min"))
                    else:
                        err = _do_register(r_email, r_password, r_name, r_team)
                        if err:
                            st.error(err)
                        else:
                            st.rerun()

        with tab_join:
            st.info(t("auth.join_info"))
            with st.form("join_form"):
                j_name = st.text_input(t("auth.full_name"), key="join_name")
                j_email = st.text_input(t("auth.email"), key="join_email")
                j_password = st.text_input(t("auth.password"), type="password", key="join_password")
                j_team_id = st.text_input(t("auth.team_id"), key="join_team_id")
                j_role = st.selectbox(
                    t("auth.role"),
                    JOINABLE_ROLES,
                    format_func=lambda r: ROLE_LABELS.get(r, r),
                    index=JOINABLE_ROLES.index("presales"),
                    key="join_role",
                )
                submitted = st.form_submit_button(t("auth.join_btn"), use_container_width=True)
                if submitted:
                    if not all([j_name, j_email, j_password, j_team_id]):
                        st.error(t("auth.fill_all"))
                    else:
                        err = _do_join_team(j_email, j_password, j_name, j_team_id, j_role)
                        if err:
                            st.error(err)
                        else:
                            st.rerun()

        # Hidden button for auth page language toggle
        _auth_lang_btn = st.button("AUTH_TOGGLE_LANG", key="btn_auth_toggle_lang")
        if _auth_lang_btn:
            new_lang = "en" if get_lang() == "es" else "es"
            set_lang(new_lang)
            st.rerun()

def _show_recovery_page():
    """Muestra formulario para establecer nueva contraseña tras recovery."""
    access_token = st.query_params.get("_rat")
    refresh_token = st.query_params.get("_rrt")
    if not access_token or not refresh_token:
        return False

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
        st.markdown(auth_lang_toggle_html(), unsafe_allow_html=True)
        st.markdown(f'<div class="auth-header"><h1>{t("auth.title")}</h1><p>{t("auth.reset_title")}</p></div>', unsafe_allow_html=True)
        with st.form("reset_pw_form"):
            new_pw = st.text_input(t("auth.new_pw"), type="password", key="new_pw")
            confirm_pw = st.text_input(t("auth.confirm_pw"), type="password", key="confirm_pw")
            if st.form_submit_button(t("auth.change_pw_btn"), use_container_width=True):
                if not new_pw or not confirm_pw:
                    st.error(t("auth.fill_both"))
                elif len(new_pw) < 6:
                    st.error(t("auth.pw_min"))
                elif new_pw != confirm_pw:
                    st.error(t("auth.pw_mismatch"))
                else:
                    try:
                        sb = _get_supabase()
                        sb.auth.set_session(access_token, refresh_token)
                        sb.auth.update_user({"password": new_pw})
                        st.success(t("auth.pw_updated"))
                        st.query_params.clear()
                    except Exception as e:
                        st.error(t("auth.pw_change_error", msg=str(e)))
    return True


def require_auth():
    """
    Auth gate: retorna True si el usuario está autenticado.
    Si no, muestra la página de login y retorna False.
    """
    # JS: captura tokens de recovery del hash fragment de Supabase y los convierte a query params
    params = st.query_params
    if not params.get("_rat"):
        components.html("""
        <script>
        (function() {
            var h = window.parent.location.hash;
            if (h && h.indexOf("type=recovery") !== -1) {
                var p = new URLSearchParams(h.substring(1));
                var at = p.get("access_token");
                var rt = p.get("refresh_token");
                if (at && rt) {
                    window.parent.location.search = "?_rat=" + encodeURIComponent(at) + "&_rrt=" + encodeURIComponent(rt);
                }
            }
        })();
        </script>
        """, height=0)

    # Si hay tokens de recovery, mostrar formulario de nueva contraseña
    if _show_recovery_page():
        return False

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
    return bool(get_current_user().get("team_id"))
