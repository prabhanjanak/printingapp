import io
import base64
import pandas as pd
import streamlit as st
from reportlab.lib.pagesizes import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

def generate_pdf(df, common_role, name_col, org_col):
    """Generates a multi-page PDF optimized for 4x1 thermal sticker printing from a DataFrame."""
    buffer = io.BytesIO()
    page_width = 4 * inch
    page_height = 1 * inch
    margin = 0.1 * inch
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=(page_width, page_height),
        leftMargin=margin, rightMargin=margin,
        topMargin=margin, bottomMargin=margin
    )
    
    styles = getSampleStyleSheet()
    style_name = ParagraphStyle(
        name='BadgeName', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=20, leading=22, alignment=1, textColor='#000000'
    )
    style_sub = ParagraphStyle(
        name='BadgeSub', parent=styles['Normal'],
        fontName='Helvetica', fontSize=11, leading=13, alignment=1, textColor='#000000'
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

def generate_single_sticker_pdf(name, org, role):
    """Generates a single 4x1 PDF for a manual, on-the-spot entry."""
    single_df = pd.DataFrame([{ 'Name': name, 'Org': org }])
    return generate_pdf(single_df, role, 'Name', 'Org')

def display_and_print_pdf(pdf_buffer):
    """Encodes PDF into base64 and renders it natively inside st.iframe."""
    base64_pdf = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
    data_url = f"data:application/pdf;base64,{base64_pdf}"
    
    # NEW API: Renders the PDF directly inside the modernized native iframe engine
    st.iframe(src=data_url, height=250)
    
    st.info("💡 To print instantly without downloading, click the printer icon inside the preview box above!")

# --- Streamlit UI Setup ---
st.set_page_config(page_title="Thermal Badge Generator", page_icon="🖨️", layout="centered")

st.title("🖨️ Thermal Sticker Badge Generator")
st.write("Generate layout batches or on-the-spot individual labels with instant direct browser printing.")

# --- DYNAMIC ROLE MANAGEMENT SECTION ---
st.subheader("🛠️ Create Custom Roles")
if 'custom_roles' not in st.session_state:
    st.session_state.custom_roles = ["Attendee", "Exhibitor", "Crew", "Speaker"]

new_role = st.text_input("Type a new role name and press Enter to save it to your master list:")
if new_role:
    cleaned_role = new_role.strip()
    if cleaned_role and cleaned_role not in st.session_state.custom_roles:
        st.session_state.custom_roles.append(cleaned_role)
        st.success(f"Added '{cleaned_role}' to your master options!")

st.write("---")

tab1, tab2 = st.tabs(["📁 Batch Upload (Excel)", "✏️ On-the-Spot Single Print"])

# --- TAB 1: BULK EXCEL UPLOADER ---
with tab1:
    st.subheader("Upload Excel File")
    batch_role = st.selectbox("Select Role for this Excel batch:", options=st.session_state.custom_roles, key="batch_role_select")
    uploaded_file = st.file_uploader("Choose your Excel file", type=["xlsx", "xls"])

    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            clean_columns = {str(col).strip().lower(): col for col in df.columns}
            
            name_key = next((orig for clean, orig in clean_columns.items() if clean == 'name'), None)
            org_key = next((orig for clean, orig in clean_columns.items() if clean in ['organisation name', 'organization name']), None)
            
            if not name_key or not org_key:
                st.error("❌ Could not match the required columns.")
            else:
                st.success(f"✅ Ready! Applied role: **{batch_role}**")
                
                if st.button("✨ Load Batch Preview", key="batch_gen"):
                    with st.spinner("Processing batch layout..."):
                        pdf_buffer = generate_pdf(df, batch_role, name_key, org_key)
                    
                    st.write("### Preview & Printer Window")
                    display_and_print_pdf(pdf_buffer)
        except Exception as e:
            st.error(f"An error occurred: {e}")

# --- TAB 2: EMERGENCY SINGLE PRINT ---
with tab2:
    st.subheader("Create a Single On-Spot Sticker")
    st.write("Enter details and click the display button below:")
    
    manual_name = st.text_input("Full Name:")
    manual_org = st.text_input("Organisation Name:")
    single_role = st.selectbox("Select Role for this person:", options=st.session_state.custom_roles, key="single_role_select")

    if st.button("✨ Load On-Spot Print Preview", key="single_gen"):
        if not manual_name:
            st.warning("⚠️ Please enter a Name before generating.")
        else:
            with st.spinner("Formatting single sticker layout..."):
                single_pdf_buffer = generate_single_sticker_pdf(manual_name, manual_org, single_role)
            
            st.success(f"✅ Layout generated for {manual_name}!")
            display_and_print_pdf(single_pdf_buffer)
