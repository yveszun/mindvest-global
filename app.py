import pandas as pd
import streamlit as st
from pathlib import Path
from scoring import rank_opportunities, funding_gap

ROOT = Path(__file__).parent / 'data'
def load(name):
    return pd.read_csv(ROOT / f'{name}.csv')

# Detect available dataset for status banner
def get_dataset_status():
    """Determine which Wellcome dataset is available."""
    full_data = ROOT / 'wellcome_full_analytical.csv'
    legacy_data = ROOT / 'wellcome_awards_imported.csv'
    
    if full_data.exists():
        df = pd.read_csv(full_data)
        # Verify it's the full dataset by checking row count and amount
        if len(df) >= 20000 and df['amount_gbp'].sum() > 1e10:
            return 'full', len(df), df['amount_gbp'].sum()
    
    if legacy_data.exists():
        df = pd.read_csv(legacy_data)
        return 'legacy', len(df), df['amount_gbp'].sum()
    
    return 'none', 0, 0

dataset_status, record_count, total_amount = get_dataset_status()

funders, investments, opportunities = load('funders'), load('investments'), load('opportunities')
needs, links, evidence = load('needs'), load('theme_links'), load('evidence')
st.set_page_config(page_title='MindVest Global', page_icon='🧠', layout='wide')
st.title('MindVest Global')

# Conditional banner based on actual loaded dataset
if dataset_status == 'full':
    st.caption(f'Mental health investment intelligence | Bundled: Complete official Wellcome grants ({record_count:,} records, 2000-2026) + clearly labeled synthetic modules')
    st.info(f'📊 BUNDLED DATASET: {record_count:,} official Wellcome grants (£{total_amount/1e9:.1f} billion, 2000-2026, amount > £0). Award-Level Explorer displays bundled data by default; uploaded alternatives are clearly indicated. Mental health keyword candidates (2,489) are unreviewed.')
elif dataset_status == 'legacy':
    st.caption('Mental health investment intelligence | Bundled: Demonstration extract + clearly labeled synthetic modules')
    st.error(f'⚠️ BUNDLED LEGACY EXTRACT: Only {record_count:,} records bundled (demonstration extract, not representative). Run PYTHONPATH=./lib python import_full_wellcome.py to upgrade to the complete 23,942-record dataset.')
else:
    st.caption('Mental health investment intelligence | Clearly labeled synthetic modules')
    st.warning('⚠️ NO BUNDLED WELLCOME DATA: Award-Level Explorer requires dataset. Upload official Wellcome grants spreadsheet or run import pipeline.')

