"""Text lines read off a lab report -> the biomarkers the intake form takes.

Rule-based and deterministic: no model decides a value. What it handles,
each seen on real slips or on the test images in tests/test_ocr.py:

- Table layout. A report prints "Test name | Result | Unit | Reference" in
  columns, and the reader returns each cell as its own line. Cells are put
  back into rows by their height on the page, after straightening the page:
  on a phone photo tilted 3-4 degrees, a row's result sits 25 px above its
  label, more than a line's half-height.
- Look-alike rows. "Blood sugar 2 hrs after breakfast", random sugar and
  HbA1c are not fasting glucose; MCH, MCHC and HbA1c are not haemoglobin.
  Reference ranges ("3.9 - 6.1", "< 7.8") and thousands ("7,800") are not
  results.
- Units. Bangladeshi labs mostly print glucose in mmol/L; the form takes
  mg/dL. The reader garbles unit text often ("g/dL" came back as "7p/6"),
  so the unit is decided by the value: a fasting glucose of 35 or less can
  only be mmol/L (35 mmol/L is 630 mg/dL; 35 mg/dL is a hypoglycaemic
  emergency, not a fasting lab result). mmol/L x 18.016 = mg/dL (glucose,
  180.16 g/mol). A haemoglobin over 25 is g/L and is divided by 10.
- Plausibility. A value outside the range a living patient can have is
  dropped with a note rather than entered.

Everything found, converted or dropped is said in `notes`, which the intake
form shows next to the values the physician must confirm.
"""

import math
import re
import statistics
from dataclasses import dataclass, field

GLUCOSE_MG_PER_MMOL = 18.016
MAX_GLUCOSE_MMOL = 35.0
LOW_CONFIDENCE = 0.80

# what a living patient's value can be; outside it the reading is wrong
PLAUSIBLE = {
    "fasting_glucose": (20.0, 700.0),  # mg/dL
    "hemoglobin": (3.0, 25.0),  # g/dL
    "systolic_bp": (60.0, 260.0),  # mmHg
    "diastolic_bp": (30.0, 160.0),
}


@dataclass(frozen=True)
class TextLine:
    text: str
    score: float
    # four corners, clockwise from the top left, in image pixels
    box: tuple[tuple[float, float], ...]


@dataclass
class LabReading:
    fasting_glucose: float | None = None  # mg/dL
    systolic_bp: float | None = None  # mmHg
    diastolic_bp: float | None = None
    hemoglobin: float | None = None  # g/dL
    notes: list[str] = field(default_factory=list)


# --- rows --------------------------------------------------------------------

def _page_angle(lines: list[TextLine]) -> float:
    """The page's tilt, from the top edges of the longer lines."""
    angles = []
    for line in lines:
        (x0, y0), (x1, y1) = line.box[0], line.box[1]
        width, height = x1 - x0, abs(line.box[3][1] - y0)
        if width > 3 * max(height, 1.0):
            angles.append(math.atan2(y1 - y0, x1 - x0))
    return statistics.median(angles) if angles else 0.0


@dataclass
class _Cell:
    text: str
    score: float
    x: float
    y: float
    height: float


def _rows(lines: list[TextLine]) -> list[list[_Cell]]:
    """Cells grouped into the page's rows, each row left to right."""
    if not lines:
        return []
    angle = _page_angle(lines)
    sin, cos = math.sin(angle), math.cos(angle)
    cells = []
    for line in lines:
        cx = sum(p[0] for p in line.box) / len(line.box)
        cy = sum(p[1] for p in line.box) / len(line.box)
        height = math.dist(line.box[0], line.box[3])
        # rotate the centre by -angle, so every row is level
        cells.append(_Cell(line.text, line.score, cx * cos + cy * sin, -cx * sin + cy * cos, height))
    tolerance = 0.5 * statistics.median(c.height for c in cells)
    cells.sort(key=lambda c: c.y)
    rows: list[list[_Cell]] = []
    for cell in cells:
        if rows and abs(cell.y - statistics.fmean(c.y for c in rows[-1])) <= tolerance:
            rows[-1].append(cell)
        else:
            rows.append([cell])
    return [sorted(row, key=lambda c: c.x) for row in rows]


