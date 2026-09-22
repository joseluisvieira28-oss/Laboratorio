CRYPTO EDGE RADAR — LOCAL FORWARD LOOP

Purpose:
Run the exact replay-safe public shadow ForwardShadowRuntime on an always-on
Windows machine without exposing an HTTP server.

Safety:
- No authenticated trading endpoints.
- No orders.
- No exchange mutation.
- No live capital.
- The launcher refuses to start unless RADAR_DATABASE_URL is already configured
  in the Windows environment.
- Never paste the database URL into this BAT file or commit it to Git.

Start:
  windows\START_FORWARD_LOOP_FAIL_CLOSED.bat

Stop:
  Press Ctrl+C in the console.

The default 30-second loop matches the canonical shadow runtime cadence.
Do not create a second concurrent local loop unless intentionally testing
idempotency. The Postgres event keys remain replay-safe, but duplicate source
polling is unnecessary.

This does not replace scientific timing authorities or promotion gates.