st.warning('SYNTHETIC: Funder Discovery, Behavioral Intelligence, Capital Gaps and Prospect Dossier use fictional data. No BehaviorGPT calls are made.')
page = st.sidebar.radio('Explore', ['Verified Evidence', 'Award-Level Explorer', 'Mental Health Triage', 'Mental Health Classification v1', 'Classification Validation', 'Overview', 'Funder Discovery', 'Behavioral Intelligence', 'Capital Gaps', 'Prospect Dossier', 'BehaviorGPT Readiness'])

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
    st.caption('Browse the complete official Wellcome grants dataset (2000-2026) or upload your own export. No data sent to BehaviorGPT.')
    from wellcome_import import import_awards
    upload = st.file_uploader('Upload alternative Wellcome CSV or Excel export (optional)', type=['csv','xlsx','xls'])
    
    # Check for full analytical dataset first, fallback to legacy 600-row extract
    full_data = ROOT / 'wellcome_full_analytical.csv'
    legacy_data = ROOT / 'wellcome_awards_imported.csv'
    
    try:
        uploaded_data = False
        data_source = None
        
        if upload is not None:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=Path(upload.name).suffix,delete=False) as tmp:
                tmp.write(upload.getvalue()); tmp_path=Path(tmp.name)
            try: 
                awards=import_awards(tmp_path)
                uploaded_data=True
                data_source='uploaded'
            finally: tmp_path.unlink(missing_ok=True)
        elif full_data.exists():
            awards=pd.read_csv(full_data,parse_dates=['award_date'])
            data_source='full'
        elif legacy_data.exists():
            awards=pd.read_csv(legacy_data,parse_dates=['award_date'])
            data_source='legacy'
        else:
            awards=None
            data_source=None
        
        if awards is None:
            st.info('No award-level dataset available. Download the official Wellcome grants spreadsheet from https://wellcome.org/research-funding/funding-portfolio and upload it here.')
        else:
            if data_source == 'uploaded':
                st.success(f'✓ {len(awards):,} records loaded from your uploaded file.')
                st.warning('⚠️ UPLOADED DATA (not bundled dataset): Verify data provenance, completeness and currency independently before use. The global banner describes the bundled dataset, not this upload.')
            elif data_source == 'full':
                total_amount = awards['amount_gbp'].sum()
                st.success(f'✓ {len(awards):,} grants loaded from bundled official Wellcome dataset (£{total_amount:,.0f}, amount > £0)')
                st.info('📊 BUNDLED SOURCE: Official Wellcome grants awarded 1 October 2000 to 9 September 2026. Zero-amount records (studentships, institutional awards) excluded from analytical layer. See data/FULL_WELLCOME_IMPORT_AUDIT.md for reconciliation.')
            elif data_source == 'legacy':
                st.success(f'{len(awards):,} records loaded from bundled legacy demonstration extract.')
                st.error('⚠️ BUNDLED LEGACY DATA: This is a 600-row extract, NOT the full dataset. Upgrade by running: PYTHONPATH=./lib python import_full_wellcome.py')
            
            # Mental health candidates metric - count only actual keyword matches in displayed dataset
            # Load the candidate file to identify actual MH candidates (not all 'not_reviewed' records)
            mh_candidate_file = ROOT / 'wellcome_full_mh_candidates_unreviewed.csv'
            if mh_candidate_file.exists() and 'grant_id' in awards.columns:
                mh_candidates_df = pd.read_csv(mh_candidate_file)
                candidate_ids = set(mh_candidates_df['grant_id'])
                n = awards['grant_id'].isin(candidate_ids).sum()
                
                if n > 0 or data_source == 'full':
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric('Total grants', f'{len(awards):,}')
                    with col2:
                        st.metric('Mental health keyword candidates', f'{n:,}')
                    
                    if data_source == 'full':
                        st.caption(f'⚠️ {n:,} keyword candidates in analytical layer (amount > £0). Total candidates across all layers: 2,489 (includes 267 zero-amount). All require manual review. NOT verified mental health funding.')
                    else:
                        st.caption('⚠️ Keyword candidates require manual review. NOT verified mental health funding.')
            
            # Award activity by year
            if 'award_date' in awards.columns:
                awards['award_date']=pd.to_datetime(awards.award_date,errors='coerce')
                valid_dates = awards[awards.award_date.notna()]
                if len(valid_dates) > 0:
                    counts=valid_dates.groupby(valid_dates.award_date.dt.year).size().rename('Award count')
                    st.subheader('Award activity by calendar year')
                    st.bar_chart(counts)
            
            st.caption('Dataset is Wellcome only, not a global funding estimate. Keyword flagging is automated, not manually validated.')
            st.warning('Titles and amounts are official source records; mental health classifications have NOT been verified by domain experts.')
            
            # Search functionality
            term=st.text_input('Search titles and descriptions', 'mental health')
            if term:
                subset=awards[
                    awards['title'].fillna('').str.contains(term,case=False,regex=False) | 
                    awards['description'].fillna('').str.contains(term,case=False,regex=False)
                ]
            else:
                subset=awards
            
            st.metric('Matching records',len(subset))
            
            if len(subset) > 0:
                display_cols = ['grant_id','award_date','title','recipient','amount_gbp']
                if 'source_url' in subset.columns:
                    display_cols.append('source_url')
                st.dataframe(subset[display_cols].head(500),hide_index=True,use_container_width=True)
                st.download_button('Download matching records',subset.to_csv(index=False),'mindvest_wellcome_filtered.csv')
            
            st.caption('Search hits are not validated mental-health classifications. No summation across duplicates, supplements, or incompatible accounting periods is implied.')
    except Exception as e:
        st.error(f'Import could not be completed: {e}')
        import traceback
        with st.expander('Error details'):
            st.code(traceback.format_exc())

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

