"""Bot de trading Polymarket — mode paper (virtuel) par défaut, mode live optionnel.

À exécuter UNIQUEMENT sur votre propre machine. Ne jamais publier votre .env
ni votre clé privée. Voir README.md.
"""

import json
import os
import sys
import time
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

GAMMA_API = "https://gamma-api.polymarket.com"
CLOB_HOST = "https://clob.polymarket.com"
STATE_PATH = Path(__file__).parent / "bot_state.json"

MODE = os.getenv("MODE", "paper").lower()
STRATEGY = os.getenv("STRATEGY", "momentum").lower()
STAKE = float(os.getenv("STAKE_USDC", "50"))
TAKE_PROFIT = float(os.getenv("TAKE_PROFIT_PCT", "10")) / 100
STOP_LOSS = float(os.getenv("STOP_LOSS_PCT", "10")) / 100
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "60"))
TOP_N = int(os.getenv("TOP_N", "10"))
MIN_VOLUME_24H = float(os.getenv("MIN_VOLUME_24H", "10000"))
TREND_WINDOW = int(os.getenv("TREND_WINDOW", "20"))
TREND_THRESHOLD = float(os.getenv("TREND_THRESHOLD_PCT", "3")) / 100
LIVE_CONFIRM = os.getenv("LIVE_CONFIRM", "").upper() == "YES"
PK = os.getenv("PK", "")


def log(msg):
    print(time.strftime("[%H:%M:%S]"), msg, flush=True)


def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {
        "bankroll": 1000.0,
        "starting_bankroll": 1000.0,
        "positions": {},
        "history": [],
        "price_history": {},
    }


def save_state(state):
    STATE_PATH.write_text(json.dumps(state, indent=2))


def fetch_markets():
    resp = requests.get(
        f"{GAMMA_API}/markets",
        params={
            "active": "true",
            "closed": "false",
            "order": "volume24hr",
            "ascending": "false",
            "limit": TOP_N,
        },
        timeout=15,
    )
    resp.raise_for_status()
    markets = []
    for m in resp.json():
        try:
            prices = json.loads(m["outcomePrices"])
            tokens = json.loads(m.get("clobTokenIds", "[]"))
            if len(prices) < 2 or not tokens:
                continue
            yes_price = float(prices[0])
            if not (0.01 <= yes_price <= 0.99):
                continue
            if float(m.get("volume24hr", 0)) < MIN_VOLUME_24H:
                continue
            markets.append({
                "slug": m["slug"],
                "question": m["question"],
                "yes_price": yes_price,
                "best_bid": float(m.get("bestBid") or yes_price),
                "best_ask": float(m.get("bestAsk") or yes_price),
                "yes_token_id": tokens[0],
                "closed": bool(m.get("closed")),
            })
        except (KeyError, ValueError, json.JSONDecodeError):
            continue
    return markets


def update_history(state, markets):
    hist = state["price_history"]
    for m in markets:
        h = hist.setdefault(m["slug"], [])
        h.append(m["yes_price"])
        if len(h) > 240:
            hist.pop(0)
    active = {m["slug"] for m in markets}
    for slug in list(hist):
        if slug not in active:
            del hist[slug]


def trend_pct(state, slug):
    h = state["price_history"].get(slug, [])
    if len(h) < TREND_WINDOW + 1:
        return 0.0
    past = h[-TREND_WINDOW - 1]
    return (h[-1] - past) / past if past else 0.0


def execute_live(side, market, price, shares):
    try:
        from py_clob_client.client import ClobClient
        from py_clob_client.clob_types import OrderArgs, OrderType
    except ImportError:
        log("MODE LIVE : installez py-clob-client (pip install py-clob-client) ou repassez en MODE=paper")
        sys.exit(1)

    client = ClobClient(host=CLOB_HOST, key=PK, chain_id=137)
    client.set_api_creds(client.create_or_derive_api_creds())
    order = client.create_order(OrderArgs(
        token_id=market["yes_token_id"],
        price=round(price, 3),
        size=round(shares, 2),
        side=side,
    ))
    resp = client.post_order(order, OrderType.GTC)
    log(f"LIVE {side} envoyé : {resp}")
    return resp


