"""Sensor platform for the ElecTempo integration."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME
from .coordinator import ElecTempoCoordinator

CURRENCY_EUR_KWH = "€/kWh"


@dataclass(frozen=True, kw_only=True)
class ElecTempoSensorDescription(SensorEntityDescription):
    data_key: str
    sub_key: str | None = None


SENSOR_DESCRIPTIONS: tuple[ElecTempoSensorDescription, ...] = (
    ElecTempoSensorDescription(
        key="couleur_actuelle",
        data_key="couleur_actuelle",
        name="Couleur actuelle",
        icon="mdi:palette",
    ),
    ElecTempoSensorDescription(
        key="couleur_aujourdhui",
        data_key="couleur_aujourdhui",
        name="Couleur aujourd'hui",
        icon="mdi:calendar-today",
    ),
    ElecTempoSensorDescription(
        key="couleur_demain",
        data_key="couleur_demain",
        name="Couleur demain",
        icon="mdi:calendar-tomorrow",
    ),
    ElecTempoSensorDescription(
        key="tarif_actuel",
        data_key="tarif_actuel",
        name="Tarif actuel",
        native_unit_of_measurement=CURRENCY_EUR_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:currency-eur",
    ),
    ElecTempoSensorDescription(
        key="tarif_hc_bleu",
        data_key="tarifs",
        sub_key="hc_bleu",
        name="Tarif HC Bleu",
        native_unit_of_measurement=CURRENCY_EUR_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-night",
    ),
    ElecTempoSensorDescription(
        key="tarif_hp_bleu",
        data_key="tarifs",
        sub_key="hp_bleu",
        name="Tarif HP Bleu",
        native_unit_of_measurement=CURRENCY_EUR_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-sunny",
    ),
    ElecTempoSensorDescription(
        key="tarif_hc_blanc",
        data_key="tarifs",
        sub_key="hc_blanc",
        name="Tarif HC Blanc",
        native_unit_of_measurement=CURRENCY_EUR_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-night",
    ),
    ElecTempoSensorDescription(
        key="tarif_hp_blanc",
        data_key="tarifs",
        sub_key="hp_blanc",
        name="Tarif HP Blanc",
        native_unit_of_measurement=CURRENCY_EUR_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-sunny",
    ),
    ElecTempoSensorDescription(
        key="tarif_hc_rouge",
        data_key="tarifs",
        sub_key="hc_rouge",
        name="Tarif HC Rouge",
        native_unit_of_measurement=CURRENCY_EUR_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-night",
    ),
    ElecTempoSensorDescription(
        key="tarif_hp_rouge",
        data_key="tarifs",
        sub_key="hp_rouge",
        name="Tarif HP Rouge",
        native_unit_of_measurement=CURRENCY_EUR_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-sunny",
    ),
    ElecTempoSensorDescription(
        key="source",
        data_key="source",
        name="Source des données",
        icon="mdi:database-check",
    ),
)

_COLOR_ICONS = {
    "bleu":    "mdi:circle",
    "blanc":   "mdi:circle-outline",
    "rouge":   "mdi:circle",
    "inconnu": "mdi:help-circle-outline",
}

_COLOR_COLORS = {
    "bleu":    "#4488FF",
    "blanc":   "#CCCCCC",
    "rouge":   "#FF3333",
    "inconnu": "#888888",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ElecTempoCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        ElecTempoSensor(coordinator, entry, desc)
        for desc in SENSOR_DESCRIPTIONS
    )


class ElecTempoSensor(CoordinatorEntity[ElecTempoCoordinator], SensorEntity):
    """A sensor for an ElecTempo data point."""

    entity_description: ElecTempoSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ElecTempoCoordinator,
        entry: ConfigEntry,
        description: ElecTempoSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=NAME,
            manufacturer="EDF",
            model="Tempo",
        )

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data
        if data is None:
            return None
        raw = data.get(self.entity_description.data_key)
        if self.entity_description.sub_key is not None:
            if isinstance(raw, dict):
                return raw.get(self.entity_description.sub_key)
            return None
        return raw

    @property
    def icon(self) -> str:
        key = self.entity_description.key
        if key in ("couleur_actuelle", "couleur_aujourdhui", "couleur_demain"):
            color = self.native_value or "inconnu"
            return _COLOR_ICONS.get(color, "mdi:help-circle-outline")
        return self.entity_description.icon or "mdi:flash"
