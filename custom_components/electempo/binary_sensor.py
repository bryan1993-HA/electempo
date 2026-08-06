"""Binary sensor platform for the ElecTempo integration (HC/HP)."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME
from .coordinator import ElecTempoCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ElecTempoCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ElecTempoHCBinarySensor(coordinator, entry)])


class ElecTempoHCBinarySensor(CoordinatorEntity[ElecTempoCoordinator], BinarySensorEntity):
    """True = Heures Creuses (off-peak), False = Heures Pleines (peak)."""

    _attr_has_entity_name = True
    _attr_name = "Heures Creuses"
    _attr_icon = "mdi:clock-time-four-outline"

    def __init__(
        self,
        coordinator: ElecTempoCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_heures_creuses"
        power = entry.data.get("contract_power", "?")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=NAME,
            manufacturer="bryan1993-HA",
            model=f"EDF Tempo {power} kVA",
        )

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("est_hc")

    @property
    def extra_state_attributes(self) -> dict:
        data = self.coordinator.data
        if data is None:
            return {}
        return {
            "couleur_actuelle": data.get("couleur_actuelle"),
            "tarif_actuel": data.get("tarif_actuel"),
        }
