import io
import os
import qrcode
import pandas as pd
import streamlit as st
from PIL import Image as PILImage
from pdf2image import convert_from_bytes
from reportlab.lib.pagesizes import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage

def generate_pdf(df, name_col, org_col, size_option, qr_col=None, reg_col=None, num_col=None):
    """Generates a multi-page PDF optimized for thermal sticker printing (4x1 or 4x2) without roles."""
    buffer = io.BytesIO()
    page_width = 4 * inch
    
    if size_option == '4" x 2"':
        page_height = 2 * inch
        margin = 0.08 * inch
    else:
        page_height = 1 * inch
        margin = 0.06 * inch  # Tightened print margins to maximize available vertical printable area

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
        fontName='Helvetica-Bold', fontSize=10, leading=11, alignment=1, textColor='#000000'
    )
    
    story = []
    
    for index, row in df.iterrows():
        name = str(row.get(name_col, '')).strip()
        org = str(row.get(org_col, '')).strip()
        
        # Clean up and extract number text formatting safely
        raw_num = row.get(num_col, '') if num_col else ''
        num_str = ""
        if pd.notna(raw_num) and str(raw_num).strip() != "":
            try:
                num_str = str(int(float(raw_num)))
            except ValueError:
                num_str = str(raw_num).strip()
            
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
            
            story.append(RLImage(qr_buffer, width=0.72*inch, height=0.72*inch))
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
            
        # 4. Advanced Continuous Auto-fitting for Organisation Name
        org_len = len(org)
        if org_len > 35:
            f_size = 6.5
            f_leading = 7.5
        elif org_len > 28:
            f_size = 7.5
            f_leading = 8.5
        elif org_len > 22:
            f_size = 8.5
            f_leading = 9.5
        elif org_len > 16:
            f_size = 9.5
            f_leading = 11
        else:
            f_size = 11
            f_leading = 13
            
        style_org = ParagraphStyle(
            name=f'BadgeOrg_{index}', parent=styles['Normal'],
            fontName='Helvetica', fontSize=f_size, leading=f_leading, 
            alignment=1, textColor='#000000'
        )
        
        if org:
            story.append(Paragraph(org, style_org))
            
        # 5. Dedicated 3rd line for the tracking number (No '#' symbol)
        if num_str:
            story.append(Spacer(1, 0.01 * inch))
            story.append(Paragraph(num_str, style_num))
        
        if index < len(df) - 1:
            from reportlab.platypus import PageBreak
            story.append(PageBreak())
            
    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_single_sticker_pdf(name, org, size_option, qr_val="", reg_val="", num_val=""):
    """Generates a single layout PDF for manual entry matching exact parameter mapping targets."""
    single_df = pd.DataFrame([{ 'Name': name, 'Org': org, 'QR': qr_val, 'Reg': reg_val, 'Num': num_val }])
    return generate_pdf(single_df, name_col='Name', org_col='Org', size_option=size_option, qr_col='QR', reg_col='Reg', num_col='Num')

def display_pdf_as_image(pdf_buffer):
    """Converts the first page of the PDF into an image securely using a headless-safe rendering workflow."""
    try:
        # Convert raw PDF bytes directly to an image without utilizing GUI OS frame buffers
        images = convert_from_bytes(pdf_buffer.getvalue(), first_page=1, last_page=1)
        if images:
            img_byte_arr = io.BytesIO()
            images[0].save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            # FIXED: Updated use_container_width=True to the new native API standard width='stretch'
            st.image(img_byte_arr, caption="Live Layout Preview (Page 1)", width="stretch")
    except Exception as e:
        st.warning("Preview generation skipped due to server environment constraints. You can still download and print your PDF safely below!")

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
            st.info("🔍 Review or select your column mapping assignments below:")
            
            clean_columns = {str(col).strip().lower(): col for col in df.columns}
            
            auto_name = next((orig for clean, orig in clean_columns.items() if clean == 'name'), df.columns[0])
            auto_org = next((orig for clean, orig in clean_columns.items() if clean in ['organisation name', 'organization name', 'org name']), df.columns[min(1, len(df.columns)-1)])
            auto_num = next((orig for clean, orig in clean_columns.items() if any(k in clean for k in ['number', 'digit', 'code', 'sl', 'id'] if k != 'organization name')), None)
            
            col1, col2 = st.columns(2)
            with col1:
                name_key = st.selectbox("Name Column:", options=df.columns, index=list(df.columns).index(auto_name))
                org_key = st.selectbox("Organisation Column:", options=df.columns, index=list(df.columns).index(auto_org))
            with col2:
                num_options = ["-- None --"] + list(df.columns)
                default_num_idx = num_options.index(auto_num) if auto_num in num_options else 0
                num_select = st.selectbox("Tracking Number Column:", options=num_options, index=default_num_idx)
                num_key = None if num_select == "-- None --" else num_select

            qr_key, reg_key = None, None
            if size_option == '4" x 2"':
                auto_qr = next((orig for clean, orig in clean_columns.items() if any(k in clean for k in ['qr', 'url', 'link'])), df.columns[0])
                auto_reg = next((orig for clean, orig in clean_columns.items() if any(k in clean for k in ['reg', 'serial', 'card id']) or (clean == 'id' and clean != auto_num)), df.columns[0])
                
                qr_key = st.selectbox("QR/URL Column:", options=df.columns, index=list(df.columns).index(auto_qr))
                reg_key = st.selectbox("Registration ID Column:", options=df.columns, index=list(df.columns).index(auto_reg))

            st.success("✅ Ready to generate layout processing!")
            
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
