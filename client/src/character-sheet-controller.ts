/**
 * CharacterSheetController — manages character sheet live data binding.
 *
 * Receives character_sheet_update and entity_delta WS events.
 * Emits REQUEST_DECLARE_ACTION on spell/ability/attack row clicks.
 * Places QuestionStamp on right-click for rulebook navigation.
 *
 * Gate UI-CS: 12 tests.
 * Gate G compliant — deterministic only.
 */

export interface SheetAbility {
  id: string;
  name: string;
  ready: boolean;
}

export interface SheetAttack {
  id: string;
  name: string;
  bonus: string;
  damage: string;
}

export interface SheetState {
  entityId: string;
  hpCurrent: number;
  hpMax: number;
  conditions: string[];
  spellSlots: Record<number, number>;     // level → remaining
  spellSlotsMax: Record<number, number>;  // level → max
  abilities: SheetAbility[];
  attacks: SheetAttack[];
}

export type DeclareActionCallback = (actionId: string, entityId: string) => void;
export type QuestionStampCallback = (actionId: string, ruleRef: string) => void;

export class CharacterSheetController {
  private _state: SheetState | null = null;
  private _onDeclareAction: DeclareActionCallback;
  private _onQuestionStamp: QuestionStampCallback;

  constructor(
    onDeclareAction: DeclareActionCallback,
    onQuestionStamp: QuestionStampCallback,
  ) {
    this._onDeclareAction = onDeclareAction;
    this._onQuestionStamp = onQuestionStamp;
  }

  /** Process character_sheet_update WS event. */
  handleSheetUpdate(data: {
    entity_id: string;
    hp_current: number;
    hp_max: number;
    conditions: string[];
    spell_slots: Record<number, number>;
    spell_slots_max: Record<number, number>;
    abilities: Array<{ id: string; name: string; ready: boolean }>;
    attacks: Array<{ id: string; name: string; bonus: string; damage: string }>;
  }): void {
    this._state = {
      entityId: data.entity_id,
      hpCurrent: data.hp_current,
      hpMax: data.hp_max,
      conditions: [...data.conditions],
      spellSlots: { ...data.spell_slots },
      spellSlotsMax: { ...data.spell_slots_max },
      abilities: data.abilities.map(a => ({ ...a })),
      attacks: data.attacks.map(a => ({ ...a })),
    };
  }

  /** Process entity_delta hp/conditions update. */
  handleEntityDelta(entityId: string, changes: {
    hp_current?: number;
    conditions?: string[];
  }): void {
    if (!this._state || this._state.entityId !== entityId) return;
    if (changes.hp_current !== undefined) {
      this._state.hpCurrent = changes.hp_current;
    }
    if (changes.conditions !== undefined) {
      this._state.conditions = [...changes.conditions];
    }
  }

  /** Called when a spell/ability/attack row is clicked. */
  onSpellRowClick(actionId: string): void {
    if (!this._state) return;
    this._onDeclareAction(actionId, this._state.entityId);
  }

  /** Called when a spell/ability/attack row is right-clicked. */
  onRowRightClick(actionId: string, ruleRef: string): void {
    this._onQuestionStamp(actionId, ruleRef);
  }

  /** HP fraction (0.0–1.0) for bar rendering. */
  get hpFraction(): number {
    if (!this._state || this._state.hpMax === 0) return 0;
    return Math.max(0, Math.min(1, this._state.hpCurrent / this._state.hpMax));
  }

  /** Current sheet state (null if no update received yet). */
  get state(): SheetState | null {
    return this._state;
  }

  /** Spell slot pip state: returns {remaining, max} for a level. */
  getSpellSlotPips(level: number): { remaining: number; max: number } {
    if (!this._state) return { remaining: 0, max: 0 };
    return {
      remaining: this._state.spellSlots[level] ?? 0,
      max: this._state.spellSlotsMax[level] ?? 0,
    };
  }

  /** Whether a stat-block click should emit an action (always false — read-only). */
  isStatBlockClickable(): boolean {
    return false;
  }
}
