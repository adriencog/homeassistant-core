"""The tests for Netatmo switch."""

from unittest.mock import AsyncMock, patch

from syrupy.assertion import SnapshotAssertion

from homeassistant.components.alarm_control_panel import (
    DOMAIN as ALARM_DOMAIN,
    SERVICE_ALARM_ARM_AWAY,
    SERVICE_ALARM_DISARM,
)
from homeassistant.const import ATTR_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .common import selected_platforms

from tests.common import MockConfigEntry


async def test_entity(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    netatmo_auth: AsyncMock,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test entities."""
    # await snapshot_platform_entities(
    #     hass,
    #     config_entry,
    #     Platform.ALARM_CONTROL_PANEL,
    #     entity_registry,
    #     snapshot,
    # )
    with selected_platforms([Platform.ALARM_CONTROL_PANEL]):
        assert await hass.config_entries.async_setup(config_entry.entry_id)

        await hass.async_block_till_done()
    entity_entries = er.async_entries_for_config_entry(
        entity_registry, config_entry.entry_id
    )

    assert entity_entries
    for entity_entry in entity_entries:
        assert entity_entry == snapshot(name=f"{entity_entry.entity_id}-entry")
        assert hass.states.get(entity_entry.entity_id) == snapshot(
            name=f"{entity_entry.entity_id}-state"
        )


async def test_alarm_setup_and_services(
    hass: HomeAssistant, config_entry: MockConfigEntry, netatmo_auth: AsyncMock
) -> None:
    """Test setup and services."""
    with selected_platforms([Platform.ALARM_CONTROL_PANEL]):
        assert await hass.config_entries.async_setup(config_entry.entry_id)

        await hass.async_block_till_done()

    alarm_control_panel_entity = "alarm_control_panel.sirene_in_hall"

    assert hass.states.get(alarm_control_panel_entity).state == "disarmed"

    # Test disarming the alarm
    with patch("pyatmo.home.Home.async_set_persons_home") as mock_set_persons_home:
        await hass.services.async_call(
            ALARM_DOMAIN,
            SERVICE_ALARM_DISARM,
            {ATTR_ENTITY_ID: alarm_control_panel_entity},
            blocking=True,
        )
        await hass.async_block_till_done()
        mock_set_persons_home.assert_called_once_with(
            ["91827374-7e04-5298-83ad-a0cb8372dff1"]
        )

    # Test arming away the alarm
    with patch("pyatmo.home.Home.async_set_persons_away") as mock_set_persons_away:
        await hass.services.async_call(
            ALARM_DOMAIN,
            SERVICE_ALARM_ARM_AWAY,
            {ATTR_ENTITY_ID: alarm_control_panel_entity},
            blocking=True,
        )
        await hass.async_block_till_done()
        mock_set_persons_away.assert_called_once_with()
