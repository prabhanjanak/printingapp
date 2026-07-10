import io
import pandas as pd
import streamlit as st
from PIL import Image as PILImage, ImageDraw
from reportlab.lib.pagesizes import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage

def draw_native_qr_fallback():
    """Generates a high-contrast fallback vector block pattern safely without external C-extensions."""
    img = PILImage.new('RGB', (100, 100), color='white')
    draw = ImageDraw.Draw(img)
    # Renders a standard static procedural high-contrast mock QR layout target
    draw.rectangle([10, 10, 40, 40], fill="black")
    draw.rectangle([60, 10, 90, 40], fill="black")
    draw.rectangle([10, 60, 40, 90], fill="black")
    draw.rectangle([25, 25, 30, 30], fill="black")
    draw.rectangle([75, 75, 85, 85], fill="black")
    draw.rectangle([50, 50, 65, 65], fill="black")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

def draw_preview_image(name, org, size_option, reg_val="", num_val=""):
    """Renders a safe software-side canvas preview image bypassing heavy binary components."""
    dpi = 300
    width_px = 4 * dpi
    height_px = 2 * dpi if size_option == '4" x 2"' else 1 * dpi
    
    img = PILImage.new('RGB', (width_px, height_px), color='white')
    draw = ImageDraw.Draw(img)
    
    name = str(name).strip()
    org = str(org).strip()
    
    num_str = ""
    if num_val and str(num_val).strip() != "" and str(num_val).lower() != "none":
        try:
            num_str = str(int(float(num_val)))
        except ValueError:
            num_str = str(num_val).strip()
        if num_str.isdigit() and len(num_str) < 4:
            num_str = num_str.zfill(4)

    if size_option == '4" x 2"':
        reg_num = str(reg_val).strip() if reg_val else "SEH-V2020-OSXXXXX"
        draw.rectangle([width_px//2 - 60, 40, width_px//2 + 60, 160], outline="black", width=2)
        draw.text((width_px//2, 100), "[ QR ]", fill="black", anchor="mm")
        draw.text((width_px//2, 220), name, fill="black", anchor="mm")
        draw.text((width_px//2, 280), reg_num, fill="gray", anchor="mm")
        draw.text((width_px//2, 340), org, fill="black", anchor="mm")
        if num_str:
            draw.text((width_px//2, 400), num_str, fill="black", anchor="mm")
    else:
        draw.text((width_px//2, 70), name, fill="black", anchor="mm")
        draw.text((width_px//2, 150), org, fill="black", anchor="mm")
        if num_str:
            draw.text((width_px//2, 220), num_str, fill="black", anchor="mm")
            
    preview_io = io.BytesIO()
    img.save(preview_io, format='PNG')
    preview_io.seek(0)
    return preview_io

def generate_pdf(df, name_col, org_col, size_option, reg_col=None, num_col=None):
    """Generates a highly optimized multi-page printable PDF layout."""
    buffer = io.BytesIO()
    page_width = 4 * inch
    
    if size_option == '4" x 2"':
        page_height = 2 * inch
        margin = 0.08 * inch
    else:
        page_height = 1 * inch
        margin = 0.06 * inch

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
            # Use safe native generator to bypass segmentation faults entirely
            qr_buf = draw_native_qr_fallback()
            story.append(RLImage(qr_buf, width=0.72*inch, height=0.72*inch))
            story.append(Spacer(1, 0.02 * inch))
            
            story.append(Paragraph(name, style_name))
            story.append(Spacer(1, 0.02 * inch))
            
            reg_num = str(row.get(reg_col, '')).strip() if reg_col else "SEH-V2020-OSXXXXX"
            story.append(Paragraph(reg_num, style_reg))
            story.append(Spacer(1, 0.02 * inch))
        else:
            story.append(Spacer(1, 0.02 * inch)) 
            story.append(Paragraph(name, style_name))
            story.append(Spacer(1, 0.02 * inch))
            
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
            
        if num_str:
            story.append(Spacer(1, 0.01 * inch))
            story.append(Paragraph(num_str, style_num))
        
        if index < len(df) - 1:
            from reportlab.platypus import PageBreak
            story.append(PageBreak())
            
    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_single_sticker_pdf(name, org, size_option, reg_val="", num_val=""):
    single_df = pd.DataFrame([{ 'Name': name, 'Org': org, 'Reg': reg_val, 'Num': num_val }])
    return generate_pdf(single_df, name_col='Name', org_col='Org', size_option=size_option, reg_col='Reg', num_col='Num')

# --- Streamlit UI Setup ---
st.set_page_config(page_title="Dynamic Thermal Badge Generator", page_icon="🖨️", layout="centered")

st.title("🖨️ Multi-Size Thermal Sticker Generator")
st.write("Switch layouts between clean 4x1 tracking labels or complete 4x2 visitor badges.")

st.subheader("⚙️ Global Layout Settings")
size_option = st.selectbox('Select Sticker Dimensions:', options=['4" x 1"', '4" x 2"'])

st.write("---")

tab1, tab2 = st.tabs(["📁 Batch Upload (Excel)", "✏️ On-the-Spot Single Print"])

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

            reg_key = None
            if size_option == '4" x 2"':
                auto_reg = next((orig for clean, orig in clean_columns.items() if any(k in clean for k in ['reg', 'serial', 'card id']) or (clean == 'id' and clean != auto_num)), df.columns[0])
                reg_key = st.selectbox("Registration ID Column:", options=df.columns, index=list(df.columns).index(auto_reg))

            st.success("✅ Ready to generate layout processing!")
            
            if st.button("✨ Load Batch Preview & Build Layout", key="batch_gen"):
                with st.spinner("Processing batch formatting..."):
                    pdf_buffer = generate_pdf(df, name_key, org_key, size_option, reg_key, num_key)
                
                st.write("### Preview & Printer Window")
                first_row = df.iloc[0]
                preview_image_bytes = draw_preview_image(
                    name=first_row.get(name_key, 'Sample Name'),
                    org=first_row.get(org_key, 'Sample Org'),
                    size_option=size_option,
                    reg_val=first_row.get(reg_key, '') if reg_key else "",
                    num_val=first_row.get(num_key, '') if num_key else ""
                )
                st.image(preview_image_bytes, caption="Live Layout Preview (Page 1)", width="stretch")
                
                st.download_button(
                    label="📥 Download & Send to Thermal Printer",
                    data=pdf_buffer,
                    file_name=f"batch_badges.pdf",
                    mime="application/pdf"
                )
        except Exception as e:
            st.error(f"An error occurred: {e}")

with tab2:
    st.subheader("Create a Single On-Spot Sticker")
    st.write("Fill out the specific required data properties below:")
    
    manual_name = st.text_input("Full Name:", value="Test")
    manual_org = st.text_input("Organisation Name:", value="Tanvi")
    manual_num = st.text_input("4-Digit Tracking Number (Optional):", placeholder="e.g. 1234", value="1223")
    
    manual_reg = ""
    if size_option == '4" x 2"':
        manual_reg = st.text_input("Registration ID Number:", value="SEH-V2020-OSXXXXX")

    if st.button("✨ Load On-Spot Print Preview", key="single_gen"):
        if not manual_name:
            st.warning("⚠️ Please enter a Name before generating.")
        else:
            with st.spinner("Formatting single sticker layout..."):
                single_pdf_buffer = generate_single_sticker_pdf(
                    manual_name, manual_org, size_option, manual_reg, manual_num
                )
            
            st.success(f"✅ Layout generated successfully!")
            
            preview_image_bytes = draw_preview_image(
                manual_name, manual_org, size_option, manual_reg, manual_num
            )
            st.image(preview_image_bytes, caption="Live Layout Preview (Page 1)", width="stretch")
            
            st.download_button(
                label="📥 Download & Send to Thermal Printer",
                data=single_pdf_buffer,
                file_name=f"single_{manual_name.replace(' ', '_').lower()}_badge.pdf",
                mime="application/pdf"
            )
