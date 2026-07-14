from __future__ import annotations

from .models import AttackResult, Unit


def resolve_duel(attacker: Unit, defender: Unit) -> None:
    """Apply simultaneous damage for one duel."""
    attacker.damage += defender.level
    defender.damage += attacker.level


def resolve_attack(attackers: list[Unit], defenders: list[Unit]) -> AttackResult:
    """Resolve attackers in order. Each attacker attacks at most once."""
    living_defenders = list(defenders)
    for attacker in attackers:
        living_defenders = [unit for unit in living_defenders if unit.alive]
        if not living_defenders:
            break
        target = living_defenders[0]
        resolve_duel(attacker, target)
        living_defenders = [unit for unit in living_defenders if unit.alive]

    attacker_survivors = tuple(unit for unit in attackers if unit.alive)
    defender_survivors = tuple(unit for unit in defenders if unit.alive)
    success = not defender_survivors and bool(attacker_survivors)

    for unit in (*attacker_survivors, *defender_survivors):
        unit.damage = 0

    return AttackResult(success, attacker_survivors, defender_survivors)
