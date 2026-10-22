# Dispatch and billing fixture, version 1

Controlled Python source for RepoPilot's V4 repair baseline. No external packages.
Invoice overdue charges are one percent of the balance per overdue day, with a
30-day cap. Negative balances/days are invalid. Zero days incurs no fee.

Job submission must authenticate first, before any policy validation. Authorized
negative attempts must raise ValueError for both permanent and transient jobs.
Authorized permanent jobs with nonnegative attempts are rejected. Transient jobs
use exponential retry delays. The operations guide says delays cap at 60 seconds;
the implementation currently caps at 300 seconds. Product intent for this cap has
not been established. Do not choose either cap without an owner decision.
