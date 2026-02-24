# CP-22 patch script for maneuver_resolver.py
L = []
L.append('def resolve_grapple(')
L.append('    intent,')
L.append('    world_state,')
L.append('    rng,')
L.append('    next_event_id,')
L.append('    timestamp,')
L.append('    aoo_events=None,')
L.append('    aoo_defeated=False,')
L.append('    aoo_dealt_damage=False,')
L.append('    causal_chain_id=None,')
L.append('):')