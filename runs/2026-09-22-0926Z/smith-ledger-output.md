# SMITH-LEDGER reconciliation — 2026-09-22-0926Z

## Task
Investigate the standing SKHY lots/broker mismatch: `lots_sum 2.0` vs `broker_qty 3.0` (delta -1.0),
previously attributed to "1 share entered by a channel that does not email."

## Method
Read `lots.json` and `trades.json` for SKHY directly (no re-parse of settled rows).

`trades.json` SKHY rows (all `price_source: email_confirmed`), net qty_change sum:
5 (08-05 entry) + 1 (08-06 add) - 5 (08-07 stop) + 10 (08-07 rebuy) - 11 (08-18 stop-exit)
+ 3 (08-20 entry) + 2 (08-20 add) - 5 (08-24 stop-exit) + 5 (08-24 entry) - 5 (09-10 stop-trim)
+ 2 (09-21 add) = **2.0** net shares — matches `lots.json`'s single remaining lot (qty 2.0, dated
2026-09-21, price_source email_confirmed).

Live holdings (`holdings_full.fa13e4d7.json`, row 25) show **qty 3** for SKHY. `compute_book.json`
qty_changes flags `SKHY prior_qty 1 -> current_qty 3, ratio 3.0, likely_corporate_action: true` for
2026-09-21 — this is the script's raw quantity-diff heuristic, not a confirmed fill; it collides
with the already-known 1-share gap and is not itself new evidence (a corporate-action ratio flag on
a name with no corporate action in evidence is exactly the kind of guess Hard Rule 1/2 exist to
block).

## Gmail search — exhaustive, widened per instructions

1. `SKHY` (bare ticker) — 2 hits, both irrelevant (INDaily digest, Micron/SKHY IPO informational
   email).
2. `"SK Hynix" OR "SK hynix" OR hynix` — 37 hits. All 10 already-recorded transaction confirmations
   present (08-05 BUY 5, 08-06 BUY 1, 08-07 SELL 5 stop, 08-07 BUY 10, 08-18 SELL 11 stop, 08-20 BUY
   3, 08-20 BUY 2, 08-24 SELL 5 stop, 08-24 BUY 5, 09-10 SELL 5 stop, 09-21 BUY 2 — that's 11 listed,
   matches the 11 trades.json rows including the 09-21 one already in the ledger), plus 1 cancelled-
   order thread (2 cancelled Limit-buy notifications, 2026-09-18, correctly excluded per Hard Rule 4),
   plus assorted crypto-digest/newsletter noise mentioning "SK Hynix" as a market topic (not
   transactions).
3. Promotional/transfer/corporate-action language (`transfer OR bonus OR gift OR "dividend
   reinvest" OR DRIP OR fractional OR split OR spinoff OR "corporate action" OR reward OR promo OR
   referral OR credit`) combined with SKHY — 1 relevant hit: the 2026-07-10 "You hold Micron stock -
   Here's what SK Hynix's IPO means for you!" email. Read in full (`get_thread`, thread
   19f4c31423f307a5): purely an informational/marketing note about SK Hynix's Nasdaq IPO and its
   read-through for Micron holders. No share grant, no allocation, no transaction language of any
   kind. It also predates the account's first SKHY buy (2026-08-05) by nearly a month, so it cannot
   be the source of an extra share.
4. `from:transactions@transactions.indmoney.com (hynix OR SKHY OR "SK HYNIX") before:2026/08/06` —
   1 hit: the 08-05 19:55 BUY confirmation itself. No transaction confirmation of any kind predates
   the account's first SKHY position.
5. `from:transactions@transactions.indmoney.com subject:(cancelled OR successful) hynix` — 12
   threads: exactly the 10 successful fills already in trades.json plus the 1 cancelled-order thread
   (2 messages). No 13th confirmation exists.

**No new BUY, transfer, bonus-share, DRIP, or corporate-action confirmation was found anywhere in
the mailbox for SKHY.**

## Broker/corporate-action check

SKHY is a US ADR held through INDmoney's US book (not the Zerodha/Kite India book), and no Alpaca
or INDmoney-US corporate-actions tool is available in this environment — only the Kite MCP (India
equities) and the INDmoney holdings snapshot. The holdings snapshot carries no corporate-action
flag or note for SKHY beyond the bare qty=3. SK Hynix's ADR IPO'd on Nasdaq 2026-07-09; no split,
bonus-issue, or ADR-ratio-change news was found for it in this search, and no such event would
explain a single extra whole share against a cost-basis lot history that already nets cleanly to
2.0 shares from 10 explicit, email-confirmed fills.

## Verdict

**Still unresolved. No new evidence.** The 1-share gap (lots_sum 2.0 vs broker_qty 3.0) is
confirmed to rest on no missing email — every SKHY-related email in the mailbox, across every
wording tried, is accounted for and matches trades.json exactly. This is consistent with the prior
finding already in the knowledge base (`cc6ae1d6c6f5`, 2026-09-20: "the position is ... an
UNRECONCILED fill with no INDmoney success confirmation"). Per Hard Rule 1/2, the residue is left
as-is — not clamped, not reconstructed, not invented. `trades.json` and `lots.json` were NOT
modified.

## Recommendation (non-binding)

If the extra share genuinely arrived through a channel that doesn't email (e.g. a manual
correction, a broker-side rounding/reconciliation credit, or an out-of-band transfer the user
remembers making), the only way to close this cleanly is for the user to confirm it directly —
no further Gmail search is likely to surface it, since this search already covered ticker, company
name, cancelled-order noise, promotional language, and the full pre-position date range.
