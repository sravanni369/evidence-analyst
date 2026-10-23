import hashlib
import json
from pathlib import Path
import streamlit as st
from core import read_csv, clean, profile, answer, regression, export_bundle

st.set_page_config(page_title='Evidence Analyst', page_icon='📊', layout='wide')
st.title('Evidence Analyst')
st.caption('CSV → quality checks → inspectable analysis → Power BI export')
upload = st.file_uploader('Upload a CSV (maximum 5 MB)', type=['csv'], max_upload_size=5)
raw = upload.getvalue() if upload else (Path(__file__).parent/'data'/'retail_demo.csv').read_bytes()
try:
    df, audit = clean(read_csv(raw))
except Exception as exc:
    st.error(str(exc)); st.stop()
identity = hashlib.sha256(raw).hexdigest()
if st.session_state.get('dataset') != identity:
    st.session_state.clear()
    st.session_state['dataset'] = identity
st.info('Bundled sample is synthetic retail data. Offline questions use fixed Python functions; AI mode uses DSPy and E2B.')
a,b,c = st.columns(3)
a.metric('Cleaned rows', len(df)); b.metric('Duplicates removed', audit['duplicates_removed']); c.metric('Missing cells', audit['missing_cells'])
with st.expander('Cleaning policy and preview', expanded=True):
    st.write(audit['policy']); st.dataframe(df.head(30), hide_index=True)
tabs = st.tabs(['Ask a question', 'Data quality', 'ML baseline', 'Export'])
with tabs[0]:
    ai_mode = st.toggle('Use DSPy + E2B (service credentials required)')
    question = st.text_input('Question', 'Revenue by region')
    if st.button('Analyze'):
        try:
            st.session_state.pop('result', None)
            st.session_state.pop('code', None)
            if ai_mode:
                from ai import generate
                st.session_state['code'] = generate(df, question)
            else:
                st.session_state['result'] = answer(df, question)
        except Exception as exc:
            st.error(str(exc))
    if st.session_state.get('code'):
        st.code(st.session_state['code'], language='python')
        consent = st.checkbox('I reviewed the code and consent to sending this dataset to E2B. Only use non-sensitive data.')
        if st.button('Run reviewed code in E2B', disabled=not consent):
            try:
                from ai import execute
                with st.spinner('Running in isolated sandbox'):
                    st.session_state['result'] = execute(df, st.session_state['code'])
            except Exception as exc:
                st.error(str(exc))
    if 'result' in st.session_state:
        st.dataframe(st.session_state['result'], hide_index=True)
with tabs[1]:
    st.dataframe(profile(df), hide_index=True); st.json(audit)
with tabs[2]:
    numeric = list(df.select_dtypes(include='number').columns)
    st.write('Regression with a random holdout and mean-prediction baseline. Select only features available at prediction time.')
    if numeric:
        target = st.selectbox('Numeric target', numeric, index=numeric.index('revenue') if 'revenue' in numeric else 0)
        candidates = [c for c in numeric if c != target]
        features = st.multiselect('Predictors (exclude IDs and target-derived columns)', candidates, default=[c for c in ['units','unit_price','discount'] if c in candidates])
        if st.button('Evaluate model'):
            try:
                metrics, predictions = regression(df, target, features)
                st.json(metrics); st.dataframe(predictions)
                st.download_button('Download evaluation', json.dumps(metrics, indent=2), 'metrics.json')
            except Exception as exc:
                st.error(str(exc))
with tabs[3]:
    st.write('Unzip, then import cleaned.csv into Power BI Desktop. See powerbi/README.md for the dashboard recipe.')
    st.download_button('Download Power BI data bundle', export_bundle(df, audit, st.session_state.get('result')), 'powerbi_bundle.zip', 'application/zip')
