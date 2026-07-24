#!/usr/bin/env python3
"""Generate synthetic, deliberately messy KPC order-to-cash source data.

KPC does not expose its live loading/dispatch/billing systems for this
hackathon, so this script simulates four raw exports that a depot
operations + finance stack would realistically produce:

    loading_events.csv   - depot gate: product loaded onto a truck
    dispatch_events.csv  - depot gate: truck exits, dispatch confirmed
    invoices.csv         - finance/billing: invoice raised against a dispatch
    payments.csv         - finance/AR: payment received against an invoice

Revenue-leakage scenarios (dispatched-not-invoiced, under-billed volume,
unpaid/partial invoices, shrinkage) and generic data-quality mess (mixed
date formats, currency-formatted numbers, alias/casing drift on depot
names, missing fields) are injected on purpose so the pipeline in
src/o2c_pipeline has something real to clean, validate, and reconcile.

Internally every event keeps a real `datetime` object so that downstream
timestamps (e.g. dispatch = loading + N minutes) are computed off true
chronology. Only the CSV-facing string is rendered in a randomly chosen,
ambiguous format (mixed "%Y-%m-%d %H:%M" / "%d/%m/%Y %H:%M") -- that
ambiguity is the mess the pipeline's cleaning step must resolve per-row,
not something the generator should ever re-parse itself.

Run: python scripts/generate_synthetic_data.py
"""

import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from o2c_pipeline.config import DATA_RAW_DIR, DEPOTS

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

START_DATE = datetime(2026, 6, 1)
NUM_DAYS = 45

CUSTOMERS = [
    "Rift Valley Fuels Ltd", "Savannah Petroleum", "Lakeview Energy",
    "Horizon Oil Marketers", "Baraka Downstream", "Tsavo Energy Group",
    "Equator Fuels", "Nyanza Petroleum Co", "Aberdare Oil Traders",
    "Coastline Energy Ltd", "Mara Fuels", "Zenith Petroleum",
    "Summit Downstream Ltd", "Uhuru Energy Partners", "Kilele Fuels",
    "Delta Oil Marketers", "Amani Petroleum", "Highland Energy Co",
    "Pioneer Fuels Kenya", "Crescent Oil Ltd",
]

PRODUCT_WEIGHTS = {"PMS": 0.45, "AGO": 0.45, "IK": 0.10}
DEPOT_ALIAS_VARIANTS = {
    "Mombasa": ["Mombasa", "MOMBASA", "mombasa", "Msa"],
    "Nairobi": ["Nairobi", "NAIROBI", "Nairobi Depot", "nrb"],
    "Kisumu": ["Kisumu", "KISUMU", "Ksm"],
    "Eldoret": ["Eldoret", "ELDORET", "Eld"],
    "Nakuru": ["Nakuru", "NAKURU", "Nku"],
    "Kisii": ["Kisii", "KISII", " Kisii "],
}
UNIT_PRICE = {"PMS": 165.50, "AGO": 155.20, "IK": 140.00}
DATE_FORMATS = ["%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M"]


def messy_date(dt: datetime) -> str:
    """Render a real datetime as a string in a randomly chosen export format.

    This is purely cosmetic mess for the CSV -- callers must keep using the
    original `dt` object for any further date arithmetic, never re-parse
    the string this returns.
    """
    return dt.strftime(random.choice(DATE_FORMATS))


def messy_depot(depot: str) -> str:
    return random.choice(DEPOT_ALIAS_VARIANTS[depot])


def messy_amount(value: float) -> str:
    """Format some amounts as comma-thousands strings, like a finance export."""
    if random.random() < 0.15:
        return f"{value:,.2f}"
    return f"{value:.2f}"


def weighted_product() -> str:
    return random.choices(list(PRODUCT_WEIGHTS), weights=list(PRODUCT_WEIGHTS.values()))[0]


def build_loading_events():
    rows = []
    loading_seq = 1
    for day_offset in range(NUM_DAYS):
        day = START_DATE + timedelta(days=day_offset)
        for depot in DEPOTS:
            n_loadings = np.random.randint(6, 16)
            for _ in range(n_loadings):
                loading_id = f"LD{loading_seq:06d}"
                loading_seq += 1
                product = weighted_product()
                volume = round(np.random.uniform(20000, 36000) / 100) * 100
                loading_dt = day + timedelta(
                    hours=random.randint(5, 22), minutes=random.randint(0, 59)
                )
                customer = random.choice(CUSTOMERS)
                if random.random() < 0.01:
                    customer = ""  # missing customer at point of capture
                truck_id = f"TRK-{random.randint(100, 999)}"
                meter_start = round(np.random.uniform(1_000_000, 5_000_000), 1)
                meter_end = round(meter_start + volume + np.random.normal(0, 5), 1)
                rows.append({
                    "loading_id": loading_id,
                    "depot": messy_depot(depot),
                    "product": product,
                    "customer": customer,
                    "truck_id": truck_id,
                    "volume_loaded_litres": volume,
                    "meter_start": meter_start,
                    "meter_end": meter_end,
                    "loading_ts": messy_date(loading_dt),
                    "_loading_dt": loading_dt,
                })
    return pd.DataFrame(rows)


