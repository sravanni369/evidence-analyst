import io
import zipfile
import pandas as pd
import pytest
from core import clean, read_csv, answer, regression, export_bundle
from ai import validate

def test_clean_preserves_nulls_and_normalizes_before_dedup():
    df, audit = clean(pd.DataFrame({'region':[' East ', 'East', None], 'revenue':[2,2,None]}))
    assert len(df) == 2 and audit['duplicates_removed'] == 1
    assert df['revenue'].isna().sum() == 1

def test_known_answer():
    df = pd.DataFrame({'region':['A','A','B'], 'revenue':[2,3,4]})
    assert answer(df,'Revenue by region')['revenue'].tolist() == [5,4]

def test_refuses_unsupported_offline_question():
    with pytest.raises(ValueError): answer(pd.DataFrame({'a':[1]}), 'invent a forecast')

def test_limits_and_empty():
    with pytest.raises(ValueError): read_csv(b'a\n')
    with pytest.raises(ValueError): read_csv(b'0' * (5*1024*1024+1))

def test_export_guards_formula_cells():
    df = pd.DataFrame({'text':['=HYPERLINK("bad")']})
    with zipfile.ZipFile(io.BytesIO(export_bundle(df, {}))) as z:
        assert "'=HYPERLINK" in z.read('cleaned.csv').decode()
        assert {'audit.json','cleaned.csv','quality.csv'} <= set(z.namelist())

def test_ml_target_leakage_guard():
    with pytest.raises(ValueError): regression(pd.DataFrame({'a':range(30)}),'a',['a'])

def test_reproducible_holdout_and_baseline():
    df = pd.DataFrame({'x':range(80), 'y':[v*2 for v in range(80)]})
    a,p = regression(df,'y',['x']); b,q = regression(df,'y',['x'])
    assert a == b and a['test_rows'] == 20
    assert a['model_mae'] < a['baseline_mae']

def test_lint_refuses_shell_import():
    with pytest.raises(ValueError): validate('import subprocess')
