"""Data update coordinator for the ElecTempo integration."""
from __future__ import annotations

import csv
import logging
from datetime import date, datetime, timedelta
from typing import Any

import requests

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_COULEUR_TEMPO_URL,
    COLOR_INCONNU,
    CONF_CONTRACT_POWER,
    HC_END_HOUR,
    HC_START_HOUR,
    NAME,
    TARIF_FALLBACK_VARIABLE,
    TARIF_HP_ROUGE_MIN_AOU_2026,
    TARIF_TEMPO_CSV_URL,
    TEMPO_COLOR_CODES,
    TEMPO_DAY_START_HOUR,
    TARIFF_REFRESH_DAYS,
)

_LOGGER = logging.getLogger(__name__)

_HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; ElecTempo/1.0; Home Assistant integration; "
        "+https://github.com/bryan1993-HA/electempo)"
    )
}


def _get(url: str, timeout: int = 10) -> requests.Response:
    return requests.get(url, headers=_HTTP_HEADERS, timeout=timeout)


class ElecTempoCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetches EDF Tempo colors and tariffs, refreshes every minute."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=NAME,
            update_interval=timedelta(minutes=1),
        )
        self.config_entry = entry
        self._color_cache: dict[str, str] = {}
        self._tariffs: dict[str, float] = {}
        self._last_tariff_fetch: datetime | None = None
        self._last_source: str = "none"

    # ------------------------------------------------------------------
    # Main update
    # ------------------------------------------------------------------

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            today = date.today()
            yesterday = today - timedelta(days=1)
            tomorrow = today + timedelta(days=1)
            now_hour = datetime.now().hour

            color_yesterday = await self._fetch_color(yesterday)
            color_today = await self._fetch_color(today)
            color_tomorrow = await self._fetch_color(tomorrow)

            # Before 06:00 we're still on yesterday's Tempo day
            couleur_actuelle = (
                color_yesterday if now_hour < TEMPO_DAY_START_HOUR else color_today
            )

            est_hc = now_hour >= HC_START_HOUR or now_hour < HC_END_HOUR
            period = "hc" if est_hc else "hp"

            await self._refresh_tariffs_if_needed()

            tarif_actuel = self._tariffs.get(f"{period}_{couleur_actuelle}")

            return {
                "couleur_aujourdhui": color_today,
                "couleur_demain": color_tomorrow,
                "couleur_actuelle": couleur_actuelle,
                "est_hc": est_hc,
                "tarif_actuel": tarif_actuel,
                "tarifs": dict(self._tariffs),
                "source": self._last_source,
            }
        except Exception as err:
            raise UpdateFailed(f"ElecTempo update failed: {err}") from err

    # ------------------------------------------------------------------
    # Color fetching
    # ------------------------------------------------------------------

    async def _fetch_color(self, d: date) -> str:
        date_str = d.strftime("%Y-%m-%d")
        if date_str in self._color_cache:
            return self._color_cache[date_str]

        color = await self.hass.async_add_executor_job(
            self._fetch_color_sync, date_str
        )
        if color != COLOR_INCONNU:
            self._color_cache[date_str] = color
        return color

    def _fetch_color_sync(self, date_str: str) -> str:
        url = API_COULEUR_TEMPO_URL.format(date=date_str)
        try:
            resp = _get(url)
            resp.raise_for_status()
            code = resp.json().get("codeJour", 0)
            color = TEMPO_COLOR_CODES.get(code, COLOR_INCONNU)
            self._last_source = "api-couleur-tempo.fr"
            _LOGGER.debug("ElecTempo color %s → %s (code %s)", date_str, color, code)
            return color
        except Exception as exc:
            _LOGGER.warning(
                "ElecTempo: failed to fetch color for %s: %s", date_str, exc
            )
            return COLOR_INCONNU

    # ------------------------------------------------------------------
    # Tariff fetching
    # ------------------------------------------------------------------

    async def _refresh_tariffs_if_needed(self) -> None:
        needs_refresh = (
            not self._tariffs
            or self._last_tariff_fetch is None
            or datetime.now() - self._last_tariff_fetch
            > timedelta(days=TARIFF_REFRESH_DAYS)
        )
        if needs_refresh:
            await self.hass.async_add_executor_job(self._fetch_tariffs_sync)

    def _fetch_tariffs_sync(self) -> None:
        power = self.config_entry.data.get(CONF_CONTRACT_POWER, "6")
        fetched: dict[str, float] = {}

        try:
            resp = _get(TARIF_TEMPO_CSV_URL, timeout=15)
            resp.raise_for_status()
            rows = list(
                csv.reader(resp.content.decode("utf-8").splitlines(), delimiter=";")
            )
            for row in rows:
                if len(row) < 17:
                    continue
                if row[1] == "" and row[2] == power:
                    fetched = {
                        "fixe":     float(row[4].replace(",", ".")),
                        "hc_bleu":  float(row[6].replace(",", ".")),
                        "hp_bleu":  float(row[8].replace(",", ".")),
                        "hc_blanc": float(row[10].replace(",", ".")),
                        "hp_blanc": float(row[12].replace(",", ".")),
                        "hc_rouge": float(row[14].replace(",", ".")),
                        "hp_rouge": float(row[16].replace(",", ".")),
                    }
                    break
        except Exception as exc:
            _LOGGER.warning("ElecTempo: tariff CSV fetch failed: %s", exc)

        if not fetched:
            _LOGGER.warning("ElecTempo: using built-in fallback tariffs (August 2026)")
            fetched = dict(TARIF_FALLBACK_VARIABLE)
            self._last_source = "fallback"
        else:
            hp_rouge = fetched.get("hp_rouge", 0)
            if round(hp_rouge, 3) < TARIF_HP_ROUGE_MIN_AOU_2026:
                _LOGGER.warning(
                    "ElecTempo: data.gouv.fr CSV not yet updated "
                    "(HP Rouge=%.4f < %.3f) — applying August 2026 rates.",
                    hp_rouge,
                    TARIF_HP_ROUGE_MIN_AOU_2026,
                )
                fetched.update(TARIF_FALLBACK_VARIABLE)
                self._last_source = "csv+override"
            else:
                self._last_source = "data.gouv.fr"

        self._tariffs = fetched
        self._last_tariff_fetch = datetime.now()
        _LOGGER.info(
            "ElecTempo tariffs loaded (source: %s): %s", self._last_source, fetched
        )
