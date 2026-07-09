import io
import pandas as pd
import streamlit as st
from reportlab.lib.pagesizes import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

def generate_pdf(df, common_role, name_col, org_col):
    """
    Generates a multi-page PDF optimized for 4x1 thermal sticker printing.
    """
    buffer = io.BytesIO()
    
    # Define custom page size: 4 inches wide, 1 inch high
    page_width = 4 * inch
    page_height = 1 * inch
    margin = 0.1 * inch
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=(page_width, page_height),
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin
    )
    
    styles = getSampleStyleSheet()
    
    style_name = ParagraphStyle(
        name='BadgeName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=22,
        alignment=1, # Center
        textColor='#000000'
    )
    
    style_sub = ParagraphStyle(
        name='BadgeSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=13,
        alignment=1, # Center
        textColor='#000000'
    )
    
    story = []
    
    for index, row in df.iterrows():
        name = str(row.get(name_col, '')).strip()
        org = str(row.get(org_col, '')).strip()
        role = str(common_role).strip()
        
        story.append(Spacer(1, 0.02 * inch)) 
        story.append(Paragraph(name, style_name))
        story.append(Spacer(1, 0.01 * inch))
        
        sub_text = f"{org} &bull; {role}" if org and role else f"{org}{role}"
        story.append(Paragraph(sub_text, style_sub))
        
        if index < len(df) - 1:
            from reportlab.platypus import PageBreak
            story.append(PageBreak())
            
    doc.build(story)
    buffer.seek(0)
    return buffer

# --- Streamlit UI Setup ---
st.set_page_config(page_title="Thermal Badge Generator", page_icon="🖨️", layout="centered")

st.title("🖨️ Thermal Sticker Badge Generator")
st.write("Manage your custom roles dynamically and generate perfectly scaled 4\" x 1\" badges.")

# --- DYNAMIC ROLE MANAGEMENT SECTION ---
st.subheader("🛠️ Role Management Setup")

# Initialize the roles list in the app session state so it doesn't disappear on button clicks
if 'custom_roles' not in st.session_state:
    st.session_state.custom_roles = ["Attendee", "Exhibitor", "Crew", "Speaker"]

# Input box to add a brand new role to the list
new_role = st.text_input("Type a new role name and press Enter to add it to the dropdown:")
if new_role:
    cleaned_role = new_role.strip()
    if cleaned_role and cleaned_role not in st.session_state.custom_roles:
        st.session_state.custom_roles.append(cleaned_role)
        st.success(f"Added '{cleaned_role}' to the option list below!")

# Dropdown menu created dynamically from the managed list
selected_role = st.selectbox("Select the active Role to apply to this batch:", options=st.session_state.custom_roles)

st.write("---")

# --- EXCEL FILE UPLOADER SECTION ---
uploaded_file = st.file_uploader("Choose your Excel file", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        
        # Clean the column names for matching
        clean_columns = {str(col).strip().lower(): col for col in df.columns}
        
        name_key = next((orig for clean, orig in clean_columns.items() if clean == 'name'), None)
        org_key = next((orig for clean, orig in clean_columns.items() if clean in ['organisation name', 'organization name']), None)
        
        if not name_key or not org_key:
            st.error("❌ Could not match the required columns.")
            st.write("Here are the column headers we detected in your file:")
            st.write(list(df.columns))
        else:
            st.success(f"✅ Columns matched successfully! Applying role: **{selected_role}**")
            
            preview_df = pd.DataFrame({
                'Name': df[name_key],
                'Organisation Name': df[org_key],
                'Role': selected_role
            })
            
            st.write("### Data Preview:")
            st.dataframe(preview_df.head())
            
            if st.button("✨ Generate Badges PDF"):
                with st.spinner("Processing layout..."):
                    pdf_buffer = generate_pdf(df, selected_role, name_key, org_key)
                    
                st.balloons()
                
                st.download_button(
                    label=f"📥 Download Badges PDF ({selected_role})",
                    data=pdf_buffer,
                    file_name=f"{selected_role.lower()}_thermal_badges.pdf",
                    mime="application/pdf"
                )
                
    except Exception as e:
        st.error(f"An error occurred: {e}")
