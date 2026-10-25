"""Tests for Ariston constants and derived values."""

from __future__ import annotations

from unittest.mock import MagicMock

from custom_components.ariston.const import _estimated_power


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
