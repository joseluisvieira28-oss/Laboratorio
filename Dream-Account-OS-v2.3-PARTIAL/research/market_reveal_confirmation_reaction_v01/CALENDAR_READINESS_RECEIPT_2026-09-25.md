# MRCR V0.1 — Calendar Readiness Receipt
As of: 2026-09-25

## Official-source status

Federal Reserve:
- the official FOMC page lists eight 2027 meetings;
- the Federal Reserve explicitly states each listed 2027 meeting date is tentative
  until confirmed at the immediately preceding meeting.

BLS Consumer Price Index:
- the official CPI schedule currently lists releases only through the November
  2026 reference month / December 10, 2026 release;
- no complete official 2027 CPI release schedule is present.

BLS Employment Situation:
- the official Employment Situation schedule currently lists releases only
  through the November 2026 reference month / December 4, 2026 release;
- no complete official 2027 Employment Situation schedule is present.

## Gate state

FOMC_2027 = AVAILABLE_TENTATIVE_OFFICIAL
CPI_2027 = NOT_COMPLETE_OFFICIAL
EMPLOYMENT_SITUATION_2027 = NOT_COMPLETE_OFFICIAL
COMPLETE_OFFICIAL_PROSPECTIVE_CALENDAR = FAIL_CLOSED

This receipt is a calendar-readiness check only. It does not select event
families for MRCR and does not authorize H02 or target observation.
