from __future__ import annotations

import argparse
import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path


SYMBOLS = {
    "SPY": 528.00,
    "QQQ": 460.00,
    "AAPL": 195.00,
    "TSLA": 185.00,
    "NVDA": 112.00,
    "AMD": 160.00,
    "META": 620.00,
    "MSFT": 430.00,
}

OPTION_TYPES = ["CALL", "PUT"]


def random_timestamp(minutes_back: int = 390) -> str:
    """Generate a random timestamp within a trading-day-sized window."""
    now = datetime.now(timezone.utc)
    random_time = now - timedelta(minutes=random.randint(0, minutes_back))
    return random_time.replace(microsecond=0).isoformat()


def get_next_friday(start_date: datetime) -> datetime:
    """Return the next Friday expiration date after the input date."""
    days_ahead = 4 - start_date.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return start_date + timedelta(days=days_ahead)


def generate_contract_symbol(
    symbol: str,
    expiration_date: datetime,
    strike: float,
    option_type: str,
) -> str:
    option_letter = "C" if option_type == "CALL" else "P"
    expiration_str = expiration_date.strftime("%Y%m%d")
    strike_str = f"{int(round(strike * 1000)):08d}"
    return f"{symbol}_{expiration_str}_{strike_str}_{option_letter}"


def get_strike_step(symbol: str) -> float:
    if symbol in {"SPY", "QQQ"}:
        return 1.0
    if symbol in {"AAPL", "AMD", "TSLA"}:
        return 2.5
    return 5.0


def round_to_step(value: float, step: float) -> float:
    return round(round(value / step) * step, 2)


def estimate_option_mid(
    underlying_price: float,
    strike: float,
    option_type: str,
    days_to_expiry: int,
    implied_volatility: float,
) -> float:
    intrinsic_value = max(underlying_price - strike, 0.0) if option_type == "CALL" else max(strike - underlying_price, 0.0)
    moneyness_gap = abs(underlying_price - strike) / underlying_price
    time_value = underlying_price * implied_volatility * max(days_to_expiry, 1) / 365 * max(0.15, 1 - moneyness_gap)
    return round(max(0.1, intrinsic_value + time_value), 2)


def generate_options_event() -> dict[str, object]:
    symbol = random.choice(list(SYMBOLS.keys()))
    base_price = SYMBOLS[symbol]
    underlying_price = round(base_price * random.uniform(0.97, 1.03), 2)
    option_type = random.choice(OPTION_TYPES)
    strike_step = get_strike_step(symbol)
    strike = round_to_step(underlying_price + random.randint(-8, 8) * strike_step, strike_step)
    expiration_date = get_next_friday(datetime.now(timezone.utc) + timedelta(days=random.randint(7, 60)))
    days_to_expiry = max((expiration_date.date() - datetime.now(timezone.utc).date()).days, 1)
    implied_volatility = round(random.uniform(0.15, 1.20), 4)
    mid_price = estimate_option_mid(
        underlying_price=underlying_price,
        strike=strike,
        option_type=option_type,
        days_to_expiry=days_to_expiry,
        implied_volatility=implied_volatility,
    )
    spread = round(max(0.01, min(mid_price * random.uniform(0.01, 0.08), 0.75)), 2)
    bid = round(max(0.01, mid_price - spread / 2), 2)
    ask = round(max(bid, mid_price + spread / 2), 2)
    last_price = round(random.uniform(bid, ask), 2)
    open_interest = random.randint(50, 15000)
    if random.random() < 0.08:
        volume = random.randint(2000, 25000)
    else:
        volume = random.randint(0, 2000)
    delta_distance = min(abs(underlying_price - strike) / max(underlying_price * 0.12, 1), 1)
    if option_type == "CALL":
        delta = round(max(0.05, min(0.95, 0.85 - delta_distance * 0.65 + random.uniform(-0.08, 0.08))), 2)
    else:
        delta = round(min(-0.05, max(-0.95, -0.85 + delta_distance * 0.65 + random.uniform(-0.08, 0.08))), 2)

    return {
        "event_id": f"evt_{uuid.uuid4().hex}",
        "symbol": symbol,
        "contract_symbol": generate_contract_symbol(
            symbol=symbol,
            expiration_date=expiration_date,
            strike=strike,
            option_type=option_type,
        ),
        "expiration_date": expiration_date.date().isoformat(),
        "strike": strike,
        "option_type": option_type,
        "bid": bid,
        "ask": ask,
        "last_price": last_price,
        "volume": volume,
        "open_interest": open_interest,
        "implied_volatility": implied_volatility,
        "delta": delta,
        "underlying_price": underlying_price,
        "event_timestamp": random_timestamp(),
        "source": "simulated",
    }


def generate_options_events(count: int) -> list[dict[str, object]]:
    return [generate_options_event() for _ in range(count)]

def write_jsonl(records: list[dict[str, object]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate simulated unusual options activity events.")
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw/options_events.jsonl",
    )

    args = parser.parse_args()

    records = generate_options_events(args.count)
    output_path = Path(args.output)
    write_jsonl(records, output_path)

    print(f"Wrote {len(records)} options events to {output_path}")


if __name__ == "__main__":
    main()
