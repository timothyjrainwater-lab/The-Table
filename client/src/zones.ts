/**
 * Zone system — defines table zone boundaries and point-in-zone checks.
 *
 * Zone data loaded from aidm/ui/zones.json (single source of truth).
 * The frontend uses these for optimistic constraint checking during drag.
 * Server remains authoritative.
 *
 * Authority: WO-UI-02, WO-UI-ZONE-AUTHORITY, DOCTRINE_04_TABLE_UI_MEMO_V4.
 */

import zoneData from '../../aidm/ui/zones.json';

export interface ZoneDef {
  name: string;
  centerX: number;
  centerZ: number;
  halfWidth: number;
  halfHeight: number;
  color: number;
}

interface ZoneJsonEntry {
  name: string;
  centerX: number;
  centerZ: number;
  halfWidth: number;
  halfHeight: number;
  color: string;
}

/**
 * Zone definitions loaded from zones.json.
 * Color strings are parsed to numeric values for Three.js.
 */
export const ZONES: ZoneDef[] = (zoneData as ZoneJsonEntry[]).map(z => ({
  name: z.name,
  centerX: z.centerX,
  centerZ: z.centerZ,
  halfWidth: z.halfWidth,
  halfHeight: z.halfHeight,
  color: parseInt(z.color, 16),
}));

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
