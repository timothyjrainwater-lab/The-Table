/**
 * RulebookSearch — maps rulebook_search query strings to rule_refs.
 *
 * Fuzzy match: lowercased query substring against known rule_refs + aliases.
 * Falls back to first spread if no match.
 *
 * Gate: 3 tests (regression guard).
 * Gate G compliant.
 */

export interface RuleRef {
  ref: string;
  aliases: string[];
}

const KNOWN_REFS: RuleRef[] = [
  { ref: 'combat.attack_roll', aliases: ['attack', 'attack roll', 'to hit'] },
  { ref: 'combat.basics',      aliases: ['combat', 'basic combat', 'fighting'] },
  { ref: 'combat.actions',     aliases: ['actions', 'action types', 'standard action', 'move action'] },
  { ref: 'combat.action_types',aliases: ['full round', 'full-round', 'swift', 'immediate', 'free action'] },
  { ref: 'conditions',         aliases: ['conditions', 'status', 'blinded', 'fatigued', 'prone', 'stunned'] },
  { ref: 'conditions.list',    aliases: ['condition list', 'all conditions'] },
];

const DEFAULT_REF = 'combat.basics';

/**
 * Find the best matching rule_ref for a search query.
 * Returns DEFAULT_REF if no match found.
 */
export function searchRuleRef(query: string): string {
  const q = query.toLowerCase().trim();
  if (!q) return DEFAULT_REF;

  for (const entry of KNOWN_REFS) {
    if (entry.ref.includes(q)) return entry.ref;
    if (entry.aliases.some(a => a.includes(q) || q.includes(a))) return entry.ref;
  }

  return DEFAULT_REF;
}
