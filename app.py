import pandas as pd
import streamlit as st
from pathlib import Path
from scoring import rank_opportunities, funding_gap

ROOT = Path(__file__).parent / 'data'
def load(name):
    return pd.read_csv(ROOT / f'{name}.csv')
funders, investments, opportunities = load('funders'), load('investments'), load('opportunities')
needs, links, evidence = load('needs'), load('theme_links'), load('evidence')
st.set_page_config(page_title='MindVest Global', page_icon='🧠', layout='wide')
st.title('MindVest Global')
st.caption('Mental health investment intelligence | Real Wellcome grant records + clearly labeled synthetic modules')
st.error('⚠️ DEMONSTRATION DATASET: Wellcome CSV files contain only 600-row extract (not 26,288 full records). This is NOT a representative sample and MUST NOT be used for population inference, financial estimates, or trend analysis. See GITHUB_STARTER_NOTE.txt.')
st.warning('SYNTHETIC: Funder Discovery, Behavioral Intelligence, Capital Gaps and Prospect Dossier use fictional data. Wellcome Award-Level Explorer uses real source records. No BehaviorGPT calls are made.')
page = st.sidebar.radio('Explore', ['Verified Evidence', 'Award-Level Explorer', 'Mental Health Triage', 'Classification Validation', 'Overview', 'Funder Discovery', 'Behavioral Intelligence', 'Capital Gaps', 'Prospect Dossier', 'BehaviorGPT Readiness'])

if page == 'Verified Evidence':
    st.header('Verified public financing evidence')
    st.success('This tab uses sourced published figures. Other tabs remain synthetic demonstrations.')
    verified = load('verified_observations')
    st.caption('Aggregate financial-report observations, NOT individual grants, and NOT BehaviorGPT predictions.')
    st.dataframe(verified[['institution','period','theme','metric','value','currency','unit','source_url','limitations']], hide_index=True, use_container_width=True)
    st.subheader('Wellcome: reported 2024 grant funding by programme')
    subset = verified[(verified.period == 2024) & (verified.metric == 'Grant funding')]
    st.bar_chart(subset.set_index('theme')['value'])
    st.caption('GBP millions. 2025 figures have different definitions and are excluded from this chart. These observations cannot support funder-level predictive validation.')
    st.markdown('**Source documents:** [Wellcome 2024 financial statements](https://wellcome.org/sites/default/files/2025-01/Wellcome-Trust-Annual-Report-And-Financial-Statements-2024.pdf) · [Wellcome 2025 financial statements](https://cms.wellcome.org/sites/default/files/2026-01/wellcome-trust-annual-report-and-financial-statements-2025.pdf)')
    st.info('Wellcome individual grant records are now available in Award-Level Explorer. They are separate from annual financial-report aggregates.')

elif page == 'Award-Level Explorer':
    st.header('Wellcome award-level explorer')
    st.caption('Load the official Wellcome grant export locally. This view does not send data to BehaviorGPT.')
    from wellcome_import import import_awards
    upload = st.file_uploader('Upload official Wellcome CSV or Excel award export', type=['csv','xlsx','xls'])
    local = ROOT / 'wellcome_awards_imported.csv'
    try:
        uploaded_data = False
        if upload is not None:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=Path(upload.name).suffix,delete=False) as tmp:
                tmp.write(upload.getvalue()); tmp_path=Path(tmp.name)
            try: awards=import_awards(tmp_path); uploaded_data=True
            finally: tmp_path.unlink(missing_ok=True)
        elif local.exists():
            awards=pd.read_csv(local,parse_dates=['award_date'])
        else:
            awards=None
        if awards is None:
            st.info('No award-level dataset imported yet. Download the official Wellcome grants spreadsheet from https://wellcome.org/research-funding/funding-portfolio and upload it here, or run the importer.')
        else:
            if uploaded_data:
                st.success(f'{len(awards):,} records loaded from uploaded file.')
                st.info('Uploaded dataset displayed. Verify data provenance and completeness independently.')
            else:
                st.success(f'{len(awards):,} records loaded from bundled demonstration data.')
                st.error('⚠️ LIMITATION: This is a 600-row extract (first 600 rows only), NOT the full 26,288-record dataset. It is NOT representative and cannot be used for population-wide inference.')
            if 'mental_health_flag' in awards.columns:
                n=int((awards.mental_health_flag=='keyword_candidate_unreviewed').sum())
                st.metric('Unreviewed mental-health keyword candidates',f'{n:,}')
            if 'award_date' in awards.columns:
                awards['award_date']=pd.to_datetime(awards.award_date,errors='coerce')
                counts=awards.groupby(awards.award_date.dt.year).size().rename('Award count')
                st.subheader('Award activity by calendar year')
                st.bar_chart(counts)
            st.caption('Keyword candidates are not verified mental health awards. The dataset is Wellcome only, not a global funding estimate.')
            st.warning('Titles and amounts are source records; thematic classifications have NOT been verified. These records are not BehaviorGPT predictions.')
            term=st.text_input('Search titles and descriptions', 'mental health')
            subset=awards[awards['title'].fillna('').str.contains(term,case=False,regex=False)|awards['description'].fillna('').str.contains(term,case=False,regex=False)] if term else awards
            st.metric('Matching records',len(subset))
            st.dataframe(subset[['grant_id','award_date','title','recipient','amount_gbp','source_url']].head(500),hide_index=True,use_container_width=True)
            st.download_button('Download matching records',subset.to_csv(index=False),'mindvest_wellcome_filtered.csv')
            st.caption('Search hits are not a validated mental-health classification. No summation across duplicates, supplements, or incompatible accounting periods is implied.')
    except Exception as e:
        st.error(f'Import could not be completed: {e}')

