from pathlib import Path
from html import escape

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def create_meeting_pdf(text: str, output_path: str) -> str:
    output_path = Path(output_path)
    output_path.parent.mkdir(exist_ok=True)

    doc = SimpleDocTemplate(str(output_path))
    styles = getSampleStyleSheet()

    story = []

    for line in text.split("\n"):
        clean_line = escape(line.strip())

        if clean_line:
            story.append(Paragraph(clean_line, styles["BodyText"]))
            story.append(Spacer(1, 8))

    doc.build(story)

    return str(output_path)