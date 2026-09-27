# RADAR SUPABASE SESSION POOLER HOST DISCOVERY V0.1 — 2026-09-27

Status: ONE-SHOT NON-SECRET NETWORK DISCOVERY

Purpose:
Discover the exact public Supavisor Session Pooler cluster host for project jqzdvgjeuveiktftyrlz without possessing or exposing a database password.

Current Supabase documentation explicitly distinguishes:
- wrong host / wrong tenant mapping -> "Tenant or user not found";
- valid shared-pooler username on the correct tenant with a wrong password -> "password authentication failed".

Frozen probe:
- region: eu-central-1
- mode: shared Supavisor Session Pooler
- port: 5432
- username: radar_runtime.jqzdvgjeuveiktftyrlz
- candidate hosts: aws-0 through aws-9 only
- SSL required
- one connection attempt per candidate maximum
- fixed intentionally invalid non-secret password
- stop at first documented password-authentication-failed signal
- no SQL is executed
- no valid credential is used
- no source/target mutation
- no password is logged
- no cutover authority
- no paid resource
- no main merge

Safety:
Repeated authentication attempts to the correct cluster are prohibited. A correct-cluster detection ends the scan immediately.
