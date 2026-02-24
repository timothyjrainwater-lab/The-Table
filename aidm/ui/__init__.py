"""UI module — Table UI protocol types and zone authority.

Components:
- table_objects: TableObjectState, ObjectPositionUpdate, TableObjectRegistry,
                 validate_zone_position, zone_for_position, VALID_ZONES
- pending: PendingRoll, PendingPoint, DeclareActionIntent, DiceTowerDropIntent,
           PendingStateMachine
- ws_protocol: MESSAGE_REGISTRY, RollResult, parse_message
- camera: (Python-side camera authority stubs, if any)

Authority: WO-UI-02, WO-UI-03, WO-UI-04, WO-UI-ZONE-AUTHORITY,
    DOCTRINE_04_TABLE_UI_MEMO_V4.
"""
