"""The local lab-slip reader: RapidOCR's text -> the intake form's values.

The parser tests build the reader's output by hand (text, box, score), so
they pin the rules without running OCR. The end-to-end tests draw a made-up
lab report, tilt and blur it like a phone photo, and read it with RapidOCR;
they skip when the reader is not installed.
"""

import io
import math

import pytest

from src.ocr.lab_report import TextLine, parse_lab_report


def _line(text: str, x: float, y: float, width: float = 0.0, height: float = 30.0,
          angle_deg: float = 0.0, score: float = 0.99) -> TextLine:
    """A reader line whose box starts at (x, y), on a page tilted by angle_deg
    (positive: the right side lower, as the reader's boxes show it)."""
    width = width or 14.0 * len(text)
    a = math.radians(angle_deg)

    def turn(px: float, py: float) -> tuple[float, float]:
        return (px * math.cos(a) - py * math.sin(a), px * math.sin(a) + py * math.cos(a))

    corners = [(x, y), (x + width, y), (x + width, y + height), (x, y + height)]
    return TextLine(text=text, score=score, box=tuple(turn(*c) for c in corners))


def _table(rows: list[list[str]], angle_deg: float = 0.0, top: float = 300.0) -> list[TextLine]:
    columns = [80, 600, 800, 960]
    lines = []
    for r, cells in enumerate(rows):
        for x, text in zip(columns, cells):
            if text:
                lines.append(_line(text, x, top + 52 * r, angle_deg=angle_deg))
    return lines


def test_a_tilted_table_keeps_each_result_on_its_row():
    # at -4 degrees a row's result sits ~36 px above its label: more than
    # the half-line tolerance unless the page is straightened first
    rows = [
        ["Fasting Blood Sugar (FBS)", "7.4", "mmol/L", "3.9 - 6.1"],
        ["Blood Sugar 2 Hrs After Breakfast", "11.8", "mmol/L", "< 7.8"],
        ["Haemoglobin (Hb)", "10.2", "7p/6", "12.0 - 15.5"],  # unit garbled, as read
        ["MCH", "24.1", "pg", "27 - 32"],
    ]
    for angle in (0.0, -4.0, 4.0):
        reading = parse_lab_report(_table(rows, angle_deg=angle))
        assert reading.fasting_glucose == 133.0, angle  # 7.4 mmol/L x 18.016
        assert reading.hemoglobin == 10.2, angle


def test_look_alike_rows_are_not_taken():
    reading = parse_lab_report(_table([
        ["Blood Sugar 2 Hrs After Breakfast", "11.8", "mmol/L", "< 7.8"],
        ["Random Blood Sugar (RBS)", "9.0", "mmol/L", ""],
        ["HbA1c", "7.1", "%", "4.0 - 5.6"],
        ["MCH", "24.1", "pg", "27 - 32"],
        ["MCHC", "31", "g/dL", "32 - 36"],
        ["Fasting Lipid Profile", "", "", ""],
    ]))
    assert reading.fasting_glucose is None and reading.hemoglobin is None
    assert "Not found on the slip: fasting glucose, haemoglobin, blood pressure." in reading.notes


def test_units_are_decided_by_the_value():
    reading = parse_lab_report([
        _line("FBS : 126 mg/dl", 80, 100),  # inline, mg/dL kept
        _line("Haemoglobin", 80, 160), _line("102", 600, 160), _line("g/L", 800, 160),
    ])
    assert reading.fasting_glucose == 126.0
    assert reading.hemoglobin == 10.2  # g/L / 10
    assert any("g/L on the slip" in note for note in reading.notes)


def test_ranges_thousands_and_dates_are_not_results():
    reading = parse_lab_report([
        _line("Glucose (Fasting)", 80, 100), _line("3.9 - 6.1", 600, 100), _line("5.8", 800, 100),
        _line("Hb%", 80, 160), _line(": 11.5 gm/dl", 600, 160),
        _line("Date: 05/11/2026   B.P. 130/85 mmHg", 80, 220, width=700),
    ])
    assert reading.fasting_glucose == round(5.8 * 18.016)
    assert reading.hemoglobin == 11.5
    assert (reading.systolic_bp, reading.diastolic_bp) == (130.0, 85.0)


