"""Download Iowa Liquor Sales, 2026 and extract one recent week for the app.

Source: Iowa Department of Revenue, Alcohol Operations Bureau, "Iowa Liquor Sales, 2026",
https://data.iowa.gov/catalog/dataset/1263 (also listed on catalog.data.gov), licensed CC BY 4.0.
Real wholesale spirits purchases by Iowa Class E liquor licensees (stores), January 2026 onward.

The extract is deliberately NOT pre-cleaned: missing counties, returns (negative bottle counts)
and duplicates stay in, so the app's own cleaning is what gets tested.

The full download is about 400 MB (zip of CSV parts) and is updated by the publisher, so its
checksum changes over time. Rows for a past week should be stable, but the publisher can revise
them; compare against the SHA-256 recorded in VALIDATION.txt.

Usage:  python scripts/prepare_iowa_2026.py [--zip PATH] [--start 2026-09-21] [--end 2026-09-27]
Output: data/iowa_liquor_2026-09-21_to_2026-09-27.csv
"""
import argparse
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

URL = 'https://idh-be.iowa.gov/api/v1/datasets/1263/rows.csv'
COLUMNS = {
    'invoice_id': 'order_id',
    'ordered_on': 'order_date',
    'store_no': 'store_no',
    'county_name': 'region',
    'category_name': 'category',
    'item_no': 'item_no',
    'sales_bottles': 'units',
    'state_bottle_retail': 'unit_price',
    'sales_dollars': 'revenue',
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--zip', type=Path, help='use an already-downloaded zip instead of downloading')
    ap.add_argument('--start', default='2026-09-21')
    ap.add_argument('--end', default='2026-09-27')
    args = ap.parse_args()

    if args.zip:
        zpath = args.zip
    else:
        zpath = Path(tempfile.gettempdir()) / 'iowa_liquor_sales_2026.zip'
        print(f'Downloading about 400 MB to {zpath} ...')
        urllib.request.urlretrieve(URL, zpath)

    parts = []
    with zipfile.ZipFile(zpath) as z:
        for name in sorted(n for n in z.namelist() if n.endswith('.csv')):
            for chunk in pd.read_csv(z.open(name), usecols=list(COLUMNS), dtype=str, chunksize=250_000):
                parts.append(chunk[(chunk['ordered_on'] >= args.start) & (chunk['ordered_on'] <= args.end)])
    week = pd.concat(parts)[list(COLUMNS)].rename(columns=COLUMNS)
    week = week.sort_values(['order_date', 'order_id', 'item_no'], kind='stable')

    out = Path(__file__).resolve().parents[1] / 'data' / f'iowa_liquor_{args.start}_to_{args.end}.csv'
    week.to_csv(out, index=False)  # values written exactly as published (read as text)
    print(f'Wrote {len(week):,} rows to {out} ({out.stat().st_size / 1e6:.2f} MB)')


if __name__ == '__main__':
    main()
