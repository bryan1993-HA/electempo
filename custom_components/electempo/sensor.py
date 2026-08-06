"""Sensor platform for the ElecTempo integration."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME, TEMPO_SAISON_QUOTAS
from .coordinator import ElecTempoCoordinator

CURRENCY_EUR_KWH = "€/kWh"


@dataclass(frozen=True, kw_only=True)
class ElecTempoSensorDescription(SensorEntityDescription):
    data_key: str
    sub_key: str | None = None
    entity_registry_enabled_default: bool = True


# ─── Ordre d'affichage logique ────────────────────────────────────────────────
#  1. Couleurs
#  2. Tarif actuel
#  3. Tarifs HC/HP par couleur (Bleu → Blanc → Rouge)
#  4. Saison : jours restants  (affiché par défaut)
#  5. Saison : jours utilisés  (masqués par défaut, disponibles si besoin)
#  6. Diagnostic
# ─────────────────────────────────────────────────────────────────────────────

SENSOR_DESCRIPTIONS: tuple[ElecTempoSensorDescription, ...] = (

    # ── Couleurs ──────────────────────────────────────────────────────────────
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

    # ── Tarif courant ─────────────────────────────────────────────────────────
    ElecTempoSensorDescription(
        key="tarif_actuel",
        data_key="tarif_actuel",
        name="Tarif actuel",
        native_unit_of_measurement=CURRENCY_EUR_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:currency-eur",
    ),

    # ── Tarifs Blanc ──────────────────────────────────────────────────────────
    ElecTempoSensorDescription(
        key="tarif_hc_blanc",
        data_key="tarifs",
        sub_key="hc_blanc",
        name="Tarif Blanc HC",
        native_unit_of_measurement=CURRENCY_EUR_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-night",
    ),
    ElecTempoSensorDescription(
        key="tarif_hp_blanc",
        data_key="tarifs",
        sub_key="hp_blanc",
        name="Tarif Blanc HP",
        native_unit_of_measurement=CURRENCY_EUR_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-sunny",
    ),

    # ── Tarifs Bleu ───────────────────────────────────────────────────────────
    ElecTempoSensorDescription(
        key="tarif_hc_bleu",
        data_key="tarifs",
        sub_key="hc_bleu",
        name="Tarif Bleu HC",
        native_unit_of_measurement=CURRENCY_EUR_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-night",
    ),
    ElecTempoSensorDescription(
        key="tarif_hp_bleu",
        data_key="tarifs",
        sub_key="hp_bleu",
        name="Tarif Bleu HP",
        native_unit_of_measurement=CURRENCY_EUR_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-sunny",
    ),

    # ── Tarifs Rouge ──────────────────────────────────────────────────────────
    ElecTempoSensorDescription(
        key="tarif_hc_rouge",
        data_key="tarifs",
        sub_key="hc_rouge",
        name="Tarif Rouge HC",
        native_unit_of_measurement=CURRENCY_EUR_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-night",
    ),
    ElecTempoSensorDescription(
        key="tarif_hp_rouge",
        data_key="tarifs",
        sub_key="hp_rouge",
        name="Tarif Rouge HP",
        native_unit_of_measurement=CURRENCY_EUR_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-sunny",
    ),

    # ── Jours restants (affichés par défaut) ──────────────────────────────────
    ElecTempoSensorDescription(
        key="jours_bleu_restants",
        data_key="jours_bleu_restants",
        name="Jours Bleu restants",
        native_unit_of_measurement="jours",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:calendar-check",
    ),
    ElecTempoSensorDescription(
        key="jours_blanc_restants",
        data_key="jours_blanc_restants",
        name="Jours Blanc restants",
        native_unit_of_measurement="jours",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:calendar-check",
    ),
    ElecTempoSensorDescription(
        key="jours_rouge_restants",
        data_key="jours_rouge_restants",
        name="Jours Rouge restants",
        native_unit_of_measurement="jours",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:calendar-alert",
    ),

    # ── Jours utilisés (masqués par défaut) ───────────────────────────────────
    ElecTempoSensorDescription(
        key="jours_bleu",
        data_key="jours_bleu",
        name="Jours Bleu utilisés",
        native_unit_of_measurement="jours",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:calendar-minus",
        entity_registry_enabled_default=False,
    ),
    ElecTempoSensorDescription(
        key="jours_blanc",
        data_key="jours_blanc",
        name="Jours Blanc utilisés",
        native_unit_of_measurement="jours",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:calendar-minus",
        entity_registry_enabled_default=False,
    ),
    ElecTempoSensorDescription(
        key="jours_rouge",
        data_key="jours_rouge",
        name="Jours Rouge utilisés",
        native_unit_of_measurement="jours",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:calendar-minus",
        entity_registry_enabled_default=False,
    ),

    # ── Diagnostic ────────────────────────────────────────────────────────────
    ElecTempoSensorDescription(
        key="saison",
        data_key="saison",
        name="Saison",
        icon="mdi:calendar-range",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ElecTempoSensorDescription(
        key="source",
        data_key="source",
        name="Source des données",
        icon="mdi:database-check",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)

_COLOR_ICONS = {
    "bleu":    "mdi:circle",
    "blanc":   "mdi:circle-outline",
    "rouge":   "mdi:circle",
    "inconnu": "mdi:help-circle-outline",
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
        self._attr_entity_registry_enabled_default = (
            description.entity_registry_enabled_default
        )
        power = entry.data.get("contract_power", "?")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=NAME,
            manufacturer="bryan1993-HA",
            model=f"EDF Tempo {power} kVA",
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

    @property
    def extra_state_attributes(self) -> dict | None:
        key = self.entity_description.key
        if key == "jours_rouge_restants":
            quota = TEMPO_SAISON_QUOTAS["rouge"]
            used = (self.coordinator.data or {}).get("jours_rouge", 0)
            return {"quota_total": quota, "utilises": used}
        if key == "jours_blanc_restants":
            quota = TEMPO_SAISON_QUOTAS["blanc"]
            used = (self.coordinator.data or {}).get("jours_blanc", 0)
            return {"quota_total": quota, "utilises": used}
        if key == "jours_bleu_restants":
            quota = TEMPO_SAISON_QUOTAS["bleu"]
            used = (self.coordinator.data or {}).get("jours_bleu", 0)
            return {"quota_total": quota, "utilises": used}
        return None
