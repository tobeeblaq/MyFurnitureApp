# CLAUDE.md

## Project
**MyFurnitureApp** — a buyer's web app for a furniture shop, built for Day 1 of a hackathon.

## Who this is for
The user has no coding background. Claude Code is responsible for picking the technology,
writing all the code, and explaining decisions in plain English. Keep changes simple,
readable, and well commented for a non-coder to follow along.

## What the app does
- A user logs in with a demo account (email + password).
- They browse a catalogue of furniture products (name, price, description, image).
- Each account has a total budget. As the user adds items to an order, the app shows
  how much of the budget is left.
- The user can only place an order if its total cost fits within their remaining budget.
- Placed orders are saved to the database and can be viewed in an order history page.

## Tech stack
- **Python 3 + Flask** — the web framework (handles pages and form submissions).
- **SQLite** — the database (a single file, `furniture.db`, no separate server needed).
- **Jinja2 templates** — plain HTML pages with small `{{ }}` placeholders for data.
- **Flask sessions + cookies** — simple hand-written login, no external auth service.
- **MongoDB (shared training database)** — one-time source for the product catalogue,
  pulled in by `seed_data.py` and copied into `furniture.db`. The app itself never talks
  to MongoDB at request time — only SQLite.
- Plain CSS for styling — no frontend framework or build step.

Why this stack: everything runs with a single command (`python app.py`), there's nothing
to install beyond a few `pip` packages, and there's no separate database server or
account to set up. That matters for a one-day hackathon demo running on a laptop.

## Folder structure
```
MyFurnitureApp/
├── app.py            # Flask routes: login, catalogue, place order, order history,
│                      #   product-image (serves each product's photo individually)
├── db.py             # database connection + queries (users, products, orders) +
│                      #   the table schema
├── seed_data.py       # creates tables, inserts demo users, and loads the product
│                      #   catalogue from MongoDB (falls back to a few placeholder
│                      #   products if MONGODB_URI isn't set or Mongo isn't reachable)
├── requirements.txt   # Python packages to install
├── .env               # local secrets - MONGODB_URI (gitignored, never committed)
├── .env.example       # template showing what .env needs
├── furniture.db       # SQLite database file (created by seed_data.py, not hand-edited)
├── templates/         # HTML pages rendered by Flask
│   ├── base.html       # shared layout (nav bar, budget display)
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
2. Copy `.env.example` to `.env` and fill in `MONGODB_URI` (ask whoever shared the
   training database credentials for the connection string).
3. `python seed_data.py` (first time only, and any time you want to re-sync the
   catalogue — creates the database, demo users, and loads products from MongoDB)
4. `python app.py`
5. Open `http://localhost:5000` in a browser

## Conventions for future changes
- Keep business logic (budget checks, order totals) in `db.py` or `app.py`, not in templates.
- Never hardcode secrets (connection strings, API keys) in code — put them in `.env`
  (gitignored) and read them with `os.environ` / `python-dotenv`.
- The product catalogue is synced from MongoDB by `seed_data.py`, not hand-edited in
  the database file. Placeholder products only appear as a fallback when MongoDB is
  unreachable.
- Favor explicit, readable code over clever shortcuts — this project prioritizes a
  non-coder being able to follow what changed and why.