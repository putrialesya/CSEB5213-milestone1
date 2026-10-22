# Gather — Event Ticket Booking System

A small event-ticket booking web app built with **Python Flask + SQLite**. It includes customer registration/login, event browsing, booking management, a simulated payment checkout, and an admin dashboard for event management.

## Features

- Customer registration and login with Werkzeug password hashing
- Session-based login and role-protected admin routes
- Browse events, view venue/date/price/capacity, and choose ticket quantity
- Booking records with pending, paid, and failed payment states
- Simulated payment success/failure — **no real payments or card details**
- Booking receipt and booking history
- Admin create/edit/delete events and view recent bookings
- SQLite foreign keys, basic form CSRF tokens, input validation, responsive layout
- Sample events are added automatically on first run

## Requirements

- Python 3.10+
- pip

## Run locally

### 1. Extract and enter the project folder

```bash
cd event_ticket_booking
```

### 2. Create a virtual environment (recommended)

Windows:

```powershell
py -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set a secret key and admin credentials

Windows PowerShell:

```powershell
$env:SECRET_KEY = "replace-with-a-long-random-secret"
$env:ADMIN_EMAIL = "admin@example.com"
$env:ADMIN_PASSWORD = "ChangeThisAdminPassword!"
```

macOS/Linux:

```bash
export SECRET_KEY="replace-with-a-long-random-secret"
export ADMIN_EMAIL="admin@example.com"
export ADMIN_PASSWORD="ChangeThisAdminPassword!"
```

If you skip these variables, the local demo uses:
- Admin email: `admin@example.com`
- Admin password: `Admin123!`

**Change the default credentials before using the app beyond a local demo.** Admin is created only if that email does not already exist in the database.

### 5. Start the app

```bash
python app.py
```

Open http://127.0.0.1:5000 in your browser. The `events.db` SQLite database and sample events are created automatically.

## Typical demo flow

1. Register a customer account.
2. Open an event and choose 1–10 tickets.
3. The app creates a pending booking and opens simulated checkout.
4. Select **Simulate successful payment** to confirm the booking, or **Simulate declined payment** to mark it failed.
5. Open **My bookings** to view status and the receipt.
6. Log out and sign in with the admin account to create, edit, or delete events and inspect recent bookings.

## Routes

| Route | Purpose | Access |
|---|---|---|
| `/` | Browse events | Public |
| `/register` | Create customer account | Public |
| `/login` | Sign in | Public |
| `/events/<id>` | Event details and availability | Public |
| `/book/<id>` | Create a booking | Logged-in user |
| `/payment/<id>` | Simulated checkout | Booking owner |
| `/my-bookings` | Booking history | Logged-in user |
| `/booking/<id>` | Booking receipt | Booking owner |
| `/admin` | Admin dashboard | Admin |
| `/admin/events/new` | Create event | Admin |
| `/admin/events/<id>/edit` | Edit event | Admin |
| `/admin/events/<id>/delete` | Delete event without booking records | Admin |

## Important demo limitations

- The payment feature is **simulated only**. It must not be represented as a real payment integration.
- This is a starter/academic project, not a production ticketing platform. Before deployment, use a strong secret key, HTTPS, secure environment configuration, a proper CSRF library, rate limiting, logging, database migrations, and a real payment provider with verified webhooks.
- Capacity is checked when creating and paying for bookings, but a high-traffic production system should use stronger transaction/locking strategies and reservation expiry to prevent race conditions.
- The sample admin account is for local development only.