# --- numbers -----------------------------------------------------------------

_NUM = r"\d+(?:\.\d+)?"
_RANGE = re.compile(rf"{_NUM}\s*(?:-|–|~|to)\s*{_NUM}", re.IGNORECASE)
_BOUND = re.compile(rf"[<>≤≥]\s*=?\s*{_NUM}")
# a result: not part of a thousands group (7,800), a date (05/11) or a range
_VALUE = re.compile(r"(?<![\d.,/])(\d{1,3}(?:\.\d{1,2})?)(?![\d,/]|\.\d)")
_PRESSURE = re.compile(r"(?<!\d)(\d{2,3})\s*/\s*(\d{2,3})(?!\d)")


_PERCENT_AFTER = re.compile(r"\s*%")
# the reader's slips inside a number: "5..2", and a decimal comma ("5,2"),
# which is not a thousands group (7,800 and the Indian 2,45,000 stay)
_DOUBLED_DOT = re.compile(r"(?<=\d)\.{2,}(?=\d)")
_DECIMAL_COMMA = re.compile(r"(?<=\d),(?=\d{1,2}(?![\d,]))")


def _numbers_only(text: str) -> str:
    """The text with reference ranges and bounds blanked out and the
    reader's slips inside numbers mended."""
    text = _DECIMAL_COMMA.sub(".", _DOUBLED_DOT.sub(".", text))
    return _BOUND.sub(" ", _RANGE.sub(" ", text))


def _first_value(text: str, percent_ok: bool = True) -> float | None:
    """The first result in `text`; with percent_ok False, a number printed
    as a percentage ("96.8 %", an Hb electrophoresis fraction) is no result."""
    cleaned = _numbers_only(text)
    for match in _VALUE.finditer(cleaned):
        if not percent_ok and _PERCENT_AFTER.match(cleaned, match.end()):
            return None
        return float(match.group(1))
    return None


def _after_label(row: list[_Cell], label: re.Pattern) -> tuple[list[_Cell], str] | None:
    """The text after the label's match in its own cell, and the cells to
    its right - where the result is printed."""
    for i, cell in enumerate(row):
        match = label.search(cell.text)
        if match:
            return row[i:], cell.text[match.end():]
    return None


def _result_in(rest: list[_Cell], tail: str, percent_ok: bool = True) -> tuple[float, float] | None:
    """The first result after a label: inline ("FBS : 7.4 mmol/L") or in
    the next cells, with the score of the cell it was read from."""
    texts = [(tail, rest[0].score)] + [(c.text, c.score) for c in rest[1:]]
    for i, (text, score) in enumerate(texts):
        if _DIGIT.search(_numbers_only(text)):
            # the first number after the label is the result: if it can't
            # be read cleanly, stop - the next number along is the previous
            # visit's result or a reference value, never this one
            value = _first_value(text, percent_ok)
            if value is None:
                return None
            # a "%" printed in the unit column marks a percentage too
            unit = texts[i + 1][0] if i + 1 < len(texts) else ""
            if not percent_ok and _PERCENT_AFTER.match(unit):
                return None
            return value, score
    return None


# --- the biomarkers ----------------------------------------------------------

_FASTING = re.compile(r"\bfasting\b|\bf\.?\s?b\.?\s?[sg]\b|\bfpg\b", re.IGNORECASE)
_GLUCOSE_WORD = re.compile(r"sugar|glucose|\bf\.?\s?b\.?\s?[sg]\b|\bfpg\b", re.IGNORECASE)
# "A1c" as the reader writes it too: the 1 comes back as l or I. No "|" in
# the class: cells are joined with " | ", and "...a | c..." is no A1c
_A1C = r"a ?[1lI] ?c\b"
_NOT_FASTING_GLUCOSE = re.compile(
    r"\b2\s*h|\bhrs?\b|after|post|\bp\.?\s?p\b|random|\brbs\b|" + _A1C + r"|ogtt|"
    r"insulin|lipid|cholesterol|triglyceride|c-?peptide",
    re.IGNORECASE)
_GLUCOSE_LABEL = re.compile(
    r"fasting[^|]*?(?:sugar|glucose)|(?:sugar|glucose)[^|]*?fasting|"
    r"\bf\.?\s?b\.?\s?[sg]\b|\bfpg\b",
    re.IGNORECASE)

_HB_LABEL = re.compile(r"\b(?:ha?emoglobin|hgb|hb)\b", re.IGNORECASE)
# HbA1c, MCH/MCHC, and the haemoglobin fractions of an electrophoresis (Hb A,
# A2, F, S, E - HbE trait is common in Bangladesh), which are percentages
_NOT_HB = re.compile(
    _A1C + r"|glyc|\bmchc?\b|electrophoresis|\bhb\s*(?:a2?|f|s|e|c|h)\b|\bhb(?:a2|f|s|e)\b",
    re.IGNORECASE)
_G_PER_L = re.compile(r"\bg\s*/\s*l\b", re.IGNORECASE)

# a section heading or a column header row: no numbers in it
_DIGIT = re.compile(r"\d")
_COLUMN_HEADER = re.compile(r"result|unit|reference|refer|range|investigation|test|value",
                            re.IGNORECASE)

_BP_LABEL = re.compile(r"blood\s*pressure|\bb\.?\s?p\b", re.IGNORECASE)


def _row_text(row: list[_Cell]) -> str:
    return " | ".join(c.text for c in row)


def _first_cell_text(row: list[_Cell]) -> str:
    return row[0].text if row else ""


def _plausible(key: str, value: float) -> bool:
    low, high = PLAUSIBLE[key]
    return low <= value <= high


def _glucose_heading_above(rows: list[list[_Cell]], index: int) -> bool:
    """Whether the row sits in a glucose section: a "BLOOD GLUCOSE" heading
    over rows labelled just "Fasting", "2 Hrs ABF". The search goes up past
    the section's other test rows and a column header row, and stops at any
    other heading ("LIPID PROFILE")."""
    for row in reversed(rows[max(0, index - 6):index]):
        text = _row_text(row)
        if _DIGIT.search(text):
            continue  # another test row of the same section
        if _GLUCOSE_WORD.search(text):
            return not _NOT_FASTING_GLUCOSE.search(text)
        if not _COLUMN_HEADER.search(text):
            return False
    return False


def _fasting_glucose(rows: list[list[_Cell]], reading: LabReading) -> None:
    for i, row in enumerate(rows):
        text = _row_text(row)
        if not _FASTING.search(text) or _NOT_FASTING_GLUCOSE.search(text):
            continue
        if not (_GLUCOSE_WORD.search(text) or _glucose_heading_above(rows, i)):
            continue
        found = _after_label(row, _GLUCOSE_LABEL) or _after_label(row, _FASTING)
        result = _result_in(*found) if found else None
        if result is None:
            continue
        value, score = result
        label = _first_cell_text(row)
        if value <= MAX_GLUCOSE_MMOL:
            mg = round(value * GLUCOSE_MG_PER_MMOL)
            note = (f"Fasting glucose: {value:g} mmol/L on the slip ('{label}'), "
                    f"entered as {mg} mg/dL.")
            value = float(mg)
        else:
            note = f"Fasting glucose: {value:g} mg/dL ('{label}')."
        if not _plausible("fasting_glucose", value):
            reading.notes.append(f"A fasting glucose of {value:g} mg/dL was read ('{label}'), "
                                 "which is not possible; it was left out.")
            return
        reading.fasting_glucose = value
        reading.notes.append(note + _confidence(score))
        return


