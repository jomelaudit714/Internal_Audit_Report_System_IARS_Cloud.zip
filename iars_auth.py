from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

import streamlit as st


AUTH_ACCESS_TOKEN_KEY = "iars_auth_access_token"
AUTH_REFRESH_TOKEN_KEY = "iars_auth_refresh_token"
AUTH_PENDING_SIGNUP_PHONE_KEY = "iars_auth_pending_signup_phone"
AUTH_PENDING_SIGNUP_NAME_KEY = "iars_auth_pending_signup_name"
AUTH_RESET_PHONE_KEY = "iars_auth_reset_phone"


@dataclass(frozen=True)
class AuthConfig:
    url: str
    anon_key: str


def _secret_value(container: Any, key: str, default: str = "") -> str:
    try:
        value = container.get(key, default)
    except Exception:
        try:
            value = container[key]
        except Exception:
            value = default
    return str(value or "").strip()


def read_auth_config(secrets: Any) -> AuthConfig:
    """Read end-user authentication settings from Streamlit Secrets.

    Preferred format:
        [supabase_auth]
        url = "https://YOUR-PROJECT.supabase.co"
        anon_key = "YOUR-ANON-OR-PUBLISHABLE-KEY"

    The URL and anon key may also be placed in [supabase]. The archive's
    service-role key is intentionally never used for user sign-in.
    """
    auth_section = {}
    supabase_section = {}
    try:
        auth_section = secrets.get("supabase_auth", {})
        supabase_section = secrets.get("supabase", {})
    except Exception:
        pass

    url = (
        _secret_value(auth_section, "url")
        or _secret_value(supabase_section, "url")
        or _secret_value(secrets, "SUPABASE_URL")
    )
    anon_key = (
        _secret_value(auth_section, "anon_key")
        or _secret_value(auth_section, "publishable_key")
        or _secret_value(supabase_section, "anon_key")
        or _secret_value(supabase_section, "publishable_key")
        or _secret_value(secrets, "SUPABASE_ANON_KEY")
        or _secret_value(secrets, "SUPABASE_PUBLISHABLE_KEY")
    )
    return AuthConfig(url=url, anon_key=anon_key)


def auth_is_configured(config: AuthConfig) -> bool:
    return bool(config.url and config.anon_key)


def create_auth_client(config: AuthConfig):
    if not auth_is_configured(config):
        raise RuntimeError("Supabase end-user authentication is not configured.")
    from supabase import create_client

    return create_client(config.url, config.anon_key)


def normalize_phone(value: str) -> str:
    """Return a phone number in E.164 format.

    Philippine convenience formats are supported:
      09171234567  -> +639171234567
      9171234567   -> +639171234567
      639171234567 -> +639171234567
    International numbers may be entered with a leading +.
    """
    raw = str(value or "").strip()
    if not raw:
        raise ValueError("Contact number is required.")

    cleaned = re.sub(r"[\s()\-.]", "", raw)
    if cleaned.startswith("00"):
        cleaned = "+" + cleaned[2:]

    if re.fullmatch(r"09\d{9}", cleaned):
        cleaned = "+63" + cleaned[1:]
    elif re.fullmatch(r"9\d{9}", cleaned):
        cleaned = "+63" + cleaned
    elif re.fullmatch(r"63\d{10}", cleaned):
        cleaned = "+" + cleaned

    if not re.fullmatch(r"\+[1-9]\d{7,14}", cleaned):
        raise ValueError(
            "Enter a valid mobile number, such as 09171234567 or +639171234567."
        )
    return cleaned


def validate_password(password: str, confirmation: str | None = None) -> str:
    password = str(password or "")
    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise ValueError("Password must contain at least one letter and one number.")
    if confirmation is not None and password != confirmation:
        raise ValueError("Passwords do not match.")
    return password


def _auth_error_message(exc: Exception) -> str:
    message = str(exc or "").strip()
    lowered = message.casefold()
    if "invalid login credentials" in lowered:
        return "Incorrect contact number or password."
    if "phone not confirmed" in lowered:
        return "Your contact number is not verified. Open Sign Up and enter the verification code."
    if "user already registered" in lowered or "already been registered" in lowered:
        return "An account already exists for this contact number. Sign in or use Forgot Password."
    if "rate limit" in lowered or "over_email_send_rate_limit" in lowered:
        return "Too many requests. Wait a short time before requesting another code."
    if "otp" in lowered and ("expired" in lowered or "invalid" in lowered):
        return "The verification code is invalid or expired. Request a new code and try again."
    return message or "Authentication could not be completed."


