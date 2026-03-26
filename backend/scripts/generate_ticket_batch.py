"""Generate synthetic ticket batches for load testing.

Run with:
./venv/bin/python -m backend.scripts.generate_ticket_batch output.json --count 10000
"""

import argparse
import json
import random
from pathlib import Path


MODULES = {
    "billing": [
        ("Card payments fail after checkout redirect", "Customers return from bank auth and payments are marked declined."),
        ("Subscription renewals missing in billing report", "Daily billing exports exclude some renewed subscriptions."),
        ("Wallet top-up errors in mobile app", "Top-up requests fail after confirmation for repeat users."),
    ],
    "auth": [
        ("SSO callback returns to login", "Enterprise users complete SAML auth but land back on the login screen."),
        ("OTP delivery delayed", "Users receive one-time passwords too late to finish login."),
        ("Password reset token rejected", "Reset links are reported invalid immediately after generation."),
    ],
    "search": [
        ("Search results miss exact SKU", "Customers searching by SKU do not see exact product matches."),
        ("Facet filters degrade relevance", "Applying filters lowers ranking quality across category pages."),
        ("Autocomplete suggestions stale", "Users see outdated suggestions after catalog updates."),
    ],
    "shipping": [
        ("Warehouse dispatch labels missing", "Bulk orders are not receiving labels from dispatch integration."),
        ("Carrier webhook updates delayed", "Shipment status updates are delayed for EU carriers."),
        ("Tracking URLs broken in notifications", "Customers click shipping links that return 404 pages."),
    ],
    "analytics": [
        ("Revenue dashboard mismatch", "Finance dashboard totals do not match payment settlement reports."),
        ("Daily cohort report stale", "Morning analytics job leaves cohort charts one day behind."),
        ("Exported KPI CSV missing rows", "Scheduled KPI exports omit some enterprise accounts."),
    ],
}

PRIORITIES = ["Low", "Medium", "High", "Critical"]
SEGMENTS = ["retail", "enterprise", "partner"]
CHANNELS = ["web", "mobile", "support", "chat"]


def build_ticket(seq: int) -> dict:
    module = random.choice(list(MODULES))
    title, description = random.choice(MODULES[module])
    segment = random.choice(SEGMENTS)
    channel = random.choice(CHANNELS)
    priority = random.choices(PRIORITIES, weights=[1, 2, 4, 2], k=1)[0]
    return {
        "title": f"[{seq}] {title}",
        "description": f"{description} Impacted segment: {segment}. Intake channel: {channel}.",
        "module": module,
        "priority": priority,
        "customer_segment": segment,
        "channel": channel,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a synthetic ticket batch file.")
    parser.add_argument("output_path", type=Path)
    parser.add_argument("--count", type=int, default=10000)
    args = parser.parse_args()

    tickets = [build_ticket(index) for index in range(1, args.count + 1)]
    args.output_path.write_text(json.dumps(tickets, indent=2), encoding="utf-8")
    print(json.dumps({"output_path": str(args.output_path), "count": len(tickets)}))


if __name__ == "__main__":
    main()