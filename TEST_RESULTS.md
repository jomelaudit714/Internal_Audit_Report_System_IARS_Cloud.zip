# Test Results — IARS v3.8.1

## Static validation

- Python syntax compilation for `app.py`: PASSED
- Python syntax compilation for `iars_auth.py`: PASSED
- Python syntax compilation for `iars_archive.py`: PASSED
- Python syntax compilation for `iars_parser.py`: PASSED
- Python syntax compilation for `iars_pdf_editor.py`: PASSED
- Old Supabase phone/SMS API calls removed from application code: PASSED
- Old `[supabase_auth]` runtime dependency removed: PASSED

## Authentication primitives

- Username normalization and nickname validation: PASSED
- Optional contact-number cleanup: PASSED
- Password length and letter/number validation: PASSED
- Salted PBKDF2-SHA256 password hashing and verification: PASSED
- Incorrect-password rejection: PASSED
- Six-digit activation/reset-code generation: PASSED
- Secret-key HMAC code verification: PASSED
- Purpose separation between activation and reset codes: PASSED

## Account workflow checks

- One administrator account is read only from Streamlit Secrets: IMPLEMENTED
- New registrations are stored as `Pending`: IMPLEMENTED
- Administrator approval changes status to `Code Issued`: IMPLEMENTED
- User activation changes status to `Active`: IMPLEMENTED
- Forgot-password requests require an administrator-issued code: IMPLEMENTED
- User suspension/reactivation/deactivation controls: IMPLEMENTED
- Five failed sign-ins cause a timed lockout: IMPLEMENTED
- Inactivity timeout and sign-out: IMPLEMENTED
- Master Data update restricted to administrator: IMPLEMENTED
- Authentication event logging: IMPLEMENTED

## Existing IARS behavior

- Automatic PDF archive compression retained: PASSED
- Exact 27-column external-system export headers retained: PASSED
- Exact Findings/Response/Frequency/Auditor labels retained: PASSED
- Blank `by02` behavior retained: PASSED
- Validated Master Data retained unchanged from the prior package: PASSED

Live Supabase table operations require running `SUPABASE_USER_AUTH_SETUP.sql` in the user's project and therefore were not executed in the offline test environment.

- Confirmed Account Administration expander is visible and expanded for the administrator.
