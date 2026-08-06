"""Config flow for the ElecTempo integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import HomeAssistant

from .const import CONF_CONTRACT_POWER, CONTRACT_POWERS, DOMAIN, NAME


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
