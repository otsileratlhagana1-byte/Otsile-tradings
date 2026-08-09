# Otsile Trading

A Render-ready Flask trading terminal inspired by the core workflow of MetaTrader 5.

## Included
- Secure login with hashed password
- Market Watch / custom watchlist
- Live broker quote hooks
- Interactive price chart
- Market and limit order ticket
- Buy / sell
- Quantity, limit price, stop-loss and take-profit fields
- Open positions
- Order/history panel
- Account/equity/buying-power panel
- Paper broker for safe testing
- Alpaca adapter for stocks/crypto
- OANDA v20 adapter for FX
- Render deployment configuration
- Otsile Trading logo
- Mobile responsive interface

## Important
This is NOT an MT5 replacement and it cannot automatically connect to a broker account without that broker's API credentials and permission. It also does not create a brokerage account, custody money, or guarantee execution.

Real-money trading is deliberately OFF by default.

### Paper mode
Set:
BROKER_MODE=paper
LIVE_TRADING_ENABLED=false

### Alpaca
Set:
BROKER_MODE=alpaca
ALPACA_API_KEY=...
ALPACA_SECRET_KEY=...
ALPACA_LIVE=false

When you have tested successfully, a live Alpaca connection can be enabled with:
ALPACA_LIVE=true
LIVE_TRADING_ENABLED=true

### OANDA
Set:
BROKER_MODE=oanda
OANDA_TOKEN=...
OANDA_ACCOUNT_ID=...
OANDA_LIVE=false

After testing:
OANDA_LIVE=true
LIVE_TRADING_ENABLED=true

Never put API keys into HTML/JavaScript. Store them only as Render environment variables.

## Deploy on Render
1. Upload this project to a GitHub repository.
2. In Render choose New -> Web Service and connect the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Set ADMIN_PASSWORD and SECRET_KEY.
6. Keep BROKER_MODE=paper until you have tested the terminal.
7. Add the broker credentials as environment variables only when ready.

Render supports Flask web services and the Gunicorn start command used above.

## Production upgrades recommended before handling public customer funds
- PostgreSQL instead of local SQLite
- Per-user broker account linking / OAuth where supported
- 2FA
- CSRF protection
- Rate limiting
- Audit logs
- WebSocket streaming
- Broker-specific symbol mapping
- Market-data licensing
- KYC/AML and financial-services compliance appropriate to your jurisdiction
- Order idempotency and reconciliation
- Persistent background workers
- Professional monitoring and backups