def open_position(state, markets_by_slug):
    if len(state["positions"]) >= 3:
        return
    for m in markets_by_slug.values():
        if m["slug"] in state["positions"]:
            continue
        tr = trend_pct(state, m["slug"])
        if STRATEGY == "momentum":
            signal = tr >= TREND_THRESHOLD
        else:
            signal = tr <= -TREND_THRESHOLD
        if not signal or state["bankroll"] < STAKE:
            continue
        price = m["best_ask"]
        shares = STAKE / price
        state["bankroll"] -= STAKE
        state["positions"][m["slug"]] = {
            "question": m["question"], "shares": shares, "entry": price, "stake": STAKE,
        }
        state["history"].append({
            "at": time.time(), "action": "BUY", "slug": m["slug"],
            "price": price, "shares": shares, "stake": STAKE,
        })
        log(f"ACHAT {m['slug']} — {shares:.1f} parts YES à {price:.3f} (tendance {tr:+.1%})")
        if MODE == "live":
            execute_live("BUY", m, price, shares)
        return


def manage_positions(state, markets_by_slug):
    for slug in list(state["positions"]):
        pos = state["positions"][slug]
        m = markets_by_slug.get(slug)
        if m is None or m["closed"]:
            exit_price = state["price_history"].get(slug, [pos["entry"]])[-1]
            reason = "marché fermé/résolu"
        else:
            exit_price = m["best_bid"]
            pnl_pct = (exit_price - pos["entry"]) / pos["entry"]
            if pnl_pct >= TAKE_PROFIT:
                reason = f"take-profit {pnl_pct:+.1%}"
            elif pnl_pct <= -STOP_LOSS:
                reason = f"stop-loss {pnl_pct:+.1%}"
            else:
                continue
        proceeds = pos["shares"] * exit_price
        state["bankroll"] += proceeds
        pnl = proceeds - pos["stake"]
        state["history"].append({
            "at": time.time(), "action": "SELL", "slug": slug,
            "price": exit_price, "shares": pos["shares"], "pnl": pnl, "reason": reason,
        })
        log(f"VENTE {slug} à {exit_price:.3f} — {reason} — P&L {pnl:+.2f} USDC")
        del state["positions"][slug]
        if MODE == "live":
            execute_live("SELL", m, exit_price, pos["shares"])


def print_summary(state):
    total = state["bankroll"] + sum(
        p["shares"] * state["price_history"].get(s, [p["entry"]])[-1]
        for s, p in state["positions"].items()
    )
    pnl = total - state["starting_bankroll"]
    log(f"Banque {state['bankroll']:.2f} · positions {len(state['positions'])} · total {total:.2f} · P&L {pnl:+.2f} USDC")


def main():
    if MODE == "live":
        if not LIVE_CONFIRM:
            log("MODE LIVE refusé : ajoutez LIVE_CONFIRM=YES dans .env après avoir lu les avertissements du README.")
            sys.exit(1)
        if not PK:
            log("MODE LIVE refusé : PK (clé privée du wallet) manquante dans .env.")
            sys.exit(1)
        log("⚠️  MODE LIVE : ordres RÉELS envoyés avec votre wallet. Argent réel en danger.")
    else:
        log("Mode PAPER : trades virtuels sur les vraies cotes Polymarket.")

    state = load_state()
    log(f"Stratégie {STRATEGY} · mise {STAKE} USDC · TP +{TAKE_PROFIT:.0%} · SL −{STOP_LOSS:.0%} · cycle {POLL_SECONDS}s")
    while True:
        try:
            markets = fetch_markets()
            update_history(state, markets)
            by_slug = {m["slug"]: m for m in markets}
            manage_positions(state, by_slug)
            open_position(state, by_slug)
            save_state(state)
            print_summary(state)
        except requests.RequestException as e:
            log(f"Erreur réseau : {e}")
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nArrêt du bot.")
