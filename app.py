import streamlit as st
import pdfplumber
import pandas as pd
import io
import random
from fpdf import FPDF

st.set_page_config(page_title="Internal Marks Processor", layout="wide")

st.title("📊 Internal Marks PDF Processor")

uploaded_file = st.file_uploader("Upload Internal Marks PDF", type=["pdf"])

if uploaded_file:
    all_student_data = []
    subject_name = "Internal Assessment"

    valid_regd_prefixes = ["26BS", "25BS", "24BS", "23BS", "22BS"]

    # -------- PDF PROCESSING --------
    with pdfplumber.open(uploaded_file) as pdf:
        first_page_text = pdf.pages[0].extract_text()

        if first_page_text:
            for line in first_page_text.split('\n'):
                if "Subject : " in line:
                    subject_name = line.replace("Subject : ", "").strip()

        for page in pdf.pages:
            table = page.extract_table()
            if table:
                for row in table[1:]:
                    clean_row = [
                        str(item).replace('\n', ' ').strip() if item else ""
                        for item in row[:4]
                    ]

                    if len(clean_row) > 1 and any(clean_row[1].startswith(prefix) for prefix in valid_regd_prefixes):
                        s_no, regd_no, student_name, total_str = clean_row

                        try:
                            total = float(total_str)

                            total_1_plus_2 = round(total / 0.40)
                            scaled_40 = round(total_1_plus_2 * 0.40)

                            half = total_1_plus_2 / 2
                            total_1 = min(round(half + random.randint(-5, 5)), 50)
                            total_2 = round(total_1_plus_2 - total_1)

                            def split_marks(t):
                                ncc = 10
                                assign = round(t * 0.20)
                                mid = round(t * 0.40)
                                seminar = t - assign - mid - ncc

                                if seminar < 0:
                                    mid += seminar
                                    seminar = 0

                                return assign, seminar, ncc, mid

                            a1, s1, n1, m1 = split_marks(total_1)
                            a2, s2, n2, m2 = split_marks(total_2)

                        except:
                            total_1_plus_2 = scaled_40 = total_1 = total_2 = ""
                            a1 = s1 = n1 = m1 = ""
                            a2 = s2 = n2 = m2 = ""

                        all_student_data.append([
                            s_no, regd_no, student_name,
                            a1, s1, n1, m1, total_1,
                            a2, s2, n2, m2, total_2,
                            total_1_plus_2, scaled_40
                        ])

    # -------- DATAFRAME --------
    columns = [
        "S.No.", "Regd.No.", "Student Name",
        "Assignment 1", "Seminar/Quiz 1", "NCC/NSS 1", "Mid I", "Total 1",
        "Assignment 2", "Seminar/Quiz 2", "NCC/NSS 2", "Mid II", "Total 2",
        "Total 1 + Total 2", "Scaled to 40"
    ]

    df = pd.DataFrame(all_student_data, columns=columns)

    st.success(f"Processed Subject: {subject_name}")
    st.dataframe(df, use_container_width=True)

    # -------- EXCEL EXPORT --------
    excel_buffer = io.BytesIO()

    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        pd.Series([f"Subject: {subject_name}"]).to_excel(
            writer, index=False, header=False
        )
        df.to_excel(writer, index=False, startrow=2)

    st.download_button(
        label="📥 Download Excel",
        data=excel_buffer.getvalue(),
        file_name=f"{subject_name}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # -------- PDF EXPORT --------
    pdf = FPDF('L', 'mm', 'A4')
    pdf.add_page()
    pdf.set_left_margin(10)

    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"Subject: {subject_name}", 0, 1, 'C')
    pdf.ln(5)

    pdf.set_font('Arial', 'B', 6)

    col_widths = [10,20,50,15,18,15,12,12,15,18,15,12,12,20,15]
    cell_height = 8

    # Header
    for i, col in enumerate(columns):
        pdf.cell(col_widths[i], cell_height, col, 1, 0, 'C')
    pdf.ln()

    pdf.set_font('Arial', '', 8)

    # Rows with page break handling
    for _, row in df.iterrows():
        if pdf.get_y() + cell_height > pdf.page_break_trigger:
            pdf.add_page()
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 10, f"Subject: {subject_name} (continued)", 0, 1, 'C')
            pdf.ln(5)

            pdf.set_font('Arial', 'B', 6)
            for i, col in enumerate(columns):
                pdf.cell(col_widths[i], cell_height, col, 1, 0, 'C')
            pdf.ln()

            pdf.set_font('Arial', '', 8)

        for i, col in enumerate(columns):
            pdf.cell(col_widths[i], cell_height, str(row[col]), 1, 0, 'C')
        pdf.ln()

    # 🔥 FIXED PDF OUTPUT
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    pdf_buffer = io.BytesIO(pdf_bytes)

    st.download_button(
        label="📥 Download PDF",
        data=pdf_buffer,
        file_name=f"{subject_name}.pdf",
        mime="application/pdf"
    )
