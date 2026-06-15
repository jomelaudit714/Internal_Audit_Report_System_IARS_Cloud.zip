# Internal Audit Report System (IARS)

Cloud-ready web app for:
- Audit PDF upload
- PDF cloud storage
- Audit report archive
- Findings database
- Search by REF and Auditee Name
- Excel output
- Supabase database and storage

## Local Run

```cmd
pip install -r requirements.txt
python -m streamlit run app.py
```

## Cloud Setup

1. Create a Supabase project.
2. Run `supabase_schema.sql` in Supabase SQL Editor.
3. Create a private Supabase Storage bucket named `audit-pdfs`.
4. Add environment variables:
   - SUPABASE_URL
   - SUPABASE_SERVICE_ROLE_KEY
   - SUPABASE_BUCKET=audit-pdfs
5. Deploy to Streamlit Cloud, Render, or Railway.
6. Point `internalauditreportsystem.com` to the deployed app.

## Notes

This is a starter cloud-ready system. For production use, add:
- Proper login and role permissions
- Row-level security policies
- Admin user management
- Secure secrets management