# ElecTempo

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue)](https://www.home-assistant.io)

Intégration Home Assistant pour le contrat **EDF Tempo** — couleurs du jour/lendemain, tarifs HC/HP précis par période (Bleu/Blanc/Rouge), et suivi énergétique par session.

---

## Fonctionnalités

- **Couleur actuelle** — gère automatiquement le basculement à 06h00
- **Couleur aujourd'hui / demain** — disponible dès 11h00 pour le lendemain
- **6 capteurs de tarifs** — HC et HP pour chaque couleur (Bleu, Blanc, Rouge)
- **Tarif actuel** — €/kWh appliqué en ce moment
- **Capteur Heures Creuses** — binary sensor ON/OFF (22h00 → 06h00)
- **Source des données** — indique quelle API ou fallback est utilisé
- **Résilience** — fallback intégré si les sources externes sont indisponibles
- **Tarifs toujours à jour** — correctif automatique si data.gouv.fr est en retard

---

## Entités créées

| Entité | Type | Description |
|--------|------|-------------|
| `sensor.electempo_couleur_actuelle` | sensor | bleu / blanc / rouge |
| `sensor.electempo_couleur_aujourdhui` | sensor | Couleur du jour Tempo |
| `sensor.electempo_couleur_demain` | sensor | Couleur du lendemain |
| `sensor.electempo_tarif_actuel` | sensor | Tarif courant (€/kWh) |
| `sensor.electempo_tarif_hc_bleu` | sensor | 0.1356 €/kWh |
| `sensor.electempo_tarif_hp_bleu` | sensor | 0.1654 €/kWh |
| `sensor.electempo_tarif_hc_blanc` | sensor | 0.1536 €/kWh |
| `sensor.electempo_tarif_hp_blanc` | sensor | 0.1921 €/kWh |
| `sensor.electempo_tarif_hc_rouge` | sensor | 0.1615 €/kWh |
| `sensor.electempo_tarif_hp_rouge` | sensor | 0.7295 €/kWh |
| `sensor.electempo_source_donnees` | sensor | Source API utilisée |
| `binary_sensor.electempo_heures_creuses` | binary_sensor | ON = heures creuses |

---

## Installation via HACS

1. Dans HACS → **Intégrations** → menu ⋮ → **Dépôts personnalisés**
2. Ajouter `https://github.com/bryan1993-HA/electempo` — catégorie **Intégration**
3. Installer **ElecTempo**
4. Redémarrer Home Assistant
5. **Paramètres → Appareils & Services → Ajouter une intégration** → chercher *ElecTempo*
6. Sélectionner votre puissance souscrite (kVA)

---

## Installation manuelle

Copier le dossier `custom_components/electempo/` dans votre répertoire de configuration HA, puis redémarrer.

---

## Sources de données

| Source | Données |
|--------|---------|
| [api-couleur-tempo.fr](https://www.api-couleur-tempo.fr) | Couleurs Tempo (principale) |
| [data.gouv.fr](https://www.data.gouv.fr) | CSV des tarifs EDF officiels |
| Fallback intégré | Tarifs août 2026 si CSV indisponible |

---

## Licence

MIT — voir [LICENSE](LICENSE)
