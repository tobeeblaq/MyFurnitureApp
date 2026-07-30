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
- An "Ask the assistant" page has a text box for a plain-English request. An AI
  agent (`agent.py`) answers using tools over the shop API: search the catalogue,
  look up one product, check balance, propose an order, confirm and place an
  order. Buying is always two messages: the agent proposes the item and price
  first, and only places the real order once a later message confirms it.

## Tech stack
- **Python 3 + Flask** — the backend. Owns all the real logic: login, the shop API
  client, and the AI agent. Exposes it two ways at once (see below).
- **A Next.js (TypeScript, React, App Router) frontend** (`frontend/`) — the primary
  UI. Talks to Flask only through the JSON API in `api.py`, never directly to the
  shop API or Azure OpenAI.
- **SQLite** — a single file, `furniture.db`, holding only our own login accounts
  (email + password hash). Nothing about products, balance, or orders lives here —
  see "Where the real data comes from" below.
- **The Day 1 furniture shop API** (`shop_api.py`) — the real source of truth for the
  catalogue, balance, and orders. See architecture.md for the endpoints used.
- **Azure OpenAI** (`agent.py`) — powers the "Ask the assistant" page. Calls the shop
  API through the same four tools, never talks to the shop directly.
- **Flask sessions + cookies** — simple hand-written login, no external auth service.
  The Next.js frontend runs on a different port, so Flask uses CORS
  (`flask-cors`, `supports_credentials=True`) to accept it and let the session
  cookie travel with each request.
- **Jinja2 templates** (`templates/`) — the *original* server-rendered pages
  (login/catalogue/assistant/orders). Still there and still work on their own at
  `http://localhost:5000` - kept as a simple, dependency-free fallback UI, but the
  Next.js frontend is what you should build new features against going forward.

Why this split: Flask alone runs with one command and nothing beyond `pip`, which
matters for a one-day hackathon demo - but the frontend needed to be Next.js (for
deploying somewhere Next.js-friendly, e.g. Vercel). Keeping all the real logic in
Flask and making the frontend a thin JSON-API client means the frontend can deploy
independently without re-implementing login, the shop API client, or the agent in
JavaScript.

## Where the real data comes from
- **Catalogue** — `GET /catalogue/search-index` (category/name/price, no images — fast).
  Not `/catalogue`, which is image-heavy and slow.
- **Balance** — `GET /users/{user_id}`.
- **Buy** — `POST /orders`.
- **Order history** — `GET /orders/{user_id}`.

The shop API only has one real account for this whole training exercise. Every demo
login in our app (alice@, bob@) acts through the same `SHOP_USER_ID` — they'll see the
same balance and order history as each other, because underneath it's the same account.

## The AI assistant's tools
`agent.py` gives the model these tools, each calling straight into `shop_api.py`:

| Tool | Calls | Can't do |
|---|---|---|
| `search_catalogue` | `GET /catalogue/search-index` | No price/colour/"vibe" filter — only an exact category name. The agent must fetch and judge results itself for anything else. |
| `get_product` | `GET /catalogue/{item_id}` | Needs an exact `item_id` — not for searching. |
| `check_balance` | `GET /users/{user_id}` | One shared account, not per-app-user. |
| `propose_order` | `GET /catalogue/{item_id}` (price lookup only) | Doesn't charge anything — just describes what buying would cost. |
| `confirm_and_place_order` | `POST /orders` | Real, immediate charge, no undo. Only works on a proposal from an *earlier* message — see below. |

Tool failures (bad item, insufficient balance, network error) are turned into a plain
`{"error": "..."}` the model sees and replies to — never left to crash the page.

**Buying is enforced as two steps, not just prompted as two steps.** `agent.ask()`
takes a `pending_purchase` (whatever `propose_order` returned last time, or `None`)
and fixes it as the *only* thing `confirm_and_place_order` may act on for this
request. `propose_order` can only update what gets persisted for the *next* request —
it can never make the current request's confirmation check pass. So even if the model
calls both tools in the same reply (whether by mistake or an adversarial prompt), the
confirm is rejected — a purchase can never be proposed and executed without a real
round-trip back to the user in between.

