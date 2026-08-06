<div align="center">

# ⚡ ElecTempo

**L'intégration Home Assistant pour le contrat EDF Tempo**
Couleurs, tarifs précis HC/HP, suivi énergétique par session — toujours à jour.

[![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-41BDF5?style=for-the-badge&logo=home-assistant)](https://www.home-assistant.io)
[![GitHub Release](https://img.shields.io/github/v/release/bryan1993-HA/electempo?style=for-the-badge&color=blue)](https://github.com/bryan1993-HA/electempo/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

</div>

---

## Pourquoi ElecTempo ?

Le contrat **EDF Tempo** facture l'électricité selon **3 couleurs × 2 périodes = 6 tarifs distincts**.
La plupart des intégrations existantes ignorent cette précision — ElecTempo non.

| | ElecTempo | Autres intégrations |
|---|:---:|:---:|
| 6 tarifs distincts (HC/HP × Bleu/Blanc/Rouge) | ✅ | ❌ |
| Basculement couleur automatique à 06h00 | ✅ | ⚠️ |
| Tarifs toujours à jour (correctif auto si CSV périmé) | ✅ | ❌ |
| Jours restants par couleur (Bleu/Blanc/Rouge) | ✅ | ❌ |
| Réinitialisation automatique chaque saison | ✅ | ❌ |
| Plages HC configurables (support double plage) | ✅ | ❌ |
| Fallback intégré si API indisponible | ✅ | ❌ |
| Source des données visible | ✅ | ❌ |
| Config via UI (aucun YAML requis) | ✅ | ⚠️ |

---

## Entités

### 🎨 Couleurs Tempo

| Entité | Description |
|--------|-------------|
| `sensor.electempo_couleur_actuelle` | Couleur en cours (gère le basculement à 06h00) |
| `sensor.electempo_couleur_aujourdhui` | Couleur du jour Tempo |
| `sensor.electempo_couleur_demain` | Couleur du lendemain (disponible dès 11h00) |

Les états possibles : `bleu` · `blanc` · `rouge` · `inconnu`

### 💶 Tarifs (€/kWh)

| Entité | Valeur août 2026 |
|--------|-----------------|
| `sensor.electempo_tarif_actuel` | Tarif appliqué en ce moment |
| `sensor.electempo_tarif_hc_bleu` | 0,1356 €/kWh |
| `sensor.electempo_tarif_hp_bleu` | 0,1654 €/kWh |
| `sensor.electempo_tarif_hc_blanc` | 0,1536 €/kWh |
| `sensor.electempo_tarif_hp_blanc` | 0,1921 €/kWh |
| `sensor.electempo_tarif_hc_rouge` | 0,1615 €/kWh |
| `sensor.electempo_tarif_hp_rouge` | **0,7295 €/kWh** |

### 🕐 Période

| Entité | Description |
|--------|-------------|
| `binary_sensor.electempo_heures_creuses` | `ON` = Heures Creuses · `OFF` = Heures Pleines |

> Attributs : couleur actuelle + tarif en cours

### 📅 Jours de saison (sept → août)

| Entité | Quota | Description |
|--------|-------|-------------|
| `sensor.electempo_jours_bleu_restants` | 300 | Jours Bleu restants dans la saison |
| `sensor.electempo_jours_blanc_restants` | 43 | Jours Blanc restants dans la saison |
| `sensor.electempo_jours_rouge_restants` | **22** | Jours Rouge restants ⚠️ |

> Attributs disponibles sur chaque capteur : `quota_total` + `utilises`
>
> Les capteurs "jours utilisés" sont disponibles mais masqués par défaut — activables dans **Paramètres → Entités**.
>
> **Réinitialisation automatique** chaque 1er septembre — aucune mise à jour requise.

### 🔌 Diagnostic

| Entité | Description |
|--------|-------------|
| `sensor.electempo_saison` | Saison en cours (ex: `2025-2026`) |
| `sensor.electempo_source_donnees` | Source utilisée : `api-couleur-tempo.fr` · `data.gouv.fr` · `csv+override` · `fallback` |

---

## Installation

### Via HACS (recommandé)

1. Dans HACS → **Intégrations** → menu ⋮ → **Dépôts personnalisés**
2. URL : `https://github.com/bryan1993-HA/electempo` — catégorie **Intégration**
3. Cliquer **Ajouter** puis **Télécharger ElecTempo**
4. Redémarrer Home Assistant
5. **Paramètres → Appareils & Services → + Ajouter une intégration** → *ElecTempo*
6. Sélectionner votre puissance souscrite (kVA) → **Soumettre**

### Installation manuelle

```bash
# Copier dans votre répertoire de configuration HA
cp -r custom_components/electempo /config/custom_components/
```

Puis redémarrer Home Assistant.

---

## Configuration

### Puissance souscrite

Sélectionnée lors de l'ajout de l'intégration. Détermine l'abonnement fixe.
Valeurs supportées : `3` · `6` · `9` · `12` · `15` · `18` · `24` · `30` · `36` kVA

### Plages Heures Creuses

Configurable via **Paramètres → Appareils & Services → ElecTempo → Configurer**

| Cas | Valeur |
|-----|--------|
| Standard EDF Tempo | `22:00-06:00` *(défaut)* |
| Double plage | `22:00-06:00,12:30-14:30` |

> **Note :** Pour le contrat Tempo, EDF fixe les HC à `22:00-06:00` pour tous les abonnés en France. L'option double plage est disponible pour les cas particuliers ou les évolutions futures du contrat.

---

## Exemples d'automatisations

### Notification couleur du lendemain

```yaml
automation:
  - alias: "Alerte couleur Tempo demain"
    triggers:
      - trigger: time
        at: "11:05:00"
    conditions:
      - condition: not
        conditions:
          - condition: state
            entity_id: sensor.electempo_couleur_demain
            state: "inconnu"
    actions:
      - action: notify.mobile_app_mon_telephone
        data:
          title: "⚡ Tempo demain"
          message: >
            Demain est un jour {{ states('sensor.electempo_couleur_demain') }}.
            {% if states('sensor.electempo_couleur_demain') == 'rouge' %}
            ⚠️ Tarif élevé — pensez à décaler vos usages !
            {% endif %}
```

### Calcul du coût de session PC (6 périodes Tempo)

```yaml
# Dans une action TTS ou notification
message: >
  {% set t_hc_bleu  = states('sensor.electempo_tarif_hc_bleu')  | float(0) %}
  {% set t_hp_bleu  = states('sensor.electempo_tarif_hp_bleu')  | float(0) %}
  {% set t_hc_blanc = states('sensor.electempo_tarif_hc_blanc') | float(0) %}
  {% set t_hp_blanc = states('sensor.electempo_tarif_hp_blanc') | float(0) %}
  {% set t_hc_rouge = states('sensor.electempo_tarif_hc_rouge') | float(0) %}
  {% set t_hp_rouge = states('sensor.electempo_tarif_hp_rouge') | float(0) %}
  Tarif actuel : {{ states('sensor.electempo_tarif_actuel') }} €/kWh
  Couleur : {{ states('sensor.electempo_couleur_actuelle') }}
  Période : {{ 'Heures Creuses' if is_state('binary_sensor.electempo_heures_creuses', 'on') else 'Heures Pleines' }}
```

---

## Comment ça fonctionne

```
API api-couleur-tempo.fr ──► Couleur hier / aujourd'hui / demain
        │
        ▼
  Cache en mémoire ──► Pas de requête inutile
        │
        ▼
  Couleur actuelle ◄── Basculement à 06h00 (hier→aujourd'hui)
        │
        ├── + HC/HP (plages configurables, défaut 22:00-06:00)
        │
        ▼
  Tarif actuel = tarifs[période][couleur]
        ▲
        │
data.gouv.fr CSV ──► 6 tarifs officiels EDF
        │
        └── Correctif auto si CSV périmé ──► Tarifs intégrés (fallback)
```

**Refresh :** toutes les minutes — transitions 06h00 et 22h00 détectées automatiquement.

---

## Sources de données

| Source | Données | Fréquence |
|--------|---------|-----------|
| [api-couleur-tempo.fr](https://www.api-couleur-tempo.fr) | Couleurs Tempo + historique saison | Au besoin (cache) |
| [data.gouv.fr](https://www.data.gouv.fr/fr/datasets/r/0c3d1d36-c412-4620-8566-e5cbb4fa2b5a) | Tarifs EDF officiels (CSV) | 1×/jour |
| Fallback intégré | Tarifs août 2026 | Si CSV indisponible ou périmé |

---

## Contribuer

Les contributions sont les bienvenues !

1. Fork le repo
2. Crée une branche : `git checkout -b feat/ma-fonctionnalite`
3. Commit : `git commit -m "feat: ma fonctionnalité"`
4. Push : `git push origin feat/ma-fonctionnalite`
5. Ouvre une **Pull Request**

Pour signaler un bug : [ouvrir une issue](https://github.com/bryan1993-HA/electempo/issues)

---

## Licence

MIT — voir [LICENSE](LICENSE)

---

<div align="center">

Fait avec ❤️ pour la communauté Home Assistant française

</div>
