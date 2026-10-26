# Synthetic fixtures

products.json powers the storefront. customers.json and orders.json are for the backend exercises (milestone 2 onward); they are deliberately not connected to the web app.

## Orders

Order snapshots use a fixed `referenceDate` of 2026-10-26 so evaluations do not change as time passes. All prices are EUR.

- `status` is `processing` or `delivered`. `deliveredAt` is `null` until delivery.
- `shippingPaid` is the outbound shipping the customer paid (€5 below €100, €0 at or above).
- Each item's `condition` and `tagsAttached` are recorded facts. Eligibility and refund amounts are not stored anywhere: your code computes them from the policies.

Each order is there to exercise something specific (outcomes are for you to work out):

| Order   | Customer | Delivered (day) | What it tests                                          |
| ------- | -------- | --------------- | ------------------------------------------------------ |
| TS-1001 | Alex     | 15 Oct (day 11) | Recent, unused, tags attached                          |
| TS-1002 | Alex     | 5 Oct (day 21)  | Inside the window, but used and without tags           |
| TS-1003 | Sam      | 20 Oct (day 6)  | An order belonging to a different customer             |
| TS-1004 | Alex     | not delivered   | Still processing                                       |
| TS-1005 | Alex     | 26 Sep (day 30) | The last day of the window                             |
| TS-1006 | Alex     | 25 Sep (day 31) | One day past the window                                |
| TS-1007 | Alex     | 10 Oct (day 16) | Two items in different conditions; €118, free shipping |

Never treat a browser-selected customer as authentication. Server tools must enforce identity and ownership on every operation. All addresses and orders here are fictional.
