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


IOWA = ROOT / 'data' / 'iowa_liquor_2026-09-21_to_2026-09-27.csv'


def test_iowa_2026_week_matches_independent_decimal_sum():
    """Iowa Liquor Sales, 2026 (Iowa Dept. of Revenue, CC BY 4.0), week of 21-27 Sep 2026."""
    df, audit = clean(read_csv(IOWA.read_bytes()))
    assert (audit['input_rows'], audit['duplicates_removed'], audit['missing_cells']) == (48778, 0, 26)
    app = answer(df, 'Revenue by region')
    app = {(r if isinstance(r, str) else None): v for r, v in zip(app['region'], app['revenue'])}
    expected = defaultdict(Decimal)
    for row in csv.DictReader(IOWA.open(newline='', encoding='utf-8')):
        expected[row['region'].strip() or None] += Decimal(row['revenue'])
    assert len(app) == len(expected) == 100  # 99 counties + rows with no county
    for region, total in expected.items():
        assert abs(Decimal(str(app[region])) - total) < Decimal('0.005'), region
    assert round(sum(app.values()), 2) == 8090651.73
    assert round(app['POLK'], 2) == 1903101.82
