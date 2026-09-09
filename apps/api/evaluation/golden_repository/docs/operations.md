# Operations Guide

## Retry Policy

Failed outbound deliveries use exponential backoff. The delay doubles after each
failure and is capped at five minutes. Permanent authentication failures are not
retried.

## Database Recovery

Restore the most recent snapshot before replaying the transaction log. Verify
record counts before returning the service to traffic.
