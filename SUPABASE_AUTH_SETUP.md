# Supabase Phone Authentication Setup for IARS

IARS v3.6 uses Supabase Auth for phone-number and password access.

## 1. Add the anon/publishable key to Streamlit Secrets

Open **Supabase → Project Settings → API Keys** and copy the project's anon or publishable key.

Add this to **Streamlit → App settings → Secrets**:

```toml
[supabase_auth]
url = "https://YOUR-PROJECT.supabase.co"
anon_key = "YOUR-ANON-OR-PUBLISHABLE-KEY"
```

Keep the existing `[supabase]` service-role configuration for the private PDF archive. Do not place the service-role key in `[supabase_auth]`.

## 2. Enable phone authentication

In **Supabase → Authentication → Providers → Phone**:

1. Enable the Phone provider.
2. Enable phone confirmation so new users must enter the SMS code.
3. Configure an SMS provider supported by Supabase, such as Twilio, MessageBird, or Vonage.
4. Save the provider settings.

## 3. Test the three flows

- **Sign Up:** Full Name, Contact Number, Password, then six-digit SMS verification code.
- **Sign In:** Verified Contact Number and Password.
- **Forgot Password:** Contact Number, SMS verification code, then New Password.

Phone numbers entered as `09171234567`, `9171234567`, or `+639171234567` are normalized to `+639171234567`.

## Production security recommendations

- Restrict registration to approved employees or require administrator approval.
- Add role-based access: Admin, Audit Manager, Auditor, and Read Only.
- Enable CAPTCHA and appropriate Supabase Auth rate limits to reduce SMS abuse.
- Add an activity log for sign-ins, uploads, deletions, Master Data changes, and exports.
- Configure an inactivity timeout for shared office computers.
- Review SMS costs and delivery coverage before broad rollout.
