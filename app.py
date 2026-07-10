import io
import fitz  # PyMuPDF
import qrcode
import pandas as pd
import streamlit as st
from reportlab.lib.pagesizes import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image

def generate_pdf(df, name_col, org_col, size_option, qr_col=None, reg_col=None, num_col=None):
    """Generates a multi-page PDF optimized for thermal sticker printing (4x1 or 4x2) without roles."""
    buffer = io.BytesIO()
    page_width = 4 * inch
    
    if size_option == '4" x 2"':
        page_height = 2 * inch
        margin = 0.08 * inch
    else:
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
        fontName='Helvetica-Bold', fontSize=18, leading=20, alignment=1, textColor='#000000'
    )
    style_reg = ParagraphStyle(
        name='BadgeReg', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=10, leading=12, alignment=1, textColor='#444444'
    )
    style_num = ParagraphStyle(
        name='BadgeNum', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=10, leading=12, alignment=1, textColor='#555555'
    )
    
    story = []
    
    for index, row in df.iterrows():
        name = str(row.get(name_col, '')).strip()
        org = str(row.get(org_col, '')).strip()
        
        # Format the 4-digit number cleanly if it exists
        raw_num = row.get(num_col, '') if num_col else ''
        num_str = ""
        if pd.notna(raw_num) and str(raw_num).strip() != "":
            num_str = str(int(float(raw_num))) if str(raw_num).replace('.','',1).isdigit() else str(raw_num).strip()
            if num_str.isdigit() and len(num_str) < 4:
                num_str = num_str.zfill(4)
        
        if size_option == '4" x 2"':
            # 1. QR Code Generation
            qr_data = str(row.get(qr_col, '')).strip() if qr_col else "https://example.com"
            if not qr_data or qr_data.lower() == 'nan':
                qr_data = "N/A"
                
            qr = qrcode.QRCode(version=1, box_size=10, border=0)
            qr.add_data(qr_data)
            qr.make(fitz=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            qr_buffer = io.BytesIO()
            qr_img.save(qr_buffer, format="PNG")
            qr_buffer.seek(0)
            
            story.append(Image(qr_buffer, width=0.72*inch, height=0.72*inch))
            story.append(Spacer(1, 0.02 * inch))
            
            # 2. Name Layout
            story.append(Paragraph(name, style_name))
            story.append(Spacer(1, 0.02 * inch))
            
            # 3. Registration ID Layout
            reg_num = str(row.get(reg_col, '')).strip() if reg_col else "SEH-V2020-OSXXXXX"
            story.append(Paragraph(reg_num, style_reg))
            story.append(Spacer(1, 0.02 * inch))
            
        else:
            # Standard 4x1 Layout structure
            story.append(Spacer(1, 0.02 * inch)) 
            story.append(Paragraph(name, style_name))
            story.append(Spacer(1, 0.02 * inch))
            
        # 4. Smart Sizing for Organization Name
        # Dynamically shrink font size if text is long and lengthy
        org_length = len(org)
        if org_length > 25:
            current_font_size = 8
            current_leading = 9
        elif org_length > 18:
            current_font_size = 9
            current_leading = 11
        else:
            current_font_size = 11
            current_leading = 13
            
        style_org = ParagraphStyle(
            name=f'BadgeOrg_{index}', parent=styles['Normal'],
            fontName='Helvetica', fontSize=current_font_size, leading=current_leading, 
            alignment=1, textColor='#000000'
        )
        
        if org:
            story.append(Paragraph(org, style_org))
            
        # 5. Dedicated line for the tracking number
        if num_str:
            story.append(Spacer(1, 0.01 * inch))
            story.append(Paragraph(f"#{num_str}", style_num))
        
        if index < len(df) - 1:
            from reportlab.platypus import PageBreak
            story.append(PageBreak())
            
    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_single_sticker_pdf(name, org, size_option, qr_val="", reg_val="", num_val=""):
    """Generates a single layout PDF for manual entry."""
    single_df = pd.DataFrame([{ 'Name': name, 'Org': org, 'QR': qr_val, 'Reg': reg_val, 'Num': num_val }])
    return generate_pdf(single_df, 'Name', 'Org', size_option, 'QR', 'Reg', 'Num')

def display_pdf_as_image(pdf_buffer):
    """Converts the first page of the PDF into a PNG image preview."""
    try:
        pdf_doc = fitz.open(stream=pdf_buffer.getvalue(), filetype="pdf")
        page = pdf_doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))
        image_bytes = pix.tobytes("png")
        st.image(image_bytes, caption="Live Layout Preview (Page 1)", use_container_width=True)
    except Exception as e:
        st.warning(f"Preview image generation skipped: {e}")

