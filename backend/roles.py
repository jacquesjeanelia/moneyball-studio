"""Map the dataset's granular position vocabulary to the three broad roles the
UI colour-codes, groups (percentile cohorts) and filters by.

The `main_position` column stores the full category label (e.g. "Center Back",
"Striker").  `broad_role()` resolves it to one of "Attack" / "Midfield" /
"Defender" for the frontend, and falls back to the short position code map
only when the label is absent or unrecognised.
"""

ATTACK = "Attack"
MIDFIELD = "Midfield"
DEFENDER = "Defender"

# Specific category label (lower-cased) -> broad role.
_CATEGORY_TO_ROLE = {
    "striker": ATTACK,
    "forward": ATTACK,
    "left winger": ATTACK,
    "right winger": ATTACK,
    "attacking midfielder": MIDFIELD,
    "central midfielder": MIDFIELD,
    "defensive midfielder": MIDFIELD,
    "left midfielder": MIDFIELD,
    "right midfielder": MIDFIELD,
    "midfielder": MIDFIELD,
    "center back": DEFENDER,
    "centre back": DEFENDER,
    "left back": DEFENDER,
    "right back": DEFENDER,
    "left wing-back": DEFENDER,
    "right wing-back": DEFENDER,
    "defender": DEFENDER,
}

# Short position code -> broad role (fallback when category is missing/unknown).
_POSITION_TO_ROLE = {
    "ST": ATTACK, "CF": ATTACK, "LW": ATTACK, "RW": ATTACK,
    "AM": MIDFIELD, "CAM": MIDFIELD, "CM": MIDFIELD, "DM": MIDFIELD, "CDM": MIDFIELD,
    "LM": MIDFIELD, "RM": MIDFIELD,
    "CB": DEFENDER, "LB": DEFENDER, "RB": DEFENDER, "LWB": DEFENDER, "RWB": DEFENDER,
}


def broad_role(main_position: str | None) -> str | None:
    """Resolve a player's broad role from their main_position value.

    ``main_position`` stores the full label (e.g. "Center Back", "Striker")
    which is looked up in ``_CATEGORY_TO_ROLE`` first.  If that fails we
    treat the value as a short code (e.g. "CB", "ST") via ``_POSITION_TO_ROLE``.
    """
    if main_position:
        val = main_position.strip()
        role = _CATEGORY_TO_ROLE.get(val.lower())
        if role:
            return role
        return _POSITION_TO_ROLE.get(val.upper())
    return None


def role_categories(role: str) -> list[str]:
    """Specific category labels (lower-cased) that map to a broad role."""
    return [k for k, v in _CATEGORY_TO_ROLE.items() if v == role]


def role_positions(role: str) -> list[str]:
    """Short position codes that map to a broad role."""
    return [k for k, v in _POSITION_TO_ROLE.items() if v == role]


# Specific role groups — the five narrow roles the UI uses for role-specific
# radar views.
_SPECIFIC_ROLES = {
    "ST": "Striker",
    "LW": "Creative Attacker", "RW": "Creative Attacker",
    "LM": "Creative Attacker", "RM": "Creative Attacker",
    "AM": "Creative Attacker", "CAM": "Creative Attacker",
    "CM": "Midfielder", "DM": "Midfielder", "CDM": "Midfielder",
    "LB": "Fullback", "RB": "Fullback", "LWB": "Fullback", "RWB": "Fullback",
    "CB": "Center Back",
}


def specific_role(main_position: str | None) -> str | None:
    """Resolve a player's specific role group from their main position code.
    Returns None when the position is not recognised."""
    if not main_position:
        return None
    return _SPECIFIC_ROLES.get(main_position.strip().upper())


def clean_position(code: str | None) -> str | None:
    """Normalise a main-position code, treating ingestion artifacts ("{}", "")
    as missing."""
    if not code:
        return None
    code = code.strip()
    if code in ("{}", "[]", "None"):
        return None
    return code or None
