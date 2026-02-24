/**
 * WS message payload types for events consumed by main.ts.
 *
 * These interfaces lock the shapes of stable, actively-consumed server→client
 * events. Unstable or no-payload events remain untyped at the bridge level.
 *
 * Source of truth: aidm/schemas/ws_protocol.py + aidm/schemas/box_events.py
 */

import type { KnowledgeState } from '../bestiary-bind';

// ---------------------------------------------------------------------------
// Rulebook
// ---------------------------------------------------------------------------

export interface RulebookOpenMsg {
  rule_ref?: string;
}

export interface RulebookSearchMsg {
  query?: string;
}

// ---------------------------------------------------------------------------
// Bestiary
// ---------------------------------------------------------------------------

export interface BestiaryRevealMsg {
  creature_id: string;
  knowledge_state: KnowledgeState;
  name?: string;
  traits?: string[];
  image_url?: string;
}

// ---------------------------------------------------------------------------
// Character sheet
// ---------------------------------------------------------------------------

export interface CharacterSheetUpdateMsg {
  entity_id: string;
  hp_current: number;
  hp_max: number;
  conditions: string[];
  spell_slots: Record<number, number>;
  spell_slots_max: Record<number, number>;
  abilities: Array<{ id: string; name: string; ready: boolean }>;
  attacks: Array<{ id: string; name: string; bonus: string; damage: string }>;
}

// ---------------------------------------------------------------------------
// Crystal Ball / TTS
// ---------------------------------------------------------------------------

export interface TtsSpeakingStartMsg {
  intensity?: number;
}

export interface NpcPortraitDisplayMsg {
  image_url?: string;
  clear?: boolean;
}

// ---------------------------------------------------------------------------
// Fog of War
// ---------------------------------------------------------------------------

export interface FogUpdateMsg {
  revealed_cells: Array<{ x: number; y: number }>;
  visible_cells: Array<{ x: number; y: number }>;
  map_bounds: { x: number; y: number; width: number; height: number };
}

// ---------------------------------------------------------------------------
// Scene image
// ---------------------------------------------------------------------------

export interface SceneImageMsg {
  image_url?: string;
}

// ---------------------------------------------------------------------------
// Notebook cover
// ---------------------------------------------------------------------------

export interface NotebookCoverNameMsg {
  player_name?: string;
}

export interface NotebookCoverImageMsg {
  image_url?: string;
}
