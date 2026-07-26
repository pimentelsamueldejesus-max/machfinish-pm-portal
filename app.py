
      import streamlit as st
import pandas as pd
import plotly.express as px

# Page configuration
st.set_page_config(
    page_title="MachFinish PM & Asset Management",
    page_icon="⚙️",
    layout="wide"
)

EXCEL_FILE = 'MACHFINISH_Preventive_Maintenance_Program.xlsx'

# Safe loader for all Excel sheets
@st.cache_data
def load_initial_data():
    xl = pd.ExcelFile(EXCEL_FILE)
    sheets = xl.sheet_names
    
    def read_sheet(keyword):
        for s in sheets:
            if keyword.lower() in s.lower():
                try:
                    df = pd.read_excel(EXCEL_FILE, sheet_name=s, header=3)
                    if df.empty or len(df.columns) < 2:
                        df = pd.read_excel(EXCEL_FILE, sheet_name=s, header=0)
                except:
                    df = pd.read_excel(EXCEL_FILE, sheet_name=s, header=0)
                return df
        return pd.DataFrame()

    df_assets = read_sheet('Asset')
    df_pm = read_sheet('Schedule')
    if df_pm.empty:
        df_pm = read_sheet('PM')
    df_tasks = read_sheet('Task')
    if df_tasks.empty:
        df_tasks = read_sheet('Library')

    return df_assets, df_pm, df_tasks

# Store in Session State so edits persist
if 'df_assets' not in st.session_state or 'df_pm' not in st.session_state:
    try:
        df_assets, df_pm, df_tasks = load_initial_data()
        
        if 'Asset ID' in df_assets.columns:
            df_assets = df_assets.dropna(subset=['Asset ID'])
        if 'Asset ID' in df_pm.columns:
            df_pm = df_pm.dropna(subset=['Asset ID'])
            
        if 'Purchase Cost' in df_assets.columns:
            df_assets['Purchase Cost'] = pd.to_numeric(df_assets['Purchase Cost'], errors='coerce').fillna(0)
        if 'Est. Labor (Hrs)' in df_pm.columns:
            df_pm['Est. Labor (Hrs)'] = pd.to_numeric(df_pm['Est. Labor (Hrs)'], errors='coerce').fillna(0)
            
        st.session_state.df_assets = df_assets
        st.session_state.df_pm = df_pm
        st.session_state.df_tasks = df_tasks
    except Exception as e:
        st.error(f"Error loading Excel file: {e}")
        st.session_state.df_assets = pd.DataFrame()
        st.session_state.df_pm = pd.DataFrame()
        st.session_state.df_tasks = pd.DataFrame()

st.title("⚙️ MachFinish Preventive Maintenance Portal")

# Sidebar Filters
st.sidebar.header("🔍 Global Filters")

lines = ["All"]
if not st.session_state.df_assets.empty and 'Facility / Line' in st.session_state.df_assets.columns:
    lines += sorted(st.session_state.df_assets['Facility / Line'].dropna().unique().tolist())
selected_line = st.sidebar.selectbox("Facility Line / Location", lines)

criticalities = ["All"]
if not st.session_state.df_assets.empty and 'Criticality' in st.session_state.df_assets.columns:
    criticalities += sorted(st.session_state.df_assets['Criticality'].dropna().unique().tolist())
selected_crit = st.sidebar.selectbox("Criticality Level", criticalities)

# Filter Data
filtered_assets = st.session_state.df_assets.copy()
filtered_pm = st.session_state.df_pm.copy()

if selected_line != "All" and 'Facility / Line' in filtered_assets.columns:
    filtered_assets = filtered_assets[filtered_assets['Facility / Line'] == selected_line]
if selected_line != "All" and 'Facility / Line' in filtered_pm.columns:
    filtered_pm = filtered_pm[filtered_pm['Facility / Line'] == selected_line]

if selected_crit != "All" and 'Criticality' in filtered_assets.columns:
    filtered_assets = filtered_assets[filtered_assets['Criticality'] == selected_crit]
if selected_crit != "All" and 'Criticality' in filtered_pm.columns:
    filtered_pm = filtered_pm[filtered_pm['Criticality'] == selected_crit]

# --- 4 TABS ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Executive Dashboard", 
    "🏭 Asset Registry", 
    "🛠️ Work Order Manager (Editable)", 
    "📋 PM Task Library"
])

