from pathlib import Path
from pypdf import PdfReader
import subprocess

PDF_FOLDER = "pdf_examples"
OUTPUT_FOLDER = "meeting_audio"

Path(OUTPUT_FOLDER).mkdir(exist_ok=True)

pdf_files = Path(PDF_FOLDER).glob("*.pdf")

for pdf_path in pdf_files:

    reader = PdfReader(str(pdf_path))

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    # çok uzun olursa say komutu sapıtmasın
    text = text[:4000]

    output_file = (
        Path(OUTPUT_FOLDER)
        / f"{pdf_path.stem}.aiff"
    )

    subprocess.run([
        "say",
        "-v",
        "Samantha",
        "-r",
        "120",
        "-o",
        str(output_file),
        text
    ])

    print(f"Created: {output_file}")