def _get_attr(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _store_auth_response(response: Any) -> Any:
    session = _get_attr(response, "session")
    user = _get_attr(response, "user")
    if session is not None:
        access_token = _get_attr(session, "access_token", "")
        refresh_token = _get_attr(session, "refresh_token", "")
        if access_token and refresh_token:
            st.session_state[AUTH_ACCESS_TOKEN_KEY] = access_token
            st.session_state[AUTH_REFRESH_TOKEN_KEY] = refresh_token
    return user


def clear_auth_session() -> None:
    for key in (
        AUTH_ACCESS_TOKEN_KEY,
        AUTH_REFRESH_TOKEN_KEY,
        AUTH_PENDING_SIGNUP_PHONE_KEY,
        AUTH_PENDING_SIGNUP_NAME_KEY,
        AUTH_RESET_PHONE_KEY,
    ):
        st.session_state.pop(key, None)


def restore_auth_session(config: AuthConfig):
    """Return a session-local Supabase client and authenticated user, if any."""
    client = create_auth_client(config)
    access_token = str(st.session_state.get(AUTH_ACCESS_TOKEN_KEY, "") or "")
    refresh_token = str(st.session_state.get(AUTH_REFRESH_TOKEN_KEY, "") or "")
    if not access_token or not refresh_token:
        return client, None

    try:
        response = client.auth.set_session(access_token, refresh_token)
        _store_auth_response(response)
        user_response = client.auth.get_user()
        user = _get_attr(user_response, "user")
        if user is None:
            clear_auth_session()
            return client, None
        return client, user
    except Exception:
        # Try a refresh once before requiring a new sign-in.
        try:
            response = client.auth.refresh_session(refresh_token)
            user = _store_auth_response(response)
            if user is None:
                user_response = client.auth.get_user()
                user = _get_attr(user_response, "user")
            return client, user
        except Exception:
            clear_auth_session()
            return client, None


def user_display_name(user: Any) -> str:
    metadata = _get_attr(user, "user_metadata", {}) or {}
    if not isinstance(metadata, dict):
        metadata = {}
    return str(metadata.get("full_name") or metadata.get("name") or "IARS User").strip()


def user_phone(user: Any) -> str:
    return str(_get_attr(user, "phone", "") or "").strip()


def _render_auth_setup_notice() -> None:
    st.error("IARS sign-in is not configured yet.")
    st.markdown(
        "Add the Supabase project URL and **anon/publishable key** to Streamlit Secrets. "
        "Do not use the service-role key for user sign-in."
    )
    st.code(
        '[supabase_auth]\n'
        'url = "https://YOUR-PROJECT.supabase.co"\n'
        'anon_key = "YOUR-ANON-OR-PUBLISHABLE-KEY"',
        language="toml",
    )
    st.info(
        "In Supabase, enable Phone authentication, require phone confirmation, and configure "
        "an SMS provider before testing verification codes."
    )


def _render_sign_in(client: Any) -> None:
    st.subheader("Sign In")
    st.caption("Use the contact number and password registered for your IARS account.")
    with st.form("iars_sign_in_form"):
        phone_input = st.text_input(
            "Contact Number",
            placeholder="09171234567",
            autocomplete="tel",
            key="auth_signin_phone",
        )
        password = st.text_input(
            "Password",
            type="password",
            autocomplete="current-password",
            key="auth_signin_password",
        )
        submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)

    if submitted:
        try:
            phone = normalize_phone(phone_input)
            response = client.auth.sign_in_with_password(
                {"phone": phone, "password": password}
            )
            user = _store_auth_response(response)
            if user is None:
                raise RuntimeError("Sign-in succeeded but no user session was returned.")
            st.success("Signed in successfully.")
            st.rerun()
        except Exception as exc:
            st.error(_auth_error_message(exc))