elif page == 'Mental Health Classification v1':
    st.header('Mental Health Classification v1')
    st.caption('Rule-based classification system for identifying mental health-related grants')
    
    # Load classifications if available
    classifications_file = ROOT / 'wellcome_mh_classifications_v1.csv'
    review_sample_file = ROOT / 'wellcome_mh_review_sample_v1.csv'
    
    # Check if classification has been run
    if not classifications_file.exists():
        st.error('⚠️ CLASSIFICATIONS NOT YET GENERATED')
        st.info('Run the classification pipeline: PYTHONPATH=./lib python mental_health_classifier_v1.py')
        st.markdown('See MENTAL_HEALTH_CLASSIFICATION_V1.md for methodology documentation.')
    else:
        classifications = pd.read_csv(classifications_file, parse_dates=['award_date'])
        
        st.success(f'✓ {len(classifications):,} grants classified using Mental Health Classification v1')
        st.warning('⚠️ ALL CLASSIFICATIONS ARE AUTOMATED AND UNREVIEWED - Human validation required before any funding calculations or policy claims')
        
        # Overview metrics
        st.subheader('Classification Overview')
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric('Total Grants', f'{len(classifications):,}')
        with col2:
            direct_integrated = classifications[classifications['mh_category_v1'].isin(['direct', 'integrated'])].shape[0]
            st.metric('Direct + Integrated MH', f'{direct_integrated:,}')
        with col3:
            uncertain = classifications[classifications['mh_category_v1'] == 'uncertain'].shape[0]
            st.metric('Uncertain (needs review)', f'{uncertain:,}')
        
        # Category distribution
        st.subheader('Category Distribution')
        category_counts = classifications['mh_category_v1'].value_counts().sort_index()
        st.bar_chart(category_counts)
        
        st.dataframe(
            pd.DataFrame({
                'Category': category_counts.index,
                'Count': category_counts.values,
                'Percentage': (category_counts.values / len(classifications) * 100).round(2)
            }),
            hide_index=True,
            use_container_width=True
        )
        
        # Category definitions
        with st.expander('📖 Category Definitions'):
            st.markdown('''
            **Direct Mental Health:** Research or programmes explicitly addressing mental health conditions, services, prevention, treatment, or psychosocial support.
            
            **Integrated Mental Health:** Mental health components embedded within broader health, social, or humanitarian programmes (HIV, maternal health, primary care, etc.).
            
            **Adjacent/Enabling:** Neuroscience, behavioral science, wellbeing research potentially relevant to mental health but without demonstrated direct or integrated mental health objectives. NOT verified mental health investment.
            
            **Not Mental Health:** No substantiated mental health relevance.
            
            **Uncertain:** Insufficient information or conflicting evidence for confident classification.
            
            See MENTAL_HEALTH_CLASSIFICATION_V1.md for complete methodology.
            ''')
        
        # Browse classified grants
        st.subheader('Browse Classified Grants')
        selected_category = st.selectbox(
            'Filter by category',
            ['All'] + sorted(classifications['mh_category_v1'].unique())
        )
        
        if selected_category == 'All':
            display_df = classifications
        else:
            display_df = classifications[classifications['mh_category_v1'] == selected_category]
        
        st.metric('Grants in view', f'{len(display_df):,}')
        
        st.dataframe(
            display_df[['grant_id', 'title', 'mh_category_v1', 'mh_confidence_v1', 'mh_evidence_v1', 'amount_gbp', 'award_date']].head(200),
            hide_index=True,
            use_container_width=True
        )
        
        st.download_button(
            'Download all classifications',
            classifications.to_csv(index=False),
            'wellcome_mh_classifications_v1.csv',
            mime='text/csv'
        )
        
        # Human validation sample
        st.subheader('Human Validation')
        
        if not review_sample_file.exists():
            st.info('📋 Generate a human review sample: PYTHONPATH=./lib python generate_review_sample_v1.py')
        else:
            review_sample = pd.read_csv(review_sample_file)
            has_validation = review_sample['human_category'].notna().any() and (review_sample['human_category'] != '').any()
            
            st.metric('Review Sample Size', f'{len(review_sample)} grants')
            
            if not has_validation:
                st.warning('⚠️ REVIEW SAMPLE NOT YET COMPLETED - Download, review, and upload completed sample')
                st.download_button(
                    'Download Review Sample for Human Validation',
                    review_sample.to_csv(index=False),
                    'wellcome_mh_review_sample_v1.csv',
                    mime='text/csv'
                )
                
                st.markdown('''
                **Instructions for reviewers:**
                1. Fill in `human_category` column: direct, integrated, adjacent, not_mh, or uncertain
                2. Fill in `reviewer_confidence`: high, medium, or low
                3. Add notes in `reviewer_notes` for borderline/uncertain cases
                4. Enter your ID in `reviewer_id` and date in `review_date`
                5. Upload completed CSV below
                
                Do not fabricate reviews. Each grant requires genuine expert judgment.
                ''')
                
                # Upload completed review
                uploaded_review = st.file_uploader('Upload completed review sample', type=['csv'], key='mh_review_upload')
                
                if uploaded_review is not None:
                    try:
                        reviewed = pd.read_csv(uploaded_review)
                        # Basic validation
                        if 'human_category' in reviewed.columns and reviewed['human_category'].notna().any():
                            # Save uploaded review (in production, would validate more thoroughly)
                            st.success(f'✓ Uploaded review with {reviewed["human_category"].notna().sum()} validated records')
                            st.info('Evaluation metrics will be available once review is saved.')
                        else:
                            st.error('Uploaded file missing human_category column or all values are blank')
                    except Exception as e:
                        st.error(f'Error reading uploaded review: {e}')
            else:
                # Show evaluation results
                st.success(f'✓ {review_sample["human_category"].notna().sum()} grants have been validated')
                
                # Run evaluation
                from evaluate_classification_v1 import compute_binary_metrics, compute_multiclass_metrics, confusion_matrix
                
                validated = review_sample[review_sample['human_category'].notna() & (review_sample['human_category'] != '')]
                y_true = validated['human_category']
                y_pred = validated['automated_category']
                
                st.subheader('Evaluation Results')
                
                # Binary metrics
                st.markdown('**Binary Classification (MH Relevant vs Not)**')
                binary_metrics = compute_binary_metrics(y_true, y_pred)
                
                if 'error' not in binary_metrics:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric('Precision', f"{binary_metrics['precision']:.3f}")
                    with col2:
                        st.metric('Recall', f"{binary_metrics['recall']:.3f}")
                    with col3:
                        st.metric('F1 Score', f"{binary_metrics['f1_score']:.3f}")
                    with col4:
                        st.metric('Accuracy', f"{binary_metrics['accuracy']:.3f}")
                
                # Multi-class metrics
                st.markdown('**Multi-Class Performance**')
                multiclass_metrics = compute_multiclass_metrics(y_true, y_pred)
                st.metric('Overall Accuracy', f"{multiclass_metrics['overall_accuracy']:.3f}")
                
                # Per-category metrics
                category_metrics_df = pd.DataFrame([
                    {
                        'Category': cat,
                        'Precision': metrics['precision'],
                        'Recall': metrics['recall'],
                        'F1 Score': metrics['f1_score'],
                        'Support': metrics['support']
                    }
                    for cat, metrics in sorted(multiclass_metrics['by_category'].items())
                ])
                
                st.dataframe(category_metrics_df, hide_index=True, use_container_width=True)
                
                # Confusion matrix
                st.markdown('**Confusion Matrix**')
                st.caption('Rows: Human labels | Columns: Automated predictions')
                conf_mat = confusion_matrix(y_true, y_pred)
                st.dataframe(conf_mat, use_container_width=True)
        
        # Safeguards
        st.subheader('⚠️ Important Limitations')
        st.error('''
        **DO NOT use automated classifications for:**
        - Calculating verified mental health funding totals
        - Making policy claims about mental health investment
        - Equating neuroscience/behavioral science with mental health funding
        - Assuming full grant value is mental health for integrated grants
        
        **Human validation is required** for all financial estimates and policy recommendations.
        ''')
        
        st.info('''
        **Classification methodology:** See MENTAL_HEALTH_CLASSIFICATION_V1.md for complete documentation including:
        - Category definitions and inclusion/exclusion criteria
        - Rule-based classification logic
        - Confidence scoring approach
        - Human validation protocol
        - Evaluation metrics definitions
        ''')

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
