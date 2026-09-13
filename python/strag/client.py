"""Small CLI client for the RAG query API.

Works against either the Python service (default, port 8000) or the Go API
(port 8080) since both expose a compatible ``POST /query`` endpoint.

Examples::

    strag-query "Are there any transactions in EUR?"
    strag-query --url http://localhost:8080/query "Get data for account_id ACC-0833"
"""

from __future__ import annotations

import argparse
import sys

import httpx


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Query the Stream RAG Agent API")
    parser.add_argument("prompt", help="the question to ask")
    parser.add_argument(
        "--url", default="http://localhost:8000/query",
        help="query endpoint (default: the Python service on :8000)",
    )
    parser.add_argument(
        "--timeout", type=float, default=120.0,
        help="request timeout in seconds (default: 120)",
    )
    args = parser.parse_args(argv)

    try:
        resp = httpx.post(
            args.url, json={"prompt": args.prompt}, timeout=args.timeout
        )
    except httpx.HTTPError as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        return 1

    if resp.status_code != httpx.codes.OK:
        print(f"HTTP {resp.status_code}: {resp.text}", file=sys.stderr)
        return 1

    data = resp.json()
    if data.get("error"):
        print(f"Error: {data['error']}", file=sys.stderr)
        return 1

    print(data.get("answer", ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
