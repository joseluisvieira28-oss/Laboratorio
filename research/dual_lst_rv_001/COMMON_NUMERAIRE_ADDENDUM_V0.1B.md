# DUAL-LST-RV-001 — COMMON NUMERAIRE ADDENDUM V0.1B

Frozen: 2026-09-27
Parent: SOURCE_DATA_GATE_FREEZE_V0.1 + SOURCE_GATE_HARDENING_ADDENDUM_V0.1A
Stage: SOURCE-ONLY / OUTCOME-BLIND

## Problem

rETH getExchangeRate is denominated in ETH per rETH.

wstETH stEthPerToken is denominated in stETH per wstETH.

A direct relative-NAV comparison requires a common protocol-accounting numeraire and must not silently assume a market stETH/ETH price of 1.

## Lido protocol accounting definition

Lido documentation defines stETH balances through protocol-controlled pooled ether and states that stETH totalSupply equals getTotalPooledEther.

Therefore this lab uses:

protocol_accounting_ETH_per_stETH =
getTotalPooledEther / stETH.totalSupply

and requires exact equality at every frozen sentinel.

When exact equality holds:
protocol_accounting_ETH_per_stETH = 1

and:

protocol_accounting_ETH_per_wstETH =
stEthPerToken * getTotalPooledEther / stETH.totalSupply

This is a PROTOCOL ACCOUNTING anchor only.
It is not a statement that market stETH/ETH trades at 1.

## Canonical stETH contract

Ethereum stETH:
0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84

Historical calls at all four sentinels:
- totalSupply()
- getTotalPooledEther()

NUMERAIRE_PASS at a sentinel requires:
- totalSupply > 0;
- getTotalPooledEther > 0;
- exact integer equality totalSupply == getTotalPooledEther.

If equality fails at any sentinel:
SOURCE_BLOCKED for this exact protocol-accounting relative-NAV definition.

No market-price substitution or synthetic stETH/ETH rescue is authorized.

## Frozen relative protocol anchor

Only if numeraire PASS:

relative_protocol_NAV_wstETH_per_rETH =
(ETH_per_rETH) / (ETH_per_wstETH)

where:
ETH_per_rETH = rETH.getExchangeRate / 1e18

ETH_per_wstETH =
wstETH.stEthPerToken / 1e18
* stETH.getTotalPooledEther / stETH.totalSupply

The source gate still opens no relative market outcomes, convergence results, direction, threshold, PnL or trading data.

## References

Lido contract documentation:
- https://docs.lido.fi/contracts/lido/
- https://docs.lido.fi/contracts/wsteth/

Promotion credit = 0.
