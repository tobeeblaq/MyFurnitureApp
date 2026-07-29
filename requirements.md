# Requirements

## User stories
- As a buyer, I can log in with an email and password so the app knows who I am.
- As a buyer, I can see my real balance as soon as I log in.
- As a buyer, I can browse the real furniture catalogue with category, name, and price.
- As a buyer, I can click "Buy" on a product (with a quantity) to place a real order.
- As a buyer, I cannot place an order that would put me over my balance - I see a
  clear message instead.
- As a buyer, if I try to buy something that's no longer available, I see a clear
  message instead of a crash.
- As a buyer, once I place an order, my balance goes down for real, and I can see it
  update on screen.
- As a buyer, I can view a list of my past orders.

## Functional requirements
1. **Login page** — email + password form. Wrong credentials show an error message.
   Successful login starts a session (the user stays logged in while browsing). This
   login is local to our app; it's separate from the shop account behind it.
2. **Catalogue page** — lists all products from the shop's search-index endpoint:
   category, name, price. Shows the buyer's real balance at the top of the page.
3. **Buy** — buyer picks a quantity and clicks "Buy" on a product, which places a
   real order through the shop API immediately (no local cart/checkout step).
4. **Order failures** — if the shop API rejects the order:
   - Insufficient balance → show "Insufficient balance for this order."
   - Item no longer exists → show "This item is no longer available."
   - Anything else (network issue, etc.) → show a clear message, never a raw error
     page or a crash.
5. **Order history page** — lists the buyer's past orders with date, items, and total,
   live from the shop API.
6. **Logout** — ends the session.

## Data the app needs to track
- **Users** (local, for our own login only): id, email, password (hashed, never
  stored in plain text).

Products, balance, and orders are **not** stored locally — they're fetched live from
the Day 1 furniture shop API on every page load. See architecture.md for the endpoints.

## Non-functional requirements
- Beginner-friendly to set up: one command to install, one command to seed demo
  login accounts, one command to run.
- Requires an internet connection and a valid API key to reach the shop API — the
  catalogue, balance, and orders are all real, live data, not local sample data.
- Simple enough to build and demo within a one-day hackathon.
- Clear error messages (e.g. "Insufficient balance for this order.") rather than
  silent failures or raw error pages.

## Out of scope for Day 1
- Payments / real checkout beyond what the shop API itself provides.
- Multiple concurrent shoppers on the same account (the shop API has one account
  for this whole exercise - every demo login shares its balance and order history).
- User self-registration (demo login accounts are pre-seeded instead).
- Admin panel for editing the catalogue (it's the shop's real, live catalogue).
