"""Multi-topic Kafka producer.

Unlike the Go producer (which only emits ``financial_transactions``), this one
can also emit ``sensor_data``, matching the second topic defined in
``configs/configs.yml``.

Examples::

    strag-producer --topic financial --rate 10
    strag-producer --topic sensor --count 500
    strag-producer --topic all
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import string
import sys
import time
from datetime import datetime, timedelta, timezone

from confluent_kafka import Producer

from .config import load_config

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("strag.producer")

FINANCIAL_TOPIC = "financial_transactions"
SENSOR_TOPIC = "sensor_data"

_TX_TYPES = ["purchase", "refund", "transfer", "withdrawal", "deposit"]
_CURRENCIES = ["USD", "EUR", "GBP", "TRY"]
_DESCRIPTIONS = [
    "Online shopping", "Utility bill payment", "Salary deposit", "ATM withdrawal",
    "Restaurant bill", "Subscription renewal", "Friend payment", "Loan repayment",
    "Investment", "Travel expense",
]
_MACHINES = ["press-01", "press-02", "lathe-07", "conveyor-03", "compressor-05"]
_SENSOR_STATUS = ["normal", "normal", "normal", "warning", "critical"]


def _rand_seq(n: int) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choice(alphabet) for _ in range(n))


def _now_iso(jitter_seconds: int = 3600) -> str:
    ts = datetime.now(timezone.utc) - timedelta(seconds=random.randint(0, jitter_seconds))
    return ts.isoformat()


def make_financial_transaction(index: int) -> tuple[str, dict]:
    tx = {
        "transaction_id": f"TXN-{index}-{_rand_seq(8)}",
        "amount": round((random.randint(0, 99999) + 1) / 100, 2),
        "currency": random.choice(_CURRENCIES),
        "type": random.choice(_TX_TYPES),
        "timestamp": _now_iso(),
        "description": random.choice(_DESCRIPTIONS),
        "account_id": f"ACC-{random.randint(1, 1000):04d}",
    }
    return tx["transaction_id"], tx


def make_sensor_reading(index: int) -> tuple[str, dict]:
    reading = {
        "sensor_id": f"SEN-{index}-{_rand_seq(6)}",
        "machine_id": random.choice(_MACHINES),
        "temperature_c": round(random.uniform(20.0, 110.0), 2),
        "pressure_bar": round(random.uniform(1.0, 12.0), 2),
        "vibration_mm_s": round(random.uniform(0.0, 8.0), 3),
        "status": random.choice(_SENSOR_STATUS),
        "timestamp": _now_iso(300),
    }
    return reading["sensor_id"], reading


_GENERATORS = {
    FINANCIAL_TOPIC: make_financial_transaction,
    SENSOR_TOPIC: make_sensor_reading,
}


def _delivery_report(err, msg) -> None:
    if err is not None:
        logger.warning("Delivery failed for %s: %s", msg.key(), err)


def run(brokers: list[str], topics: list[str], rate: float, count: int) -> None:
    producer = Producer({"bootstrap.servers": ",".join(brokers)})
    interval = 1.0 / rate if rate > 0 else 0.0
    logger.info(
        "Producing to %s via %s (rate=%s msg/s, count=%s)",
        ", ".join(topics), brokers, rate, count or "infinite",
    )

    sent = 0
    try:
        i = 0
        while count == 0 or sent < count:
            topic = topics[i % len(topics)]
            key, payload = _GENERATORS[topic](i)
            producer.produce(
                topic,
                key=key.encode("utf-8"),
                value=json.dumps(payload).encode("utf-8"),
                on_delivery=_delivery_report,
            )
            producer.poll(0)
            sent += 1
            i += 1
            if sent % 50 == 0:
                logger.info("Sent %d messages", sent)
            if interval:
                time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Interrupted, flushing...")
    finally:
        producer.flush(10)
        logger.info("Done. Total messages sent: %d", sent)


def _resolve_topics(selection: str) -> list[str]:
    if selection == "financial":
        return [FINANCIAL_TOPIC]
    if selection == "sensor":
        return [SENSOR_TOPIC]
    if selection == "all":
        return [FINANCIAL_TOPIC, SENSOR_TOPIC]
    # Treat anything else as an explicit topic name.
    return [selection]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stream RAG Agent Kafka producer")
    parser.add_argument(
        "--topic", default="financial",
        help="financial | sensor | all | <explicit topic name> (default: financial)",
    )
    parser.add_argument(
        "--rate", type=float, default=10.0,
        help="messages per second, 0 for as-fast-as-possible (default: 10)",
    )
    parser.add_argument(
        "--count", type=int, default=0,
        help="total messages to send, 0 for infinite (default: 0)",
    )
    parser.add_argument(
        "--brokers", default=None,
        help="comma-separated broker list; overrides config/env",
    )
    args = parser.parse_args(argv)

    cfg = load_config()
    brokers = (
        [b.strip() for b in args.brokers.split(",") if b.strip()]
        if args.brokers
        else cfg.kafka.brokers
    )
    topics = _resolve_topics(args.topic)
    run(brokers, topics, args.rate, args.count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