elif page == 'Mental Health Triage':
    st.header('Mental health grant triage — human review required')
    st.error('⚠️ DEMONSTRATION EXTRACT: Triage results based on 600-row extract only. Counts CANNOT be extrapolated to full dataset.')
    st.warning('All classifications below are automated keyword priorities, NOT verified grant classifications or evidence of investment amounts in mental health.')
    triage_file = ROOT / 'wellcome_mental_health_triage.csv'
    if not triage_file.exists():
        st.info('Run python build_triage.py to generate the local triage dataset.')
    else:
        t = pd.read_csv(triage_file, low_memory=False)
        st.metric('Records triaged', f'{len(t):,}')
        st.dataframe(t.groupby('triage_category').size().rename('record_count').reset_index(), hide_index=True, use_container_width=True)
        cat = st.selectbox('Review queue', sorted(t.triage_category.unique()))
        q = t[t.triage_category == cat]
        st.dataframe(q[['grant_id','title','recipient','award_date','triage_reason','source_url']].head(200), hide_index=True, use_container_width=True)
        st.download_button('Download review queue', q.to_csv(index=False), 'wellcome_review_queue.csv')
        st.caption('No funding totals are calculated from unreviewed categories. A manual audit is needed before interpreting thematic or geographic trends.')

elif page == 'Classification Validation':
    st.header('Human validation of mental health screening')
    st.error('⚠️ DEMONSTRATION EXTRACT: Sample drawn from 600-row extract only, NOT from full 26,288-record dataset. Results NOT representative.')
    st.warning('The sample is UNLABELLED. No grant has been manually verified. Do not treat screening flags as confirmed awards.')
    from validation import LABELS, audit_report
    sample_path = ROOT / 'wellcome_validation_sample.csv'
    sample = pd.read_csv(sample_path, keep_default_na=False)
    st.write('Stratified audit: 30 randomly selected grants per screening category (150 total), fixed seed for reproducibility.')
    st.dataframe(sample[['grant_id','triage_category','title','description','reviewer_label','adjudicated_label']],hide_index=True,use_container_width=True)
    st.download_button('Download blank reviewer worksheet',sample.to_csv(index=False),'wellcome_validation_sample.csv',mime='text/csv')
    st.markdown('Label each record **direct**, **integrated**, **not_mental_health**, or **uncertain**. Record reviewer ID and rationale; reconcile disagreements in `adjudicated_label`. Review descriptions and source links, not just keywords.')
    uploaded=st.file_uploader('Upload reviewed worksheet (CSV)',type=['csv'],key='reviewed_audit')
    if uploaded is not None:
        try:
            reviewed=pd.read_csv(uploaded,keep_default_na=False)
            # Validate schema
            required_cols = ['grant_id', 'triage_category', 'adjudicated_label']
            missing_cols = [col for col in required_cols if col not in reviewed.columns]
            if missing_cols:
                st.error(f'Uploaded file is missing required columns: {", ".join(missing_cols)}')
            elif set(reviewed.grant_id)!=set(sample.grant_id) or len(reviewed)!=len(sample):
                st.error('Uploaded IDs must match the full original audit sample exactly.')
            elif not reviewed.adjudicated_label.isin(LABELS+['']).all():
                st.error('Invalid adjudicated labels; use: '+', '.join(LABELS))
            else:
                population=pd.read_csv(ROOT/'wellcome_mental_health_triage.csv',usecols=['grant_id','triage_category'])
                report,estimate,complete=audit_report(reviewed,population)
                st.dataframe(report,hide_index=True,use_container_width=True)
                if complete:
                    st.metric('Stratified estimate of mental-health-relevant records',f'{estimate:,.0f}')
                    st.caption('Exploratory estimate, not a verified census or financial total. Requires uncertainty intervals, independent review, and source adjudication before publication.')
                else:
                    st.info('Audit incomplete or uncertain labels remain. No overall prevalence estimate is displayed.')
        except Exception as exc:
            st.error(f'Cannot process review file: {exc}')

