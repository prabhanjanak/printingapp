import io
import pandas as pd
import streamlit as st
from reportlab.lib.pagesizes import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

def generate_pdf(df, common_role, name_col, org_col):
    """
    Generates a multi-page PDF using the dynamically matched column names.
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
        fontSize=16,
        leading=18,
        alignment=1,
        textColor='#000000'
    )
    
    style_sub = ParagraphStyle(
        name='BadgeSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=11,
        alignment=1,
        textColor='#444444'
    )
    
    story = []
    
    for index, row in df.iterrows():
        # Read from the dynamically discovered column names
        name = str(row.get(name_col, '')).strip()
        org = str(row.get(org_col, '')).strip()
        role = str(common_role).strip()
        
        story.append(Spacer(1, 0.05 * inch)) 
        story.append(Paragraph(name, style_name))
        story.append(Spacer(1, 0.02 * inch))
        
        sub_text = f"{org} &bull; {role}" if org and role else f"{org}{role}"
        story.append(Paragraph(sub_text, style_sub))
        
        if index < len(df) - 1:
            from reportlab.platypus import PageBreak
            story.append(PageBreak())
            
    doc.build(story)
    buffer.seek(0)
    return buffer

# --- Streamlit UI Setup ---
st.set_page_config(page_title="Badge PDF Generator", page_icon="📇", layout="centered")

st.title("📇 Custom Badge PDF Generator")
st.write("Upload your Excel sheet to generate a multi-page **4\" x 1\"** printable PDF.")

common_role = st.text_input("Enter the Role to apply to everyone:", value="Attendee")

uploaded_file = st.file_uploader("Choose your Excel file", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        
        # --- SMART COLUMN MATCHING ---
        # 1. Clean the column names (remove hidden spaces, convert to lowercase for matching)
        clean_columns = {str(col).strip().lower(): col for col in df.columns}
        
        # 2. Look for matches flexibly
        name_key = next((orig for clean, orig in clean_columns.items() if clean == 'name'), None)
        org_key = next((orig for clean, orig in clean_columns.items() if clean in ['organisation name', 'organization name']), None)
        
        # Validate if we found them
        if not name_key or not org_key:
            st.error("❌ Could not match the required columns.")
            st.write("Here are the column headers we detected in your file (check for odd characters):")
            st.write(list(df.columns))
        else:
            st.success("✅ Columns matched successfully!")
            
            # Create preview using the matched columns
            preview_df = pd.DataFrame({
                'Name': df[name_key],
                'Organisation Name': df[org_key],
                'Role': common_role
            })
            
            st.write("### Data Preview (First 5 Rows):")
            st.dataframe(preview_df.head())
            
            if st.button("✨ Generate Badges PDF"):
                with st.spinner("Processing layout..."):
                    pdf_buffer = generate_pdf(df, common_role, name_key, org_key)
                    
                st.balloons()
                
                st.download_button(
                    label="📥 Download Badges PDF",
                    data=pdf_buffer,
                    file_name="event_badges.pdf",
                    mime="application/pdf"
                )
                
    except Exception as e:
        st.error(f"An error occurred: {e}")
