# Telegram ID Bot - Production Ready

A comprehensive Telegram bot for selling Telegram accounts with session management, OTP handling, admin panel, and payment processing.

## Features

✅ **User Management**
- User registration and balance tracking
- Purchase history and transaction logs
- Deposit management with admin approval

✅ **Account Sales**
- Country-based Telegram account inventory
- Real-time OTP monitoring
- Session string generation
- 2FA password support

✅ **Admin Panel** (Web-based)
- Dashboard with statistics
- Country and account management
- Deposit approval workflow
- User balance adjustment
- Broadcast messaging

✅ **Advanced Features**
- Device/session management (Pyrogram)
- OTP interception and display
- Session generator with 2FA
- Admin broadcast to all users

✅ **Stability & Performance**
- 30-connection database pool
- Global error handlers (zero crashes)
- Request timeout protection (30s)
- Handles 100+ concurrent users

---

## Tech Stack

### Backend
- **Framework**: FastAPI + Aiogram (Bot)
- **Database**: PostgreSQL (Supabase)
- **ORM**: SQLAlchemy (async)
- **Session Management**: Pyrogram
- **Server**: Gunicorn + Uvicorn workers

### Frontend
- **Framework**: React + Vite
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **Routing**: React Router

### Deployment
- **Backend**: Koyeb (Docker)
- **Frontend**: Vercel
- **Database**: Supabase (PostgreSQL)

---

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/Devashishprog99/TELEGRAMIDBOT.git
cd TELEGRAMIDBOT
```

### 2. Configure Environment

Copy `deploy.env` and fill in your values:

```bash
cp deploy.env .env
# Edit .env with your credentials
```

### 3. Deploy Backend (Koyeb)

1. Create account on https://www.koyeb.com
2. Connect your GitHub repository
3. Set environment variables from `.env`
4. Deploy!

See [KOYEB_DEPLOYMENT.md](KOYEB_DEPLOYMENT.md) for detailed instructions.

### 4. Deploy Frontend (Vercel)

```bash
cd frontend
vercel
# Follow prompts
```

---

## Environment Variables

See `deploy.env` for full list. Key variables:

- `BOT_TOKEN` - Your Telegram bot token
- `DATABASE_URL` - PostgreSQL connection string
- `ADMIN_TELEGRAM_ID` - Your Telegram user ID
- `API_ID`, `API_HASH` - Telegram API credentials
- `BASE_WEBHOOK_URL` - Your Koyeb app URL

---

## Project Structure

```
├── backend/
│   ├── main.py              # FastAPI server & admin API
│   ├── bot.py               # Telegram bot handlers
│   ├── database.py          # DB connection & config
│   ├── models.py            # SQLAlchemy models
│   ├── session_manager.py   # OTP monitoring
│   ├── device_manager.py    # Session management
│   ├── broadcast.py         # Admin broadcast feature
│   └── requirements.txt     # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── pages/          # Admin panel pages
│   │   ├── components/     # React components
│   │   └── main.jsx        # App entry point
│   ├── package.json
│   └── vercel.json
│
├── Dockerfile              # Backend container config
├── Procfile               # Deployment config
└── deploy.env             # Environment template
```

---

## Admin Commands

- `/start` - Start bot
- `/broadcast` - Send message to all users (admin only)

---

## Features in Detail

### Session Management
Users can view and revoke active Telegram sessions for purchased accounts directly through the bot.

### OTP Monitoring
Real-time OTP code interception from Telegram's official notifications (777000).

### Admin Panel
Web-based dashboard for managing:
- Countries and pricing
- Account inventory
- User deposits and balance
- System statistics

### Broadcast System
Admin can send announcements to all users with progress tracking and delivery reports.

---

## Security Features

- ✅ Admin-only commands with Telegram ID verification
- ✅ JWT-based admin panel authentication
- ✅ Input validation on all endpoints
- ✅ Environment variable protection
- ✅ PostgreSQL with connection pooling

---

## Performance Optimizations

- **Database**: 30-connection pool with 10s timeout
- **Error Recovery**: Global error handlers prevent crashes
- **Request Timeout**: 30s max per request
- **Rate Limiting**: Built-in delays for broadcast
- **Logging**: Comprehensive logging for debugging

---

## Support

For issues or questions:
1. Check existing GitHub issues
2. Create new issue with details
3. Provide logs if applicable

---

## License

Private use only. Contact owner for licensing.

---

## Credits

Developed by @AKHILESCROW

---

## Deployment Status

- Backend: Koyeb [![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://www.koyeb.com)
- Frontend: Vercel [![Deploy](https://vercel.com/button)](https://vercel.com/import)

---

**Built with ❤️ for selling Telegram accounts efficiently**
