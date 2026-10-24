"""Known-answer tests on one real month of the UCI Online Retail dataset (CC BY 4.0).

Expected values were computed independently of pandas, with Python's csv module and
exact Decimal arithmetic over data/online_retail_2010-12.csv (see VALIDATION.txt).
"""
import csv
import io
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from core import answer, clean, read_csv

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'online_retail_2010-12.csv'


@pytest.fixture(scope='module')
def cleaned():
    return clean(read_csv(DATA.read_bytes()))


def test_real_cleaning_audit(cleaned):
    _, audit = cleaned
    assert audit['input_rows'] == 42481
    assert audit['output_rows'] == 41981
    assert audit['duplicates_removed'] == 500
    assert audit['missing_cells'] == 15627  # all missing customer IDs, kept, not imputed


def test_real_revenue_by_region_matches_independent_decimal_sum(cleaned):
    df, _ = cleaned
    app = answer(df, 'Revenue by region').set_index('region')['revenue']
    rows = list(csv.DictReader(DATA.open(newline='', encoding='utf-8')))
    seen, expected = set(), defaultdict(Decimal)
    for row in rows:
        key = tuple(v.strip() for v in row.values())
        if key not in seen:
            seen.add(key)
            expected[row['region'].strip()] += Decimal(row['revenue'])
    assert len(app) == len(expected) == 24
    for region, total in expected.items():
        assert abs(Decimal(str(app[region])) - total) < Decimal('0.005'), region
    assert round(float(app.sum()), 2) == 746723.61
    assert round(float(app['United Kingdom']), 2) == 674615.86


def test_uploaded_file_is_not_labelled_synthetic(monkeypatch):
    import streamlit

    class Upload(io.BytesIO):
        name = 'online_retail_2010-12.csv'

    monkeypatch.setattr(streamlit, 'file_uploader', lambda *a, **kw: Upload(DATA.read_bytes()))
    app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=60).run()
    assert not app.exception
    banner = app.info[0].value
    assert 'online_retail_2010-12.csv' in banner and 'synthetic' not in banner
    assert [m.value for m in app.metric] == ['41981', '500', '15627']