**Retrying a failed confirm is safe.** Each proposal gets one `idempotency_key`
(generated once, in `propose_order`), reused for every confirm attempt on it. If a
confirm call times out without telling us whether it went through, the proposal stays
pending with the same key — retrying returns the original result instead of charging
twice (this is the shop API's own `Idempotency-Key` contract).

## Folder structure
```
MyFurnitureApp/
├── app.py            # Flask HTML routes (the original pages) + CORS setup +
│                      #   registers the JSON API from api.py
├── api.py             # JSON API for the Next.js frontend: /api/me, /api/login,
│                      #   /api/logout, /api/catalogue, /api/buy, /api/assistant,
│                      #   /api/orders - same business logic as app.py's HTML routes
├── agent.py           # the AI shopping assistant: tool schemas, Azure OpenAI call,
│                      #   the tool-call loop
├── shop_api.py        # client for the real furniture shop API (catalogue, balance,
│                      #   orders) + typed errors (ProductNotFoundError,
│                      #   InsufficientBalanceError, ShopApiError)
├── db.py             # database connection + the users table (local login only)
├── seed_data.py       # creates the users table and inserts demo login accounts
├── requirements.txt   # Python packages to install (now incl. flask-cors)
├── .env               # local secrets - shop API_KEY/SHOP_USER_ID, Azure OpenAI
│                      #   AZURE_ENDPOINT/API_VERSION/DEPLOYMENT/AZURE_API_KEY,
│                      #   FRONTEND_ORIGIN (gitignored, never committed)
├── .env.example       # template showing what .env needs
├── furniture.db       # SQLite database file (created by seed_data.py, not hand-edited)
├── templates/         # the original server-rendered HTML pages (still work standalone)
│   ├── base.html
│   ├── login.html
│   ├── catalogue.html
│   ├── assistant.html
│   └── orders.html
├── static/
│   └── style.css
├── frontend/          # the Next.js app - the primary UI (see its own layout below)
├── requirements.md    # what the app needs to do
└── architecture.md    # how it's built
```

`frontend/` (Next.js, TypeScript, App Router):
```
frontend/
├── src/app/
│   ├── layout.tsx      # root layout: fonts, <AuthProvider><AppShell>
│   ├── globals.css      # the same design system as static/style.css, ported to CSS
│   ├── page.tsx         # catalogue/home page ("/")
│   ├── login/page.tsx
│   ├── assistant/page.tsx
│   └── orders/page.tsx
├── src/components/
│   ├── AppShell.tsx      # header/nav/balance/logout + footer, reads auth from context
│   ├── ProductCard.tsx
│   └── ErrorBanner.tsx
├── src/lib/
│   ├── api.ts            # fetch wrapper for every /api/* call (credentials: "include")
│   ├── AuthContext.tsx    # fetches /api/me once, shares {email, balance} app-wide
│   ├── useRequireAuth.ts  # redirects to /login if not authenticated
│   └── formatReply.tsx    # renders the agent's bullet-style replies as real <ul><li>
├── .env.local          # NEXT_PUBLIC_API_BASE_URL (gitignored)
└── .env.local.example
```

## How to run it (once built)
This is now two servers - start both.

**Backend (Flask):**
1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in `API_KEY`/`SHOP_USER_ID` (from the Day 1
   Participant Guide) and `AZURE_ENDPOINT`/`API_VERSION`/`DEPLOYMENT`/`AZURE_API_KEY`
   (Azure OpenAI access, for the assistant page).
3. `python seed_data.py` (first time only — creates the database and demo login accounts)
4. `python app.py` (serves the JSON API, and the original pages, at `:5000`)

**Frontend (Next.js) - in a second terminal:**
1. `cd frontend && npm install`
2. Copy `.env.local.example` to `.env.local` (default already points at the local
   Flask backend)
3. `npm run dev`
4. Open `http://localhost:3000` in a browser

(The original pages still work directly at `http://localhost:5000` too, without
needing Node at all.)

## Conventions for future changes
- Keep business logic in `db.py`/`shop_api.py`/`agent.py`/`app.py`/`api.py`, not in
  templates or in the Next.js frontend. The frontend should only ever call `/api/*`
  and render what comes back - no shop API or Azure OpenAI calls from JavaScript.
- `api.py` never imports from `app.py` (`from app import app` would re-execute
  app.py as a second module when Flask is run directly, registering routes on a
  throwaway second Flask instance that never actually serves). Instead, `api.py`
  exposes `register_api_routes(app, current_user, shop_user_id)`, and `app.py` calls
  it after those are defined.
- Never hardcode secrets (API keys, account ids) in code — put them in `.env`
  (gitignored) and read them with `os.environ` / `python-dotenv`. Note `API_KEY` (shop)
  and `AZURE_API_KEY` (Azure OpenAI) are separate variables — don't collide them.
- If you add a new page to the Next.js frontend, add the matching JSON endpoint to
  `api.py` first, the same way the existing pages each have one.
- Any call to the shop API can fail (network issue, item gone, insufficient balance) —
  catch `shop_api.ShopApiError` (and its subclasses) at the route level and flash a
  clear message. Never let a shop API error produce a raw Flask error page. The same
  goes for `agent.AgentError` around calls to `agent.ask(...)`.
- Don't collapse `propose_order`/`confirm_and_place_order` back into one step, and
  don't generate a fresh idempotency key per confirm attempt — both exist specifically
  so a purchase always needs a real round-trip to the user, and a retry after a
  dropped connection can't double-charge.
- Favor explicit, readable code over clever shortcuts — this project prioritizes a
  non-coder being able to follow what changed and why.
- Always update `requirements.md` after any change that affects what the app does.
- Use short, plain words in responses — this project is for a non-coder.