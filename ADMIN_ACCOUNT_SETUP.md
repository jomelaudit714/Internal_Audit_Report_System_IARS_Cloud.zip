# IARS v3.8.1 — Multi-User Admin-Approved Login Setup

This version does **not** use SMS, Twilio, phone OTP, or Supabase Phone Auth.

## 1. Create the account tables

In the same Supabase project used by the PDF archive:

1. Open **SQL Editor**.
2. Create a new query.
3. Paste and run `SUPABASE_USER_AUTH_SETUP.sql`.
4. A successful run normally shows **Success. No rows returned**.

The SQL creates:

- `iars_users` — standard user accounts and verification/reset-code status
- `iars_auth_log` — sign-in, activation, reset, and administration events

## 2. Configure one administrator account

Open **Streamlit → Manage app → Settings → Secrets**.

Keep the existing `[supabase]` and `[archive]` sections, then add:

```toml
[iars_admin]
username = "jomel"
password = "REPLACE-WITH-A-STRONG-ADMIN-PASSWORD"
full_name = "Jomel Santiago"
code_secret = "REPLACE-WITH-A-LONG-RANDOM-SECRET"
session_timeout_minutes = 30
```

Requirements:

- `username`: 3–30 lowercase letters/numbers, with optional `.`, `_`, or `-`
- `password`: use a unique strong passphrase
- `code_secret`: use a long random value, preferably 32+ characters
- Never place these values in GitHub

The system has exactly **one administrator account**, defined in Streamlit Secrets. Standard users cannot become administrators through sign-up.

## 3. Remove the old SMS configuration

The following section is no longer used and may be removed from Streamlit Secrets:

```toml
[supabase_auth]
url = "..."
anon_key = "..."
```

You may also disable **Authentication → Providers → Phone** in Supabase. The new IARS version does not call Supabase Phone Auth.

## 4. User account process

1. The user opens **Sign Up**.
2. The user provides:
   - Full name
   - Username/nickname
   - Optional contact number
   - Password
3. The registration is saved as `Pending`.
4. The administrator signs in and opens **Account Administration** in the sidebar.
5. The administrator selects the pending user and clicks **Approve and Generate Activation Code**.
6. IARS displays a six-digit one-time code.
7. The administrator personally gives the code to the user.
8. The user opens **Verify Account**, enters the username and code, then signs in normally.

Activation codes expire after 24 hours and become invalid after five incorrect attempts.

## 5. Forgot-password process

1. The user opens **Forgot Password** and submits the username.
2. The administrator sees the reset request in **Account Administration**.
3. The administrator generates a reset code and gives it directly to the user.
4. The user enters the username, reset code, and new password.

Reset codes expire after 30 minutes and become invalid after five incorrect attempts.

## 6. Included security controls

- Passwords are stored as salted PBKDF2-SHA256 hashes, not plain text.
- Verification and reset codes are stored as secret-key HMAC hashes.
- Five failed sign-in attempts cause a 15-minute lockout.
- Sessions automatically expire after inactivity.
- Only the administrator can approve, suspend, reactivate, or deactivate users.
- Master Data updates are restricted to the administrator.
- Authentication events are recorded in `iars_auth_log`.

## 7. Existing v3.6.0 phone-auth accounts

Accounts previously created through Supabase Phone Auth are not automatically copied into `iars_users`. After deploying v3.8.1, each standard user should submit a new username-based registration, or the administrator may keep the system limited to the single administrator account until user access is needed.