def build_dispatch_events(loadings: pd.DataFrame):
    rows = []
    dispatch_seq = 1
    for _, ld in loadings.iterrows():
        if random.random() < 0.01:
            continue  # gate never confirmed dispatch -- capture gap
        loading_dt = ld["_loading_dt"]
        dispatch_dt = loading_dt + timedelta(minutes=random.randint(30, 180))
        volume_loaded = ld["volume_loaded_litres"]

        if random.random() < 0.012:
            # material shrinkage / suspected theft or meter drift in transit
            loss_pct = np.random.uniform(0.03, 0.08)
            volume_dispatched = round(volume_loaded * (1 - loss_pct))
        else:
            volume_dispatched = round(volume_loaded + np.random.normal(0, volume_loaded * 0.003))

        status = "Dispatched"
        if random.random() < 0.01:
            status = "Cancelled"

        dispatch_id = f"DS{dispatch_seq:06d}"
        dispatch_seq += 1
        rows.append({
            "dispatch_id": dispatch_id,
            "loading_id": ld["loading_id"],
            "destination_customer": ld["customer"],
            "volume_dispatched_litres": volume_dispatched,
            "dispatch_ts": messy_date(dispatch_dt),
            "status": status,
            "_dispatch_dt": dispatch_dt,
        })
    return pd.DataFrame(rows)


def build_invoices(dispatches: pd.DataFrame, loadings: pd.DataFrame):
    loading_lookup = loadings.set_index("loading_id")
    rows = []
    invoice_seq = 1
    for _, ds in dispatches.iterrows():
        if ds["status"] == "Cancelled":
            continue
        if random.random() < 0.015:
            continue  # dispatched but never invoiced -- core O2C leak

        ld = loading_lookup.loc[ds["loading_id"]]
        product = ld["product"]
        dispatch_dt = ds["_dispatch_dt"]
        invoice_lag_days = np.random.choice([0, 1, 2, 3, 7, 10], p=[0.45, 0.25, 0.15, 0.08, 0.05, 0.02])
        invoice_dt = dispatch_dt + timedelta(days=int(invoice_lag_days), hours=random.randint(0, 8))

        volume_dispatched = ds["volume_dispatched_litres"]
        if random.random() < 0.02:
            volume_invoiced = round(volume_dispatched * np.random.uniform(0.90, 0.985))
        else:
            volume_invoiced = volume_dispatched

        unit_price = UNIT_PRICE[product] * np.random.uniform(0.98, 1.02)
        unit_price_str = "" if random.random() < 0.02 else f"{unit_price:.2f}"
        amount = volume_invoiced * unit_price

        invoice_id = f"INV{invoice_seq:06d}"
        invoice_seq += 1
        customer = ds["destination_customer"] or ld["customer"]
        rows.append({
            "invoice_id": invoice_id,
            "dispatch_id": ds["dispatch_id"],
            "customer": customer,
            "product": product,
            "volume_invoiced_litres": volume_invoiced,
            "unit_price_kes": unit_price_str,
            "amount_kes": messy_amount(amount),
            "invoice_date": messy_date(invoice_dt),
            "currency": "KES",
            "_invoice_dt": invoice_dt,
        })

        if random.random() < 0.01:
            # accidental duplicate invoice for the same dispatch
            dup_invoice_id = f"INV{invoice_seq:06d}"
            invoice_seq += 1
            dup_invoice_dt = invoice_dt + timedelta(hours=1)
            rows.append({
                "invoice_id": dup_invoice_id,
                "dispatch_id": ds["dispatch_id"],
                "customer": customer,
                "product": product,
                "volume_invoiced_litres": volume_invoiced,
                "unit_price_kes": unit_price_str,
                "amount_kes": messy_amount(amount),
                "invoice_date": messy_date(dup_invoice_dt),
                "currency": "KES",
                "_invoice_dt": dup_invoice_dt,
            })
    return pd.DataFrame(rows)


def build_payments(invoices: pd.DataFrame):
    rows = []
    payment_seq = 1
    for _, inv in invoices.iterrows():
        roll = random.random()
        invoice_dt = inv["_invoice_dt"]
        amount = float(str(inv["amount_kes"]).replace(",", ""))

        if roll < 0.02:
            continue  # never paid

        if roll < 0.05:
            paid_amount = round(amount * np.random.uniform(0.3, 0.85), 2)
        else:
            paid_amount = amount

        pay_lag_days = np.random.choice(
            [1, 3, 7, 14, 21, 30, 45, 60],
            p=[0.15, 0.2, 0.2, 0.15, 0.1, 0.1, 0.06, 0.04],
        )
        payment_dt = invoice_dt + timedelta(days=int(pay_lag_days))
        payment_id = f"PMT{payment_seq:06d}"
        payment_seq += 1
        method = random.choice(["Bank Transfer", "RTGS", "Cheque", "Mobile Money"])
        rows.append({
            "payment_id": payment_id,
            "invoice_id": inv["invoice_id"],
            "amount_paid_kes": messy_amount(paid_amount),
            "payment_date": messy_date(payment_dt),
            "payment_method": method,
        })
    return pd.DataFrame(rows)


def main():
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

    loadings = build_loading_events()
    dispatches = build_dispatch_events(loadings)
    invoices = build_invoices(dispatches, loadings)
    payments = build_payments(invoices)

    # Drop internal-only true-chronology helper columns before writing the
    # "raw export" CSVs -- real KPC exports would never carry these.
    loadings.drop(columns=["_loading_dt"]).to_csv(DATA_RAW_DIR / "loading_events.csv", index=False)
    dispatches.drop(columns=["_dispatch_dt"]).to_csv(DATA_RAW_DIR / "dispatch_events.csv", index=False)
    invoices.drop(columns=["_invoice_dt"]).to_csv(DATA_RAW_DIR / "invoices.csv", index=False)
    payments.to_csv(DATA_RAW_DIR / "payments.csv", index=False)

    print(f"loading_events:  {len(loadings):>5} rows")
    print(f"dispatch_events: {len(dispatches):>5} rows")
    print(f"invoices:        {len(invoices):>5} rows")
    print(f"payments:        {len(payments):>5} rows")


if __name__ == "__main__":
    main()
