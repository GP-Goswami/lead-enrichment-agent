import json
import pandas as pd
import streamlit as st
import requests

# Page Config
st.set_page_config(
    page_title="Autonomous Lead Enrichment Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #76B900; /* NVIDIA Green */
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.0rem;
        color: #A0A0A0;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #1E1E1E;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #333;
    }
</style>
""", unsafe_allow_html=True)

# Initialize persistent session state
if "results_list" not in st.session_state:
    st.session_state.results_list = []
if "failed_domains" not in st.session_state:
    st.session_state.failed_domains = []
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False

# Header
st.markdown('<div class="main-header">⚡ Autonomous Lead Enrichment Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Selenium Headless Crawler + NVIDIA NIM API (deepseek-ai/deepseek-v4-flash-0731)</div>', unsafe_allow_html=True)

# Sidebar Config
with st.sidebar:
    st.header("⚙️ Configuration")
    backend_url = st.text_input("FastAPI Backend URL", value="http://localhost:8000")
    
    st.divider()
    st.markdown("### 📌 Test Target Domains")
    st.code("postman.com\nsupabase.com\nvapi.ai", language="text")
    
    st.divider()
    st.markdown("### 🤖 Architecture")
    st.caption("- **Scraper**: Selenium Headless WebDriver")
    st.caption("- **LLM Engine**: NVIDIA NIM API")
    st.caption("- **Backend**: FastAPI Engine")
    st.caption("- **Fallback**: DuckDuckGo Search API")
    
    if st.session_state.results_list or st.session_state.failed_domains:
        st.divider()
        if st.button("🔄 Reset / Clear Results", use_container_width=True, type="secondary"):
            st.session_state.results_list = []
            st.session_state.failed_domains = []
            st.session_state.is_processing = False
            st.rerun()

# Main Content Layout
tab1, tab2 = st.tabs(["🚀 Lead Extraction Pipeline", "ℹ️ System Status & Docs"])

with tab1:
    st.subheader("1. Enter Domains or Upload File")
    
    input_method = st.radio("Choose Input Method", ["Text Input / Comma List", "Upload File (CSV / TXT)"], horizontal=True)
    
    domains_to_process = []
    
    if input_method == "Text Input / Comma List":
        default_domains = "postman.com, supabase.com, vapi.ai"
        user_input = st.text_area("Enter domains (one per line or comma-separated):", value=default_domains, height=100)
        if user_input.strip():
            raw_list = user_input.replace("\n", ",").split(",")
            domains_to_process = [d.strip() for d in raw_list if d.strip()]
            
    else:
        uploaded_file = st.file_uploader("Upload CSV or TXT file", type=["csv", "txt"])
        if uploaded_file is not None:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
                st.write("Uploaded Preview:", df.head(3))
                column_name = st.selectbox("Select Domain Column", df.columns)
                domains_to_process = df[column_name].dropna().astype(str).tolist()
            else:
                content = uploaded_file.read().decode("utf-8")
                domains_to_process = [line.strip() for line in content.splitlines() if line.strip()]

    st.write(f"**Selected Domains to Enrich ({len(domains_to_process)}):** `{', '.join(domains_to_process)}`")

    # Run Pipeline Button
    if st.button("✨ Run Lead Enrichment Pipeline", type="primary", use_container_width=True):
        if not domains_to_process:
            st.error("Please provide at least one domain to process.")
        else:
            # Clear previous runs for a fresh search session
            st.session_state.results_list = []
            st.session_state.failed_domains = []
            st.session_state.is_processing = True

            st.divider()
            st.subheader("2. Enrichment Execution Results")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_domains = len(domains_to_process)
            
            for idx, dom in enumerate(domains_to_process):
                status_text.info(f"⏳ Processing Domain ({idx+1}/{total_domains}): `{dom}`...")
                progress_bar.progress(int((idx / total_domains) * 100))
                
                try:
                    resp = requests.post(f"{backend_url}/api/v1/enrich", json={"domains": [dom]}, timeout=180)
                    if resp.status_code == 200:
                        res_data = resp.json()
                        if res_data.get("status") == "failed" or res_data.get("data_confidence_score", 0) == 0.0:
                            st.session_state.failed_domains.append(dom)
                            st.toast(f"⚠️ `{dom}` enrichment failed.", icon="⚠️")
                        else:
                            st.session_state.results_list.append(res_data)
                            st.toast(f"✅ `{dom}` enriched! Score: {res_data.get('data_confidence_score')}")
                    else:
                        st.session_state.failed_domains.append(dom)
                        st.error(f"Backend error on `{dom}` ({resp.status_code}): {resp.text}")
                except Exception as req_err:
                    st.session_state.failed_domains.append(dom)
                    st.error(f"⚠️ Connection or Timeout error on `{dom}`: {req_err}")
                
                progress_bar.progress(int(((idx + 1) / total_domains) * 100))
                
            status_text.success("🎉 Lead Enrichment Pipeline execution completed!")
            st.session_state.is_processing = False

    # Display Results from st.session_state (Preserved permanently across download clicks!)
    if st.session_state.results_list:
        st.divider()
        st.subheader("2. Extracted Intelligence Results")
        
        # Metrics Banner
        c1, c2, c3, c4 = st.columns(4)
        avg_conf = sum(r.get('data_confidence_score', 0) for r in st.session_state.results_list) / len(st.session_state.results_list)
        tot_tokens = sum(r.get('tokens_used', {}).get('total_tokens', 0) for r in st.session_state.results_list)
        tot_cost = sum(r.get('estimated_cost_usd', 0) for r in st.session_state.results_list)

        c1.metric("Domains Enriched", f"{len(st.session_state.results_list)}")
        c2.metric("Avg Confidence Score", f"{avg_conf:.2f}")
        c3.metric("Total Tokens Used", f"{tot_tokens:,}")
        c4.metric("Estimated Cost ($USD)", f"${tot_cost:.5f}")

        st.markdown("### 📊 Extracted Intelligence Summary Table")
        
        table_rows = []
        for res in st.session_state.results_list:
            emails = ", ".join(res.get("contact_points", [])) if res.get("contact_points") else "None found"
            leaders = [f"{m.get('name')} ({m.get('title')})" for m in res.get("key_leadership", [])]
            leaders_str = ", ".join(leaders) if leaders else "None found"
            
            table_rows.append({
                "Domain": res.get("domain"),
                "Company Name": res.get("company_name"),
                "Overview": res.get("company_overview"),
                "Target ICP": res.get("target_audience_icp"),
                "Emails": emails,
                "Key Leadership": leaders_str,
                "Confidence Score": res.get("data_confidence_score"),
                "Cost ($)": f"${res.get('estimated_cost_usd'):.5f}"
            })
            
        df_results = pd.DataFrame(table_rows)
        st.dataframe(df_results, use_container_width=True)

        st.markdown("### 🔎 Detailed Company Intelligence Cards")
        for res in st.session_state.results_list:
            with st.expander(f"🏢 {res.get('company_name')} ({res.get('domain')}) — Score: {res.get('data_confidence_score')}"):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"**Company Overview:**\n{res.get('company_overview')}")
                    st.markdown(f"**Target Audience / ICP:**\n{res.get('target_audience_icp')}")
                    st.markdown(f"**Contact Points:** `{', '.join(res.get('contact_points', [])) or 'None'}`")
                    st.markdown(f"**Crawled Subpages:** `{', '.join(res.get('crawled_subpages', []))}`")
                with col_b:
                    st.markdown("**Key Leadership & Team Members:**")
                    for leader in res.get("key_leadership", []):
                        name = leader.get("name")
                        title = leader.get("title")
                        url = leader.get("linkedin_url")
                        if url:
                            st.markdown(f"- **{name}** ({title}) — [LinkedIn Profile]({url})")
                        else:
                            st.markdown(f"- **{name}** ({title})")
                    st.caption(f"Tokens: {res.get('tokens_used')} | Estimated Cost: ${res.get('estimated_cost_usd'):.6f}")

        # Export Section
        st.divider()
        st.markdown("### 💾 Export Results")
        col_exp1, col_exp2 = st.columns(2)
        
        json_data = json.dumps(st.session_state.results_list, indent=2)
        csv_data = df_results.to_csv(index=False)

        col_exp1.download_button(
            label="📥 Download output.json",
            data=json_data,
            file_name="output.json",
            mime="application/json",
            use_container_width=True
        )

        col_exp2.download_button(
            label="📥 Download output.csv",
            data=csv_data,
            file_name="output.csv",
            mime="text/csv",
            use_container_width=True
        )

    # Failed Domains List Section
    if st.session_state.failed_domains:
        st.divider()
        st.subheader("⚠️ Domains Requiring Re-Processing / Failed List")
        st.warning(f"The following {len(st.session_state.failed_domains)} domain(s) encountered errors or extraction issues:")
        failed_text = "\n".join(st.session_state.failed_domains)
        st.code(failed_text, language="text")
        st.download_button(
            label="📥 Download Failed Domains List (.txt)",
            data=failed_text,
            file_name="failed_domains.txt",
            mime="text/plain",
            use_container_width=True
        )

with tab2:
    st.subheader("System Architecture & API Docs")
    st.markdown("""
    - **Backend API**: Running on FastAPI (`/docs` OpenAPI available)
    - **Scraping Engine**: Selenium Headless Browser with JS Rendering
    - **LLM Engine**: NVIDIA NIM API (`meta/llama-3.3-70b-instruct`)
    - **Search Fallback**: DuckDuckGo text search for missing LinkedIn profiles
    """)
    if st.button("Check Backend API Health"):
        try:
            res = requests.get(f"{backend_url}/api/v1/health")
            st.json(res.json())
        except Exception as e:
            st.error(f"Health check failed: {e}")
