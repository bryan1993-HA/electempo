"""Constants for the ElecTempo integration."""

from homeassistant.const import Platform

DOMAIN = "electempo"
NAME = "ElecTempo"

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]

CONF_CONTRACT_POWER = "contract_power"
CONTRACT_POWERS = ["3", "6", "9", "12", "15", "18", "24", "30", "36"]

# Tempo schedule (EDF standard)
TEMPO_DAY_START_HOUR = 6     # new color day starts at 06:00
TEMPO_TOMORROW_AVAIL_HOUR = 11  # tomorrow's color available from 11:00

# HC configuration
CONF_HC_RANGES = "hc_ranges"
# EDF Tempo: HC toujours 22:00-06:00 pour tous les abonnés Tempo
# Format: "HH:MM-HH:MM" séparés par des virgules pour plusieurs plages
DEFAULT_HC_RANGES = "22:00-06:00"

# Colors
COLOR_BLEU = "bleu"
COLOR_BLANC = "blanc"
COLOR_ROUGE = "rouge"
COLOR_INCONNU = "inconnu"

TEMPO_COLOR_CODES = {
    0: COLOR_INCONNU,
    1: COLOR_BLEU,
    2: COLOR_BLANC,
    3: COLOR_ROUGE,
}

# API — primary source
API_COULEUR_TEMPO_URL = "https://www.api-couleur-tempo.fr/api/jourTempo/{date}"

# Tariff CSV from data.gouv.fr (EDF Tempo)
TARIF_TEMPO_CSV_URL = "https://www.data.gouv.fr/fr/datasets/r/0c3d1d36-c412-4620-8566-e5cbb4fa2b5a"

# Fallback tariffs when CSV is stale or unavailable
# Values: August 2026 (effective 2026-08-01), all kVA have same variable rates
# Source: EDF official August 2026 tariff schedule
TARIF_FALLBACK_VARIABLE = {
    "hc_bleu":  0.1356,
    "hp_bleu":  0.1654,
    "hc_blanc": 0.1536,
    "hp_blanc": 0.1921,
    "hc_rouge": 0.1615,
    "hp_rouge": 0.7295,
}

# Detection threshold: HP Rouge < 0.720 means CSV is still on Feb 2026 rates
TARIF_HP_ROUGE_MIN_AOU_2026 = 0.720

# Cache TTL
TARIFF_REFRESH_DAYS = 1
COLOR_CACHE_MAX_DAYS = 7
