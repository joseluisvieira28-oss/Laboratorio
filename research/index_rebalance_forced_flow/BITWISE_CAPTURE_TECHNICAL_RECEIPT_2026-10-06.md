# Bitwise capture parser technical correction
Date: 2026-10-06.
Initial source-only run 37423751766 returned CAPTURE_BLOCKED / unrecognized notification layout.
HTML splits the footer into separate text nodes: "A team of", "crypto", "experts at your fingertips.".
Join visible text nodes with spaces rather than newlines before bounding the notice. No dates, asset actions or gate rules change.
Public source inspection identified this error; no Bitwise market outcomes were opened.
This does not alter CD20 discovery run 37423771026 or its NO_EDGE_DISCOVERY. Never rerun the economic discovery.
Collector repaired for prospective metadata capture only. Stale September 2026 notice remains ineligible.
