"""Tests for Ariston constants and derived values."""

from __future__ import annotations

from unittest.mock import MagicMock

from ariston.const import ConsumptionTimeInterval, ConsumptionType
from homeassistant.util import dt as dt_util

from custom_components.ariston.const import (
    _daily_energy,
    _energy_last_reset,
    _estimated_power,
)


def _entity(rated_power_w, is_heating):
    entity = MagicMock()
    entity.coordinator.rated_power_w = rated_power_w
    entity.device.is_heating = is_heating
    return entity


def test_estimated_power_disabled_without_rated_power():
    """No rated power configured means no power estimate."""
    assert _estimated_power(_entity(None, True)) is None


def test_estimated_power_while_heating():
    """The resistor draws the rated power while heating."""
    assert _estimated_power(_entity(1500, True)) == 1500


def test_estimated_power_while_idle():
    """No power draw when the water heater is not heating."""
    assert _estimated_power(_entity(1500, False)) == 0


def test_estimated_power_unknown_state():
    """A missing heating state is reported as no consumption."""
    assert _estimated_power(_entity(1500, None)) == 0


def _energy_entity(sequences):
    entity = MagicMock()
    entity.device.consumptions_sequences = sequences
    return entity


def test_daily_energy_sums_hourly_series():
    """Today's total is the sum of the hourly values, not the last one."""
    sequences = [
        {
            "k": ConsumptionType.DOMESTIC_HOT_WATER_ELECTRICITY.value,
            "p": ConsumptionTimeInterval.LAST_DAY.value,
            "v": [0, 0, 0.5, 1.25, 0, 0.25],
        }
    ]

    assert (
        _daily_energy(
            _energy_entity(sequences), ConsumptionType.DOMESTIC_HOT_WATER_ELECTRICITY
        )
        == 2.0
    )


def test_daily_energy_ignores_other_series():
    """Only the matching consumption type and period are used."""
    sequences = [
        {"k": ConsumptionType.CENTRAL_HEATING_GAS.value, "p": 2, "v": [5]},
        {
            "k": ConsumptionType.DOMESTIC_HOT_WATER_ELECTRICITY.value,
            "p": ConsumptionTimeInterval.LAST_WEEK.value,
            "v": [7],
        },
    ]

    assert (
        _daily_energy(
            _energy_entity(sequences), ConsumptionType.DOMESTIC_HOT_WATER_ELECTRICITY
        )
        is None
    )


def test_daily_energy_missing_series():
    """A device without metering has no consumption sequence."""
    assert (
        _daily_energy(
            _energy_entity([]), ConsumptionType.DOMESTIC_HOT_WATER_ELECTRICITY
        )
        is None
    )


def test_daily_energy_skips_empty_and_null_values():
    """Empty series and null samples do not break the sum."""
    sequences = [
        {
            "k": ConsumptionType.DOMESTIC_HOT_WATER_ELECTRICITY.value,
            "p": ConsumptionTimeInterval.LAST_DAY.value,
            "v": [None, 1.0],
        }
    ]

    assert (
        _daily_energy(
            _energy_entity(sequences), ConsumptionType.DOMESTIC_HOT_WATER_ELECTRICITY
        )
        == 1.0
    )
    sequences[0]["v"] = []
    assert (
        _daily_energy(
            _energy_entity(sequences), ConsumptionType.DOMESTIC_HOT_WATER_ELECTRICITY
        )
        is None
    )


def test_energy_last_reset_is_local_midnight():
    """Daily counters reset at the start of the local day."""
    last_reset = _energy_last_reset(_energy_entity([]))

    assert last_reset.tzinfo is not None
    assert (last_reset.hour, last_reset.minute, last_reset.second) == (0, 0, 0)
    assert last_reset.date() == dt_util.now().date()
