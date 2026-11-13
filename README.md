# DORIAN - TRADING BOT

Application de trading web (paper trading) + bot local Python, **gratuit et open source** (licence MIT).

🌐 **App web** : https://cashmoneybets.github.io/meme-trader/

## C'est quoi ?

Deux outils complémentaires :

1. **L'app web** (`index.html`) — un terminal de trading futuriste qui tourne 100 % dans le
   navigateur, sans serveur et sans installation :
   - prix **réels en direct** (WebSocket Binance) : or, argent, pétrole, gaz naturel, BTC + 13 cryptos
   - 3 bots de trading sur un **compte paper partagé de 500 €** (matières premières, crypto, bot AI)
   - frais simulés 0,10 %/côté, objectif mensuel, dashboard de performance
   - Live Quant Control Center, AI Command Center, Neural Grid : monitoring quantitatif animé
   - interface EN / DE / FR / AL, mobile-friendly

2. **Le bot local** (`bot/`) — un bot Python qui tourne **sur votre machine** et trade les
   vraies cotes Polymarket, en mode paper (virtuel) ou live (réel, optionnel). Voir
   [`bot/README.md`](bot/README.md).

## ⚠️ Argent et clés API — à lire

- L'app web est **100 % paper trading** : aucun ordre réel, aucune clé API à saisir.
- Le bot local ne doit **jamais** être lancé avec un wallet ou une clé API principale.
  Créez un wallet/compte **dédié**, avec les droits de trade uniquement et **sans droit de
  retrait**, financé par une petite somme que vous êtes prêt à perdre intégralement.
- Vos clés restent **chez vous** (fichier `.env` local, ignoré par git). Ce projet n'a ni
  serveur, ni accès à vos fonds, et n'en demandera jamais.

## Démarrage rapide

**App web** : ouvrez simplement https://cashmoneybets.github.io/meme-trader/ (rien à installer).

**Bot local** :

```bash
cd bot
python3 -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python bot.py
```

## Licence

[MIT](LICENSE) — utilisez, modifiez et partagez librement.

## Avertissement

Logiciel fourni à titre **éducatif**, sans garantie. Le trading (crypto, matières
premières, marchés de prédiction) comporte un risque de perte totale des fonds engagés.
Rien ici n'est un conseil financier. Renseignez-vous sur la réglementation et la fiscalité
applicables dans votre pays de résidence.