elif page == 'Overview':
    a,b,c = st.columns(3)
    a.metric('Illustrative funders', len(funders))
    b.metric('Illustrative funding records', len(investments))
    c.metric('Candidate opportunities', len(opportunities))
    st.subheader('The three engines')
    st.markdown('**Discover** potential funders · **Analyze** historical choices · **Compare** financing needs with available resources')
    st.dataframe(opportunities[['name','theme','intervention']], hide_index=True, use_container_width=True)

elif page == 'Funder Discovery':
    st.header('Funder discovery')
    selected = st.selectbox('Select institution', funders.name)
    f = funders[funders.name == selected].iloc[0]
    st.write(f"**Mandate:** {f['mandate']}  |  **Type:** {f['type']}")
    history = investments[investments.funder_id == f.funder_id].sort_values('year')
    st.dataframe(history[['year','theme','country','amount','currency','instrument','finance_status']], hide_index=True, use_container_width=True)
    ranks = rank_opportunities(f.funder_id, funders, investments, opportunities, links)
    st.subheader('Candidate opportunities — transparent baseline')
    st.dataframe(ranks, hide_index=True, use_container_width=True)
    st.info('Baseline scores count matching historical themes; they are not probabilities or BehaviorGPT predictions. Funder type eligibility is only a coarse demonstration filter.')

elif page == 'Behavioral Intelligence':
    st.header('Behavioral intelligence')
    selected = st.selectbox('Institution', funders.name)
    fid = funders.loc[funders.name == selected,'funder_id'].iloc[0]
    hist = investments[investments.funder_id == fid].sort_values(['year','investment_id'])
    st.write('Observed sequence in the synthetic sample (not inferred searches or proposal reviews):')
    for _, record in hist.iterrows():
        st.write(f"**{record['year']}** · {record['theme']} · {record['instrument']} ({record['finance_status']})")
    st.bar_chart(hist.groupby('theme').size().rename('records'))
    st.caption('The bar chart counts records, not financial value. Different financing instruments are not summed.')

elif page == 'Capital Gaps':
    st.header('Capital gap explorer')
    st.caption('Hypothetical financing scenarios; not national funding estimates.')
    country = st.selectbox('Country', needs.country)
    r = needs[needs.country == country].iloc[0]
    gap = funding_gap(r.estimated_need_usd, r.available_financing_usd)
    a,b,c = st.columns(3)
    a.metric('Illustrative need (USD)', f"${r.estimated_need_usd:,.0f}")
    b.metric('Illustrative available financing (USD)', f"${r.available_financing_usd:,.0f}")
    c.metric('Illustrative gap (USD)', f"${gap:,.0f}" if gap is not None else 'Unknown')
    st.write('Intervention:',r.intervention)
    st.warning('A financing gap is only meaningful if need and available financing use matching years, geography, scope and accounting definitions. Missing data must not be interpreted as zero.')

elif page == 'Prospect Dossier':
    st.header('Prospect dossier')
    selected = st.selectbox('Funder', funders.name)
    f = funders[funders.name == selected].iloc[0]
    ranked = rank_opportunities(f.funder_id, funders, investments, opportunities, links)
    choice = st.selectbox('Opportunity', ranked.opportunity)
    r = ranked[ranked.opportunity == choice].iloc[0]
    st.markdown(f"### {selected} → {choice}")
    st.write('**Historical thematic overlap:**', r.matching_themes)
    st.write('**Illustrative eligibility by institution type:**', 'Matches' if r.eligible_type else 'Does not match')
    st.write('**Uncertainties:** institutional strategy, open calls, geographic eligibility, decision makers, budget, and current priorities require verification.')
    st.write('**Evidence status:** synthetic example; no external funding claim established.')
    st.download_button('Download brief', data=f'MindVest DEMO prospect brief\nFunder: {selected}\nOpportunity: {choice}\nThematic overlap: {r.matching_themes}\nEvidence: SYNTHETIC DEMO ONLY\n', file_name='mindvest_demo_brief.txt')

elif page == 'BehaviorGPT Readiness':
    st.header('BehaviorGPT integration readiness')
    st.write('The documented SDK can rank a catalog from ordered Search, View, and Order histories. We will experimentally treat confirmed awards as Order events, without inventing views or searches.')
    st.write('**Current state:** offline baseline only. No API key is read, no catalog is uploaded, and no external API is called.')
    st.write('**Next integration:** prepare the 15-column Parquet catalog; review mapping and data rights; explicitly approve upload; use `UnboxAIClient.complete` with the resulting `catalog_id`; evaluate against historical holdouts.')
    st.code('from behaviorgpt import UnboxAIClient, Order\n# After an approved catalog upload and with UNBOXAI_API_KEY in the environment:\n# client = UnboxAIClient(market="US")\n# result = client.complete([Order(["catalog_item_id"])], catalog_id="your_catalog_id", limit=5)', language='python')
    st.caption('Example is documentation-aligned scaffolding, not executed. Event IDs must correspond to items in the uploaded catalog.')
