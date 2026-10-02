# MEXC EVENT FUTURES LAB — V0.6.4.2 NUMERIC TOKEN PARSER FIX

Date: 2026-10-02
Status: SOURCE-ONLY / TECHNICAL CORRECTION / READ-ONLY

## Reason

V0.6.4.1 still produced zero valid numeric pairs.

The audit log shows the Event Futures chart context contains text shaped like:

`... Open: 84,591.1 Close: 84,769.0 High: ...`

DOM formatting does not reliably place a newline after the Close value. The V0.6.4.1 parser captured all text until newline, so digits from subsequent fields could be concatenated into an invalid numeric token.

## Frozen correction

Only the numeric parser changes.

Immediately after the literal `Close:`, capture the first numeric token matching:

`[+-]?[0-9][0-9,]*(?:\.[0-9]+)?`

Directional/invisible Unicode marks and whitespace may occur between `Close:` and that token.

All original V0.6.4 scientific/source gates remain unchanged:
- five frozen assets;
- 12 observations per asset;
- ~2 seconds between observations;
- target 60 pairs;
- at least 55 valid pairs;
- >=95% within 1.0 bp;
- median difference <=0.25 bp;
- public GET endpoint unchanged;
- settlement equivalence remains NOT_PROVEN regardless of outcome.

No order, login, account request, non-GET request, or exchange mutation is permitted.
