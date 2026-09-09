export function buildCacheKey(tenantId: string, reportId: string): string {
  // Isolate cached reports by tenant and report identifier.
  return `report:${tenantId}:${reportId}`;
}

export function cacheLifetimeSeconds(isPreview: boolean): number {
  return isPreview ? 30 : 300;
}
