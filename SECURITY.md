# Security checklist

Before enabling live trading:
- Change ADMIN_PASSWORD.
- Set a long random SECRET_KEY.
- Keep all broker keys in Render Environment Variables.
- Never commit `.env` or broker credentials.
- Test with paper accounts first.
- Use HTTPS only.
- Add 2FA and CSRF protection before opening the service to public users.
- Use PostgreSQL/persistent storage for production user/account data.
- Review the broker's terms, market-data permissions, and API limits.
- Review South African and any other applicable financial-services regulations before offering trading to customers.