# TAB 1: EXECUTIVE DASHBOARD
with tab1:
    k1, k2, k3 = st.columns(3)
    k1.metric("Total Active Assets", len(filtered_assets))
    
    cost_sum = filtered_assets['Purchase Cost'].sum() if 'Purchase Cost' in filtered_assets.columns else 0
    k2.metric("Portfolio Asset Value", f"${cost_sum:,.2f}")
    
    k3.metric("Scheduled Work Orders", len(filtered_pm))
    
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if 'Criticality' in filtered_assets.columns and not filtered_assets.empty:
            fig1 = px.pie(filtered_assets, names='Criticality', title="Asset Criticality Breakdown",
                          color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("No criticality data available.")
            
    with c2:
        if 'Completion Status' in filtered_pm.columns and not filtered_pm.empty:
            fig2 = px.histogram(filtered_pm, x='Completion Status', title="Work Order Status Breakdown",
                                color='Completion Status', color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No work order status data available.")

# TAB 2: ASSET REGISTRY
with tab2:
    st.subheader("Asset Registry")
    st.dataframe(filtered_assets, use_container_width=True, hide_index=True)

# TAB 3: EDITABLE WORK ORDERS
with tab3:
    st.subheader("Interactive Work Order Manager")
    
    if not st.session_state.df_pm.empty:
        st.markdown("#### Option 1: Edit Table Directly")
        st.info("Double-click cells below to change status or service notes:")
        
        cols_to_show = [c for c in ['Asset ID', 'Equipment Description', 'Facility / Line', 'Criticality', 'Completion Status', 'Assigned Task / Service Standard'] if c in st.session_state.df_pm.columns]
        
        edited_df = st.data_editor(
            st.session_state.df_pm[cols_to_show],
            key="pm_editor",
            use_container_width=True,
            hide_index=True
        )
        
        if st.button("Save Table Updates"):
            st.session_state.df_pm.update(edited_df)
            st.success("Work orders updated successfully!")

        st.markdown("---")

        st.markdown("#### Option 2: Single Work Order Update Form")
        if 'Asset ID' in st.session_state.df_pm.columns:
            asset_ids = sorted(st.session_state.df_pm['Asset ID'].dropna().unique())
            if asset_ids:
                wo_asset = st.selectbox("Select Asset ID to Edit", asset_ids)
                
                row_idx = st.session_state.df_pm[st.session_state.df_pm['Asset ID'] == wo_asset].index[0]
                current_row = st.session_state.df_pm.loc[row_idx]
                
                with st.form("single_wo_form"):
                    desc = current_row.get('Equipment Description', wo_asset)
                    st.write(f"Editing Asset: **{desc}**")
                    
                    status_options = ["Scheduled", "In Progress", "Completed", "On Hold"]
                    curr_status = str(current_row.get('Completion Status', 'Scheduled'))
                    default_index = status_options.index(curr_status) if curr_status in status_options else 0
                    
                    new_status = st.selectbox("Status", status_options, index=default_index)
                    curr_task = str(current_row.get('Assigned Task / Service Standard', ''))
                    new_task = st.text_area("Assigned Task / Service Standard", value=curr_task)
                    
                    submit = st.form_submit_button("Update Work Order")
                    if submit:
                        if 'Completion Status' in st.session_state.df_pm.columns:
                            st.session_state.df_pm.loc[row_idx, 'Completion Status'] = new_status
                        if 'Assigned Task / Service Standard' in st.session_state.df_pm.columns:
                            st.session_state.df_pm.loc[row_idx, 'Assigned Task / Service Standard'] = new_task
                        st.success(f"Work order for **{wo_asset}** updated successfully!")
                        st.rerun()
    else:
        st.warning("No PM Schedule data found.")

# TAB 4: PM TASK LIBRARY & PROCEDURES
with tab4:
    st.subheader("PM Task Library & Standard Operating Procedures")
    if not st.session_state.df_tasks.empty:
        st.dataframe(st.session_state.df_tasks, use_container_width=True, hide_index=True)
    else:
        st.info("Showing PM Schedule task references:")
        if not st.session_state.df_pm.empty:
            task_cols = [c for c in ['Asset ID', 'Equipment Description', 'Assigned Task / Service Standard', 'Frequency', 'Est. Labor (Hrs)'] if c in st.session_state.df_pm.columns]
            st.dataframe(st.session_state.df_pm[task_cols], use_container_width=True, hide_index=True)
        else:
            st.write("No task library data found.")
     
