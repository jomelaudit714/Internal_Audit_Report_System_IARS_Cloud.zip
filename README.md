# IARS v3.6.0 — Secure Phone Login and Automatic PDF Compression

This release keeps all v3.5.3 extraction, exact database headers, Master Data behavior, blank Auditor 2 behavior, and automatic PDF archive compression.

## New authentication features

The entire IARS application is now protected by Supabase Auth.

### Sign Up

Users provide only:

- Full Name
- Contact Number
- Password
- Password confirmation

After registration, Supabase sends a six-digit SMS code. The user must enter the code before the account becomes verified.

### Sign In

Verified users sign in using:

- Contact Number
- Password

### Forgot Password

Users can reset their password using:

1. Registered Contact Number
2. SMS verification code
3. New Password

### Account controls

- The signed-in user's name and contact number appear in the sidebar.
- A Sign Out button securely clears the current Streamlit session.
- Philippine mobile-number formats are automatically normalized to E.164 format.
- Passwords require at least eight characters with at least one letter and one number.
- The archive's service-role key is not used for user authentication.

## Required Supabase setup

Phone authentication cannot send codes until a supported SMS provider is configured in Supabase.

See `SUPABASE_AUTH_SETUP.md` and update Streamlit Secrets using `.streamlit/secrets.toml.example`.

## Existing PDF compression behavior

Every original or tagged PDF saved to the private Supabase archive is optimized before upload when a smaller safe result can be produced. Searchable text and page count are preserved, and signed or encrypted PDFs are retained unchanged.

## Deployment

Deploy all files from this ZIP together, including the new `iars_auth.py` file. Commit the changes and reboot the Streamlit app.
