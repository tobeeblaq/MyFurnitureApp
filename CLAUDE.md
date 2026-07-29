# CLAUDE.md

## Project
**MyFurnitureApp** — a buyer's web app for a furniture shop, built for Day 1 of a hackathon.

## Who this is for
The user has no coding background. Claude Code is responsible for picking the technology,
writing all the code, and explaining decisions in plain English. Keep changes simple,
readable, and well commented for a non-coder to follow along.

## What the app does
- A user logs in with a demo account (email + password) — this login is local to our app.
- They browse the real furniture catalogue (category, name, price), live from the Day 1
  furniture shop API.
- The page shows their real balance, also live from the shop API.
- Clicking "Buy" places a real order through the shop API (this actually spends the
  balance). Insufficient balance or a no-longer-available item shows a clear, friendly
  message instead of a crash or a raw error.
- Past orders are shown on an order history page, live from the shop API.

## Tech stack
- **Python 3 + Flask** — the web framework (handles pages and form submissions).
- **SQLite** — a single file, `furniture.db`, holding only our own login accounts
  (email + password hash). Nothing about products, balance, or orders lives here —
  see "Where the real data comes from" below.
- **The Day 1 furniture shop API** (`shop_api.py`) — the real source of truth for the
  catalogue, balance, and orders. See architecture.md for the endpoints used.
- **Jinja2 templates** — plain HTML pages with small `{{ }}` placeholders for data.
- **Flask sessions + cookies** — simple hand-written login, no external auth service.
- Plain CSS for styling — no frontend framework or build step.

Why this stack: everything runs with a single command (`python app.py`), there's nothing
to install beyond a few `pip` packages, and there's no separate database server or
account to set up. That matters for a one-day hackathon demo running on a laptop.

## Where the real data comes from
- **Catalogue** — `GET /catalogue/search-index` (category/name/price, no images — fast).
  Not `/catalogue`, which is image-heavy and slow.
- **Balance** — `GET /users/{user_id}`.
- **Buy** — `POST /orders`.
- **Order history** — `GET /orders/{user_id}`.

The shop API only has one real account for this whole training exercise. Every demo
login in our app (alice@, bob@) acts through the same `SHOP_USER_ID` — they'll see the
same balance and order history as each other, because underneath it's the same account.

## Folder structure
```
MyFurnitureApp/
├── app.py            # Flask routes: login, catalogue + balance, buy, order history
├── shop_api.py        # client for the real furniture shop API (catalogue, balance,
│                      #   orders) + typed errors (ProductNotFoundError,
│                      #   InsufficientBalanceError, ShopApiError)
├── db.py             # database connection + the users table (local login only)
├── seed_data.py       # creates the users table and inserts demo login accounts
├── requirements.txt   # Python packages to install
├── .env               # local secrets - API_KEY, SHOP_USER_ID (gitignored, never committed)
├── .env.example       # template showing what .env needs
├── furniture.db       # SQLite database file (created by seed_data.py, not hand-edited)
├── templates/         # HTML pages rendered by Flask
│   ├── base.html       # shared layout (nav bar, balance display)
│   ├── login.html
│   ├── catalogue.html
│   └── orders.html
├── static/
│   └── style.css
├── requirements.md    # what the app needs to do
└── architecture.md    # how it's built
```

## How to run it (once built)
1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in `API_KEY` and `SHOP_USER_ID` (from the
   Day 1 Participant Guide).
3. `python seed_data.py` (first time only — creates the database and demo login accounts)
4. `python app.py`
5. Open `http://localhost:5000` in a browser

## Conventions for future changes
- Keep business logic in `db.py`/`shop_api.py`/`app.py`, not in templates.
- Never hardcode secrets (API keys, account ids) in code — put them in `.env`
  (gitignored) and read them with `os.environ` / `python-dotenv`.
- Any call to the shop API can fail (network issue, item gone, insufficient balance) —
  catch `shop_api.ShopApiError` (and its subclasses) at the route level and flash a
  clear message. Never let a shop API error produce a raw Flask error page.
- Favor explicit, readable code over clever shortcuts — this project prioritizes a
  non-coder being able to follow what changed and why.
