"""Data update coordinator for the ElecTempo integration."""
from __future__ import annotations

import csv
import logging
import re
from datetime import date, datetime, timedelta
from typing import Any

import requests

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_COULEUR_TEMPO_RANGE_URL,
    API_COULEUR_TEMPO_URL,
    COLOR_BLEU,
    COLOR_BLANC,
    COLOR_INCONNU,
    COLOR_ROUGE,
    CONF_CONTRACT_POWER,
    CONF_HC_RANGES,
    DEFAULT_HC_RANGES,
    NAME,
    TARIF_FALLBACK_VARIABLE,
    TARIF_HP_ROUGE_MIN_AOU_2026,
    TARIF_TEMPO_CSV_URL,
    TEMPO_COLOR_CODES,
    TEMPO_DAY_START_HOUR,
    TEMPO_SAISON_QUOTAS,
    TARIFF_REFRESH_DAYS,
)

_LOGGER = logging.getLogger(__name__)

_HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; ElecTempo/1.0; Home Assistant integration; "
        "+https://github.com/bryan1993-HA/electempo)"
    )
}

_HC_RANGE_RE = re.compile(
    r'^([01]?\d|2[0-3]):[0-5]\d-([01]?\d|2[0-3]):[0-5]\d$'
)


def _get(url: str, timeout: int = 10) -> requests.Response:
    return requests.get(url, headers=_HTTP_HEADERS, timeout=timeout)


def _parse_time(s: str):
    return datetime.strptime(s.strip(), "%H:%M").time()


def _time_in_range(now, start, end) -> bool:
    """True if now is in [start, end[, handles overnight ranges."""
    if start <= end:
        return start <= now < end
    return start <= now or now < end


def _is_hc(ranges_str: str) -> bool:
    """Return True if current time falls within any configured HC range."""
    now = datetime.now().time()
    for r in ranges_str.split(","):
        r = r.strip()
        if not _HC_RANGE_RE.match(r):
            continue
        start_s, end_s = r.split("-")
        if _time_in_range(now, _parse_time(start_s), _parse_time(end_s)):
            return True
    return False


def _get_season_start(today: date) -> date:
    """Return the start date of the current Tempo season (Sept 1)."""
    if today.month >= 9:
        return date(today.year, 9, 1)
    return date(today.year - 1, 9, 1)


def _season_label(season_start: date) -> str:
    """Return e.g. '2025-2026'."""
    return f"{season_start.year}-{season_start.year + 1}"


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
        # Season day counts cache
        self._season_counts: dict[str, int] = {}
        self._last_season_fetch: datetime | None = None
        self._last_season_start: date | None = None

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

            # HC/HP — uses configurable ranges from options, default 22:00-06:00
            hc_ranges = self.config_entry.options.get(CONF_HC_RANGES, DEFAULT_HC_RANGES)
            est_hc = _is_hc(hc_ranges)
            period = "hc" if est_hc else "hp"

            await self._refresh_tariffs_if_needed()
            await self._refresh_season_if_needed(today)

            tarif_actuel = self._tariffs.get(f"{period}_{couleur_actuelle}")

            season_start = _get_season_start(today)
            counts = self._season_counts

            return {
                "couleur_aujourdhui": color_today,
                "couleur_demain": color_tomorrow,
                "couleur_actuelle": couleur_actuelle,
                "est_hc": est_hc,
                "hc_ranges": hc_ranges,
                "tarif_actuel": tarif_actuel,
                "tarifs": dict(self._tariffs),
                "source": self._last_source,
                # Saison
                "saison": _season_label(season_start),
                "jours_bleu":  counts.get(COLOR_BLEU, 0),
                "jours_blanc": counts.get(COLOR_BLANC, 0),
                "jours_rouge": counts.get(COLOR_ROUGE, 0),
                "jours_bleu_restants":  max(0, TEMPO_SAISON_QUOTAS[COLOR_BLEU]  - counts.get(COLOR_BLEU, 0)),
                "jours_blanc_restants": max(0, TEMPO_SAISON_QUOTAS[COLOR_BLANC] - counts.get(COLOR_BLANC, 0)),
                "jours_rouge_restants": max(0, TEMPO_SAISON_QUOTAS[COLOR_ROUGE] - counts.get(COLOR_ROUGE, 0)),
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
    # Season day counts
    # ------------------------------------------------------------------

    async def _refresh_season_if_needed(self, today: date) -> None:
        season_start = _get_season_start(today)
        needs_refresh = (
            not self._season_counts
            or self._last_season_fetch is None
            or self._last_season_start != season_start       # new season started
            or datetime.now() - self._last_season_fetch > timedelta(hours=6)
        )
        if needs_refresh:
            await self.hass.async_add_executor_job(
                self._fetch_season_sync, season_start, today
            )

    def _fetch_season_sync(self, season_start: date, today: date) -> None:
        url = API_COULEUR_TEMPO_RANGE_URL.format(
            start=season_start.strftime("%Y-%m-%d"),
            end=today.strftime("%Y-%m-%d"),
        )
        try:
            resp = _get(url, timeout=15)
            resp.raise_for_status()
            days = resp.json()

            counts: dict[str, int] = {COLOR_BLEU: 0, COLOR_BLANC: 0, COLOR_ROUGE: 0}
            for entry in days:
                code = entry.get("codeJour", 0)
                color = TEMPO_COLOR_CODES.get(code)
                if color and color != COLOR_INCONNU:
                    counts[color] = counts.get(color, 0) + 1

            self._season_counts = counts
            self._last_season_fetch = datetime.now()
            self._last_season_start = season_start
            _LOGGER.info(
                "ElecTempo season %s: bleu=%d blanc=%d rouge=%d",
                _season_label(season_start),
                counts[COLOR_BLEU],
                counts[COLOR_BLANC],
                counts[COLOR_ROUGE],
            )
        except Exception as exc:
            _LOGGER.warning("ElecTempo: season fetch failed: %s", exc)

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
