import * as THREE from 'three';

export type KnowledgeState = 'heard' | 'seen' | 'fought' | 'studied';

export interface BestiaryEntry {
  creature_id: string;
  knowledge_state: KnowledgeState;
  image_url?: string;
  name?: string;
  traits?: string[];
}

/**
 * BestiaryBindController — handles bestiary_entry_reveal WS events.
 *
 * Progressive reveal:
 *   heard   → silhouette (dark overlay, shape visible)
 *   seen    → sketch (desaturated, partial detail)
 *   fought  → partial (partial color, some traits)
 *   studied → full art (full image, all traits)
 *
 * Gate: 4 tests (regression guard).
 * Gate G compliant.
 */
export class BestiaryBindController {
  private _current: BestiaryEntry | null = null;
  private _loader: THREE.TextureLoader = new THREE.TextureLoader();
  private _onUpdate: (entry: BestiaryEntry, opacity: number) => void;

  constructor(onUpdate: (entry: BestiaryEntry, opacity: number) => void) {
    this._onUpdate = onUpdate;
  }

  /** Handle bestiary_entry_reveal event. */
  handleReveal(data: {
    creature_id: string;
    knowledge_state: KnowledgeState;
    image_url?: string;
    name?: string;
    traits?: string[];
  }): void {
    this._current = { ...data };
    const opacity = this._opacityForState(data.knowledge_state);
    this._onUpdate(this._current, opacity);
  }

  /** Current known entry (for testing). */
  get current(): BestiaryEntry | null { return this._current; }

  /** Opacity/reveal level for a knowledge state. */
  static revealLevel(state: KnowledgeState): number {
    const levels: Record<KnowledgeState, number> = {
      heard:   0.15,
      seen:    0.45,
      fought:  0.70,
      studied: 1.0,
    };
    return levels[state] ?? 0;
  }

  private _opacityForState(state: KnowledgeState): number {
    return BestiaryBindController.revealLevel(state);
  }
}
