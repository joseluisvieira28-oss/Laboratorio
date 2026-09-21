# Institutional source access constraints

## Environment audit

The environment contained no named entitlement or executable for LSEG/Refinitiv/Eikon,
Bloomberg, FactSet, Factiva, Econoday, Haver, Macrobond, or Trading Economics. Only names of
environment variables were inspected; no secret values were printed or stored.

No account was created, no trial was started, no identity was submitted, no paywall was
circumvented, and no subscription was purchased.

## Provider constraints

- Trading Economics requires an API subscription/key. Public documentation is readable,
  but target payload retrieval is not legitimately available in this environment.
- Reuters/LSEG Workspace/Eikon and Refinitiv datasets require licensed entitlement.
- Bloomberg requires a Terminal or enterprise/API entitlement.
- FactSet, Factiva, Econoday, Haver, and Macrobond require licensed access for the relevant
  archive/feed/API.
- Macrobond's point-in-time revision history and third-party data do not, by themselves,
  prove release-specific consensus field completeness.
- Factiva archives publications rather than a normalized economic consensus survey. It can
  prove an article existed before T0 only when the article itself is retrieved with metadata.

## What access alone would not solve

Even with a licence, acceptance requires an export or API response containing the target
event, exact field, consensus statistic/value, forecast-version timestamp strictly before
T0, timezone, provider identity, and immutable version/audit identifier. A current historical
calendar row is still insufficient.
