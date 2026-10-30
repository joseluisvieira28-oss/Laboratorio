"""SPCX public Event10m status and index lineage fail-closed classification, no outcomes."""
def classify(receipt):
    c=receipt.get("futures") or {}
    i=receipt.get("index") or {}
    e=receipt.get("event") or {}
    if c.get("symbol")!="SPCXSTOCK_USDT" or c.get("status")!="FUTURES_CONTRACT_METADATA_PRESENT":
        return "FUTURES_SOURCE_BLOCKED"
    if i.get("symbol")!="SPCXSTOCK_USDT" or i.get("status")!="PUBLIC_INDEX_PRICE_PRESENT":
        return "INDEX_SOURCE_BLOCKED"
    if e.get("exact_matches")!=1 or 10 not in (e.get("minute_cycles") or []):
        return "EVENT_10M_NOT_PROVEN_AVAILABLE"
    if e.get("product_state")!="ONLINE":
        return "EVENT_10M_PAUSED_OR_UNAVAILABLE"
    if e.get("status")!="EXACT_PUBLIC_EVENT_PRODUCT_10M_PRESENT":
        return "EVENT_10M_NOT_EXECUTION_READY"
    if not all(receipt.get(k) is True for k in
       ("provider_defined_cash_to_tracker_relation_certified",
        "provider_defined_tracker_to_event_expiry_index_certified",
        "actual_event_server_openprice_settlement_parity_certified")):
        return "REFERENCE_PRICE_PARITY_NOT_CERTIFIED"
    return "PROSPECTIVE_SHADOW_SOURCE_ONLY__NOT_ECONOMIC_GO"
