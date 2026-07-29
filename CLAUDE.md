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
- **Python 3 + Flask** — the web framework (handles pages and form submissions).
- **SQLite** — a single file, `furniture.db`, holding only our own login accounts
  (email + password hash). Nothing about products, balance, or orders lives here —
  see "Where the real data comes from" below.
- **The Day 1 furniture shop API** (`shop_api.py`) — the real source of truth for the
  catalogue, balance, and orders. See architecture.md for the endpoints used.
- **Azure OpenAI** (`agent.py`) — powers the "Ask the assistant" page. Calls the shop
  API through the same four tools, never talks to the shop directly.
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
├── app.py            # Flask routes: login, catalogue + balance, buy, order history,
│                      #   /assistant (the AI text box)
├── agent.py           # the AI shopping assistant: tool schemas, Azure OpenAI call,
│                      #   the tool-call loop
├── shop_api.py        # client for the real furniture shop API (catalogue, balance,
│                      #   orders) + typed errors (ProductNotFoundError,
│                      #   InsufficientBalanceError, ShopApiError)
├── db.py             # database connection + the users table (local login only)
├── seed_data.py       # creates the users table and inserts demo login accounts
├── requirements.txt   # Python packages to install
├── .env               # local secrets - shop API_KEY/SHOP_USER_ID, Azure OpenAI
│                      #   AZURE_ENDPOINT/API_VERSION/DEPLOYMENT/AZURE_API_KEY
│                      #   (gitignored, never committed)
├── .env.example       # template showing what .env needs
├── furniture.db       # SQLite database file (created by seed_data.py, not hand-edited)
├── templates/         # HTML pages rendered by Flask
│   ├── base.html       # shared layout (nav bar, balance display)
│   ├── login.html
│   ├── catalogue.html
│   ├── assistant.html  # the AI text box + reply + "what it did" trace
│   └── orders.html
├── static/
│   └── style.css
├── requirements.md    # what the app needs to do
└── architecture.md    # how it's built
```

## How to run it (once built)
1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in `API_KEY`/`SHOP_USER_ID` (from the Day 1
   Participant Guide) and `AZURE_ENDPOINT`/`API_VERSION`/`DEPLOYMENT`/`AZURE_API_KEY`
   (Azure OpenAI access, for the assistant page).
3. `python seed_data.py` (first time only — creates the database and demo login accounts)
4. `python app.py`
5. Open `http://localhost:5000` in a browser

## Conventions for future changes
- Keep business logic in `db.py`/`shop_api.py`/`agent.py`/`app.py`, not in templates.
- Never hardcode secrets (API keys, account ids) in code — put them in `.env`
  (gitignored) and read them with `os.environ` / `python-dotenv`. Note `API_KEY` (shop)
  and `AZURE_API_KEY` (Azure OpenAI) are separate variables — don't collide them.
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