# --- Streamlit UI Setup ---
st.set_page_config(page_title="Dynamic Thermal Badge Generator", page_icon="🖨️", layout="centered")

st.title("🖨️ Multi-Size Thermal Sticker Generator")
st.write("Switch layouts between clean 4x1 tracking labels or complete 4x2 QR code visitor badges.")

# --- MASTER CONFIGURATION ---
st.subheader("⚙️ Global Layout Settings")
size_option = st.selectbox('Select Sticker Dimensions:', options=['4" x 1"', '4" x 2"'])

st.write("---")

tab1, tab2 = st.tabs(["📁 Batch Upload (Excel)", "✏️ On-the-Spot Single Print"])

# --- TAB 1: BULK EXCEL UPLOADER ---
with tab1:
    st.subheader("Upload Excel File")
    uploaded_file = st.file_uploader("Choose your Excel file", type=["xlsx", "xls"])

    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            clean_columns = {str(col).strip().lower(): col for col in df.columns}
            
            name_key = next((orig for clean, orig in clean_columns.items() if clean == 'name'), None)
            org_key = next((orig for clean, orig in clean_columns.items() if clean in ['organisation name', 'organization name']), None)
            num_key = next((orig for clean, orig in clean_columns.items() if any(k in clean for k in ['number', 'digit', 'code', 'sl', 'id'] if k != 'organization name')), None)
            
            qr_key, reg_key = None, None
            if size_option == '4" x 2"':
                qr_key = next((orig for clean, orig in clean_columns.items() if any(k in clean for k in ['qr', 'url', 'link'])), None)
                reg_key = next((orig for clean, orig in clean_columns.items() if any(k in clean for k in ['reg', 'serial', 'card id']) or (clean == 'id' and clean != num_key)), None)

            if not name_key or not org_key:
                st.error("❌ Missing required 'Name' or 'Organisation Name' columns.")
            elif size_option == '4" x 2"' and (not qr_key or not reg_key):
                st.error("❌ For 4\" x 2\" stickers, we couldn't auto-detect your QR/URL column or Registration ID column.")
                st.write("Detected Columns inside your file:", list(df.columns))
            else:
                st.success(f"✅ Columns matched successfully for layout size {size_option}!")
                
                if st.button("✨ Load Batch Preview & Build Layout", key="batch_gen"):
                    with st.spinner("Processing batch formatting..."):
                        pdf_buffer = generate_pdf(df, name_key, org_key, size_option, qr_key, reg_key, num_key)
                    
                    st.write("### Preview & Printer Window")
                    display_pdf_as_image(pdf_buffer)
                    
                    st.download_button(
                        label="📥 Download & Send to Thermal Printer",
                        data=pdf_buffer,
                        file_name=f"batch_{size_option.replace(' ', '').replace('&quot;', '')}_badges.pdf",
                        mime="application/pdf"
                    )
        except Exception as e:
            st.error(f"An error occurred: {e}")

# --- TAB 2: EMERGENCY SINGLE PRINT ---
with tab2:
    st.subheader("Create a Single On-Spot Sticker")
    st.write("Fill out the specific required data properties below:")
    
    manual_name = st.text_input("Full Name:")
    manual_org = st.text_input("Organisation Name:")
    manual_num = st.text_input("4-Digit Tracking Number (Optional):", placeholder="e.g. 1234")
    
    manual_qr = ""
    manual_reg = ""
    if size_option == '4" x 2"':
        manual_qr = st.text_input("QR Code URL / Content Data:", value="https://example.com")
        manual_reg = st.text_input("Registration ID Number:", value="SEH-V2020-OSXXXXX")

    if st.button("✨ Load On-Spot Print Preview", key="single_gen"):
        if not manual_name:
            st.warning("⚠️ Please enter a Name before generating.")
        else:
            with st.spinner("Formatting single sticker layout..."):
                single_pdf_buffer = generate_single_sticker_pdf(
                    manual_name, manual_org, size_option, manual_qr, manual_reg, manual_num
                )
            
            st.success(f"✅ Layout generated successfully!")
            display_pdf_as_image(single_pdf_buffer)
            
            st.download_button(
                label="📥 Download & Send to Thermal Printer",
                data=single_pdf_buffer,
                file_name=f"single_{manual_name.replace(' ', '_').lower()}_badge.pdf",
                mime="application/pdf"
            )