def _render_sign_up(client: Any) -> None:
    pending_phone = str(st.session_state.get(AUTH_PENDING_SIGNUP_PHONE_KEY, "") or "")
    pending_name = str(st.session_state.get(AUTH_PENDING_SIGNUP_NAME_KEY, "") or "")

    st.subheader("Sign Up")
    if not pending_phone:
        st.caption("Provide only your name, contact number, and a password.")
        with st.form("iars_sign_up_form"):
            full_name = st.text_input(
                "Full Name",
                placeholder="Juan Dela Cruz",
                autocomplete="name",
                key="auth_signup_full_name",
            )
            phone_input = st.text_input(
                "Contact Number",
                placeholder="09171234567",
                autocomplete="tel",
                key="auth_signup_phone",
            )
            password = st.text_input(
                "Password",
                type="password",
                autocomplete="new-password",
                help="At least 8 characters with at least one letter and one number.",
                key="auth_signup_password",
            )
            confirmation = st.text_input(
                "Confirm Password",
                type="password",
                autocomplete="new-password",
                key="auth_signup_password_confirm",
            )
            submitted = st.form_submit_button(
                "Create Account and Send Code",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            try:
                clean_name = " ".join(str(full_name or "").split()).strip()
                if len(clean_name) < 3:
                    raise ValueError("Enter your complete name.")
                phone = normalize_phone(phone_input)
                validate_password(password, confirmation)
                response = client.auth.sign_up(
                    {
                        "phone": phone,
                        "password": password,
                        "options": {
                            "data": {
                                "full_name": clean_name,
                                "contact_number": phone,
                            }
                        },
                    }
                )
                session = _get_attr(response, "session")
                if session is not None:
                    # This happens when phone confirmation is disabled in Supabase.
                    _store_auth_response(response)
                    st.warning(
                        "The account was created without an SMS verification step because "
                        "Confirm phone is disabled in Supabase. Enable phone confirmation to "
                        "require a code for future sign-ups."
                    )
                    st.rerun()
                st.session_state[AUTH_PENDING_SIGNUP_PHONE_KEY] = phone
                st.session_state[AUTH_PENDING_SIGNUP_NAME_KEY] = clean_name
                st.success(f"A verification code was sent to {phone}.")
                st.rerun()
            except Exception as exc:
                st.error(_auth_error_message(exc))
        return

    st.caption(f"Enter the verification code sent to **{pending_phone}**.")
    with st.form("iars_signup_verify_form"):
        token = st.text_input(
            "Verification Code",
            max_chars=6,
            placeholder="123456",
            autocomplete="one-time-code",
            key="auth_signup_otp",
        )
        submitted = st.form_submit_button(
            "Verify Account",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        try:
            code = re.sub(r"\D", "", str(token or ""))
            if len(code) != 6:
                raise ValueError("Enter the 6-digit verification code.")
            response = client.auth.verify_otp(
                {"phone": pending_phone, "token": code, "type": "sms"}
            )
            user = _store_auth_response(response)
            if user is None:
                raise RuntimeError("The code was accepted, but no user session was returned.")
            st.session_state.pop(AUTH_PENDING_SIGNUP_PHONE_KEY, None)
            st.session_state.pop(AUTH_PENDING_SIGNUP_NAME_KEY, None)
            st.success(f"Account verified. Welcome, {pending_name or 'IARS User'}.")
            st.rerun()
        except Exception as exc:
            st.error(_auth_error_message(exc))

    action_left, action_right = st.columns(2)
    with action_left:
        if st.button("Resend Code", key="signup_resend_code", use_container_width=True):
            try:
                client.auth.sign_in_with_otp(
                    {
                        "phone": pending_phone,
                        "options": {"should_create_user": False},
                    }
                )
                st.success("A new verification code was sent.")
            except Exception as exc:
                st.error(_auth_error_message(exc))
    with action_right:
        if st.button("Use Another Number", key="signup_change_number", use_container_width=True):
            st.session_state.pop(AUTH_PENDING_SIGNUP_PHONE_KEY, None)
            st.session_state.pop(AUTH_PENDING_SIGNUP_NAME_KEY, None)
            st.rerun()


def _render_forgot_password(client: Any) -> None:
    reset_phone = str(st.session_state.get(AUTH_RESET_PHONE_KEY, "") or "")
    st.subheader("Forgot Password")

    if not reset_phone:
        st.caption("We will send a one-time code to your verified contact number.")
        with st.form("iars_password_reset_request_form"):
            phone_input = st.text_input(
                "Registered Contact Number",
                placeholder="09171234567",
                autocomplete="tel",
                key="auth_reset_phone",
            )
            submitted = st.form_submit_button(
                "Send Reset Code",
                type="primary",
                use_container_width=True,
            )
        if submitted:
            try:
                phone = normalize_phone(phone_input)
                client.auth.sign_in_with_otp(
                    {
                        "phone": phone,
                        "options": {"should_create_user": False},
                    }
                )
                st.session_state[AUTH_RESET_PHONE_KEY] = phone
                st.success("A password-reset code was sent to your registered contact number.")
                st.rerun()
            except Exception as exc:
                st.error(_auth_error_message(exc))
        return

    st.caption(f"Enter the code sent to **{reset_phone}**, then choose a new password.")
    with st.form("iars_password_reset_verify_form"):
        token = st.text_input(
            "Verification Code",
            max_chars=6,
            placeholder="123456",
            autocomplete="one-time-code",
            key="auth_reset_otp",
        )
        new_password = st.text_input(
            "New Password",
            type="password",
            autocomplete="new-password",
            key="auth_reset_new_password",
        )
        confirmation = st.text_input(
            "Confirm New Password",
            type="password",
            autocomplete="new-password",
            key="auth_reset_new_password_confirm",
        )
        submitted = st.form_submit_button(
            "Verify and Change Password",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        try:
            code = re.sub(r"\D", "", str(token or ""))
            if len(code) != 6:
                raise ValueError("Enter the 6-digit verification code.")
            validate_password(new_password, confirmation)
            response = client.auth.verify_otp(
                {"phone": reset_phone, "token": code, "type": "sms"}
            )
            _store_auth_response(response)
            client.auth.update_user({"password": new_password})
            try:
                client.auth.sign_out()
            except Exception:
                pass
            clear_auth_session()
            st.success("Password changed successfully. Sign in using your new password.")
            st.rerun()
        except Exception as exc:
            st.error(_auth_error_message(exc))

    action_left, action_right = st.columns(2)
    with action_left:
        if st.button("Resend Reset Code", key="reset_resend_code", use_container_width=True):
            try:
                client.auth.sign_in_with_otp(
                    {
                        "phone": reset_phone,
                        "options": {"should_create_user": False},
                    }
                )
                st.success("A new password-reset code was sent.")
            except Exception as exc:
                st.error(_auth_error_message(exc))
    with action_right:
        if st.button("Use Another Number", key="reset_change_number", use_container_width=True):
            st.session_state.pop(AUTH_RESET_PHONE_KEY, None)
            st.rerun()


def render_auth_gate(config: AuthConfig):
    """Require authentication before allowing the rest of IARS to render."""
    if not auth_is_configured(config):
        st.title("Internal Audit Report System (IARS)")
        _render_auth_setup_notice()
        st.stop()

    try:
        client, user = restore_auth_session(config)
    except Exception as exc:
        st.title("Internal Audit Report System (IARS)")
        st.error(f"Unable to initialize Supabase Auth: {_auth_error_message(exc)}")
        st.stop()

    if user is not None:
        return client, user

    st.title("Internal Audit Report System (IARS)")
    st.caption("Secure access for authorized Internal Audit users")
    sign_in_tab, sign_up_tab, forgot_tab = st.tabs(
        ["Sign In", "Sign Up", "Forgot Password"]
    )
    with sign_in_tab:
        _render_sign_in(client)
    with sign_up_tab:
        _render_sign_up(client)
    with forgot_tab:
        _render_forgot_password(client)
    st.stop()


def render_account_sidebar(client: Any, user: Any) -> None:
    st.header("Account")
    st.write(f"**{user_display_name(user)}**")
    phone = user_phone(user)
    if phone:
        st.caption(phone)
    if st.button("Sign Out", key="iars_sign_out", use_container_width=True):
        try:
            client.auth.sign_out()
        except Exception:
            pass
        clear_auth_session()
        st.rerun()
