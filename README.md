# IARS v3.8.1 — Multi-User Admin-Approved Login

This release restores multi-user access without SMS/phone OTP while retaining all existing extraction, exact external-system headers, Master Data behavior, blank Auditor 2 behavior, Supabase PDF archive, and automatic PDF compression.

## Account design

### One administrator account

IARS has exactly one administrator account configured privately in Streamlit Secrets. The administrator can:

- Approve pending registrations
- Generate and reissue activation codes
- Generate forgot-password reset codes
- Suspend, reactivate, or deactivate standard users
- Update Master Data

### Standard user sign-up

Users provide only:

- Full Name
- Username/Nickname
- Contact Number (optional profile information)
- Password and confirmation

The contact number is not used as the username and no SMS is sent.

### Manual account verification

1. A new account is saved as `Pending`.
2. The administrator approves it and IARS generates a six-digit one-time activation code.
3. The administrator gives the code directly to the user.
4. The user enters the username and code under **Verify Account**.
5. The account becomes `Active` and the user can sign in with username and password.

### Forgot password

The user requests a reset using the username. The administrator generates a one-time reset code and gives it directly to the user. No SMS or email sender is required.

## Security controls

- Salted PBKDF2-SHA256 password hashes
- Secret-key HMAC protection for activation/reset codes
- Activation code expiry after 24 hours
- Reset code expiry after 30 minutes
- Maximum five code attempts
- Five failed sign-ins trigger a 15-minute lockout
- Automatic logout after inactivity
- Administrator-only account management and Master Data update
- Authentication activity log in Supabase

## Required setup

1. Run `SUPABASE_USER_AUTH_SETUP.sql` in the Supabase SQL Editor.
2. Add the `[iars_admin]` section shown in `.streamlit/secrets.toml.example` to Streamlit Secrets.
3. Remove the old `[supabase_auth]` section if it is still present.
4. Phone Auth and an SMS provider may be disabled because this version does not use them.

See `ADMIN_ACCOUNT_SETUP.md` for the exact steps.

## PDF compression

Every original or tagged PDF saved to the private Supabase archive is automatically optimized when a smaller safe copy can be produced. Searchable text and page count are preserved. Signed, encrypted, or already optimized files are retained unchanged.

## Deployment

Upload all package files together, commit them to the branch used by Streamlit, run the SQL setup once, update Streamlit Secrets, and reboot the app.


## Visibility improvement

After the administrator signs in, **Account Administration (Admin Only)** is expanded automatically in the sidebar so pending registrations and account controls are immediately visible.
