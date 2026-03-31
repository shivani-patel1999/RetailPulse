# Phase 1 Setup Guide — Synthetic Data Generator

## What This Does
Generates ~500 realistic retail transactions daily and uploads them
directly to Google Cloud Storage as a dated CSV file, e.g.:

```
gs://retailpulse-raw/raw_sales/2024/03/2024-03-15.csv
```

Runs automatically every night at 00:15 UTC via GitHub Actions.

---

## One-Time Setup (do this once)

### Step 1 — Create your GitHub repo
1. Go to github.com → New repository → name it `retailpulse`
2. Clone it to your computer:
   ```bash
   git clone https://github.com/YOUR_USERNAME/retailpulse.git
   ```
3. Copy all project files into the cloned folder

### Step 2 — Create a GCS Bucket
1. Go to console.cloud.google.com
2. Search "Cloud Storage" → Create Bucket
3. Name it: `retailpulse-raw` (must be globally unique — add your initials if taken)
4. Region: `us-central1` (cheapest)
5. Leave all other settings as default → Create

### Step 3 — Create a GCP Service Account Key
This is how GitHub Actions authenticates with GCP securely.

1. In GCP Console → IAM & Admin → Service Accounts
2. Click "Create Service Account"
   - Name: `retailpulse-uploader`
   - Click "Create and Continue"
3. Grant role: **Storage Object Admin** → Continue → Done
4. Click the service account → Keys tab → Add Key → JSON
5. A `.json` file downloads — keep this safe, treat it like a password

### Step 4 — Add GitHub Secrets
1. Go to your GitHub repo → Settings → Secrets and variables → Actions
2. Add these two secrets:

| Secret Name              | Value                                      |
|--------------------------|--------------------------------------------|
| `GCS_BUCKET_NAME`        | `retailpulse-raw` (your bucket name)       |
| `GCP_SERVICE_ACCOUNT_KEY`| Paste the ENTIRE contents of the JSON file |

### Step 5 — Push to GitHub
```bash
cd retailpulse
git add .
git commit -m "feat: add Phase 1 data generator"
git push origin main
```

---

## Testing It Works

### Option A — Manual trigger (recommended first test)
1. Go to your GitHub repo → Actions tab
2. Click "Daily Retail Data Generation" workflow
3. Click "Run workflow" → Run workflow
4. Watch the logs — you should see:
   ```
   🛒 Generating 500 transactions for 2024-03-14 ...
   ☁️  Uploading to GCS bucket 'retailpulse-raw' ...
   ✅ Uploaded 500 rows → gs://retailpulse-raw/raw_sales/2024/03/2024-03-14.csv
   🎉 Done!
   ```
5. Check your GCS bucket — the file should be there!

### Option B — Run locally
```bash
pip install -r data_generator/requirements.txt
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/key.json"
export GCS_BUCKET_NAME="retailpulse-raw"
python data_generator/generate_data.py
```

---

## What the Data Looks Like

| Column         | Type    | Example                    | Notes                        |
|----------------|---------|----------------------------|------------------------------|
| order_id       | string  | ORD-20240315-00142         | Unique per transaction       |
| timestamp      | datetime| 2024-03-15 14:32:11        | Store hours only (8am–10pm)  |
| store_id       | string  | STORE_03                   | 5 stores across US cities    |
| store_city     | string  | Chicago                    |                              |
| product_sku    | string  | SKU-8821                   | Randomly assigned            |
| category       | string  | Electronics                | 6 categories                 |
| quantity       | int     | 2                          | 1–5 units                    |
| unit_price     | float   | 49.99                      | Varies by category           |
| discount_pct   | float   | 0.10                       | 0%, 5%, 10%, 15%, 20%, 25%   |
| net_amount     | float   | 89.98                      | quantity × price × (1-disc)  |
| payment_method | string  | Credit Card                | 5 methods                    |
| customer_age   | int     | 34                         | 18–75                        |
| return_flag    | boolean | False                      | ~4% return rate              |

---

## Folder Structure After Phase 1
```
retailpulse/
├── .github/
│   └── workflows/
│       └── daily_data.yml      ← GitHub Actions schedule
├── data_generator/
│   ├── generate_data.py        ← main script
│   └── requirements.txt        ← dependencies
└── PHASE1_SETUP.md             ← this file
```

---

## Next Step → Phase 2
Once data is landing in GCS daily, Phase 2 will set up BigQuery
to auto-ingest each new CSV file into a queryable data warehouse table.
