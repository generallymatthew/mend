# Stripe Checkout Setup (Headless Buying Flow)

Implements the "headless enterprise" commercial model from
[03_TECHNICAL_ARCHITECTURE_AND_WATCHER.md](03_TECHNICAL_ARCHITECTURE_AND_WATCHER.md#headless-enterprise-architecture-no-portal-no-accounts-email-only):
a buyer never creates an account or logs into anything Thimble operates.
They pick a tier on the static marketing site, pay on Stripe's own hosted
checkout, land on a static thank-you page, and everything after that —
access code, invoicing, support, the monthly digest — happens by email.

Two files are already built and committed in the repo root:

- `buy.html` — the pricing/checkout page, two tiers (company-wide flat
  tier, single-team pilot), each with a "Continue to checkout" button.
- `buy-thanks.html` — the static thank-you page Stripe redirects to.

Both are placeholders until a real Stripe account exists. **Creating the
Stripe account itself is something you need to do directly** — it needs
your own business/banking details and identity verification, which is
exactly the kind of account-creation and financial-credential step that
should never run through an AI agent. Everything below is what to do once
that account exists.

## 1. Create the account (you, not Claude)

Sign up at `stripe.com`, complete business verification, and set your
payout bank account. This is a one-time step.

**Legal/business name to use:** "Thimble" (Thimble LLC) — per the
2026-11-18 decision to register the LLC under that name rather than
"Mend." Use the same name on the business bank account so it matches
what you enter on Stripe; a mismatch between the Stripe account's legal
name and the receiving bank account's name is a common cause of delayed
or held payouts.

## 2. Create two Products

In the Stripe dashboard, **Product catalog → Add product**, create:

**Product A — "Thimble — Company-wide Access"**
- Pricing model: Standard pricing, recurring **monthly**
- Price: $5.00 / employee / month (so $500/month covers 100 employees) —
  updated 2026-11-17 down from an earlier $9k/yr ($7.50/seat) figure,
  since most companies won't come close to full simultaneous usage and
  the price should track actual expected load, not a per-seat enterprise
  rate. See [02_COMMERCIAL_PRICING_STRATEGY.md](02_COMMERCIAL_PRICING_STRATEGY.md)
  for the current numbers.
- Stripe Payment Links support an **adjustable quantity**, so you don't
  need a separate product per company size — see step 3.

**Product B — "Thimble — Single-Team Pilot"**
- Pricing model: Standard pricing, recurring
- Price: $20.00 / month

## 3. Create a Payment Link for each product

**Payment Links → New.** For each product:

- Select the product/price created above.
- For Product A only: under quantity, enable **"Customer can adjust
  quantity"** with a minimum of 1 — this is how a buyer sets their own
  employee count at checkout without you building a custom form. (If you
  used a flat $9,000 one-time price, skip the quantity toggle and instead
  offer a few fixed quantities, or just let the one price stand for the
  100-FTE benchmark and handle larger/smaller companies by email before
  sending them the link.)
- Collect customer info: turn on **"Phone number"** and require a
  **billing email** (on by default) — the billing email is the only
  identifier you need; there's no account behind it.
- After payment, under "After payment," choose **"Redirect to a website"**
  and set it to `https://withthimble.com/buy-thanks.html` (or whatever
  the live domain is once `buy.html`/`buy-thanks.html` are deployed there
  — see [project_trymend_domain.md] in memory for the domain status).
- Save, and copy the resulting Payment Link URL (looks like
  `https://buy.stripe.com/xxxxxxxxxxxx`).

## 4. Wire the real links into `buy.html`

Open `buy.html` and replace the two placeholder values:

```html
data-stripe-payment-link="REPLACE_WITH_STRIPE_PAYMENT_LINK_COMPANY"
```
```html
data-stripe-payment-link="REPLACE_WITH_STRIPE_PAYMENT_LINK_TEAM"
```

with the two real Payment Link URLs from step 3. Nothing else on the page
needs to change — the seat-count field on the company tier is cosmetic
(it only updates the displayed estimate); the actual billable quantity is
whatever the buyer sets on Stripe's own checkout page.

## 5. Turn on the payment notification

In Stripe, **Settings → Notifications**, make sure "Successful payments"
emails go to the inbox you'll be running the email-only relationship
from (`support@withthimble.com` — decided 2026-11-18 as the real support
address, not yet set up to receive mail anywhere; see
[33_EVIDENCE_STRATEGY_AND_BUYER_PERSONAS.md](33_EVIDENCE_STRATEGY_AND_BUYER_PERSONAS.md)
for why that inbox, not a ticketing system, is the whole support surface
for now). That email is your trigger to manually send the welcome/rollout
email — draft in
[../../pitch/outreach-emails.md](../../pitch/outreach-emails.md) — with
the buyer's access code.

No webhook, server, or backend is required for this first version. A
`checkout.session.completed` webhook that auto-generates and auto-sends
the access code is a reasonable automation to add later, once manual
volume justifies it — not needed to go live.

## What's still manual (by design)

- Generating each buyer's rotating access code or blind tokens.
- Sending the welcome/rollout email.
- Issuing invoices for anything outside Stripe's own receipt (Stripe's
  receipt email is usually sufficient; a separate PDF invoice is only
  needed if a buyer's AP department requires one).
- Revoking/rotating a code when a company asks for one (see the seat
  hygiene note in the architecture doc).

## Status

Scaffolding only — `buy.html` and `buy-thanks.html` exist and render, but
checkout does not actually work yet because no Stripe account or Payment
Link exists. Nothing on this page processes a real payment, creates a
real account, or should be treated as live until steps 1-4 above are done
by you.
