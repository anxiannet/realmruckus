from __future__ import annotations

import itertools
from dataclasses import replace

from .models import AttackResult, Unit


def resolve_duel(attacker: Unit, defender: Unit) -> None:
    """Apply simultaneous damage for one duel."""
    assert attacker.level is not None and defender.level is not None
    attacker.damage += defender.level
    defender.damage += attacker.level


def resolve_attack(attackers: list[Unit], defenders: list[Unit]) -> AttackResult:
    """Resolve one deterministic plan: given attacker order, target first live defender."""
    living_defenders = list(defenders)
    defeated_attackers: list[Unit] = []
    defeated_defenders: list[Unit] = []
    target_order: list[str] = []

    for attacker in attackers:
        living_defenders = [unit for unit in living_defenders if unit.alive]
        if not living_defenders:
            break
        target = living_defenders[0]
        target_order.append(target.mechanic_id)
        resolve_duel(attacker, target)
        if not attacker.alive:
            defeated_attackers.append(attacker)
        if not target.alive:
            defeated_defenders.append(target)
        living_defenders = [unit for unit in living_defenders if unit.alive]

    attacker_survivors = tuple(unit for unit in attackers if unit.alive)
    defender_survivors = tuple(unit for unit in defenders if unit.alive)
    success = not defender_survivors and bool(attacker_survivors)

    for unit in (*attacker_survivors, *defender_survivors):
        unit.damage = 0

    return AttackResult(
        success=success,
        attacker_survivors=attacker_survivors,
        defender_survivors=defender_survivors,
        attacker_defeated=tuple(defeated_attackers),
        defender_defeated=tuple(defeated_defenders),
        attack_order=tuple(unit.mechanic_id for unit in attackers),
        target_order=tuple(target_order),
    )


def generate_attack_results(
    attackers: list[Unit],
    defenders: list[Unit],
) -> tuple[AttackResult, ...]:
    """Enumerate attacker orders and every legal defender target sequence.

    Returned units are independent snapshots and do not mutate the input lists.
    """
    if not attackers or not defenders:
        return ()

    results: list[AttackResult] = []

    for attacker_order in itertools.permutations(range(len(attackers))):
        initial_attacker_damage = [0] * len(attackers)
        initial_defender_damage = [0] * len(defenders)

        def recurse(
            position: int,
            attacker_damage: list[int],
            defender_damage: list[int],
            target_indices: list[int],
        ) -> None:
            live_defenders = [
                index
                for index, unit in enumerate(defenders)
                if defender_damage[index] < int(unit.level)
            ]
            if position >= len(attacker_order) or not live_defenders:
                attacker_snapshots = [
                    replace(unit, damage=attacker_damage[index])
                    for index, unit in enumerate(attackers)
                ]
                defender_snapshots = [
                    replace(unit, damage=defender_damage[index])
                    for index, unit in enumerate(defenders)
                ]
                surviving_attackers = tuple(
                    unit for unit in attacker_snapshots if unit.alive
                )
                surviving_defenders = tuple(
                    unit for unit in defender_snapshots if unit.alive
                )
                defeated_attackers = tuple(
                    unit for unit in attacker_snapshots if not unit.alive
                )
                defeated_defenders = tuple(
                    unit for unit in defender_snapshots if not unit.alive
                )
                for unit in (*surviving_attackers, *surviving_defenders):
                    unit.damage = 0
                results.append(
                    AttackResult(
                        success=not surviving_defenders and bool(surviving_attackers),
                        attacker_survivors=surviving_attackers,
                        defender_survivors=surviving_defenders,
                        attacker_defeated=defeated_attackers,
                        defender_defeated=defeated_defenders,
                        attack_order=tuple(
                            attackers[index].mechanic_id for index in attacker_order
                        ),
                        target_order=tuple(
                            defenders[index].mechanic_id for index in target_indices
                        ),
                    )
                )
                return

            attacker_index = attacker_order[position]
            attacker = attackers[attacker_index]
            assert attacker.level is not None
            for defender_index in live_defenders:
                defender = defenders[defender_index]
                assert defender.level is not None
                next_attacker_damage = list(attacker_damage)
                next_defender_damage = list(defender_damage)
                next_attacker_damage[attacker_index] += defender.level
                next_defender_damage[defender_index] += attacker.level
                recurse(
                    position + 1,
                    next_attacker_damage,
                    next_defender_damage,
                    [*target_indices, defender_index],
                )

        recurse(0, initial_attacker_damage, initial_defender_damage, [])

    unique: dict[tuple[object, ...], AttackResult] = {}
    for result in results:
        key = (
            result.attack_order,
            result.target_order,
            tuple(sorted(unit.mechanic_id for unit in result.attacker_survivors)),
            tuple(sorted(unit.mechanic_id for unit in result.defender_survivors)),
        )
        unique[key] = result
    return tuple(unique.values())
