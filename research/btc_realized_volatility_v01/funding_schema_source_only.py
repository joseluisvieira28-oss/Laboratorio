"""SOURCE-ONLY inspection of Binance 2021-01 funding CSV structure. No returns, trades or PnL."""
from collections import Counter
import datetime as dt
from rv_v1_engine import verified_rows,HOUR,ts_ms

receipt=[]
rs=verified_rows("fundingRate/BTCUSDT","BTCUSDT-fundingRate-2021-01.zip",receipt)
print("FUNDING_SOURCE_SCHEMA_ONLY")
print("published_sha256",receipt[0]["publisher_sha256"])
print("total_rows",len(rs))
print("header_redacted_rate_values",rs[0][:10])
numeric = [r for r in rs[1:] if r and r[0].strip().isdigit()]
print("rows_numeric_first_column",len(numeric))
print("column_count_hist",dict(Counter(map(len,rs))))
for i,r in enumerate(numeric[:6]):
    print("record",i,"time_candidate",r[0],
          "modulo_1h_ms",int(r[0]) % HOUR,
          "candidate_cols_1_2_type",[
            ("integer" if field.strip().isdigit() else "float_or_text")
            for field in r[1:3]])
print("source_semantics_not_outcomes")
