# ticketmy — Event Ticket Booking Demo

A Ticket2U Malaysia-inspired educational event ticketing app built with Flask, SQLite, server-rendered HTML templates, CSS, and minimal JavaScript. It is an independent demo and is not affiliated with Ticket2U. Payments are simulated; no card data is collected.

## Features

- Customer registration, login, logout, hashed passwords, and customer-only booking history.
- Search and browse active events, event detail pages, ticket type prices and remaining inventory.
- Booking flow with attendee details, quantity validation, total preview, simulated success/failure, unique booking reference, and e-ticket page.
- Admin dashboard to add/edit/remove events, manage ticket prices and inventory, and view all bookings.
- Foreign keys enabled, transaction-locked booking writes, availability recheck, and saved booking-time unit prices.
- Three-layer layout: routes/presentation, services/business logic, and database access.

## Requirements

- Python 3.10+
- pip

## Run locally

```bash
# 1. Extract the project and enter the folder
cd event_ticket_booking

# 2. Create and activate a virtual environment
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create the SQLite database, admin account, and sample events
python seed.py

# 5. Start the server
python run.py
```

Open http://127.0.0.1:5000

### Demo admin

- Email: `admin@ticketdemo.local`
- Password: `Admin123!`

The seed script is repeatable and will not overwrite an existing admin password. For a real deployment, set a strong `SECRET_KEY`, change/remove demo credentials, disable debug mode, and use HTTPS.

## Folder structure

```text
event_ticket_booking/
├── app/
│   ├── __init__.py
│   ├── models/
│   │   └── database.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── events.py
│   │   ├── bookings.py
│   │   └── admin.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── event_service.py
│   │   └── booking_service.py
│   ├── static/style.css
│   └── templates/
├── config.py
├── run.py
├── seed.py
└── requirements.txt
```

## Payment simulation and inventory behaviour

On the booking form, select either “Successful payment” or “Failed payment”. A successful simulated payment confirms the booking and deducts inventory. A failed simulated payment creates a failed booking/payment record for auditability but does not confirm the booking or deduct tickets. The booking, payment, and inventory change occur in one SQLite transaction.

Booking quantities are limited to 1–10 per booking. The server recalculates the price from the database; the browser total is only a convenience preview. A unique booking reference is generated server-side. Customers can only see their own booking records; admin routes require the admin role.

## Important production-hardening notes

This is a learning/demo implementation, not production-ready ticketing software. Before deployment, add CSRF protection (for example Flask-WTF), rate limiting and login throttling, email verification/password reset, stronger audit logging, tests, a production WSGI server, secure secret management, and proper payment-provider integration if real payments are ever needed. Do not use real payment card data in this demo.
