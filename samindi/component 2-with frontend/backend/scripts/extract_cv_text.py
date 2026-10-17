import os
import pandas as pd
import pymupdf

# =====================================================
# PATH SETTINGS
# =====================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CV_FOLDER = os.path.join(BASE_DIR, "data", "cvs")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "cv_extracted_text.csv")


# =====================================================
# EXTRACT TEXT FROM ONE PDF
# =====================================================
def extract_text_from_pdf(pdf_path):
    text = ""

    try:
        document = pymupdf.open(pdf_path)

        for page in document:
            text += page.get_text("text") + " "

        document.close()

    except Exception as error:
        print("Error reading PDF:", pdf_path)
        print("Error:", error)

    text = " ".join(text.split())
    return text


# =====================================================
# MAIN FUNCTION
# =====================================================
def main():
    print("===================================")
    print("CV PDF TEXT EXTRACTION STARTED")
    print("===================================")

    if not os.path.exists(CV_FOLDER):
        print("CV folder not found:", CV_FOLDER)
        return

    pdf_files = [
        file_name for file_name in os.listdir(CV_FOLDER)
        if file_name.lower().endswith(".pdf")
    ]

    if not pdf_files:
        print("No PDF files found in:", CV_FOLDER)
        return

    records = []

    for file_name in pdf_files:
        pdf_path = os.path.join(CV_FOLDER, file_name)

        print("Extracting:", file_name)

        extracted_text = extract_text_from_pdf(pdf_path)

        if len(extracted_text.strip()) < 50:
            print("Skipped because extracted text is too short:", file_name)
            continue

        records.append({
            "file_name": file_name,
            "cv_text": extracted_text
        })

    if not records:
        print("No CV text extracted.")
        print("Possible reason: PDFs may be scanned image PDFs.")
        return

    output_df = pd.DataFrame(records)
    output_df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

    print("\n===================================")
    print("CV TEXT EXTRACTION COMPLETED")
    print("===================================")
    print("Total PDF files found:", len(pdf_files))
    print("Total CV text extracted:", len(output_df))
    print("Saved file:", OUTPUT_FILE)

    print("\nSample output:")
    print(output_df.head())


if __name__ == "__main__":
    main()