def test_an_unreadable_result_is_left_blank_not_taken_from_the_next_column():
    # the first number after the label is the result; when it can't be read
    # the parser must not move on to the previous visit's column
    reading = parse_lab_report([
        _line("Haemoglobin", 80, 100), _line("12,500", 520, 100), _line("10.4", 700, 100),
    ])
    assert reading.hemoglobin is None


def test_the_readers_slips_inside_numbers_are_mended():
    # "5..2" once became 5.0 mmol/L (90 mg/dL instead of 94)
    reading = parse_lab_report([
        _line("Fasting Plasma Glucose", 80, 100), _line("5..2", 520, 100), _line("6.9", 700, 100),
        _line("Haemoglobin", 80, 160), _line("11,3", 520, 160), _line("10.4", 700, 160),
    ])
    assert reading.fasting_glucose == round(5.2 * 18.016)
    assert reading.hemoglobin == 11.3


def test_electrophoresis_fractions_and_a1c_misread_are_not_haemoglobin():
    # "Hb A 96.8 %" must not become 9.7 g/dL; the reader writes A1c as "Alc"
    reading = parse_lab_report(_table([
        ["HB ELECTROPHORESIS", "", "", ""],
        ["Hb A", "96.8", "%", "95 - 98"],
        ["Hb A2", "2.6", "%", "1.5 - 3.5"],
        ["Hb E", "0.0", "%", ""],
        ["Hb Alc", "7.1", "%", "4.0 - 5.6"],
        ["HbAlc", "7.1", "%", "4.0 - 5.6"],
    ]))
    assert reading.hemoglobin is None
    # and a haemoglobin over 25 with no g/L on the slip is a misreading
    assert parse_lab_report([_line("Haemoglobin", 80, 100), _line("102", 600, 100),
                             _line("g/dL", 800, 100)]).hemoglobin is None


def test_a_glucose_section_heading_carries_to_its_fasting_row():
    reading = parse_lab_report(_table([
        ["BLOOD GLUCOSE", "", "", ""],
        ["Test", "Result", "Unit", "Reference"],
        ["Fasting", "6.2", "mmol/L", "3.9 - 6.1"],
        ["2 Hrs ABF", "8.9", "mmol/L", "< 7.8"],
    ]))
    assert reading.fasting_glucose == round(6.2 * 18.016)
    # another heading in between ends the glucose section
    assert parse_lab_report(_table([
        ["BLOOD GLUCOSE", "", "", ""],
        ["Random", "6.2", "mmol/L", ""],
        ["LIPID PROFILE", "", "", ""],
        ["Fasting", "5.4", "mmol/L", ""],
    ])).fasting_glucose is None


def test_an_upside_down_page_is_read_the_right_way_up():
    rows = [["Fasting Blood Sugar (FBS)", "7.4", "mmol/L", "3.9 - 6.1"],
            ["Haemoglobin (Hb)", "10.2", "g/dL", "12.0 - 15.5"]]
    lines = _table(rows)
    # the reader's view of the same page upside down: each line's text the
    # right way round, every box turned half a turn about the page centre
    flipped = [TextLine(l.text, l.score, tuple((1240 - x, 1754 - y) for x, y in
                                               (l.box[2], l.box[3], l.box[0], l.box[1])))
               for l in lines]
    for page in (lines, flipped):
        reading = parse_lab_report(page)
        assert (reading.fasting_glucose, reading.hemoglobin) == (133.0, 10.2)


def test_impossible_values_are_left_out_with_a_note():
    reading = parse_lab_report([
        _line("Haemoglobin", 80, 100), _line("1.2", 600, 100),
        _line("Blood Pressure 85/140 mmHg", 80, 160, width=500),
        _line("Fasting Blood Sugar", 80, 220), _line("999", 600, 220),
    ])
    assert reading.hemoglobin is None and reading.systolic_bp is None
    assert reading.fasting_glucose is None
    assert sum("not possible" in note for note in reading.notes) == 3


def test_an_unsure_reading_is_flagged():
    reading = parse_lab_report([_line("Haemoglobin", 80, 100), _line("10.8", 600, 100, score=0.55)])
    assert reading.hemoglobin == 10.8
    assert any("unsure" in note for note in reading.notes)


# --- end to end, with the real reader ------------------------------------------

