# Synthetic fixtures

products.json powers the storefront. customers.json and orders.json are reserved for later backend exercises; they are deliberately not connected to the web app.

Order snapshots use a fixed referenceDate of 2026-10-26 so later evaluations do not change as time passes. All prices are EUR; refund eligibility and arithmetic must be implemented by you, not inferred from fixture labels.

Never treat a browser-selected customer as authentication. Future server tools must enforce identity and ownership on every operation. All addresses and orders here are fictional.
