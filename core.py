"""Deterministic analysis. Generated Python is never executed on this host."""
import io
import json
import zipfile
import pandas as pd

MAX_BYTES = 5 * 1024 * 1024

def read_csv(data):
    if len(data) > MAX_BYTES:
        raise ValueError('CSV exceeds 5 MB limit')
    df = pd.read_csv(io.BytesIO(data))
    if df.empty or len(df) > 50000 or len(df.columns) > 100:
        raise ValueError('Use 1–50,000 rows and at most 100 columns')
    return df

def clean(df):
    result = df.copy()
    for col in result.select_dtypes(include=['object', 'string']):
        result[col] = result[col].str.strip().replace('', pd.NA)
    result = result.drop_duplicates().reset_index(drop=True)
    audit = {'input_rows': len(df), 'output_rows': len(result),
             'duplicates_removed': len(df)-len(result),
             'missing_cells': int(result.isna().sum().sum()),
             'policy': 'Trim strings and remove exact duplicates; preserve missing values. No automatic imputation.'}
    return result, audit

def profile(df):
    return pd.DataFrame({'column': df.columns, 'dtype': [str(x) for x in df.dtypes],
        'missing': df.isna().sum().values, 'unique': df.nunique().values})

def answer(df, question):
    q = question.lower().strip().rstrip('?')
    if q in ['how many rows', 'how many rows are there']:
        return pd.DataFrame({'rows': [len(df)]})
    if q in ['show missing values', 'what values are missing']:
        return profile(df)[['column', 'missing']]
    if q in ['summarize numeric columns', 'show summary statistics']:
        return df.describe().reset_index()
    if q in ['revenue by region', 'what is revenue by region'] and {'revenue', 'region'} <= set(df.columns):
        return df.groupby('region', dropna=False)['revenue'].sum(min_count=1).reset_index()
    raise ValueError('Offline demo supports: How many rows?; Show missing values; Summarize numeric columns; Revenue by region. Use AI mode for other questions.')

def regression(df, target, features):
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import make_pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.dummy import DummyRegressor
    from sklearn.metrics import mean_absolute_error
    if not features or target in features:
        raise ValueError('Select predictors that exclude the target')
    if not all(pd.api.types.is_numeric_dtype(df[c]) for c in [target] + features):
        raise ValueError('This demo requires numeric target and predictors')
    data = df.dropna(subset=[target]).drop_duplicates(subset=features + [target])
    if len(data) < 20 or data[target].nunique() < 2:
        raise ValueError('Need 20 distinct labeled rows and a varying target')
    if any(data[c].notna().sum() == 0 for c in features):
        raise ValueError('A predictor is entirely missing')
    xtrain, xtest, ytrain, ytest = train_test_split(data[features], data[target], test_size=.25, random_state=42)
    model = make_pipeline(SimpleImputer(strategy='median'), RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=1))
    model.fit(xtrain, ytrain)
    baseline = DummyRegressor(strategy='mean').fit(xtrain, ytrain)
    pred = model.predict(xtest)
    metrics = {'model_mae': float(mean_absolute_error(ytest, pred)),
        'baseline_mae': float(mean_absolute_error(ytest, baseline.predict(xtest))),
        'train_rows': len(xtrain), 'test_rows': len(xtest), 'seed': 42,
        'caution': 'Random holdout only. Manually exclude leakage; use time/group split for dependent records. A low error on a target derived from the predictors is not business validation.'}
    return metrics, pd.DataFrame({'actual': ytest.to_numpy(), 'predicted': pred})

def export_bundle(df, audit, result=None):
    buffer = io.BytesIO()
    def safe_csv(frame):
        frame = frame.copy()
        for col in frame.select_dtypes(include=['object', 'string']):
            frame[col] = frame[col].map(lambda v: "'" + v if isinstance(v,str) and v.startswith(('=', '+', '-', '@', '\t', '\r')) else v)
        return frame.to_csv(index=False)
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('cleaned.csv', safe_csv(df))
        z.writestr('quality.csv', profile(df).to_csv(index=False))
        z.writestr('audit.json', json.dumps(audit, indent=2))
        if result is not None:
            z.writestr('answer.csv', safe_csv(result))
    return buffer.getvalue()
