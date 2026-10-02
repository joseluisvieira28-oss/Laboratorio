# MEXC EVENT FUTURES LAB — CURRENT PRODUCT HORIZON MATRIX CORRECTION V0.6.3.4

Date: 2026-10-02
Status: SOURCE-ONLY / TECHNICAL / READ-ONLY / FAIL-CLOSED

## New source fact

The public Event Futures selector is not identical across all five displayed underlyings in the current product UI.

Observed from the read-only V0.6.3.3 run:
- BTCUSDT: 10m / 30m / 1H / 1D
- ETHUSDT: 10m / 30m / 1H / 1D
- NVDAUSDT: 10m / 30m / 1H / 4H
- MUUSDT: 10m / 30m / 1H / 4H
- SPCXUSDT: 10m / 30m / 1H / 4H

The 10m label is unique to the Event Futures horizon group and is used only as a read-only DOM anchor.

This is a product/source correction, not a strategy change.

## V0.6.3.4 mission

Discover the exact current four-label Event Futures horizon set per asset directly from the validated public selector group, then collect exact current Up/Down payout for every currently offered asset × horizon cell.

Expected current matrix size:
5 assets × 4 horizons = 20 cells.

Do not require 1D when the public product currently exposes 4H instead.

## Read-only boundary

- public page only;
- GET navigation;
- exact horizon-selector clicks only;
- all POST/PUT/PATCH/DELETE aborted;
- no login;
- no amount;
- no Up/Down click;
- no order;
- no account mutation;
- no trading strategy;
- no merge to main.

## PASS rule

PASS_CURRENT_PRODUCT_MATRIX requires:
- four distinct Event Futures horizons discovered for every asset;
- numeric Up and Down payout captured for all 20 current product cells;
- each record carries observation UTC timestamp and DOM hash.

No profitability conclusion is allowed in this source gate.
