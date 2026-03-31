"""
RetailPulse — Daily Synthetic Data Generator
Generates ~500 realistic retail transactions for the previous day
and uploads the CSV directly to Google Cloud Storage.

Usage:
  Local:          python generate_data.py
  GitHub Actions: runs automatically via .github/workflows/daily_data.yml
"""

import os
import io
import random
from datetime import datetime, timedelta

import pandas as pd
from faker import Faker
from google.cloud import storage

# ── Config ────────────────────────────────────────────────────────────────────

GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", "retailpulse-raw")
NUM_TRANSACTIONS = 500
RANDOM_SEED      = 42  # remove for true randomness each run

fake = Faker()
Faker.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

# ── Reference Data ────────────────────────────────────────────────────────────

STORES = {
    "STORE_01": "New York",
    "STORE_02": "Los Angeles",
    "STORE_03": "Chicago",
    "STORE_04": "Houston",
    "STORE_05": "Phoenix",
}

CATEGORIES = {
    "Electronics":   {"min": 29.99,  "max": 999.99, "weight": 0.15},
    "Clothing":      {"min": 9.99,   "max": 199.99, "weight": 0.25},
    "Groceries":     {"min": 2.99,   "max": 89.99,  "weight": 0.30},
    "Home & Garden": {"min": 14.99,  "max": 399.99, "weight": 0.15},
    "Sports":        {"min": 19.99,  "max": 299.99, "weight": 0.10},
    "Toys":          {"min": 4.99,   "max": 149.99, "weight": 0.05},
}

PAYMENT_METHODS = ["Credit Card", "Debit Card", "Cash", "Mobile Pay", "Gift Card"]
PAYMENT_WEIGHTS  = [0.40,          0.30,         0.10,  0.15,          0.05]

DISCOUNT_TIERS = [0.0, 0.0, 0.0, 0.05, 0.10, 0.15, 0.20, 0.25]  # 0.0 weighted heavily = no discount


# ── Generator ─────────────────────────────────────────────────────────────────

def generate_transactions(date: datetime.date, n: int = NUM_TRANSACTIONS) -> pd.DataFrame:
    """Generate n synthetic retail transactions for a given date."""

    categories = list(CATEGORIES.keys())
    cat_weights = [CATEGORIES[c]["weight"] for c in categories]

    rows = []
    for i in range(1, n + 1):
        category    = random.choices(categories, weights=cat_weights)[0]
        cat_info    = CATEGORIES[category]
        unit_price  = round(random.uniform(cat_info["min"], cat_info["max"]), 2)
        quantity    = random.choices([1, 2, 3, 4, 5], weights=[0.55, 0.25, 0.10, 0.06, 0.04])[0]
        discount    = random.choice(DISCOUNT_TIERS)
        net_amount  = round(unit_price * quantity * (1 - discount), 2)
        store_id    = random.choice(list(STORES.keys()))
        is_return   = random.random() < 0.04  # ~4% return rate

        # Transactions happen mostly during store hours (8am–10pm)
        hour        = random.choices(range(8, 23), weights=[3,4,5,7,8,9,10,10,9,8,7,6,5,4,3])[0]
        minute      = random.randint(0, 59)
        second      = random.randint(0, 59)
        timestamp   = datetime.combine(date, datetime.min.time()).replace(
                          hour=hour, minute=minute, second=second)

        rows.append({
            "order_id":        f"ORD-{date.strftime('%Y%m%d')}-{i:05d}",
            "timestamp":       timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "store_id":        store_id,
            "store_city":      STORES[store_id],
            "product_sku":     f"SKU-{random.randint(1000, 9999)}",
            "category":        category,
            "quantity":        quantity,
            "unit_price":      unit_price,
            "discount_pct":    discount,
            "net_amount":      net_amount,
            "payment_method":  random.choices(PAYMENT_METHODS, weights=PAYMENT_WEIGHTS)[0],
            "customer_age":    random.randint(18, 75),
            "return_flag":     is_return,
        })

    df = pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)
    return df


# ── GCS Upload ────────────────────────────────────────────────────────────────

def upload_to_gcs(df: pd.DataFrame, date: datetime.date, bucket_name: str) -> str:
    """Upload DataFrame as CSV to GCS. Returns the GCS URI."""

    blob_name = f"raw_sales/{date.strftime('%Y/%m')}/{date.isoformat()}.csv"

    client = storage.Client()           # authenticates via GOOGLE_APPLICATION_CREDENTIALS
    bucket = client.bucket(bucket_name)
    blob   = bucket.blob(blob_name)

    # Write CSV to in-memory buffer (no temp file needed)
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    blob.upload_from_string(buffer.getvalue(), content_type="text/csv")

    gcs_uri = f"gs://{bucket_name}/{blob_name}"
    print(f"✅ Uploaded {len(df)} rows → {gcs_uri}")
    return gcs_uri


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Generate data for yesterday (so a midnight run always covers the full day)
    target_date = (datetime.utcnow() - timedelta(days=1)).date()
    print(f"🛒 Generating {NUM_TRANSACTIONS} transactions for {target_date} ...")

    df = generate_transactions(target_date)
    print(df.head(3).to_string(index=False))
    print(f"   ... {len(df)} rows total\n")

    print(f"☁️  Uploading to GCS bucket '{GCS_BUCKET_NAME}' ...")
    gcs_uri = upload_to_gcs(df, target_date, GCS_BUCKET_NAME)

    print(f"\n🎉 Done! File available at: {gcs_uri}")


if __name__ == "__main__":
    main()
