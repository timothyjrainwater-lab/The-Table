/**
 * Zone system — defines table zone boundaries and point-in-zone checks.
 *
 * Zones mirror the backend definitions in aidm/ui/table_objects.py.
 * The frontend uses these for optimistic constraint checking during drag.
 * Server remains authoritative.
 *
 * Authority: WO-UI-02, DOCTRINE_04_TABLE_UI_MEMO_V4.
 */

export interface ZoneDef {
  name: string;
  centerX: number;
  centerZ: number;
  halfWidth: number;
  halfHeight: number;
  color: number;
}

/**
 * Zone definitions matching addZone() calls in main.ts and backend _ZONE_BOUNDS.
 */
export const ZONES: ZoneDef[] = [
  { name: 'player', centerX: 0, centerZ: 3, halfWidth: 5, halfHeight: 0.75, color: 0x44ff88 },
  { name: 'map', centerX: 0, centerZ: -0.5, halfWidth: 3, halfHeight: 2, color: 0x4488ff },
  { name: 'dm', centerX: 0, centerZ: -3.5, halfWidth: 5, halfHeight: 0.75, color: 0xff4444 },
];

export const VALID_ZONE_NAMES = new Set(ZONES.map(z => z.name));

/**
 * Returns the zone name at (x, z), or null if outside all zones.
 * Checks in priority order: player, map, dm.
 */
export function zoneAtPosition(x: number, z: number): string | null {
  for (const z_ of ZONES) {
    if (
      x >= z_.centerX - z_.halfWidth && x <= z_.centerX + z_.halfWidth &&
      z >= z_.centerZ - z_.halfHeight && z <= z_.centerZ + z_.halfHeight
    ) {
      return z_.name;
    }
  }
  return null;
}

/**
 * Returns the ZoneDef for a given zone name, or undefined if not found.
 */
export function getZone(name: string): ZoneDef | undefined {
  return ZONES.find(z => z.name === name);
}
