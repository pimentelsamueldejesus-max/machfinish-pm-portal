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

# Initialize data in Streamlit Session State so changes persist during the session
if 'df_assets' not in st.session_state or 'df_pm' not in st.session_state:
    df_assets = pd.read_excel(EXCEL_FILE, sheet_name='Asset Registry', header=3).dropna(subset=['Asset ID'])
    df_pm = pd.read_excel(EXCEL_FILE, sheet_name='PM Schedule', header=3).dropna(subset=['Asset ID'])
    
    # Clean numeric types
    df_assets['Purchase Cost'] = pd.to_numeric(df_assets['Purchase Cost'], errors='coerce').fillna(0)
    df_pm['Est. Labor (Hrs)'] = pd.to_numeric(df_pm['Est. Labor (Hrs)'], errors='coerce').fillna(0)
    
    st.session_state.df_assets = df_assets
    st.session_state.df_pm = df_pm

st.title("⚙️ MachFinish Preventive Maintenance Portal")

# Sidebar Filters
st.sidebar.header("🔍 Global Filters")

lines = ["All"] + sorted(st.session_state.df_assets['Facility / Line'].dropna().unique().tolist())
selected_line = st.sidebar.selectbox("Facility Line / Location", lines)

criticalities = ["All"] + sorted(st.session_state.df_assets['Criticality'].dropna().unique().tolist())
selected_crit = st.sidebar.selectbox("Criticality Level", criticalities)

# Filter Data
filtered_assets = st.session_state.df_assets.copy()
filtered_pm = st.session_state.df_pm.copy()

if selected_line != "All":
    filtered_assets = filtered_assets[filtered_assets['Facility / Line'] == selected_line]
    filtered_pm = filtered_pm[filtered_pm['Facility / Line'] == selected_line]

if selected_crit != "All":
    filtered_assets = filtered_assets[filtered_assets['Criticality'] == selected_crit]
    filtered_pm = filtered_pm[filtered_pm['Criticality'] == selected_crit]

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🏭 Asset Registry", "🛠️ Work Orders (Editable)"])

with tab1:
    k1, k2, k3 = st.columns(3)
    k1.metric("Total Active Assets", len(filtered_assets))
    k2.metric("Portfolio Value", f"${filtered_assets['Purchase Cost'].sum():,.2f}")
    k3.metric("Scheduled PM Orders", len(filtered_pm))
    
    st.markdown("---")
    fig = px.pie(filtered_assets, names='Criticality', title="Criticality Breakdown", color='Criticality',
                 color_discrete_map={'High': '#EF4444', 'Medium': '#F59E0B', 'Low': '#10B981'})
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Asset Registry")
    st.dataframe(filtered_assets, use_container_width=True, hide_index=True)

# TAB 3: EDITABLE WORK ORDERS
with tab3:
    st.subheader("Interactive Work Order Manager")
    
    # 1. Edit using the Data Editor Table directly
    st.markdown("#### Option 1: Edit Table Directly")
    st.info("Double-click any cell in the **Completion Status** or **Assigned Task** columns below to edit:")
    
    edited_df = st.data_editor(
        st.session_state.df_pm[['Asset ID', 'Equipment Description', 'Facility / Line', 'Criticality', 'Completion Status', 'Assigned Task / Service Standard']],
        key="pm_editor",
        use_container_width=True,
        hide_index=True
    )
    
    if st.button("Save Table Updates"):
        # Update session state with edited table values
        st.session_state.df_pm.update(edited_df)
        st.success("Work orders updated successfully!")

    st.markdown("---")

    # 2. Edit single Work Order via Form
    st.markdown("#### Option 2: Update Single Work Order")
    wo_asset = st.selectbox("Select Asset ID", sorted(st.session_state.df_pm['Asset ID'].unique()))
    
    # Find matching row index
    row_idx = st.session_state.df_pm[st.session_state.df_pm['Asset ID'] == wo_asset].index[0]
    current_row = st.session_state.df_pm.loc[row_idx]
    
    with st.form("single_wo_form"):
        st.write(f"Editing: **{current_row['Equipment Description']}**")
        
        status_options = ["Scheduled", "In Progress", "Completed", "On Hold"]
        curr_status = current_row['Completion Status']
        default_index = status_options.index(curr_status) if curr_status in status_options else 0
        
        new_status = st.selectbox("Status", status_options, index=default_index)
        new_task = st.text_area("Assigned Task / Service Standard", value=str(current_row['Assigned Task / Service Standard']))
        
        submit = st.form_submit_button("Update Work Order")
        if submit:
            st.session_state.df_pm.loc[row_idx, 'Completion Status'] = new_status
            st.session_state.df_pm.loc[row_idx, 'Assigned Task / Service Standard'] = new_task
            st.success(f"Work order for **{wo_asset}** updated to **{new_status}**!")
            st.rerun()
      
     
