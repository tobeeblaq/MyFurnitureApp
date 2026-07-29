# Requirements

## User stories
- As a buyer, I can log in with an email and password so the app knows who I am.
- As a buyer, I can see my remaining budget as soon as I log in.
- As a buyer, I can browse a catalogue of furniture products with name, price,
  description, and an image.
- As a buyer, I can add a product and a quantity to my current order.
- As a buyer, I can see the running total of my current order compared to my
  remaining budget before I confirm it.
- As a buyer, I cannot place an order that would put me over my remaining budget.
- As a buyer, once I place an order, it's saved, and my remaining budget goes down
  by the order total.
- As a buyer, I can view a list of my past orders.

## Functional requirements
1. **Login page** — email + password form. Wrong credentials show an error message.
   Successful login starts a session (the user stays logged in while browsing).
2. **Catalogue page** — lists all products from the database: name, price,
   description, image. Shows the buyer's remaining budget at the top of the page.
3. **Order form** — buyer picks a product and a quantity, adds it to a running
   "cart" for the current order, and sees a live total.
4. **Budget validation** — when the buyer tries to confirm the order, the app
   checks: order total ≤ remaining budget. If it fails, show a clear error and
   don't save the order. If it passes, save the order and reduce the remaining
   budget.
5. **Order history page** — lists the buyer's past orders with date, items, and total.
6. **Logout** — ends the session.

## Data the app needs to track
- **Users**: id, email, password (hashed, never stored in plain text), total budget,
  amount already spent.
- **Products**: id, name, description, price, image.
- **Orders**: id, user, date placed, total cost.
- **Order items**: which products (and quantities) belong to each order.

## Non-functional requirements
- Beginner-friendly to set up: one command to install, one command to seed sample
  data, one command to run.
- Runs entirely on the user's own laptop — no paid service, no cloud account,
  no internet connection required after setup.
- Simple enough to build and demo within a one-day hackathon.
- Clear error messages (e.g. "This order would put you $42 over budget") rather
  than silent failures or raw error pages.

## Out of scope for Day 1
- Payments / real checkout.
- Multiple concurrent shoppers on the same account.
- User self-registration (demo accounts are pre-seeded instead).
- Admin panel for editing the catalogue (products are loaded from a shared
  MongoDB training database by `seed_data.py` - see architecture.md).