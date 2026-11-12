# 🤖 Bot local Polymarket

Bot de trading qui tourne **sur votre machine** (jamais publié, jamais hébergé).
Il lit les **vraies cotes** Polymarket via l'API publique Gamma et trade selon
une stratégie tendance ou contre-tendance, avec take-profit et stop-loss.

- **MODE=paper** (par défaut) : trades **virtuels** sur les **vraies cotes**. Aucun risque.
- **MODE=live** : ordres **réels** avec votre wallet. Argent réel en danger — lisez tout avant.

## Installation

```bash
cd bot
python3 -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

## Utilisation (mode paper — commencez par là)

```bash
python bot.py
```

Le bot affiche chaque cycle les marchés suivis, ses achats/ventes et votre P&L.
Tout l'état est sauvegardé dans `bot_state.json` (bankroll virtuelle de 1 000 USDC
au premier lancement). Supprimez ce fichier pour repartir de zéro.

Laissez-le tourner plusieurs jours en paper avant de songer au live. Si la
stratégie perd de l'argent virtuel, elle perdra de l'argent réel.

## Mode live (argent réel) — à lire intégralement

1. `pip install py-clob-client` (décommentez la ligne dans `requirements.txt`).
2. Créez un **wallet dédié** (ex. nouveau compte sur Polymarket) — **jamais votre
   wallet principal**. Déposez uniquement une petite somme que vous êtes prêt à
   perdre intégralement.
3. Mettez la clé privée de ce wallet dans `.env` (`PK=0x...`) — ce fichier est
   ignoré par git, ne le partagez jamais.
4. Ajoutez `LIVE_CONFIRM=YES` et `MODE=live` dans `.env`.
5. Le bot envoie des ordres limite GTC au best ask (achat) / best bid (vente)
   sur le token YES des marchés suivis.

### Règles de sécurité

- Clé privée dans `.env` uniquement. Jamais dans le code, jamais sur GitHub.
- Le bot ne peut pas retirer de fonds : ne donnez jamais d'autorisation USDC
  illimitée à un contrat dont vous ne comprenez pas le rôle.
- Surveillez les premiers trades en direct et coupez avec Ctrl+C à tout moment.
- Vérifiez que Polymarket est accessible légalement depuis votre pays de
  résidence et renseignez-vous sur la fiscalité de vos gains.

## Fichiers

| Fichier | Rôle |
|---|---|
| `bot.py` | Le bot (données Gamma API, stratégie, exécution paper/live) |
| `.env.example` | Modèle de configuration à copier vers `.env` |
| `requirements.txt` | Dépendances Python |
| `bot_state.json` | État du bot (créé au premier lancement, ignoré par git) |

## Avertissement

Logiciel fourni à titre éducatif, sans garantie. Le trading de marchés de
prédiction et de crypto peut faire perdre la totalité des fonds engagés.
Aucune stratégie ne garantit des gains. Utilisez le mode live à vos risques
et périls, avec de très petites sommes.
