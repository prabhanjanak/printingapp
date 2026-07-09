import io
import pandas as pd
import streamlit as st
from reportlab.lib.pagesizes import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

def generate_pdf(df, common_role):
    """
    Generates a multi-page PDF from a DataFrame where each row is a 4x1 inch page.
    """
    buffer = io.BytesIO()
    
    # Define custom page size: 4 inches wide, 1 inch high
    page_width = 4 * inch
    page_height = 1 * inch
    
    # Establish tight margins to maximize printable area and ensure centering
    margin = 0.1 * inch
    
    # Create the ReportLab document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=(page_width, page_height),
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin
    )
    
    # Initialize styles
    styles = getSampleStyleSheet()
    
    # Custom style for the Name (Title)
    style_name = ParagraphStyle(
        name='BadgeName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=18,
        alignment=1, # 1 = Center alignment
        textColor='#000000'
    )
    
    # Custom style for Organisation Name and Role (Subtitle)
    style_sub = ParagraphStyle(
        name='BadgeSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=11,
        alignment=1, # 1 = Center alignment
        textColor='#444444'
    )
    
    story = []
    
    for index, row in df.iterrows():
        # Clean up data and map to your exact column names
        name = str(row.get('Name', '')).strip()
        org = str(row.get('Organisation Name', '')).strip()
        role = str(common_role).strip()
        
        # Build the text layout for the current page
        story.append(Spacer(1, 0.05 * inch)) 
        story.append(Paragraph(name, style_name))
        story.append(Spacer(1, 0.02 * inch))
        
        # Combine Subtitles into a scannable format
        sub_text = f"{org} &bull; {role}" if org and role else f"{org}{role}"
        story.append(Paragraph(sub_text, style_sub))
        
        # Keep pages distinct: add a PageBreak for all but the last item
        if index < len(df) - 1:
            from reportlab.platypus import PageBreak
            story.append(PageBreak())
            
    # Build the document into the buffer
    doc.build(story)
    buffer.seek(0)
    return buffer

# --- Streamlit UI Setup ---
st.set_page_config(page_title="Badge PDF Generator", page_icon="📇", layout="centered")

st.title("📇 Custom Badge PDF Generator")
st.write("Upload your Excel sheet to generate a multi-page **4\" x 1\"** printable PDF.")

# 1. Ask user for the global Role to apply to everyone
common_role = st.text_input("Enter the Role to apply to everyone:", value="Attendee")

# Important expectations for the user
with st.expander("💡 View Excel Sheet Column Requirements"):
    st.markdown("""
    Your Excel file must contain these exact columns (other columns will be ignored):
    * `Name`
    * `Organisation Name`
    """)

uploaded_file = st.file_uploader("Choose your Excel file", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        # Read Excel File
        df = pd.read_excel(uploaded_file)
        
        # Validate Column presence for Name and Organisation Name
        required_columns = ['Name', 'Organisation Name']
        missing_cols = [col for col in required_columns if col not in df.columns]
        
        if missing_cols:
            st.error(f"❌ Missing required columns: {', '.join(missing_cols)}. Please check your spelling.")
        else:
            st.success("✅ Excel file loaded successfully!")
            
            # Filter and show just the data we need + the typed role for confirmation
            preview_df = df[required_columns].copy()
            preview_df['Role'] = common_role
            
            st.write("### Data Preview (First 5 Rows):")
            st.dataframe(preview_df.head())
            
            # Generate Button
            if st.button("✨ Generate Badges PDF"):
                with st.spinner("Processing layout and generating PDF..."):
                    pdf_buffer = generate_pdf(df, common_role)
                    
                st.balloons()
                
                # Download Button for the final PDF artifact
                st.download_button(
                    label="📥 Download Badges PDF",
                    data=pdf_buffer,
                    file_name="event_badges.pdf",
                    mime="application/pdf"
                )
                
    except Exception as e:
        st.error(f"An error occurred while processing the file: {e}")
