"""
Módulo de autenticación para PG Machine.
Login, registro, gestión de sesión con bcrypt (local auth, Neon PostgreSQL).
"""
import streamlit as st
import streamlit.components.v1 as components
import bcrypt
from lib.i18n import t, get_lang, set_lang, auth_lang_toggle_html
from lib import db

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

# Sentinel hash used for migrated accounts that need a password reset
_TEMP_HASH_PREFIX = b"$2b$12$TEMP"


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def _check_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def _is_temp_hash(hashed: str) -> bool:
    """Detect migrated accounts with temporary password."""
    return hashed.encode().startswith(_TEMP_HASH_PREFIX)


def _store_session(profile: dict):
    """Almacena datos de sesión en session_state."""
    st.session_state.user = {
        "id": str(profile["id"]),
        "email": profile["email"],
        "full_name": profile.get("full_name", profile["email"]),
        "team_id": str(profile["team_id"]),
        "role": profile.get("role", "presales"),
        "specialty": profile.get("specialty", ""),
    }


def logout():
    """Cierra sesión del usuario."""
    st.session_state.pop("user", None)
    st.rerun()


def _do_login(email: str, password: str):
    """Ejecuta login con email/password."""
    profile = db.fetch_one(
        "SELECT * FROM profiles WHERE email = %s",
        (email.strip().lower(),),
    )
    if not profile:
        return t("auth.invalid_login")

    if not _check_password(password, profile["password_hash"]):
        return t("auth.invalid_login")

    # Check if migrated account needs password change
    if _is_temp_hash(profile["password_hash"]):
        st.session_state["_needs_pw_reset"] = profile
        return None

    _store_session(profile)
    return None


def _do_register(email: str, password: str, full_name: str, team_name: str):
    """Registra un nuevo usuario + crea equipo y perfil."""
    email = email.strip().lower()
    try:
        # Check if email already exists
        existing = db.fetch_one("SELECT id FROM profiles WHERE email = %s", (email,))
        if existing:
            return t("auth.email_exists")

        # 1. Create team
        team = db.execute_returning(
            "INSERT INTO teams (name) VALUES (%s) RETURNING *",
            (team_name,),
        )
        team_id = team["id"]

        # 2. Create profile (first user = admin)
        pw_hash = _hash_password(password)
        profile = db.execute_returning(
            """INSERT INTO profiles (team_id, full_name, email, password_hash, role)
               VALUES (%s, %s, %s, %s, 'admin') RETURNING *""",
            (str(team_id), full_name, email, pw_hash),
        )

        _store_session(profile)
        return None

    except Exception as e:
        msg = str(e)
        if "duplicate key" in msg.lower() or "unique" in msg.lower():
            return t("auth.email_exists")
        return t("auth.register_error", msg=msg)


def _do_join_team(email: str, password: str, full_name: str, team_id: str, role: str = "presales"):
    """Registra un usuario que se une a un equipo existente."""
    if role not in JOINABLE_ROLES:
        role = "presales"
    email = email.strip().lower()
    try:
        # Validate team exists
        team = db.fetch_one("SELECT id FROM teams WHERE id = %s", (team_id,))
        if not team:
            return t("auth.join_error", msg="Team not found")

        # Check email uniqueness
        existing = db.fetch_one("SELECT id FROM profiles WHERE email = %s", (email,))
        if existing:
            return t("auth.email_exists")

        pw_hash = _hash_password(password)
        profile = db.execute_returning(
            """INSERT INTO profiles (team_id, full_name, email, password_hash, role)
               VALUES (%s, %s, %s, %s, %s) RETURNING *""",
            (team_id, full_name, email, pw_hash, role),
        )

        _store_session(profile)
        return None

    except Exception as e:
        return t("auth.join_error", msg=str(e))


def _show_set_password_page():
    """Show form for migrated users to set a new password."""
    profile = st.session_state.get("_needs_pw_reset")
    if not profile:
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
        st.markdown(f'<div class="auth-header"><h1>{t("auth.title")}</h1><p>{t("auth.reset_title")}</p></div>', unsafe_allow_html=True)
        with st.form("set_pw_form"):
            new_pw = st.text_input(t("auth.new_pw"), type="password", key="set_new_pw")
            confirm_pw = st.text_input(t("auth.confirm_pw"), type="password", key="set_confirm_pw")
            if st.form_submit_button(t("auth.change_pw_btn"), use_container_width=True):
                if not new_pw or not confirm_pw:
                    st.error(t("auth.fill_both"))
                elif len(new_pw) < 6:
                    st.error(t("auth.pw_min"))
                elif new_pw != confirm_pw:
                    st.error(t("auth.pw_mismatch"))
                else:
                    pw_hash = _hash_password(new_pw)
                    db.execute(
                        "UPDATE profiles SET password_hash = %s WHERE id = %s",
                        (pw_hash, str(profile["id"])),
                    )
                    st.session_state.pop("_needs_pw_reset", None)
                    _store_session(profile)
                    st.success(t("auth.pw_updated"))
                    st.rerun()
    return True


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


def require_auth():
    """
    Auth gate: retorna True si el usuario está autenticado.
    Si no, muestra la página de login y retorna False.
    """
    # Migrated user needs to set password
    if st.session_state.get("_needs_pw_reset"):
        _show_set_password_page()
        return False

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