def _lab_slip(angle: float = 3.5) -> bytes:
    """A made-up lab report, tilted, blurred and JPEG-compressed like a
    phone photo."""
    from PIL import Image, ImageDraw, ImageFilter, ImageFont

    font = ImageFont.load_default(size=26)
    bold = ImageFont.load_default(size=34)
    page = Image.new("RGB", (1240, 1100), "white")
    draw = ImageDraw.Draw(page)
    draw.text((80, 60), "DEMO DIAGNOSTIC LABORATORY", font=bold, fill="black")
    draw.text((80, 120), "Patient: Test Patient   Age: 40 Y   Sex: Female", font=font, fill="black")
    rows = [
        ("Test Name", "Result", "Unit", "Reference Value"),
        ("Fasting Blood Sugar (FBS)", "7.4", "mmol/L", "3.9 - 6.1"),
        ("Blood Sugar 2 Hrs After Breakfast", "11.8", "mmol/L", "< 7.8"),
        ("HbA1c", "7.1", "%", "4.0 - 5.6"),
        ("Haemoglobin (Hb)", "10.2", "g/dL", "12.0 - 15.5"),
        ("Total WBC Count", "7,800", "/cumm", "4,000 - 11,000"),
        ("MCH", "24.1", "pg", "27 - 32"),
    ]
    for r, cells in enumerate(rows):
        for x, text in zip((80, 600, 800, 960), cells):
            draw.text((x, 220 + 56 * r), text, font=font, fill="black")
    draw.text((80, 680), "Vitals: Blood Pressure 150/95 mmHg   Pulse 82 /min", font=font, fill="black")
    photo = page.rotate(angle, resample=Image.BICUBIC, expand=True, fillcolor=(205, 200, 190))
    photo = photo.filter(ImageFilter.GaussianBlur(1.0))
    out = io.BytesIO()
    photo.save(out, "JPEG", quality=75)
    return out.getvalue()


@pytest.mark.parametrize("angle", [3.5, 180, 90, 270])
def test_reads_a_photo_of_a_lab_slip_whichever_way_it_was_taken(angle):
    # 180: "9.9" came back as "6.6" until an upside-down page was turned and
    # read again; 90/270: on its side, without an EXIF turn
    pytest.importorskip("rapidocr")
    from src.ocr.engine import read_lines

    reading = parse_lab_report(read_lines(_lab_slip(angle)))
    assert reading.fasting_glucose == 133.0
    assert reading.hemoglobin == 10.2
    assert (reading.systolic_bp, reading.diastolic_bp) == (150.0, 95.0)


def test_api_reads_the_slip_on_this_server(client, monkeypatch):
    pytest.importorskip("rapidocr")
    monkeypatch.setattr("src.core.config.settings.ocr_engine", "auto")
    monkeypatch.setattr("src.core.config.settings.anthropic_api_key", "")
    response = client.post("/intake/ocr",
                           files={"file": ("slip.jpg", _lab_slip(), "image/jpeg")})
    assert response.status_code == 200
    body = response.json()
    assert body["engine"] == "RapidOCR"
    assert body["biomarkers"] == {"fasting_glucose": 133.0, "systolic_bp": 150.0,
                                  "diastolic_bp": 95.0, "hemoglobin": 10.2}
    assert "entered as 133 mg/dL" in body["notes"]
    assert any("Haemoglobin" in line for line in body["text"])
    assert client.get("/health").json()["ocr_reader"] == "RapidOCR"


def _text_pdf(pages: list[list[tuple[float, float, str]]]) -> bytes:
    """A minimal PDF with real text, as a lab's reporting system makes one:
    each page a list of (x, y from the top, text) in points, Helvetica."""
    def escaped(text: str) -> str:
        return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    # objects 1 catalog, 2 page tree, 3 font; then each page's content
    # stream and page, numbered 4 and 5, 6 and 7...
    page_ids = [5 + 2 * i for i in range(len(pages))]
    objects = ["<< /Type /Catalog /Pages 2 0 R >>",
               f"<< /Type /Pages /Kids [{' '.join(f'{i} 0 R' for i in page_ids)}] "
               f"/Count {len(pages)} >>",
               "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    for page_id, cells in zip(page_ids, pages):
        content = "".join(f"BT /F1 11 Tf {x} {842 - y} Td ({escaped(t)}) Tj ET\n" for x, y, t in cells)
        objects.append(f"<< /Length {len(content)} >>\nstream\n{content}endstream")
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                       f"/Contents {page_id - 1} 0 R /Resources << /Font << /F1 3 0 R >> >> >>")
    out = b"%PDF-1.4\n"
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n{body}\nendobj\n".encode("latin-1")
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    out += "".join(f"{offset:010d} 00000 n \n" for offset in offsets).encode()
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return out


