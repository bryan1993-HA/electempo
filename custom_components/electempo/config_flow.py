"""Config flow for the ElecTempo integration."""
from __future__ import annotations

import re
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback

from .const import (
    CONF_CONTRACT_POWER,
    CONF_HC_RANGES,
    CONTRACT_POWERS,
    DEFAULT_HC_RANGES,
    DOMAIN,
    NAME,
)

HC_RANGE_PATTERN = re.compile(
    r'^([01]?\d|2[0-3]):[0-5]\d-([01]?\d|2[0-3]):[0-5]\d$'
)


def _validate_hc_ranges(value: str) -> str:
    """Validate one or more HC time ranges (comma-separated HH:MM-HH:MM)."""
    ranges = [r.strip() for r in value.split(",") if r.strip()]
    if not ranges:
        raise vol.Invalid("Au moins une plage horaire est requise.")
    for r in ranges:
        if not HC_RANGE_PATTERN.match(r):
            raise vol.Invalid(
                f"Format invalide : « {r} ». Attendu : HH:MM-HH:MM (ex: 22:00-06:00)"
            )
    return ",".join(ranges)


class ElecTempoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ElecTempo."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors: dict[str, str] = {}

        if user_input is not None:
            return self.async_create_entry(
                title=f"{NAME} — {user_input[CONF_CONTRACT_POWER]} kVA",
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_CONTRACT_POWER, default="6"): vol.In(CONTRACT_POWERS),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return ElecTempoOptionsFlow(config_entry)


class ElecTempoOptionsFlow(OptionsFlow):
    """Handle ElecTempo options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        current_hc = self._config_entry.options.get(CONF_HC_RANGES, DEFAULT_HC_RANGES)

        if user_input is not None:
            try:
                user_input[CONF_HC_RANGES] = _validate_hc_ranges(
                    user_input[CONF_HC_RANGES]
                )
                return self.async_create_entry(title="", data=user_input)
            except vol.Invalid:
                errors[CONF_HC_RANGES] = "invalid_hc_ranges"

        schema = vol.Schema(
            {
                vol.Required(CONF_HC_RANGES, default=current_hc): str,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )
