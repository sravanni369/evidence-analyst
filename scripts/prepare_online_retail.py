"""Download one real month of the UCI Online Retail dataset and map it to the app's columns.

Source: Daqing Chen, "Online Retail", UCI Machine Learning Repository (2015),
https://doi.org/10.24432/C5BW33, licensed CC BY 4.0. Real UK online-retailer transactions,
December 2010 to December 2011.

The month is deliberately NOT pre-cleaned: duplicates, missing customer IDs and
cancellations (negative quantities) stay in, so the app's own cleaning is what gets tested.

Usage:  python scripts/prepare_online_retail.py            (needs openpyxl and internet)
Output: data/online_retail_2010-12.csv
"""
import hashlib
import io
import sys
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

URL = 'https://archive.ics.uci.edu/static/public/352/online+retail.zip'
SHA256 = 'f5385cbb54bbebf7196389109c6b0621faab0c304e3702548165e71c84aede8b'
MONTH = '2010-12'
OUT = Path(__file__).resolve().parents[1] / 'data' / f'online_retail_{MONTH}.csv'


def main():
    raw = urllib.request.urlopen(URL, timeout=120).read()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SHA256:
        sys.exit(f'Checksum mismatch: got {digest}. The upstream file changed; review before using it.')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        df = pd.read_excel(z.open('Online Retail.xlsx'), dtype={'InvoiceNo': str, 'StockCode': str})
    month = df[df['InvoiceDate'].dt.strftime('%Y-%m') == MONTH]
    out = pd.DataFrame({
        'order_id': month['InvoiceNo'],
        'stock_code': month['StockCode'],
        'order_date': month['InvoiceDate'].dt.strftime('%Y-%m-%d %H:%M'),
        'region': month['Country'],
        'customer_id': month['CustomerID'].astype('Int64'),
        'units': month['Quantity'],
        'unit_price': month['UnitPrice'],
        # Line revenue as recorded: quantity x unit price. Cancellations are negative.
        'revenue': (month['Quantity'] * month['UnitPrice']).round(2),
    })
    OUT.write_text(out.to_csv(index=False), encoding='utf-8')
    print(f'Wrote {len(out):,} rows to {OUT} ({OUT.stat().st_size / 1e6:.2f} MB)')


if __name__ == '__main__':
    main()