_PDF_PAGE_1 = [(40, 60, "DEMO DIAGNOSTIC LABORATORY"), (40, 90, "Patient: Test Patient  Age: 40 Y"),
               (40, 140, "Investigation"), (260, 140, "Result"), (340, 140, "Unit"),
               (420, 140, "Reference"),
               (40, 165, "Fasting Blood Sugar (FBS)"), (260, 165, "7.4"), (340, 165, "mmol/L"),
               (420, 165, "3.9 - 6.1"),
               (40, 190, "HbA1c"), (260, 190, "7.1"), (340, 190, "%"), (420, 190, "4.0 - 5.6")]
_PDF_PAGE_2 = [(40, 60, "HAEMATOLOGY"),
               (40, 90, "Haemoglobin (Hb)"), (260, 90, "10.2"), (340, 90, "g/dL"),
               (420, 90, "12.0 - 15.5"),
               (40, 115, "MCH"), (260, 115, "24.1"), (340, 115, "pg"), (420, 115, "27 - 32")]


def test_reads_a_labs_pdf_from_its_text_without_ocr():
    pytest.importorskip("pypdfium2")
    from src.ocr.engine import read_pdf_lines

    lines, scanned = read_pdf_lines(_text_pdf([_PDF_PAGE_1, _PDF_PAGE_2]))
    assert scanned == 0  # text taken as printed: every score is 1.0
    assert "Haemoglobin (Hb)" in [line.text for line in lines]
    reading = parse_lab_report(lines)
    # haemoglobin is on page 2: the pages stack, their rows never merge
    assert (reading.fasting_glucose, reading.hemoglobin) == (133.0, 10.2)


def test_reads_a_scan_saved_as_pdf_with_ocr():
    pytest.importorskip("pypdfium2")
    pytest.importorskip("rapidocr")
    from PIL import Image

    from src.ocr.engine import read_pdf_lines

    scan = io.BytesIO()
    Image.open(io.BytesIO(_lab_slip(1.5))).save(scan, "PDF", resolution=150)
    lines, scanned = read_pdf_lines(scan.getvalue())
    assert scanned == 1
    reading = parse_lab_report(lines)
    assert (reading.fasting_glucose, reading.hemoglobin) == (133.0, 10.2)


def test_api_reads_a_pdf_on_this_server_whatever_the_photo_reader(client, monkeypatch):
    pytest.importorskip("pypdfium2")
    # Claude chosen for photos and no key: a PDF's text is still read here
    monkeypatch.setattr("src.core.config.settings.ocr_engine", "claude")
    monkeypatch.setattr("src.core.config.settings.anthropic_api_key", "")
    response = client.post("/intake/ocr", files={
        "file": ("report.pdf", _text_pdf([_PDF_PAGE_1, _PDF_PAGE_2]), "application/pdf")})
    assert response.status_code == 200
    body = response.json()
    assert body["engine"] == "PDF text"
    assert body["biomarkers"]["fasting_glucose"] == 133.0
    assert body["biomarkers"]["hemoglobin"] == 10.2
    # a damaged PDF is refused, not a server error
    broken = client.post("/intake/ocr", files={
        "file": ("report.pdf", b"%PDF-1.4\nnot really a pdf", "application/pdf")})
    assert broken.status_code == 415


def test_api_says_when_no_reader_is_set_up(client, monkeypatch):
    monkeypatch.setattr("src.api.routes.intake.local_available", lambda: False)
    monkeypatch.setattr("src.core.config.settings.anthropic_api_key", "")
    monkeypatch.setattr("src.core.config.settings.ocr_engine", "auto")
    response = client.post("/intake/ocr",
                           files={"file": ("report.png", b"\x89PNG fake", "image/png")})
    assert response.status_code == 503
    assert "No lab-slip reader" in response.json()["detail"]
    assert client.get("/health").json()["ocr_reader"] is None


def test_api_rejects_an_image_it_cannot_decode(client, monkeypatch):
    pytest.importorskip("rapidocr")
    monkeypatch.setattr("src.core.config.settings.ocr_engine", "local")
    response = client.post("/intake/ocr",
                           files={"file": ("report.png", b"\x89PNG not really", "image/png")})
    assert response.status_code == 415