def _hemoglobin(rows: list[list[_Cell]], reading: LabReading) -> None:
    for row in rows:
        text = _row_text(row)
        if not _HB_LABEL.search(text) or _NOT_HB.search(text):
            continue
        found = _after_label(row, _HB_LABEL)
        result = _result_in(*found, percent_ok=False) if found else None
        if result is None:
            continue
        value, score = result
        label = _first_cell_text(row)
        note = f"Haemoglobin: {value:g} g/dL ('{label}')."
        # g/L only when the slip says so: a number over 25 under any other
        # unit is a misreading, not a unit to guess
        if value > PLAUSIBLE["hemoglobin"][1] and _G_PER_L.search(text):
            note = f"Haemoglobin: {value:g} g/L on the slip ('{label}'), entered as {value / 10:g} g/dL."
            value = value / 10
        if not _plausible("hemoglobin", value):
            reading.notes.append(f"A haemoglobin of {value:g} g/dL was read ('{label}'), "
                                 "which is not possible; it was left out.")
            return
        reading.hemoglobin = value
        reading.notes.append(note + _confidence(score))
        return


def _blood_pressure(rows: list[list[_Cell]], reading: LabReading) -> None:
    for row in rows:
        found = _after_label(row, _BP_LABEL)
        if found is None:
            continue
        rest, tail = found
        for text, score in [(tail, rest[0].score)] + [(c.text, c.score) for c in rest[1:]]:
            match = _PRESSURE.search(text)
            if not match:
                continue
            systolic, diastolic = float(match.group(1)), float(match.group(2))
            if (_plausible("systolic_bp", systolic) and _plausible("diastolic_bp", diastolic)
                    and systolic > diastolic):
                reading.systolic_bp, reading.diastolic_bp = systolic, diastolic
                reading.notes.append(f"Blood pressure: {systolic:g}/{diastolic:g} mmHg."
                                     + _confidence(score))
            else:
                reading.notes.append(f"A blood pressure of {match.group(0)} was read, which is "
                                     "not possible; it was left out.")
            return


def _confidence(score: float) -> str:
    return " The reader was unsure of this one; check it." if score < LOW_CONFIDENCE else ""


def _turned(lines: list[TextLine]) -> list[TextLine]:
    """The same lines on the page turned upside down: every point rotated
    half a turn, each box's corners renamed so its top left is the text's."""
    return [TextLine(line.text, line.score,
                     tuple((-x, -y) for x, y in (line.box[2], line.box[3], line.box[0], line.box[1])))
            for line in lines]


def _found(reading: LabReading) -> int:
    return sum(v is not None for v in (reading.fasting_glucose, reading.hemoglobin,
                                       reading.systolic_bp))


def upside_down(lines: list[TextLine]) -> bool:
    """Whether the page reads better turned half a turn. The reader turns
    each upside-down line the right way up but leaves the page as
    photographed, so on an upside-down photo a label's result sits to its
    left: read both ways up, the turned page finds more."""
    upright = _found(_parse(lines))
    return upright < 3 and _found(_parse(_turned(lines))) > upright


def parse_lab_report(lines: list[TextLine]) -> LabReading:
    """The biomarkers on the slip. src.ocr.engine.read_lines hands over the
    page the right way up; lines from anywhere else that lie upside down
    are read turned, as the better of the two."""
    if upside_down(lines):
        return _parse(_turned(lines))
    return _parse(lines)


def _parse(lines: list[TextLine]) -> LabReading:
    reading = LabReading()
    rows = _rows(lines)
    _fasting_glucose(rows, reading)
    _hemoglobin(rows, reading)
    _blood_pressure(rows, reading)
    missing = [name for name, value in (
        ("fasting glucose", reading.fasting_glucose),
        ("haemoglobin", reading.hemoglobin),
        ("blood pressure", reading.systolic_bp),
    ) if value is None]
    if missing:
        reading.notes.append("Not found on the slip: " + ", ".join(missing) + ".")
    return reading
