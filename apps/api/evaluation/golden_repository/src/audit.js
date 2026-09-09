export function redactAuditFields(event) {
  const { password, accessToken, ...safeFields } = event;
  return safeFields;
}

export function appendAuditTimestamp(event, timestamp) {
  return { ...event, recordedAt: timestamp };
}
