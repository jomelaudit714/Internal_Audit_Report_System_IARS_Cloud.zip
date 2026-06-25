# Test Results — IARS v3.6.0

- Python syntax compilation for `app.py`: PASSED
- Python syntax compilation for `iars_auth.py`: PASSED
- Python syntax compilation for `iars_archive.py`: PASSED
- Python syntax compilation for `iars_parser.py`: PASSED
- Python syntax compilation for `iars_pdf_editor.py`: PASSED
- Philippine phone normalization (`0917`, `917`, `63`, `+63` formats): PASSED
- Invalid phone-number rejection: PASSED
- Password minimum-length validation: PASSED
- Password letter-and-number validation: PASSED
- Password confirmation matching: PASSED
- Sign-up integration uses phone, password, and full-name metadata: VERIFIED AGAINST SUPABASE-PY 2.31.0 API
- SMS OTP verification uses `type="sms"`: VERIFIED AGAINST SUPABASE-PY 2.31.0 API
- Sign-in integration uses phone and password: VERIFIED AGAINST SUPABASE-PY 2.31.0 API
- Forgot-password flow uses phone OTP followed by authenticated password update: VERIFIED AGAINST SUPABASE-PY 2.31.0 API
- Session tokens are stored only in Streamlit session state: IMPLEMENTED
- Archive service-role key is separated from the end-user anon key: IMPLEMENTED
- Account sidebar and sign-out control: IMPLEMENTED
- Existing v3.5.3 PDF compression retained: PASSED
- Existing v3.5.2 parser and Master Data retained unchanged: PASSED

Live SMS delivery requires the user's Supabase Phone provider and SMS provider credentials and therefore cannot be completed in the offline test environment.
