"""
build_chapter23.py – Sinh file Word hoàn chỉnh Chương 2 và Chương 3
Đề tài: Per-Title Encoding – Tối ưu hóa bitrate ladder theo từng nội dung video
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from docx import Document
    from docx.shared import Pt, Cm, RGBColor, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
    from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    import docx.opc.constants
except ImportError:
    print("Cài python-docx: pip install python-docx")
    sys.exit(1)

# ── Helpers ─────────────────────────────────────────────────────────────────

def _set_heading_style(para, level: int):
    """Set heading level 1–4 on an existing paragraph."""
    style_map = {1: "Heading 1", 2: "Heading 2", 3: "Heading 3", 4: "Heading 4"}
    para.style = style_map.get(level, "Heading 1")


def _run_font(run, size_pt: float, bold=False, italic=False, color=None):
    run.font.name = "Times New Roman"
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.italic = italic
    if color:
        run.font.color.rgb = RGBColor(*color)


def _para_format(para, space_before=6, space_after=6,
                 first_indent=True, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY):
    fmt = para.paragraph_format
    fmt.space_before = Pt(space_before)
    fmt.space_after = Pt(space_after)
    fmt.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    fmt.line_spacing = 1.3
    fmt.alignment = alignment
    if first_indent:
        fmt.first_line_indent = Cm(1.27)


def add_heading(doc: Document, text: str, level: int) -> None:
    """Add a numbered heading."""
    para = doc.add_heading("", level=level)
    _set_heading_style(para, level)
    run = para.add_run(text)
    sizes = {1: 14, 2: 13, 3: 13, 4: 12}
    _run_font(run, sizes.get(level, 12), bold=True)
    fmt = para.paragraph_format
    fmt.space_before = Pt(12 if level == 1 else 8)
    fmt.space_after = Pt(6)
    fmt.keep_with_next = True


def add_body(doc: Document, text: str, first_indent=True, bold_parts: list[str] | None = None) -> None:
    """Add a body paragraph."""
    para = doc.add_paragraph()
    _para_format(para, first_indent=first_indent)
    if bold_parts:
        remaining = text
        for bp in bold_parts:
            idx = remaining.find(bp)
            if idx >= 0:
                before = remaining[:idx]
                after = remaining[idx + len(bp):]
                if before:
                    r = para.add_run(before)
                    _run_font(r, 13)
                r2 = para.add_run(bp)
                _run_font(r2, 13, bold=True)
                remaining = after
        if remaining:
            r3 = para.add_run(remaining)
            _run_font(r3, 13)
    else:
        run = para.add_run(text)
        _run_font(run, 13)


def add_formula(doc: Document, formula: str, label: str = "") -> None:
    """Add a formula paragraph (centered, slightly smaller font)."""
    para = doc.add_paragraph()
    fmt = para.paragraph_format
    fmt.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fmt.space_before = Pt(4)
    fmt.space_after = Pt(4)
    fmt.first_line_indent = Pt(0)
    run = para.add_run(formula)
    _run_font(run, 12, italic=True)
    if label:
        run2 = para.add_run(f"  {label}")
        _run_font(run2, 11)


def add_note(doc: Document, text: str) -> None:
    """Add italic note paragraph."""
    para = doc.add_paragraph()
    _para_format(para, first_indent=False)
    run = para.add_run(text)
    _run_font(run, 12, italic=True)
    run.font.color.rgb = RGBColor(0x44, 0x44, 0x44)


def add_placeholder(doc: Document, text: str) -> None:
    """Add a [PLACEHOLDER] paragraph."""
    para = doc.add_paragraph()
    _para_format(para, first_indent=False)
    run = para.add_run(text)
    _run_font(run, 12, bold=True)
    run.font.color.rgb = RGBColor(0xCC, 0x44, 0x00)


def add_bullet(doc: Document, items: list[str], style="List Bullet") -> None:
    """Add bullet list items."""
    for item in items:
        para = doc.add_paragraph(style=style)
        _para_format(para, first_indent=False, space_before=2, space_after=2)
        run = para.add_run(item)
        _run_font(run, 13)


def add_table_title(doc: Document, text: str) -> None:
    para = doc.add_paragraph()
    fmt = para.paragraph_format
    fmt.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fmt.space_before = Pt(8)
    fmt.space_after = Pt(4)
    fmt.first_line_indent = Pt(0)
    run = para.add_run(text)
    _run_font(run, 12, bold=True)


def make_table(doc: Document, headers: list[str], rows: list[list[str]],
               col_widths: list[float] | None = None) -> None:
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Header row
    hrow = table.rows[0]
    for i, h in enumerate(headers):
        cell = hrow.cells[i]
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        para = cell.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = para.add_run(h)
        _run_font(run, 12, bold=True)
        shading = OxmlElement("w:shd")
        shading.set(qn("w:fill"), "D9E2F3")
        shading.set(qn("w:color"), "auto")
        shading.set(qn("w:val"), "clear")
        cell._tc.get_or_add_tcPr().append(shading)

    # Data rows
    for ri, row_data in enumerate(rows):
        drow = table.rows[ri + 1]
        for ci, val in enumerate(row_data):
            cell = drow.cells[ci]
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            para = cell.paragraphs[0]
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER if ci > 0 else WD_ALIGN_PARAGRAPH.LEFT
            run = para.add_run(str(val))
            _run_font(run, 12)

    # Set column widths
    if col_widths:
        for row in table.rows:
            for ci, w in enumerate(col_widths):
                row.cells[ci].width = Cm(w)

    doc.add_paragraph()  # spacing after table


def add_page_break(doc: Document) -> None:
    doc.add_page_break()


def set_document_margins(doc: Document) -> None:
    for section in doc.sections:
        section.top_margin = Cm(3.0)
        section.bottom_margin = Cm(3.0)
        section.left_margin = Cm(3.5)
        section.right_margin = Cm(2.0)
        section.header_distance = Cm(1.5)
        section.footer_distance = Cm(1.5)


def add_footer_page_number(doc: Document) -> None:
    for section in doc.sections:
        footer = section.footer
        para = footer.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = para.add_run()
        _run_font(run, 11)
        fldChar1 = OxmlElement("w:fldChar")
        fldChar1.set(qn("w:fldCharType"), "begin")
        instrText = OxmlElement("w:instrText")
        instrText.text = " PAGE "
        fldChar2 = OxmlElement("w:fldChar")
        fldChar2.set(qn("w:fldCharType"), "end")
        run._r.append(fldChar1)
        run._r.append(instrText)
        run._r.append(fldChar2)


# ── Cover page ──────────────────────────────────────────────────────────────

def build_cover(doc: Document) -> None:
    doc.add_paragraph()
    for _ in range(4):
        doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("TRƯỜNG ĐẠI HỌC")
    _run_font(r, 14)

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run("BÁO CÁO ĐỀ TÀI")
    _run_font(r2, 14)

    for _ in range(3):
        doc.add_paragraph()

    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r3 = p3.add_run("Per-Title Encoding – Tối ưu hóa Bitrate Ladder\ntheo Từng Nội Dung Video")
    _run_font(r3, 16, bold=True)

    for _ in range(2):
        doc.add_paragraph()

    p4 = doc.add_paragraph()
    p4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r4 = p4.add_run("Tài liệu nội bộ:\nChương 2 – Cơ sở lý thuyết và các chỉ số đánh giá\nChương 3 – Phương pháp nghiên cứu và quy trình đề xuất")
    _run_font(r4, 14, italic=True)

    for _ in range(6):
        doc.add_paragraph()

    p5 = doc.add_paragraph()
    p5.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r5 = p5.add_run("Năm học: 2025–2026")
    _run_font(r5, 13)

    add_page_break(doc)


# ── TOC placeholder ──────────────────────────────────────────────────────────

def build_toc(doc: Document) -> None:
    add_heading(doc, "MỤC LỤC", 1)
    add_note(doc, "[Mục lục tự động – Nhấn Ctrl+A rồi F9 trong Word để cập nhật sau khi mở file]")
    add_page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# CHƯƠNG 2
# ══════════════════════════════════════════════════════════════════════════════

def build_chapter2(doc: Document) -> None:

    # ── Tiêu đề chương ──────────────────────────────────────────────────────
    add_heading(doc, "CHƯƠNG 2. CƠ SỞ LÝ THUYẾT VÀ CÁC CHỈ SỐ ĐÁNH GIÁ", 1)
    add_body(doc,
        "Chương này trình bày nền tảng lý thuyết cần thiết để hiểu và phân tích các bước trong "
        "quy trình thực nghiệm Per-Title Encoding. Nội dung được tổ chức theo mạch logic: từ cơ sở "
        "video encoding và các tham số ảnh hưởng, qua bitrate ladder, đến các chỉ số đánh giá chất "
        "lượng và phức tạp nội dung, rồi đến các công cụ phân tích và lựa chọn candidate. Cuối "
        "chương trình bày các chỉ số định lượng dùng để đánh giá hiệu quả tối ưu hóa."
    )

    # ══════════════════════════════════════════════════════════════════════════
    # 2.1
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "2.1. Cơ sở video encoding và các tham số ảnh hưởng", 2)
    add_body(doc,
        "Mục này xây dựng nền tảng kỹ thuật cho toàn bộ đề tài. Hiểu đúng các tham số encoding "
        "và mối quan hệ giữa chúng là điều kiện tiên quyết để thiết kế không gian candidate, "
        "giải thích kết quả đo lường và lựa chọn bitrate ladder hợp lý."
    )

    # 2.1.1
    add_heading(doc, "2.1.1. Video encoding và nén video", 3)
    add_body(doc,
        "Video kỹ thuật số ở dạng nguyên gốc (raw video) tiêu tốn dung lượng rất lớn. Một video "
        "Full HD (1920×1080 pixel), 30 fps, 8-bit màu YCbCr 4:2:0 yêu cầu khoảng 746 MB cho mỗi "
        "phút phát lại. Con số này khiến việc lưu trữ và truyền tải raw video trở nên không khả thi "
        "trong thực tế."
    )
    add_body(doc,
        "Video encoding (hay mã hóa video) là quá trình chuyển đổi raw video sang định dạng nén "
        "bằng cách khai thác các dạng dư thừa trong dữ liệu hình ảnh. Có hai dạng dư thừa chính: "
        "(1) dư thừa không gian (spatial redundancy) – các pixel lân cận trong cùng một khung hình "
        "có giá trị gần nhau; (2) dư thừa thời gian (temporal redundancy) – các vùng ảnh giữa các "
        "khung liên tiếp ít thay đổi. Codec hiện đại khai thác cả hai dạng này để giảm kích thước "
        "file xuống hàng chục đến hàng trăm lần so với raw video."
    )
    add_body(doc,
        "Video compression được thực hiện theo hai cơ chế: nén không tổn hao (lossless) và nén "
        "có tổn hao (lossy). Hầu hết các ứng dụng truyền phát video sử dụng nén có tổn hao – nghĩa "
        "là một phần thông tin hình ảnh bị loại bỏ có kiểm soát để đổi lấy dung lượng nhỏ hơn. "
        "Mức độ tổn hao có thể được điều chỉnh thông qua các tham số encode, trực tiếp ảnh hưởng "
        "đến chất lượng hình ảnh và kích thước file đầu ra."
    )

    # 2.1.2
    add_heading(doc, "2.1.2. Bitrate, độ phân giải và frame rate", 3)
    add_body(doc,
        "Ba tham số cơ bản nhất quyết định đặc tính của một luồng video được mã hóa là bitrate, "
        "độ phân giải và frame rate. Hiểu đúng vai trò của từng tham số là cơ sở để thiết kế "
        "không gian candidate trong đề tài."
    )
    add_body(doc, "Bitrate (tốc độ bit) là lượng dữ liệu được truyền tải hoặc xử lý trong một đơn "
        "vị thời gian, thường tính bằng kilobits per second (kbps) hoặc megabits per second (Mbps). "
        "Đây là tham số trực tiếp quyết định dung lượng file và gián tiếp ảnh hưởng đến chất "
        "lượng hình ảnh. Kích thước file được tính xấp xỉ theo công thức:"
    )
    add_formula(doc, "Kích thước file ≈ Bitrate (kbps) × Thời lượng (s) / 8 / 1024  [MB]", "(2.1)")
    add_body(doc,
        "trong đó phép chia cho 8 chuyển đổi từ kilobits sang kilobytes, và chia cho 1024 để quy "
        "về megabytes. Ví dụ, một video 30 giây ở 3000 kbps có kích thước xấp xỉ "
        "3000 × 30 / 8 / 1024 ≈ 10,99 MB."
    )
    add_body(doc,
        "Độ phân giải (resolution) xác định số pixel trên mỗi khung hình, thường được biểu diễn "
        "bằng chiều rộng × chiều cao (ví dụ: 1920×1080). Độ phân giải quyết định mức độ chi tiết "
        "tối đa mà video có thể thể hiện. Khi giảm độ phân giải, encoder phải xử lý ít pixel hơn, "
        "do đó cần ít bit hơn để đạt cùng mức chất lượng tương đối. Tuy nhiên, nếu video được "
        "hiển thị trên màn hình lớn hơn độ phân giải gốc, chất lượng cảm nhận sẽ giảm do "
        "phải upscale. Trong đề tài, upscale bị cấm: mỗi candidate chỉ encode ở độ phân giải "
        "bằng hoặc nhỏ hơn video nguồn."
    )
    add_body(doc,
        "Frame rate (tốc độ khung hình, fps – frames per second) là số khung hình được hiển thị "
        "trong một giây. Frame rate cao hơn tạo ra chuyển động mượt mà hơn nhưng yêu cầu bitrate "
        "lớn hơn để duy trì cùng mức chất lượng mỗi khung. Trong đề tài, frame rate của video đầu "
        "ra được giữ nguyên theo video nguồn để bảo đảm so sánh công bằng giữa các candidate "
        "và với baseline."
    )
    add_body(doc,
        "Quan hệ giữa ba tham số này không độc lập. Khi tăng độ phân giải mà giữ nguyên bitrate, "
        "mỗi pixel nhận được ít bit hơn, dẫn đến chất lượng có thể giảm. Ngược lại, tăng bitrate "
        "cho cùng độ phân giải thường cải thiện chất lượng nhưng theo mức độ giảm dần – hiện "
        "tượng sẽ được phân tích chi tiết ở Mục 2.5."
    )

    # 2.1.3
    add_heading(doc, "2.1.3. Codec và H.264/AVC trong phạm vi đề tài", 3)
    add_body(doc,
        "Codec (viết tắt của coder-decoder) là bộ phần mềm hoặc phần cứng thực hiện quá trình "
        "mã hóa và giải mã video theo một chuẩn nén cụ thể. Cùng một video khi được encode bằng "
        "các codec khác nhau sẽ cho ra chất lượng và dung lượng khác nhau ở cùng bitrate."
    )
    add_body(doc,
        "H.264/AVC (Advanced Video Coding), được chuẩn hóa bởi ITU-T và ISO/IEC năm 2003, là "
        "một trong những codec video phổ biến nhất hiện nay. H.264 sử dụng các kỹ thuật nén "
        "tiên tiến bao gồm: bù chuyển động (motion compensation) để loại dư thừa thời gian, "
        "biến đổi cosine rời rạc (DCT) và lượng tử hóa (quantization) để nén dữ liệu không gian, "
        "cùng với entropy coding để giảm thêm kích thước."
    )
    add_body(doc,
        "Trong đề tài, codec được sử dụng là libx264 – triển khai mã nguồn mở của H.264 "
        "thông qua FFmpeg. Đây là lựa chọn phù hợp vì: (1) H.264 được hỗ trợ rộng rãi trên "
        "các thiết bị và nền tảng phát lại; (2) libx264 là encoder trưởng thành với nhiều tài "
        "liệu kỹ thuật và tham số có thể kiểm soát; (3) việc tái tạo kết quả dễ dàng hơn so với "
        "các codec mới hơn như H.265/HEVC hay AV1 vốn có yêu cầu phần cứng và thời gian encode "
        "cao hơn đáng kể."
    )
    add_body(doc,
        "Việc giới hạn ở H.264/AVC có nghĩa là kết quả thực nghiệm chỉ đại diện cho đặc tính "
        "của encoder này. Per-Title Encoding với các codec khác có thể cho kết quả khác biệt "
        "về mức tiết kiệm bitrate cụ thể, nhưng nguyên lý phân tích vẫn áp dụng được."
    )

    # 2.1.4
    add_heading(doc, "2.1.4. Chế độ kiểm soát bitrate: CBR, VBR và CRF", 3)
    add_body(doc,
        "Encoder H.264 cung cấp nhiều cơ chế khác nhau để kiểm soát lượng bit phân bổ cho từng "
        "đoạn video. Hiểu rõ sự khác biệt giữa các chế độ này là quan trọng để giải thích tại "
        "sao bitrate mục tiêu và bitrate thực tế đo được có thể khác nhau."
    )
    add_body(doc,
        "CBR (Constant Bitrate) giữ bitrate gần như không đổi trong suốt thời lượng video. "
        "Encoder phân bổ đều lượng bit, bất kể đoạn video phức tạp hay đơn giản. Ưu điểm là "
        "dễ dự đoán băng thông, nhưng nhược điểm là lãng phí bit ở đoạn đơn giản và thiếu bit "
        "ở đoạn phức tạp."
    )
    add_body(doc,
        "VBR (Variable Bitrate) cho phép encoder phân bổ nhiều bit hơn cho các đoạn phức tạp "
        "và ít bit hơn cho đoạn đơn giản, miễn là bitrate trung bình không vượt mức mục tiêu. "
        "Chế độ này thường cho chất lượng tốt hơn CBR ở cùng mức bitrate trung bình."
    )
    add_body(doc,
        "CRF (Constant Rate Factor) là chế độ kiểm soát chất lượng trực tiếp, không đặt "
        "mục tiêu bitrate. Thay vào đó, encoder tự điều chỉnh bitrate để duy trì mức chất lượng "
        "nhất định trên toàn video. Giá trị CRF từ 0 (lossless) đến 51 (chất lượng thấp nhất), "
        "với mặc định thường là 23 trong libx264. CRF phù hợp khi mục tiêu là chất lượng đồng "
        "đều, nhưng không kiểm soát được bitrate đầu ra."
    )
    add_body(doc,
        "Trong đề tài, mỗi candidate được encode theo chế độ VBR một lượt (single-pass VBR): "
        "encoder được cho một giá trị bitrate mục tiêu (target bitrate) và được phép biến động "
        "trong phạm vi nhất định (bufsize = 2× target bitrate). Điều này có nghĩa là bitrate thực "
        "tế đo được sau encode có thể lệch so với target bitrate, đặc biệt đối với video ngắn "
        "hoặc video có đặc điểm nội dung bất thường. Trong quá trình phân tích, đề tài sử dụng "
        "bitrate thực tế đo được (không phải target bitrate) làm tọa độ trục X trên đường cong "
        "bitrate–quality."
    )

    # 2.1.5
    add_heading(doc, "2.1.5. Quan hệ bitrate–chất lượng–dung lượng", 3)
    add_body(doc,
        "Ba đại lượng bitrate, chất lượng và dung lượng file có mối quan hệ phụ thuộc lẫn nhau "
        "và là trọng tâm của bài toán tối ưu hóa trong đề tài."
    )
    add_body(doc,
        "Khi tăng bitrate (với độ phân giải cố định), encoder có nhiều bit hơn để biểu diễn "
        "chi tiết hình ảnh, do đó chất lượng thường tăng. Tuy nhiên, mối quan hệ này không tuyến "
        "tính: ở bitrate rất thấp, mỗi kbps tăng thêm mang lại cải thiện chất lượng đáng kể; "
        "ở bitrate cao, tăng thêm bit chỉ mang lại cải thiện nhỏ. Đây là hiện tượng lợi ích "
        "biên giảm dần (diminishing returns), được phân tích chi tiết ở Mục 2.5."
    )
    add_body(doc,
        "Quan hệ giữa bitrate và dung lượng là tuyến tính theo công thức (2.1). Vì vậy, mọi "
        "quyết định giảm bitrate đều trực tiếp giảm dung lượng file – điều này quan trọng với "
        "hệ thống VOD vì giảm chi phí lưu trữ và truyền tải."
    )
    add_body(doc,
        "Quan hệ giữa độ phân giải và bitrate mang tính bổ trợ: mỗi cặp (độ phân giải, bitrate) "
        "tạo ra một điểm trong không gian chất lượng. Để đạt cùng mức chất lượng, video độ phân "
        "giải thấp hơn có thể cần bitrate thấp hơn đáng kể so với video cùng nội dung ở độ phân "
        "giải cao. Đây là lý do tại sao không gian candidate trong đề tài bao gồm nhiều tổ hợp "
        "khác nhau của độ phân giải và bitrate."
    )

    add_table_title(doc, "Bảng 2.1. Ví dụ minh họa quan hệ bitrate–dung lượng "
                         "(video 30 giây, chỉ mang tính chất ví dụ minh họa)")
    make_table(doc,
        headers=["Bitrate mục tiêu (kbps)", "Dung lượng xấp xỉ (MB)", "Tỉ lệ so với 6000 kbps"],
        rows=[
            ["365", "≈ 1,34", "6,1%"],
            ["730", "≈ 2,67", "12,2%"],
            ["3 000", "≈ 10,99", "50,0%"],
            ["6 000", "≈ 21,97", "100,0%"],
        ],
        col_widths=[6, 5, 6]
    )
    add_note(doc, "Lưu ý: Bảng 2.1 mang tính ví dụ minh họa. Dung lượng thực tế phụ thuộc "
                  "vào nội dung video và tham số encode.")

    # 2.1.6
    add_heading(doc, "2.1.6. Các tham số cố định và thay đổi trong thực nghiệm", 3)
    add_body(doc,
        "Để bảo đảm so sánh công bằng giữa các candidate, đề tài phân chia rõ ràng các tham số "
        "thành hai nhóm: tham số cố định trong toàn bộ thực nghiệm và tham số thay đổi giữa "
        "các candidate."
    )
    add_body(doc,
        "Việc cố định các tham số encoder (codec, preset, pixel format, keyframe interval) đảm "
        "bảo rằng sự khác biệt về chất lượng giữa các candidate phản ánh đúng ảnh hưởng của "
        "độ phân giải và bitrate, không bị nhiễu bởi sự khác biệt trong cấu hình encoder. "
        "Điều này là nguyên tắc kiểm soát biến (controlled variable) trong thiết kế thực nghiệm "
        "khoa học."
    )

    add_table_title(doc, "Bảng 2.2. Phân loại tham số encoding trong thực nghiệm")
    make_table(doc,
        headers=["Tham số", "Giá trị", "Vai trò"],
        rows=[
            ["Codec", "libx264 (H.264/AVC)", "Cố định – controlled"],
            ["Preset", "veryfast", "Cố định – controlled"],
            ["Pixel format", "yuv420p", "Cố định – controlled"],
            ["Keyframe interval", "2.0 giây", "Cố định – controlled"],
            ["Audio", "Tắt (-an)", "Cố định – chỉ đánh giá video"],
            ["Two-pass", "Không (single-pass)", "Cố định – controlled"],
            ["Độ phân giải (height)", "360/432/720/1080p", "Thay đổi – experimental variable"],
            ["Target bitrate", "250–6000 kbps", "Thay đổi – experimental variable"],
        ],
        col_widths=[5, 6, 6.5]
    )

    # ══════════════════════════════════════════════════════════════════════════
    # 2.2
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "2.2. Bitrate ladder và các mức chất lượng", 2)
    add_body(doc,
        "Bitrate ladder là cấu trúc cốt lõi của hệ thống truyền phát video thích ứng (Adaptive "
        "Bitrate Streaming – ABR). Mục này trình bày khái niệm và nguyên tắc của bitrate ladder, "
        "làm cơ sở lý thuyết cho việc xây dựng ladder đề xuất ở Chương 3."
    )

    add_heading(doc, "2.2.1. Khái niệm rung thang và bitrate ladder", 3)
    add_body(doc,
        "Trong hệ thống ABR, video được encode thành nhiều phiên bản song song với các mức chất "
        "lượng khác nhau. Mỗi phiên bản như vậy được gọi là một representation hay một rung "
        "thang (rung). Mỗi rung được đặc trưng bởi một cặp (độ phân giải, bitrate) xác định. "
        "Toàn bộ tập hợp các rung được sắp xếp theo thứ tự tăng dần tạo thành bitrate ladder."
    )
    add_body(doc,
        "Khi người dùng phát video, trình phát (player) tự động chọn rung phù hợp dựa trên "
        "băng thông mạng hiện tại và khả năng hiển thị của thiết bị. Ở kết nối chậm, player "
        "chọn rung thấp để tránh gián đoạn; khi mạng tốt, player nâng lên rung cao hơn để "
        "tăng chất lượng. Quá trình chuyển đổi này diễn ra tự động, tạo ra trải nghiệm phát "
        "video liên tục."
    )
    add_body(doc,
        "Mỗi rung trong ladder của đề tài được đặc trưng bởi: tên định danh (ví dụ: 720p_2000k), "
        "chiều cao khung hình (height), chiều rộng tương ứng giữ nguyên tỉ lệ khung (aspect ratio), "
        "và bitrate mục tiêu (kbps). Đề tài không upscale: rung có height lớn hơn video nguồn sẽ "
        "bị loại khỏi ladder."
    )

    add_heading(doc, "2.2.2. Quan hệ giữa độ phân giải và bitrate trong một rung", 3)
    add_body(doc,
        "Trong một rung, độ phân giải và bitrate không được chọn độc lập mà phải kết hợp hợp lý "
        "để đạt chất lượng mục tiêu. Một rung có bitrate quá thấp so với độ phân giải của nó sẽ "
        "cho chất lượng kém vì encoder không có đủ bit để biểu diễn chi tiết. Ngược lại, bitrate "
        "quá cao so với độ phân giải là lãng phí vì độ phân giải thấp tự nó đã giới hạn mức chi "
        "tiết có thể biểu diễn."
    )
    add_body(doc,
        "Trong thực tế, mỗi độ phân giải có một vùng bitrate hợp lý (optimal bitrate range) mà "
        "tại đó tỉ lệ chất lượng/bit là tốt nhất. Dưới vùng này, tăng bitrate mang lại cải thiện "
        "chất lượng lớn; trên vùng này, tăng thêm bitrate gần như không cải thiện thêm. Xác định "
        "vùng bitrate tối ưu này cho từng độ phân giải là một trong những mục tiêu của phân tích "
        "đường cong bitrate–quality (Mục 2.5)."
    )

    add_heading(doc, "2.2.3. Vì sao cần nhiều mức chất lượng", 3)
    add_body(doc,
        "Nếu chỉ có một phiên bản video, hệ thống phải chọn giữa hai tình huống bất lợi: "
        "(1) encode ở bitrate cao để bảo đảm chất lượng tốt, nhưng người dùng mạng chậm "
        "không thể phát được; hoặc (2) encode ở bitrate thấp để bảo đảm khả năng phát, nhưng "
        "chất lượng kém với người dùng mạng tốt. Bitrate ladder giải quyết mâu thuẫn này bằng "
        "cách cung cấp nhiều lựa chọn song song."
    )
    add_body(doc,
        "Số lượng rung cũng ảnh hưởng đến chi phí lưu trữ và chi phí encode. Quá nhiều rung "
        "làm tăng chi phí lưu trữ và thời gian encode; quá ít rung làm giảm khả năng thích ứng "
        "với điều kiện mạng. Đề tài giới hạn ladder đề xuất tối đa 4 rung, đây là ràng buộc "
        "thực tế phù hợp với quy mô demo."
    )

    add_heading(doc, "2.2.4. Ladder cố định và ladder tối ưu theo nội dung", 3)
    add_body(doc,
        "Ladder cố định (fixed ladder) áp dụng cùng một bộ (độ phân giải, bitrate) cho mọi "
        "video, bất kể nội dung. Đây là phương pháp đơn giản, dễ triển khai và dự đoán được, "
        "nhưng không tận dụng đặc điểm riêng của từng video. Video đơn giản (ít chuyển động, "
        "ít chi tiết) được encode với cùng bitrate như video phức tạp, dẫn đến lãng phí bit "
        "không cần thiết. Ngược lại, video rất phức tạp có thể không được phân bổ đủ bitrate "
        "ở các rung thấp."
    )
    add_body(doc,
        "Ladder tối ưu theo nội dung (per-title ladder hay content-aware ladder) chọn các rung "
        "dựa trên đặc điểm của video cụ thể đó. Ý tưởng cơ bản là: mỗi video có một đường cong "
        "bitrate–quality riêng, và ladder tốt nhất phải bám theo đường cong này thay vì dùng "
        "các giá trị cố định. Per-Title Encoding là phương pháp hiện thực hóa ý tưởng này."
    )
    add_body(doc,
        "Sự khác biệt cơ bản giữa hai phương pháp: ladder cố định ưu tiên đơn giản trong "
        "vận hành; ladder per-title ưu tiên hiệu quả bitrate–quality nhưng đòi hỏi phân tích "
        "từng video riêng. Trong phạm vi đề tài, cả hai đều được xây dựng và so sánh."
    )

    # ══════════════════════════════════════════════════════════════════════════
    # 2.3
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "2.3. Đánh giá chất lượng video bằng VMAF", 2)
    add_body(doc,
        "Để so sánh các candidate và lựa chọn ladder, đề tài cần một chỉ số định lượng phản ánh "
        "chất lượng hình ảnh cảm nhận. Mục này giới thiệu nền tảng lý thuyết của đánh giá chất "
        "lượng video và VMAF – chỉ số chính được sử dụng trong đề tài."
    )

    add_heading(doc, "2.3.1. Tổng quan về đánh giá chất lượng video", 3)
    add_body(doc,
        "Chất lượng video có thể được đánh giá theo hai hướng: đánh giá chủ quan và đánh giá "
        "khách quan. Đánh giá chủ quan (subjective quality assessment) sử dụng người xem thực "
        "để cho điểm theo các phương pháp chuẩn hóa như MOS (Mean Opinion Score, ITU-T P.910). "
        "Đây là phương pháp chính xác nhất về mặt cảm nhận, nhưng tốn kém và không thể tự "
        "động hóa trong quy trình encode."
    )
    add_body(doc,
        "Đánh giá khách quan (objective quality metrics) sử dụng các thuật toán tự động so "
        "sánh video đã mã hóa với video tham chiếu gốc (full-reference metrics). Đây là phương "
        "pháp được sử dụng trong đề tài vì có thể tự động hóa hoàn toàn và lặp lại được. Các "
        "chỉ số phổ biến bao gồm PSNR (Peak Signal-to-Noise Ratio), SSIM (Structural Similarity "
        "Index) và VMAF. Mỗi chỉ số có ưu điểm và hạn chế riêng, nhưng VMAF được lựa chọn làm "
        "chỉ số chính trong đề tài vì lý do trình bày ở các mục tiếp theo."
    )

    add_heading(doc, "2.3.2. VMAF: khái niệm và mục đích", 3)
    add_body(doc,
        "VMAF (Video Multi-method Assessment Fusion) là chỉ số đánh giá chất lượng video "
        "được phát triển bởi Netflix và công bố là mã nguồn mở [CẦN BỔ SUNG NGUỒN THAM KHẢO: "
        "Li, Z. et al., \"VMAF: The Journey Continues\", Netflix Tech Blog, 2018]. VMAF được "
        "thiết kế với mục tiêu chính là dự đoán chính xác chất lượng cảm nhận của người xem "
        "khi so sánh một video đã mã hóa với video gốc."
    )
    add_body(doc,
        "Điểm VMAF nằm trong khoảng từ 0 đến 100. Điểm cao hơn phản ánh chất lượng cảm "
        "nhận tốt hơn. Ngưỡng diễn giải tham khảo: dưới 40 là chất lượng kém, 40–60 trung "
        "bình, 60–80 khá, trên 80 tốt, trên 93 rất tốt và khó phân biệt được sự khác biệt so "
        "với video gốc qua màn hình thông thường. Tuy nhiên, các ngưỡng này phụ thuộc vào nội "
        "dung, thiết bị xem và điều kiện đo; không nên áp dụng cứng nhắc."
    )
    add_body(doc,
        "VMAF phù hợp với bài toán so sánh candidate vì: (1) nó được tối ưu hóa để tương quan "
        "với đánh giá chủ quan của người xem trên màn hình TV/máy tính; (2) nó nhạy cảm với "
        "các loại méo hình ảnh thường gặp khi nén video; (3) nó cho kết quả nhất quán và "
        "có thể tái tạo; (4) nó được tích hợp sẵn vào FFmpeg qua filter libvmaf."
    )

    add_heading(doc, "2.3.3. Nguyên lý hoạt động của VMAF", 3)
    add_body(doc,
        "VMAF hoạt động theo nguyên lý fusion (kết hợp): thay vì dựa vào một phép đo duy "
        "nhất, nó tổng hợp nhiều đặc trưng chất lượng bổ sung cho nhau và sử dụng mô hình "
        "học máy (Support Vector Machine – SVM) được huấn luyện trên điểm MOS chủ quan để "
        "tổng hợp điểm cuối cùng."
    )
    add_body(doc,
        "Các đặc trưng chính được VMAF tính toán bao gồm: (1) VIF (Visual Information Fidelity) "
        "– đo lường mức độ thông tin thị giác được bảo toàn sau khi mã hóa, tính trên nhiều "
        "thang tần số; (2) DLM (Detail Loss Metric) – đánh giá mức độ mất chi tiết; "
        "(3) motion score – ước lượng mức độ chuyển động trong video. "
        "Mỗi đặc trưng phản ánh một khía cạnh khác nhau của chất lượng hình ảnh cảm nhận."
    )
    add_body(doc,
        "Để tính VMAF, cần có hai đầu vào: (1) video tham chiếu (reference) – video nguồn gốc "
        "chưa nén hoặc nén ở chất lượng cao nhất có thể coi là tham chiếu; (2) video đã mã "
        "hóa (distorted) – video sau khi chạy qua pipeline encode. Hai video phải có cùng "
        "độ phân giải khi so sánh. Nếu khác nhau, video đã mã hóa cần được upscale về độ "
        "phân giải của tham chiếu trước khi tính VMAF."
    )

    add_heading(doc, "2.3.4. Điều kiện đo VMAF trong đề tài", 3)
    add_body(doc,
        "Để bảo đảm so sánh công bằng giữa các candidate, đề tài thống nhất các điều kiện "
        "đo VMAF như sau. Video tham chiếu là video nguồn gốc (input video) chưa qua encode. "
        "Video được đánh giá là mỗi candidate sau khi encode bằng FFmpeg. Trước khi tính VMAF, "
        "video candidate được upscale về độ phân giải của video tham chiếu bằng thuật toán "
        "bicubic scaling. Điều này bảo đảm điểm VMAF phản ánh cả tác động của việc giảm "
        "độ phân giải lẫn nén video."
    )
    add_body(doc,
        "Mô hình VMAF được sử dụng là vmaf_v0.6.1 – model chuẩn tích hợp sẵn trong libvmaf, "
        "không cần tệp model ngoài. Kết quả ghi nhận là điểm VMAF trung bình trên toàn video "
        "(mean VMAF score). Đề tài không tự tạo hay suy đoán điểm VMAF: điểm phải được FFmpeg "
        "thực sự tính toán và trả về qua filter libvmaf; nếu không parse được, pipeline sẽ "
        "báo lỗi."
    )
    add_body(doc,
        "Ngoài VMAF, đề tài cũng đo PSNR và SSIM như các chỉ số phụ để tham khảo, nhưng "
        "VMAF là chỉ số quyết định trong phân tích và lựa chọn candidate."
    )

    add_heading(doc, "2.3.5. Ưu điểm và giới hạn của VMAF", 3)
    add_body(doc,
        "VMAF có một số ưu điểm nổi bật: (1) tương quan cao với đánh giá chủ quan trong "
        "điều kiện phát lại trên màn hình; (2) nhạy hơn PSNR với các loại méo hình ảnh có "
        "liên quan đến trải nghiệm người dùng; (3) cho phép so sánh các candidate ở độ phân "
        "giải khác nhau thông qua bước upscale chuẩn hóa; (4) kết quả ổn định và lặp lại được."
    )
    add_body(doc,
        "Tuy nhiên, VMAF cũng có các giới hạn quan trọng cần lưu ý: (1) VMAF không đồng nhất "
        "với chất lượng cảm nhận tuyệt đối – điểm VMAF 90 trên màn hình di động nhỏ có thể "
        "cảm nhận tốt hơn điểm VMAF 90 trên TV 65 inch; (2) VMAF có thể cho kết quả không "
        "trực quan với một số nội dung đặc biệt như hoạt hình, grain film, hay synthetic test "
        "patterns; (3) VMAF model vmaf_v0.6.1 được tối ưu cho HD content trên màn hình; "
        "(4) không nên sử dụng VMAF như chỉ số duy nhất để kết luận về mọi khía cạnh chất "
        "lượng mà không xem xét ngữ cảnh nội dung và thiết bị xem."
    )
    add_body(doc,
        "Trong phạm vi đề tài, các giới hạn này được chấp nhận vì mục tiêu là so sánh tương "
        "đối giữa các candidate và giữa ladder đề xuất với baseline, không phải xác định chất "
        "lượng tuyệt đối."
    )

    # ══════════════════════════════════════════════════════════════════════════
    # 2.4
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "2.4. Phân tích đặc điểm nội dung: Spatial Information và Temporal Information", 2)
    add_body(doc,
        "Trước và song song với quá trình encode, đề tài phân tích hai đặc trưng đặc điểm nội "
        "dung là Spatial Information (SI) và Temporal Information (TI). Đây là các chỉ số đơn "
        "giản nhưng hữu ích để định tính mức độ phức tạp của video đầu vào, từ đó hỗ trợ "
        "diễn giải kết quả encode."
    )

    add_heading(doc, "2.4.1. Spatial Information (SI) – Thông tin không gian", 3)
    add_body(doc,
        "Spatial Information (SI) đo lường mức độ phức tạp không gian của nội dung hình ảnh "
        "trong một khung hình. SI cao cho thấy khung hình có nhiều chi tiết, biên cạnh, kết "
        "cấu bề mặt; SI thấp cho thấy nội dung đơn giản, nhiều vùng đồng đều màu sắc."
    )
    add_body(doc,
        "SI cao có ý nghĩa trực quan rõ ràng: video có nhiều chi tiết (ví dụ: cảnh thiên "
        "nhiên, kết cấu vải, chữ trên nền phức tạp) khó nén hơn và cần nhiều bit hơn để "
        "đạt cùng mức chất lượng so với video đơn giản (ví dụ: slide presentation, cảnh "
        "nền tối đồng nhất). Mối liên hệ này là lý do SI được dùng như indicator về nhu "
        "cầu bitrate của video."
    )
    add_body(doc,
        "Phương pháp tính SI trong đề tài được lấy cảm hứng từ ITU-T P.910 nhưng có "
        "điều chỉnh phù hợp với mục tiêu thực nghiệm. Với mỗi khung hình dạng grayscale, "
        "SI được tính theo các bước: (1) áp dụng bộ lọc Sobel để phát hiện biên theo hai "
        "hướng ngang (Gx) và dọc (Gy); (2) tính biên độ gradient; (3) tính độ lệch chuẩn "
        "của biên độ gradient. Cụ thể:"
    )
    add_formula(doc, "Gx = [−1  0  +1; −2  0  +2; −1  0  +1] * F", "(2.2a)")
    add_formula(doc, "Gy = [−1  −2  −1; 0  0  0; +1  +2  +1] * F", "(2.2b)")
    add_formula(doc, "G = √(Gx² + Gy²)", "(2.2c)")
    add_formula(doc, "SI(F) = σ(G)", "(2.2d)")
    add_body(doc,
        "trong đó F là ma trận pixel của khung hình grayscale, * biểu thị phép tích chập "
        "(convolution), G là biên độ gradient Sobel tại mỗi pixel, và σ(G) là độ lệch chuẩn "
        "của toàn bộ các giá trị biên độ. Độ lệch chuẩn phản ánh mức độ biến thiên của biên "
        "cạnh trong ảnh – ảnh phức tạp có biên cạnh phân bố rộng và không đều, dẫn đến σ lớn."
    )
    add_body(doc,
        "Trong triển khai của đề tài, SI được tính trên các khung hình được lấy mẫu ở 2 fps, "
        "thu nhỏ về chiều rộng 320 pixel (giữ tỉ lệ khung) để giảm tải tính toán. Kết quả "
        "cuối cùng là giá trị trung vị (median) của SI trên tất cả khung lấy mẫu (tối đa 40 "
        "khung). Trung vị được chọn thay vì giá trị lớn nhất (như trong P.910 gốc) để giảm "
        "ảnh hưởng của những khung bất thường như cảnh cắt đột ngột."
    )
    add_body(doc,
        "Giới hạn của SI: SI không phân biệt được nguồn gốc của chi tiết – biên cạnh tự nhiên "
        "và nhiễu ảnh (noise) đều làm tăng SI. Video có grain film hoặc noise cao có thể có "
        "SI cao nhưng không nhất thiết khó nén hơn video sạch. SI cũng không phản ánh phân "
        "bố không gian của chi tiết (tập trung hay phân tán đều). Do đó, SI chỉ là một "
        "indicator tham khảo."
    )

    add_heading(doc, "2.4.2. Temporal Information (TI) – Thông tin thời gian", 3)
    add_body(doc,
        "Temporal Information (TI) đo lường mức độ thay đổi giữa các khung hình liên tiếp, "
        "phản ánh mức độ chuyển động và biến đổi theo thời gian trong video. TI cao cho thấy "
        "video có nhiều chuyển động (action scenes, sports, dancing); TI thấp cho thấy cảnh "
        "tĩnh hoặc chuyển động chậm."
    )
    add_body(doc,
        "TI cao quan trọng với encoding vì các bộ mã hóa video khai thác dư thừa thời gian "
        "để giảm bitrate. Video ít chuyển động cho phép encoder dự đoán khung tiếp theo từ "
        "khung hiện tại với sai số nhỏ, cần ít bit hơn. Video nhiều chuyển động làm sai số "
        "dự đoán tăng cao, encoder cần nhiều bit hơn. Vì vậy, TI là chỉ số bổ sung quan trọng "
        "bên cạnh SI để hiểu nhu cầu bitrate của video."
    )
    add_body(doc,
        "Phương pháp tính TI trong đề tài: với mỗi cặp khung liên tiếp (Fn-1, Fn), tính hiệu "
        "pixel-wise rồi lấy độ lệch chuẩn của hiệu đó:"
    )
    add_formula(doc, "TI(Fn) = σ(Fn − Fn-1)", "(2.3)")
    add_body(doc,
        "trong đó Fn và Fn-1 là ma trận pixel grayscale của khung hiện tại và khung trước đó, "
        "phép trừ là phép trừ từng phần tử (element-wise), và σ là độ lệch chuẩn của ma trận "
        "hiệu. Độ lệch chuẩn của hiệu pixel lớn khi có nhiều vùng thay đổi mạnh, phản ánh "
        "chuyển động phức tạp."
    )
    add_body(doc,
        "Tương tự SI, TI được tính trên các khung lấy mẫu (2 fps, tối đa 40 khung), co về "
        "320 pixel chiều rộng. Kết quả cuối là trung vị của TI trên các cặp khung liên tiếp. "
        "Cần ít nhất 2 khung để tính được TI."
    )
    add_body(doc,
        "Giới hạn của TI: TI tính từ hiệu pixel thô (pixel difference) không tách biệt được "
        "chuyển động thực sự của đối tượng và chuyển động camera (pan, zoom). Cả hai đều làm "
        "tăng TI. Ngoài ra, cảnh chuyển tiếp đột ngột (scene cut) tạo ra đỉnh TI rất cao "
        "không phản ánh nội dung thực; tuy nhiên, việc dùng trung vị giúp giảm bớt tác động "
        "của các đỉnh này."
    )

    add_heading(doc, "2.4.3. Vai trò của SI/TI trong đề tài", 3)
    add_body(doc,
        "Trong đề tài, SI và TI đóng vai trò phân tích và mô tả đặc điểm nội dung, không "
        "phải quyết định tự động bitrate ladder. Cụ thể:"
    )
    add_bullet(doc, [
        "SI và TI cung cấp context để diễn giải kết quả encode: video có SI cao và TI thấp "
        "(chi tiết không gian nhiều nhưng ít chuyển động) sẽ có đặc tính đường cong bitrate–quality "
        "khác với video SI thấp, TI cao.",
        "SI và TI hỗ trợ giải thích tại sao một video cần bitrate cao hơn để đạt cùng điểm "
        "VMAF so với video khác.",
        "Trong phương pháp heuristic (k × fixed ladder, chỉ dùng để đối chiếu), SI và TI được "
        "kết hợp thành chỉ số complexity index để điều chỉnh bitrate, nhưng phương pháp này "
        "không phải phương pháp chính của đề tài.",
        "Phương pháp chính (hull-based per-title) không sử dụng SI/TI để sinh ladder; ladder "
        "được chọn dựa trực tiếp trên dữ liệu VMAF và bitrate thực đo từ các candidate."
    ])
    add_body(doc,
        "SI và TI không thay thế VMAF trong việc đánh giá chất lượng. Chúng cũng không tự "
        "động quyết định bitrate ladder vì mối quan hệ giữa SI/TI và hiệu quả encode là gần "
        "đúng và phụ thuộc nhiều vào nội dung cụ thể. Kết quả VMAF thực đo luôn là cơ sở "
        "quyết định trong đề tài."
    )

    # Complexity index formula
    add_body(doc,
        "Để tham khảo, chỉ số độ phức tạp được tính theo công thức:"
    )
    add_formula(doc,
        "complexity_index = clip(0.55 × (SI / SI_ref) + 0.45 × (TI / TI_ref), 0, 1.5)", "(2.4)"
    )
    add_body(doc,
        "trong đó SI_ref = 80.0 và TI_ref = 40.0 là giá trị tham chiếu kinh nghiệm được "
        "cấu hình trong đề tài. Hệ số 0.55 và 0.45 phản ánh trọng số đặt ra cho SI và TI "
        "trong công thức tổng hợp. Đây là quy tắc do đề tài đề xuất cho mục đích heuristic, "
        "không phải tiêu chuẩn chính thức."
    )

    # ══════════════════════════════════════════════════════════════════════════
    # 2.5
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "2.5. Đường cong bitrate–quality (Rate–Quality Curve)", 2)
    add_body(doc,
        "Đường cong bitrate–quality (hay rate–quality curve, R–Q curve) là công cụ trực quan "
        "hóa quan trọng nhất trong đề tài. Nó là nền tảng để thực hiện Pareto analysis và "
        "lựa chọn bitrate ladder."
    )

    add_heading(doc, "2.5.1. Khái niệm và cách xây dựng từ các candidate", 3)
    add_body(doc,
        "Đường cong bitrate–quality được xây dựng bằng cách: với mỗi candidate (một tổ hợp "
        "độ phân giải × bitrate), thực hiện encode và đo hai giá trị: (1) bitrate thực tế "
        "sau encode (trục X, đơn vị kbps); (2) điểm VMAF tương ứng (trục Y, thang 0–100). "
        "Mỗi candidate tạo ra một điểm (R, Q) trong không gian hai chiều này."
    )
    add_body(doc,
        "Tập hợp các điểm (R, Q) từ tất cả candidate tạo thành đám mây điểm (point cloud). "
        "Khi vẽ các điểm này, đặc biệt là nhóm theo từng độ phân giải, ta có thể nhìn thấy "
        "xu hướng của đường cong: chất lượng tăng dần khi bitrate tăng nhưng với tốc độ giảm "
        "dần. Đường nối các điểm trong một nhóm độ phân giải gọi là rate–quality curve "
        "của độ phân giải đó."
    )

    add_table_title(doc, "Bảng 2.3. Ví dụ minh họa các điểm trên đường cong bitrate–quality "
                         "(số liệu giả định, chỉ mang tính ví dụ)")
    make_table(doc,
        headers=["Candidate", "Độ phân giải", "Bitrate đích (kbps)", "VMAF (ví dụ)"],
        rows=[
            ["360p_250k", "360p", "250", "~55"],
            ["360p_500k", "360p", "500", "~72"],
            ["360p_700k", "360p", "700", "~80"],
            ["720p_1000k", "720p", "1 000", "~65"],
            ["720p_2000k", "720p", "2 000", "~82"],
            ["720p_3000k", "720p", "3 000", "~88"],
            ["1080p_3000k", "1080p", "3 000", "~78"],
            ["1080p_6000k", "1080p", "6 000", "~92"],
        ],
        col_widths=[4.5, 3.5, 5, 4.5]
    )
    add_note(doc, "Bảng 2.3 mang tính ví dụ minh họa, không phải kết quả thực nghiệm của đề tài. "
                  "Số liệu VMAF thực tế phụ thuộc vào nội dung video và tham số encode.")

    add_heading(doc, "2.5.2. Hiện tượng lợi ích biên giảm dần", 3)
    add_body(doc,
        "Một quan sát quan trọng trên đường cong bitrate–quality là hiện tượng lợi ích biên "
        "giảm dần (diminishing returns): mức cải thiện chất lượng trên mỗi kbps tăng thêm "
        "giảm dần khi bitrate đã cao."
    )
    add_body(doc,
        "Ví dụ minh họa (với số liệu giả định): tăng bitrate từ 250 kbps lên 500 kbps "
        "(tăng 250 kbps) có thể cải thiện VMAF từ 55 lên 72 (tăng 17 điểm). Nhưng tăng từ "
        "500 kbps lên 750 kbps (cũng tăng 250 kbps) có thể chỉ cải thiện thêm 8 điểm VMAF. "
        "Tăng từ 2000 kbps lên 2250 kbps có thể chỉ cải thiện 1–2 điểm, hoặc thậm chí "
        "không đo được sự cải thiện."
    )
    add_body(doc,
        "Hiện tượng này giải thích tại sao không phải lúc nào tăng bitrate cũng mang lại "
        "lợi ích tương xứng. Phân tích đường cong giúp xác định 'điểm uốn' (knee point) – "
        "vùng bitrate mà tại đó lợi ích biên bắt đầu giảm mạnh. Candidate nằm sau điểm "
        "uốn thường không hiệu quả trong ladder."
    )

    add_heading(doc, "2.5.3. Vai trò trong phân tích candidate", 3)
    add_body(doc,
        "Đường cong bitrate–quality đóng vai trò nền tảng cho hai bước tiếp theo trong "
        "quy trình: Pareto filtering (loại bỏ candidate kém hiệu quả) và lựa chọn ladder "
        "(chọn tập con candidate tốt nhất). Không có đường cong này, không thể thực hiện "
        "được hai bước đó một cách có căn cứ."
    )
    add_body(doc,
        "Ngoài ra, đường cong còn cho phép so sánh trực quan giữa ladder đề xuất và baseline: "
        "nếu vẽ các điểm của cả hai ladder lên cùng biểu đồ, có thể dễ dàng nhận thấy ladder "
        "nào nằm 'cao hơn bên trái' (chất lượng tốt hơn tại cùng bitrate, hoặc bitrate thấp "
        "hơn tại cùng chất lượng)."
    )
    add_placeholder(doc, "[HÌNH 2.1. Đường cong bitrate–quality – CÓ THỂ NHÚNG "
                         "d:\\DPT\\per-title-encoding\\docs\\chapter23_figures\\fig_2_1_bitrate_quality.png]")

    # ══════════════════════════════════════════════════════════════════════════
    # 2.6
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "2.6. Phân tích Pareto frontier và Upper Convex Hull", 2)
    add_body(doc,
        "Để từ tập hợp tất cả candidate xác định được những candidate có hiệu quả bitrate–"
        "quality tốt nhất, đề tài áp dụng hai công cụ phân tích: Pareto frontier và upper "
        "convex hull. Đây là hai khái niệm liên quan nhưng khác nhau, cần được phân biệt "
        "rõ ràng."
    )

    add_heading(doc, "2.6.1. Pareto dominance và Pareto frontier", 3)
    add_body(doc,
        "Trong không gian bitrate–quality, mỗi candidate là một điểm (R, Q) với hai thuộc "
        "tính: bitrate R (muốn nhỏ để tiết kiệm băng thông) và chất lượng Q (muốn lớn để "
        "đảm bảo trải nghiệm). Đây là bài toán tối ưu hóa hai mục tiêu mâu thuẫn nhau."
    )
    add_body(doc,
        "Pareto dominance (quan hệ chi phối) được định nghĩa như sau: candidate B chi phối "
        "candidate A (ký hiệu B ≻ A) nếu và chỉ nếu B đồng thời tốt hơn hoặc bằng A ở cả "
        "hai mục tiêu, và tốt hơn nghiêm ngặt ở ít nhất một mục tiêu. Trong bài toán "
        "bitrate–quality:"
    )
    add_formula(doc,
        "B ≻ A  ⟺  (R_B ≤ R_A  AND  Q_B ≥ Q_A)  AND  (R_B < R_A  OR  Q_B > Q_A)", "(2.5)"
    )
    add_body(doc,
        "Nói cách khác, B chi phối A nếu B có cùng hoặc ít bitrate hơn A, cùng hoặc chất "
        "lượng tốt hơn A, và ít nhất một trong hai điều kiện là nghiêm ngặt. Một candidate "
        "bị chi phối (dominated) nghĩa là luôn tồn tại một candidate khác vừa rẻ hơn vừa "
        "tốt hơn hoặc bằng; vì vậy candidate bị chi phối không bao giờ là lựa chọn hợp lý."
    )
    add_body(doc,
        "Pareto frontier (hay non-dominated set) là tập hợp các candidate không bị chi phối "
        "bởi bất kỳ candidate nào khác. Các điểm trên Pareto frontier đại diện cho những "
        "đánh đổi tốt nhất giữa bitrate và chất lượng: không thể cải thiện chất lượng mà "
        "không tăng bitrate, và không thể giảm bitrate mà không giảm chất lượng."
    )
    add_placeholder(doc, "[HÌNH 2.2. Minh họa Pareto frontier – CÓ THỂ NHÚNG "
                         "d:\\DPT\\per-title-encoding\\docs\\chapter23_figures\\fig_2_2_pareto.png]")

    add_heading(doc, "2.6.2. Upper Convex Hull (upper convex envelope)", 3)
    add_body(doc,
        "Upper Convex Hull (UCH) là một tập con của Pareto frontier, được xác định bằng "
        "tính lồi (convexity) của đường nối các điểm. Trong không gian bitrate–quality, "
        "UCH là đường bao phía trên lồi nhất (convex envelope) của các điểm Pareto – tức "
        "là đường nối các điểm sao cho không có điểm nào nằm phía trên đường nối đó."
    )
    add_body(doc,
        "Về mặt hình học, UCH loại bỏ các điểm 'lõm' nằm trên Pareto frontier nhưng không "
        "nằm trên đường bao lồi. Các điểm này có thể là Pareto-optimal nhưng không nằm ở "
        "những đánh đổi có lợi nhất về mặt hiệu quả bitrate–quality theo đơn vị."
    )
    add_body(doc,
        "Thuật toán monotone chain được sử dụng trong đề tài để tính UCH: các điểm được "
        "sắp xếp theo bitrate tăng dần, sau đó thêm vào hull theo thứ tự và loại bỏ các "
        "điểm gây ra 'quẹo phải' (cross product ≥ 0 trong hệ tọa độ bitrate–VMAF), giữ lại "
        "chỉ những điểm tạo ra đường bao lồi phía trên."
    )
    add_placeholder(doc, "[HÌNH 2.3. So sánh Pareto frontier và Upper Convex Hull – CÓ THỂ NHÚNG "
                         "d:\\DPT\\per-title-encoding\\docs\\chapter23_figures\\fig_2_3_convex_hull.png]")

    add_heading(doc, "2.6.3. Phân biệt Pareto filtering và lựa chọn ladder cuối cùng", 3)
    add_body(doc,
        "Đây là điểm quan trọng cần phân biệt rõ: Pareto filtering và UCH analysis là các "
        "bước phân tích (filtering/ranking), không phải bước chọn ladder cuối cùng."
    )
    add_body(doc,
        "Pareto filtering loại bỏ các candidate bị chi phối – những candidate không bao giờ "
        "là lựa chọn hợp lý. Bước này giảm không gian ứng cử viên nhưng không quyết định "
        "ladder. Sau khi lọc, các điểm còn lại trên Pareto frontier có thể vẫn nhiều hơn "
        "số rung cần thiết trong ladder."
    )
    add_body(doc,
        "Lựa chọn ladder cuối cùng là bước riêng biệt, áp dụng thêm các ràng buộc thực tế: "
        "số rung tối đa, mỗi độ phân giải một đại diện, bitrate tăng dần nghiêm ngặt, và "
        "mức chất lượng tối thiểu. Đây là bước phụ thuộc vào mục tiêu ứng dụng và ràng buộc "
        "thiết kế, không chỉ là đặc tính toán học của tập candidate."
    )
    add_body(doc,
        "Tóm lại: Pareto frontier ≠ bitrate ladder cuối cùng. UCH là tập con của Pareto "
        "frontier. Ladder cuối cùng là tập con của UCH, được lựa chọn theo các ràng buộc "
        "thực tế của đề tài."
    )

    # ══════════════════════════════════════════════════════════════════════════
    # 2.7
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "2.7. Tiêu chí đánh giá bitrate ladder", 2)
    add_body(doc,
        "Để so sánh hai ladder (đề xuất và baseline), cần xác định trước một bộ tiêu chí "
        "đánh giá rõ ràng. Mục này trình bày các tiêu chí định tính và định lượng được "
        "sử dụng trong đề tài."
    )
    add_bullet(doc, [
        "Chất lượng hình ảnh: điểm VMAF của các rung trong ladder. Ladder tốt nên cung "
        "cấp chất lượng đủ cao tại mỗi mức bitrate.",
        "Bitrate: bitrate thực tế của mỗi rung. Ladder hiệu quả nên đạt chất lượng mục "
        "tiêu với bitrate thấp hơn.",
        "Dung lượng file: kích thước file encode tương ứng mỗi rung, ảnh hưởng đến chi "
        "phí lưu trữ và băng thông truyền tải.",
        "Số lượng rung: ít rung hơn nghĩa là ít phiên bản cần encode và lưu trữ. Tuy "
        "nhiên, quá ít rung làm giảm khả năng thích ứng ABR.",
        "Độ bao phủ chất lượng (quality coverage): khoảng chất lượng từ rung thấp nhất "
        "đến rung cao nhất. Ladder tốt nên bao phủ đủ rộng để phục vụ cả người dùng "
        "mạng chậm và mạng nhanh.",
        "Tính hợp lý của độ phân giải: mỗi rung nên sử dụng độ phân giải phù hợp với "
        "bitrate của nó, không có cặp (độ phân giải, bitrate) bất hợp lý.",
        "Hiệu quả bitrate–quality: không có rung dư thừa (tăng bitrate mà chất lượng "
        "cải thiện không đáng kể so với rung liền trước).",
        "Tính nhất quán điều kiện so sánh: cả hai ladder phải được encode và đo lường "
        "trong cùng điều kiện để so sánh công bằng."
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # 2.8
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "2.8. Các chỉ số định lượng đánh giá hiệu quả tối ưu hóa", 2)
    add_body(doc,
        "Mục này định nghĩa chính xác các chỉ số định lượng (KPI – Key Performance Indicators) "
        "được sử dụng để đo lường và so sánh hiệu quả của ladder đề xuất so với baseline. "
        "Đây là cơ sở để trình bày kết quả ở Chương 5."
    )

    add_heading(doc, "2.8.1. Tiết kiệm bitrate tại chất lượng tương đương", 3)
    add_body(doc,
        "Chỉ số bitrate saving đo lường mức giảm bitrate của ladder đề xuất so với baseline "
        "khi đạt cùng mức chất lượng. Điều kiện 'cùng mức chất lượng' được xác định bằng "
        "cách chọn một điểm VMAF tham chiếu chung và xác định bitrate cần thiết của mỗi "
        "ladder để đạt điểm VMAF đó."
    )
    add_formula(doc,
        "Bitrate Saving (%) = (R_baseline − R_proposed) / R_baseline × 100%", "(2.6)"
    )
    add_body(doc,
        "trong đó R_baseline là bitrate của ladder cố định tại mức VMAF tham chiếu, và "
        "R_proposed là bitrate của ladder đề xuất tại cùng mức VMAF đó. Giá trị dương cho "
        "thấy ladder đề xuất tiết kiệm bitrate; giá trị âm cho thấy ladder đề xuất tốn "
        "bitrate hơn tại cùng chất lượng."
    )
    add_body(doc,
        "Lưu ý quan trọng: trong thực tế, hai ladder có thể không có rung nào với chính xác "
        "cùng điểm VMAF. Khi đó, cần nội suy hoặc chọn điểm VMAF gần nhất làm tham chiếu "
        "và ghi rõ phương pháp nội suy. Không nên so sánh bitrate saving nếu điểm VMAF "
        "của hai ladder chênh lệch quá lớn."
    )

    add_heading(doc, "2.8.2. Chênh lệch chất lượng tại bitrate tương đương", 3)
    add_body(doc,
        "Chỉ số ΔVMAF đo lường sự chênh lệch chất lượng giữa hai ladder khi so sánh ở "
        "cùng mức bitrate:"
    )
    add_formula(doc, "ΔVMAF = VMAF_proposed − VMAF_baseline", "(2.7)")
    add_body(doc,
        "ΔVMAF dương cho thấy ladder đề xuất đạt chất lượng cao hơn tại cùng mức bitrate; "
        "ΔVMAF âm cho thấy ladder baseline có chất lượng tốt hơn. Chỉ số này được sử dụng "
        "bổ sung khi muốn đánh giá chất lượng thay vì tiết kiệm bitrate. Điều kiện áp dụng "
        "tương tự: hai ladder cần được so sánh tại mức bitrate gần nhau, với phương pháp "
        "chọn điểm so sánh được ghi rõ."
    )

    add_heading(doc, "2.8.3. So sánh dung lượng và số lượng rung", 3)
    add_body(doc,
        "Ngoài chất lượng và bitrate, hai chỉ số thực tế quan trọng là tổng dung lượng "
        "và số lượng rung của ladder:"
    )
    add_bullet(doc, [
        "Dung lượng file mỗi rung (MB): phản ánh chi phí lưu trữ tương ứng mỗi mức bitrate. "
        "Tổng dung lượng toàn ladder ảnh hưởng đến chi phí lưu trữ trên server.",
        "Số lượng rung: ladder đề xuất có thể ít rung hơn baseline nếu một số rung baseline "
        "bị coi là kém hiệu quả và bị loại. Ít rung hơn nghĩa là ít encode và lưu trữ hơn.",
        "Tổng bitrate đại diện: tổng hoặc trung bình bitrate của các rung trong ladder, "
        "dùng để so sánh tổng tải truyền tải kỳ vọng."
    ])

    add_heading(doc, "2.8.4. Giới hạn của các chỉ số đánh giá", 3)
    add_body(doc,
        "Không nên chỉ dựa vào một KPI để kết luận về hiệu quả của ladder. Mỗi chỉ số "
        "phản ánh một khía cạnh khác nhau và có giới hạn riêng:"
    )
    add_bullet(doc, [
        "Khó xác định 'tương đương tuyệt đối': hai ladder hiếm khi có rung với chính xác "
        "cùng VMAF hoặc cùng bitrate; phương pháp nội suy ảnh hưởng đến kết quả so sánh.",
        "Kết quả phụ thuộc vào video: ladder đề xuất có thể tiết kiệm bitrate lớn với "
        "video đơn giản nhưng không đáng kể với video phức tạp – hoặc ngược lại.",
        "Kết quả phụ thuộc vào số lượng và phân bố candidate: nếu không gian candidate "
        "không đủ dày hoặc không phủ đủ rộng, kết quả phân tích bị giới hạn.",
        "Kết quả chỉ đại diện cho codec và preset đã chọn: các chỉ số tiết kiệm bitrate "
        "sẽ khác với H.265/HEVC hoặc AV1.",
        "Không khẳng định quá mức từ một video thử nghiệm: kết quả thực nghiệm trên "
        "một video ngắn là minh họa nguyên lý, không phải đánh giá thống kê tổng quát."
    ])

    add_page_break(doc)

    # ══════════════════════════════════════════════════════════════════════════
    # CHƯƠNG 3
    # ══════════════════════════════════════════════════════════════════════════

def build_chapter3(doc: Document) -> None:

    add_heading(doc, "CHƯƠNG 3. PHƯƠNG PHÁP NGHIÊN CỨU VÀ QUY TRÌNH ĐỀ XUẤT", 1)
    add_body(doc,
        "Chương này mô tả phương pháp giải quyết bài toán Per-Title Encoding trong phạm vi "
        "thực nghiệm của đề tài. Trên cơ sở lý thuyết đã trình bày ở Chương 2, chương này "
        "trả lời câu hỏi: từ một video đầu vào, đề tài sử dụng những dữ liệu, công cụ và "
        "bước xử lý nào để xây dựng và đánh giá bitrate ladder đề xuất?"
    )

    # ══════════════════════════════════════════════════════════════════════════
    # 3.1
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "3.1. Phát biểu bài toán", 2)

    add_heading(doc, "3.1.1. Mô hình đầu vào–đầu ra", 3)
    add_body(doc,
        "Bài toán của đề tài được phát biểu như sau: cho một video nguồn V và một không gian "
        "candidate C = {(ri, bj)} bao gồm các tổ hợp độ phân giải ri và bitrate mục tiêu bj, "
        "tìm một bitrate ladder L* ⊆ C sao cho L* đạt hiệu quả bitrate–quality tốt hơn "
        "ladder cố định cùng điều kiện."
    )
    add_body(doc,
        "Đầu vào bao gồm: video nguồn (một file video ngắn khoảng 10–30 giây), tệp cấu "
        "hình chứa không gian candidate và các tham số encode, và tệp cấu hình ladder "
        "cố định dùng làm baseline."
    )
    add_body(doc,
        "Quá trình xử lý gồm các bước tuần tự: chuẩn hóa video, phân tích SI/TI, encode "
        "tất cả candidate, đo VMAF và bitrate thực tế, xây dựng đường cong bitrate–quality, "
        "lọc Pareto, phân tích upper convex hull, và lựa chọn ladder theo quy tắc thực nghiệm."
    )
    add_body(doc,
        "Đầu ra gồm: bitrate ladder đề xuất L* (danh sách các rung được chọn), bitrate "
        "ladder cố định baseline, tập dữ liệu kết quả đo lường của tất cả candidate, "
        "đường cong bitrate–quality, và các KPI so sánh."
    )
    add_placeholder(doc, "[HÌNH 3.0. Sơ đồ mô hình đầu vào–đầu ra – CÓ THỂ NHÚNG "
                          "d:\\DPT\\per-title-encoding\\docs\\chapter23_figures\\fig_3_0_io.png]")

    add_heading(doc, "3.1.2. Các mục tiêu cần cân bằng", 3)
    add_body(doc,
        "Bài toán lựa chọn ladder cần cân bằng đồng thời bốn mục tiêu:"
    )
    add_bullet(doc, [
        "Tối đa hóa chất lượng hình ảnh (VMAF) tại mỗi rung.",
        "Tối thiểu hóa bitrate (và dung lượng) tại mỗi mức chất lượng.",
        "Bảo đảm độ bao phủ chất lượng đủ rộng cho các điều kiện mạng khác nhau.",
        "Giữ số lượng rung không vượt quá giới hạn thực tế (tối đa 4 rung trong đề tài)."
    ])
    add_body(doc,
        "Bốn mục tiêu này có thể mâu thuẫn: tăng số rung cải thiện độ bao phủ nhưng tăng "
        "chi phí encode và lưu trữ; tăng bitrate cải thiện chất lượng nhưng tăng dung lượng. "
        "Quy tắc lựa chọn ladder đề xuất ở Mục 3.9 xử lý các mâu thuẫn này thông qua "
        "ràng buộc thiết kế."
    )

    add_heading(doc, "3.1.3. Giả định và giới hạn của bài toán", 3)
    add_bullet(doc, [
        "Codec duy nhất: H.264/AVC (libx264). Kết quả không áp dụng trực tiếp cho các codec khác.",
        "Không upscale: candidate có độ phân giải lớn hơn video nguồn bị loại tự động.",
        "VMAF là chỉ số chất lượng chính. PSNR và SSIM chỉ là chỉ số phụ.",
        "Single-pass VBR: không dùng two-pass để giảm thời gian encode trong demo.",
        "Không có audio trong encode: pipeline chỉ đánh giá video track.",
        "Một video thử nghiệm chính: kết quả là minh họa nguyên lý, không phải thống kê tổng quát.",
        "Demo quy mô nhỏ: không triển khai HLS/DASH packaging, không adaptive streaming thực tế.",
        "Per-Shot Encoding không được triển khai: đề tài chỉ thực hiện Per-Title Encoding."
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # 3.2
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "3.2. Video thử nghiệm và không gian candidate", 2)

    add_heading(doc, "3.2.1. Lựa chọn video thử nghiệm", 3)
    add_body(doc,
        "Video thử nghiệm chính của demo là một video ngắn khoảng 10–30 giây. Đề tài ưu "
        "tiên lựa chọn video có đặc điểm nội dung điển hình (không quá đơn giản cũng không "
        "quá cực đoan) để kết quả phân tích có tính đại diện cho nguyên lý."
    )

    add_table_title(doc, "Bảng 3.1. Đặc điểm video thử nghiệm chính")
    make_table(doc,
        headers=["Thuộc tính", "Giá trị"],
        rows=[
            ["Tên file", "[ĐIỀN THÔNG SỐ THỰC NGHIỆM]"],
            ["Định dạng container", "[ĐIỀN THÔNG SỐ THỰC NGHIỆM]"],
            ["Codec nguồn", "[ĐIỀN THÔNG SỐ THỰC NGHIỆM]"],
            ["Độ phân giải (W×H)", "[ĐIỀN THÔNG SỐ THỰC NGHIỆM]"],
            ["Frame rate", "[ĐIỀN THÔNG SỐ THỰC NGHIỆM]"],
            ["Thời lượng", "[ĐIỀN THÔNG SỐ THỰC NGHIỆM]"],
            ["Nội dung", "[ĐIỀN THÔNG SỐ THỰC NGHIỆM]"],
            ["Lý do lựa chọn", "[ĐIỀN THÔNG SỐ THỰC NGHIỆM]"],
        ],
        col_widths=[7, 10]
    )
    add_note(doc, "Lưu ý: Các trường [ĐIỀN THÔNG SỐ THỰC NGHIỆM] cần bổ sung sau khi "
                  "xác định video thực tế sử dụng trong demo. Không tự điền số liệu giả định.")
    add_body(doc,
        "Ngoài video chính, đề tài có thể thực hiện thực nghiệm bổ sung trên các video "
        "khác (ví dụ: testsrc, smptebars, testsrc2 do FFmpeg sinh ra) để minh họa sự "
        "khác biệt về đặc điểm nội dung. Các thực nghiệm này được ghi nhận là thực nghiệm "
        "mở rộng và không phải phân tích chính."
    )

    add_heading(doc, "3.2.2. Xây dựng không gian candidate", 3)
    add_body(doc,
        "Trong đề tài, một candidate được định nghĩa là một tổ hợp (độ phân giải, bitrate "
        "mục tiêu) xác định một phiên bản encode cụ thể. Không gian candidate là tập hợp "
        "tất cả các candidate được xem xét, được xây dựng dưới dạng lưới "
        "Resolution × Bitrate."
    )
    add_body(doc,
        "Nguyên tắc lựa chọn candidate: (1) các độ phân giải bao phủ từ thấp đến cao, "
        "phủ khoảng bitrate thực tế của các thiết bị và điều kiện mạng phổ biến; (2) với "
        "mỗi độ phân giải, khảo sát nhiều mức bitrate để có đủ điểm xây dựng đường cong "
        "bitrate–quality; (3) không upscale – độ phân giải của candidate không được vượt "
        "độ phân giải video nguồn; (4) các tổ hợp (độ phân giải, bitrate) phải thực tế, "
        "tránh các tổ hợp rõ ràng vô lý (bitrate quá thấp cho độ phân giải quá cao)."
    )

    add_table_title(doc, "Bảng 3.2. Không gian candidate được định nghĩa trong cấu hình đề tài")
    make_table(doc,
        headers=["Height", "Bitrate mục tiêu (kbps)", "Số candidate", "Ghi chú"],
        rows=[
            ["360p", "250 / 365 / 500 / 700", "4", "Bị loại nếu nguồn < 360p"],
            ["432p", "500 / 730 / 1 000 / 1 500", "4", "Theo Apple HLS spec"],
            ["720p", "1 000 / 1 500 / 2 000 / 3 000", "4", "Bị loại nếu nguồn < 720p"],
            ["1080p", "2 000 / 3 000 / 4 500 / 6 000", "4", "Bị loại nếu nguồn < 1080p"],
            ["Tổng tối đa", "—", "16", "Phụ thuộc độ phân giải nguồn"],
        ],
        col_widths=[3, 7, 4, 6.5]
    )
    add_body(doc,
        "Chiều rộng (width) của mỗi candidate được tính tự động giữ nguyên tỉ lệ khung "
        "(aspect ratio) của video nguồn. Cả width và height đều được làm tròn xuống số chẵn "
        "để tương thích với pixel format yuv420p. Tên candidate có dạng: "
        "{height}p_{bitrate}k, ví dụ: 720p_2000k."
    )

    add_table_title(doc, "Bảng 3.3. Các tham số encoding của candidate")
    make_table(doc,
        headers=["Tham số", "Giá trị", "Loại"],
        rows=[
            ["Codec", "libx264 (H.264/AVC)", "Cố định"],
            ["Preset", "veryfast", "Cố định"],
            ["Pixel format", "yuv420p", "Cố định"],
            ["Keyframe interval", "2.0 giây (g = fps × 2)", "Cố định"],
            ["sc_threshold", "0 (tắt scene cut tự động)", "Cố định"],
            ["Two-pass", "Không (single-pass VBR)", "Cố định"],
            ["Audio", "Tắt (-an)", "Cố định"],
            ["Chiều cao (height)", "360 / 432 / 720 / 1080p", "Thay đổi"],
            ["Bitrate mục tiêu", "250 – 6 000 kbps", "Thay đổi"],
            ["Bufsize", "2 × bitrate mục tiêu", "Phái sinh từ bitrate"],
        ],
        col_widths=[5, 7, 4.5]
    )

    # ══════════════════════════════════════════════════════════════════════════
    # 3.3
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "3.3. Thiết lập điều kiện thực nghiệm", 2)

    add_heading(doc, "3.3.1. Biến được kiểm soát (Controlled Variables)", 3)
    add_body(doc,
        "Để bảo đảm kết quả đo lường phản ánh đúng ảnh hưởng của độ phân giải và bitrate, "
        "các biến sau đây được giữ cố định trong toàn bộ thực nghiệm:"
    )
    add_bullet(doc, [
        "Video nguồn: cùng một file video đầu vào cho tất cả candidate và baseline.",
        "Codec và encoder: libx264 (H.264/AVC) với cùng bộ tham số.",
        "Preset: veryfast – kiểm soát tốc độ/chất lượng của encoder.",
        "Pixel format: yuv420p – định dạng màu chuẩn cho video web.",
        "Keyframe interval: 2.0 giây – bảo đảm cùng cấu trúc GOP.",
        "Phương pháp đo VMAF: cùng mô hình vmaf_v0.6.1, cùng thuật toán upscale bicubic.",
        "Điều kiện hệ thống: cùng môi trường phần cứng và phần mềm."
    ])

    add_heading(doc, "3.3.2. Biến thực nghiệm (Experimental Variables)", 3)
    add_body(doc,
        "Chỉ hai biến sau đây thay đổi giữa các candidate:"
    )
    add_bullet(doc, [
        "Độ phân giải mục tiêu (target height): 360p / 432p / 720p / 1080p.",
        "Bitrate mục tiêu (target bitrate): 250 kbps đến 6000 kbps theo bảng candidate."
    ])
    add_body(doc,
        "Tất cả sự khác biệt trong kết quả VMAF và bitrate thực tế giữa các candidate "
        "đều là hệ quả của hai biến này, không phải của bất kỳ sự khác biệt nào trong "
        "cấu hình encoder."
    )

    add_heading(doc, "3.3.3. Điều kiện đo lường", 3)
    add_body(doc,
        "Với mỗi candidate, ba giá trị được đo và ghi nhận: (1) bitrate thực tế sau encode "
        "(đo bằng FFprobe từ file output); (2) kích thước file thực tế (byte); (3) điểm "
        "VMAF (đo bằng FFmpeg filter libvmaf với upscale bicubic về độ phân giải nguồn). "
        "Điểm PSNR và SSIM cũng được đo như chỉ số phụ. Không đo MOS chủ quan."
    )
    add_body(doc,
        "Biến bitrate thực tế và target bitrate được ghi nhận riêng biệt. Phân tích "
        "đường cong bitrate–quality sử dụng bitrate thực tế (không phải target) để phản "
        "ánh đúng đặc tính của file encode."
    )

    # ══════════════════════════════════════════════════════════════════════════
    # 3.4
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "3.4. Quy trình chuẩn hóa video đầu vào", 2)
    add_body(doc,
        "Trước khi encode, video đầu vào được kiểm tra và chuẩn hóa để bảo đảm tính nhất "
        "quán. Bước này sử dụng FFprobe để trích xuất metadata của video nguồn."
    )
    add_body(doc,
        "Các thông tin được kiểm tra: độ phân giải (width × height), frame rate thực tế, "
        "thời lượng, codec nguồn và pixel format. Các thông tin này cần thiết cho: (1) loại "
        "bỏ candidate có độ phân giải vượt nguồn (tránh upscale); (2) tính chính xác "
        "keyframe interval theo fps thực tế; (3) đặt tham số upscale khi đo VMAF về "
        "đúng độ phân giải nguồn."
    )
    add_body(doc,
        "Pixel format yuv420p được cố định trong encode, không phụ thuộc vào pixel format "
        "của video nguồn. Điều này bảo đảm tính tương thích với decoder phổ thông và với "
        "filter libvmaf. Nếu video nguồn có pixel format khác (ví dụ: yuv444p), FFmpeg sẽ "
        "tự động chuyển đổi trong quá trình encode."
    )
    add_body(doc,
        "Đề tài không thực hiện các bước chuẩn hóa phức tạp hơn như deinterlacing, "
        "color space conversion hay trim/cut vì video thử nghiệm đã ở định dạng phù hợp. "
        "Nếu video nguồn có định dạng đặc biệt, cần bổ sung các bước này trước khi đưa "
        "vào pipeline."
    )

    # ══════════════════════════════════════════════════════════════════════════
    # 3.5
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "3.5. Quy trình encode và đo lường candidate bằng FFmpeg", 2)
    add_body(doc,
        "Đây là bước tốn nhiều thời gian nhất trong pipeline và tạo ra tập dữ liệu cốt "
        "lõi cho toàn bộ phân tích. Mỗi candidate được encode và đo lường độc lập."
    )

    add_heading(doc, "3.5.1. Cấu trúc lệnh FFmpeg encode", 3)
    add_body(doc,
        "Mỗi candidate được encode bằng một lệnh FFmpeg với cấu trúc sau:"
    )
    add_body(doc,
        "Bước 1: Đọc video nguồn (-i source.mp4). "
        "Bước 2: Áp dụng scale filter: -vf scale=W:H:flags=bicubic (trong đó W, H là kích "
        "thước candidate, tính từ height giữ tỉ lệ khung nguồn). "
        "Bước 3: Thiết lập codec: -c:v libx264 -preset veryfast. "
        "Bước 4: Thiết lập bitrate: -b:v Bk -maxrate Bk -bufsize 2Bk (trong đó B là target "
        "bitrate kbps). "
        "Bước 5: Thiết lập keyframe: -g GOP -keyint_min GOP -sc_threshold 0 "
        "(GOP = round(fps × 2.0)). "
        "Bước 6: Thiết lập pixel format: -pix_fmt yuv420p -an (không audio). "
        "Bước 7: Ghi file đầu ra."
    )
    add_body(doc,
        "Tham số -maxrate bằng -b:v biến encode thành chế độ CBR-like trong FFmpeg: "
        "encoder cố gắng không vượt quá maxrate, với bộ đệm bufsize để hấp thụ biến động. "
        "Thực tế, single-pass với bufsize = 2× bitrate cho phép biến động nhất định."
    )

    add_heading(doc, "3.5.2. Bitrate mục tiêu và bitrate thực tế", 3)
    add_body(doc,
        "Sau khi encode, bitrate thực tế được đo bằng FFprobe từ file output. Nếu FFprobe "
        "trả về bit_rate của video stream, giá trị đó được dùng trực tiếp. Nếu không, "
        "bitrate được ước tính từ kích thước file và thời lượng:"
    )
    add_formula(doc,
        "Bitrate_actual (kbps) = file_size_bytes × 8 / duration_seconds / 1000", "(3.1)"
    )
    add_body(doc,
        "Trong thực tế, bitrate thực tế thường lệch so với target bitrate, đặc biệt với "
        "video ngắn (< 10 giây), video có đặc điểm nội dung đặc biệt, hoặc khi target "
        "bitrate rất thấp. Lệch này là bình thường và phải được ghi nhận. Phân tích đường "
        "cong bitrate–quality luôn sử dụng bitrate thực tế."
    )

    add_heading(doc, "3.5.3. Đo VMAF với video tham chiếu", 3)
    add_body(doc,
        "Sau khi có file encode của mỗi candidate, VMAF được đo bằng FFmpeg filter "
        "libvmaf. Quy trình đo:"
    )
    add_body(doc,
        "Input 1 (distorted): file encoded candidate. "
        "Input 2 (reference): video nguồn gốc. "
        "Filter complex: upscale encoded lên độ phân giải nguồn bằng bicubic, sau đó tính libvmaf. "
        "Cú pháp filter: [0:v]scale=W_ref:H_ref:flags=bicubic,setsar=1[d]; "
        "[1:v]setsar=1[r]; [d][r]libvmaf=model=version=vmaf_v0.6.1:n_threads=4. "
        "Output: FFmpeg in ra 'VMAF score: X.xx' trong stderr, pipeline parse giá trị này."
    )
    add_body(doc,
        "Cùng pipeline đo PSNR và SSIM với filter psnr và ssim tương ứng. "
        "Nếu parse VMAF thất bại (không có 'VMAF score:' trong output), pipeline báo lỗi "
        "và dừng – không bịa đặt hay ước tính điểm VMAF."
    )

    add_heading(doc, "3.5.4. Cấu trúc dữ liệu kết quả mỗi candidate", 3)
    add_body(doc,
        "Sau encode và đo lường, mỗi candidate tạo ra một bản ghi (record) gồm:"
    )
    add_table_title(doc, "Bảng 3.4. Các trường dữ liệu kết quả của mỗi candidate")
    make_table(doc,
        headers=["Trường dữ liệu", "Mô tả", "Đơn vị"],
        rows=[
            ["rung_name", "Tên candidate (vd: 720p_2000k)", "—"],
            ["height", "Chiều cao encode thực tế", "pixel"],
            ["width", "Chiều rộng encode thực tế", "pixel"],
            ["target_bitrate_kbps", "Bitrate mục tiêu cấu hình", "kbps"],
            ["actual_bitrate_kbps", "Bitrate thực tế đo bằng FFprobe", "kbps"],
            ["size_bytes", "Kích thước file encode", "byte"],
            ["vmaf", "Điểm VMAF trung bình", "0–100"],
            ["psnr", "Điểm PSNR trung bình (phụ)", "dB"],
            ["ssim", "Điểm SSIM trung bình (phụ)", "0–1"],
            ["encode_seconds", "Thời gian encode", "giây"],
            ["output_file", "Đường dẫn file encode", "—"],
        ],
        col_widths=[5.5, 6, 3]
    )
    add_body(doc,
        "Toàn bộ kết quả được lưu vào file CSV và JSON để phân tích ở các bước tiếp theo. "
        "Tên file đầu ra có cấu trúc: {video_stem}_{method}_{rung_name}_{bitrate}k.mp4."
    )

    # Pseudocode
    add_body(doc, "Pseudocode quy trình encode và đo lường candidate:")
    add_body(doc,
        "FOREACH candidate IN candidate_list:\n"
        "    IF candidate.height > source.height: SKIP  # không upscale\n"
        "    width, height = scale_keep_aspect(candidate.height, source)\n"
        "    encoded_file = ffmpeg_encode(source, width, height, candidate.bitrate_kbps)\n"
        "    actual_bitrate = ffprobe_bitrate(encoded_file)\n"
        "    file_size = file_size_bytes(encoded_file)\n"
        "    vmaf, psnr, ssim = ffmpeg_measure_quality(encoded_file, source)\n"
        "    record = RQPoint(actual_bitrate, vmaf, height, width, ...)\n"
        "    results.append(record)\n"
        "SAVE results to CSV/JSON",
        first_indent=False
    )

    # ══════════════════════════════════════════════════════════════════════════
    # 3.6
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "3.6. Phân tích đặc điểm nội dung bằng SI/TI", 2)
    add_body(doc,
        "Phân tích SI/TI được thực hiện trên video nguồn, song song hoặc trước quá trình "
        "encode candidate. Bước này cung cấp context mô tả đặc điểm nội dung video."
    )

    add_heading(doc, "3.6.1. Quy trình tính SI và TI", 3)
    add_body(doc,
        "Bước 1 – Trích xuất khung hình: dùng FFmpeg pipe để decode video nguồn và trích "
        "xuất các khung grayscale tại tốc độ lấy mẫu 2.0 fps, thu nhỏ về chiều rộng 320 pixel "
        "(giữ tỉ lệ khung). Tối đa 40 khung được sử dụng. Dữ liệu khung được đọc trực tiếp "
        "từ stdout của FFmpeg dạng rawvideo pipe."
    )
    add_body(doc,
        "Bước 2 – Tính SI từng khung: với mỗi khung F, áp dụng bộ lọc Sobel (công thức "
        "2.2a–2.2d ở Chương 2) để tính SI(F) = σ(G). Kết quả là một danh sách giá trị SI "
        "theo thứ tự thời gian."
    )
    add_body(doc,
        "Bước 3 – Tính TI từng cặp khung: với mỗi cặp (F_{n-1}, F_n), tính "
        "TI(F_n) = σ(F_n − F_{n-1}) theo công thức (2.3). Kết quả là danh sách giá trị TI "
        "với độ dài ít hơn danh sách SI một phần tử."
    )
    add_body(doc,
        "Bước 4 – Tổng hợp: lấy trung vị (median) của danh sách SI để có SI_median; "
        "lấy trung vị của danh sách TI để có TI_median. Trung vị được chọn thay vì giá trị "
        "lớn nhất để giảm ảnh hưởng của các khung bất thường (scene cut, artifact)."
    )
    add_body(doc,
        "Bước 5 – Tính complexity index: theo công thức (2.4):"
    )
    add_formula(doc,
        "CI = clip(0.55 × (SI_median / 80.0) + 0.45 × (TI_median / 40.0), 0, 1.5)", "(3.2)"
    )
    add_body(doc,
        "Bước 6 – Phân loại: dựa trên CI, video được phân loại là 'easy' (CI < 0.35), "
        "'medium' (0.35 ≤ CI < 0.65) hoặc 'hard' (CI ≥ 0.65). Phân loại này chỉ được dùng "
        "cho phương pháp heuristic (k × fixed), không dùng trong phương pháp hull-based chính."
    )

    add_heading(doc, "3.6.2. Sử dụng kết quả SI/TI trong phân tích", 3)
    add_body(doc,
        "Kết quả SI/TI được sử dụng theo hai cách: (1) Mô tả đặc điểm video: SI_median "
        "và TI_median được báo cáo cùng với kết quả để giải thích tại sao video cần "
        "nhiều hoặc ít bitrate hơn; (2) Đối chiếu giữa các video: nếu thực nghiệm có nhiều "
        "video, SI/TI giúp giải thích sự khác biệt trong đường cong bitrate–quality giữa "
        "các video."
    )
    add_body(doc,
        "Quan trọng: SI/TI không tự động sinh bitrate ladder. Trong phương pháp hull-based "
        "per-title (phương pháp chính), ladder được lựa chọn hoàn toàn dựa trên dữ liệu "
        "(R, Q) thực đo. SI/TI chỉ là metadata mô tả, không can thiệp vào quy trình "
        "lựa chọn này."
    )

    # ══════════════════════════════════════════════════════════════════════════
    # 3.7
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "3.7. Phương pháp xây dựng đường cong bitrate–quality", 2)
    add_body(doc,
        "Sau khi encode và đo lường tất cả candidate, tập dữ liệu kết quả được sử dụng "
        "để xây dựng đường cong bitrate–quality."
    )
    add_body(doc,
        "Mỗi candidate tạo ra một điểm (R, Q) trong không gian hai chiều, trong đó "
        "R = actual_bitrate_kbps (trục X) và Q = vmaf (trục Y). Tập hợp tất cả điểm "
        "này tạo thành đám mây điểm candidate."
    )
    add_body(doc,
        "Để phân tích đường cong, các điểm được nhóm theo độ phân giải. Với mỗi nhóm "
        "độ phân giải, các điểm được sắp xếp theo R tăng dần và nối thành đường cong. "
        "Xu hướng của đường cong thể hiện: chất lượng tăng dần khi bitrate tăng, với "
        "tốc độ giảm dần ở vùng bitrate cao (diminishing returns, Mục 2.5.2)."
    )
    add_body(doc,
        "Trên biểu đồ, các nhóm độ phân giải được phân biệt bằng màu sắc khác nhau. "
        "Biểu đồ này là công cụ trực quan chính để: (1) nhận biết vùng bitrate hợp lý "
        "của mỗi độ phân giải; (2) so sánh hiệu quả giữa các độ phân giải tại cùng bitrate; "
        "(3) xác định candidate tiềm năng cho ladder."
    )
    add_body(doc,
        "Trục X sử dụng thang logarithm nếu khoảng bitrate quá rộng (từ 250 kbps đến "
        "6000 kbps) để phân bố đều các điểm. Trục Y là thang tuyến tính từ 0 đến 100."
    )

    # ══════════════════════════════════════════════════════════════════════════
    # 3.8
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "3.8. Pareto filtering và phân tích Upper Convex Hull", 2)
    add_body(doc,
        "Đây là bước lọc và phân tích để thu hẹp không gian ứng cử viên từ tất cả "
        "candidate xuống còn các điểm hiệu quả nhất, làm đầu vào cho bước lựa chọn ladder."
    )

    add_heading(doc, "3.8.1. Xác định và loại bỏ candidate bị chi phối", 3)
    add_body(doc,
        "Với tập dữ liệu tất cả candidate (danh sách các điểm RQPoint), thuật toán "
        "remove_dominated_points được áp dụng theo định nghĩa Pareto dominance (công thức "
        "2.5 ở Chương 2). Cụ thể, với mỗi candidate A, kiểm tra xem có tồn tại candidate "
        "B nào thỏa mãn đồng thời: R_B ≤ R_A AND Q_B ≥ Q_A AND (R_B < R_A OR Q_B > Q_A) "
        "hay không. Nếu có, A bị coi là dominated và bị loại khỏi Pareto frontier."
    )
    add_body(doc,
        "Độ phức tạp của bước này là O(n²) với n là số candidate. Với n = 16 candidate "
        "(hoặc ít hơn tùy độ phân giải nguồn), độ phức tạp này hoàn toàn chấp nhận được "
        "trong quy mô demo."
    )

    add_heading(doc, "3.8.2. Xây dựng Pareto frontier", 3)
    add_body(doc,
        "Sau bước loại bỏ, các điểm còn lại (không bị chi phối bởi bất kỳ điểm nào) "
        "tạo thành Pareto frontier. Pareto frontier được sắp xếp theo bitrate tăng dần. "
        "Dữ liệu Pareto frontier được ghi nhận và biểu diễn trên biểu đồ riêng, phân biệt "
        "với các điểm bị loại."
    )
    add_body(doc,
        "Pareto frontier là kết quả của bước lọc, không phải là ladder. Số điểm trên "
        "Pareto frontier có thể nhiều hơn số rung cần thiết trong ladder. Bước tiếp theo "
        "thu hẹp Pareto frontier thêm bằng upper convex hull."
    )

    add_heading(doc, "3.8.3. Phân tích Upper Convex Hull", 3)
    add_body(doc,
        "Upper convex hull được tính trên Pareto frontier bằng thuật toán monotone chain "
        "(Mục 2.6.2). Bước này loại bỏ các điểm trên Pareto frontier nhưng không nằm "
        "trên đường bao lồi phía trên."
    )
    add_body(doc,
        "Các điểm bị loại ở bước này (nằm trên Pareto frontier nhưng không trên UCH) là "
        "các điểm 'lõm': có thể là non-dominated nhưng không nằm ở những đánh đổi hiệu "
        "quả nhất. Trong thực tế, việc chọn những điểm này vào ladder sẽ tạo ra rung có "
        "chất lượng tăng chậm hơn mức kỳ vọng nếu nội suy tuyến tính."
    )
    add_body(doc,
        "Sau bước này, tập hợp các điểm UCH là đầu vào cho bước lựa chọn ladder cuối cùng. "
        "Lưu ý: UCH chứa ít điểm hơn Pareto frontier; Pareto frontier chứa ít điểm hơn "
        "toàn bộ candidate ban đầu."
    )
    add_body(doc,
        "Toàn bộ luồng: All Candidates → Pareto Filtering → Pareto Frontier → "
        "Upper Convex Hull → Hull Points → Ladder Selection"
    )

    # ══════════════════════════════════════════════════════════════════════════
    # 3.9
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "3.9. Quy tắc lựa chọn bitrate ladder đề xuất (Hull-Based Selection)", 2)
    add_body(doc,
        "Đây là bước trung tâm của phương pháp per-title. Từ tập hợp các điểm UCH, "
        "quy tắc lựa chọn hull-based per-title xác định ladder cuối cùng L* theo các "
        "ràng buộc được cấu hình trong đề tài. Phương pháp này được gọi là "
        "'Hull-Based Per-Title Ladder Selection' – không phải tối ưu toàn cục, không "
        "phải tiêu chuẩn chính thức của bất kỳ tổ chức nào."
    )

    add_heading(doc, "3.9.1. Mục tiêu lựa chọn", 3)
    add_bullet(doc, [
        "Duy trì chất lượng hình ảnh đủ tốt tại mỗi rung (VMAF ≥ ngưỡng tối thiểu).",
        "Giảm bitrate không cần thiết (loại bỏ các rung lãng phí bit).",
        "Bảo đảm độ bao phủ chất lượng từ thấp đến cao.",
        "Giới hạn số rung ≤ 4 (max_representations).",
        "Không đưa rung có độ phân giải cao hơn video nguồn vào ladder."
    ])

    add_heading(doc, "3.9.2. Các ràng buộc lựa chọn", 3)
    add_table_title(doc, "Bảng 3.5. Các ràng buộc lựa chọn ladder trong cấu hình đề tài")
    make_table(doc,
        headers=["Ràng buộc", "Giá trị cấu hình", "Ý nghĩa"],
        rows=[
            ["max_representations", "4", "Tối đa 4 rung trong ladder"],
            ["min_vmaf", "0", "Không lọc theo VMAF tối thiểu trong demo"],
            ["prefer_one_per_height", "True", "Mỗi độ phân giải chọn tối đa 1 đại diện"],
            ["Bitrate tăng dần", "Nghiêm ngặt", "Bitrate mỗi rung phải > bitrate rung trước"],
        ],
        col_widths=[5.5, 5, 7]
    )

    add_heading(doc, "3.9.3. Quy trình lựa chọn từng bước", 3)
    add_body(doc,
        "Bước 1 – Lọc theo VMAF tối thiểu: loại bỏ điểm UCH có VMAF < min_vmaf. "
        "Nếu sau lọc không còn điểm nào, dùng toàn bộ UCH."
    )
    add_body(doc,
        "Bước 2 – Chọn đại diện mỗi height (nếu prefer_one_per_height = True): "
        "Nhóm các điểm UCH theo height. Với mỗi nhóm height, chọn điểm có VMAF cao nhất; "
        "nếu bằng VMAF, chọn điểm có bitrate thấp hơn (tối ưu bitrate). "
        "Kết quả: tối đa một đại diện mỗi độ phân giải."
    )
    add_body(doc,
        "Bước 3 – Sắp xếp theo height tăng dần, sau đó bitrate tăng dần."
    )
    add_body(doc,
        "Bước 4 – Lọc monotonic bitrate: duyệt tuần tự các điểm đã sắp xếp. Chỉ giữ "
        "điểm có bitrate > bitrate của điểm được chọn trước đó. Bước này bảo đảm ladder "
        "có bitrate tăng dần nghiêm ngặt."
    )
    add_body(doc,
        "Bước 5 – Giới hạn số rung: nếu số điểm còn lại > max_representations, chọn "
        "max_representations điểm phân bố đều theo chỉ số (dùng phép nội suy đều): "
        "chọn các chỉ số i = round(j × (n-1) / (max_reps-1)) với j = 0, 1, ..., max_reps-1."
    )
    add_body(doc,
        "Kết quả: danh sách LadderRung với source='hull', chứa các thông tin: name, "
        "width, height, bitrate_kbps (target bitrate của điểm UCH tương ứng)."
    )

    add_heading(doc, "3.9.4. Xây dựng và kiểm tra ladder cuối cùng", 3)
    add_body(doc,
        "Sau khi có danh sách rung, ladder được kiểm tra tính hợp lệ:"
    )
    add_bullet(doc, [
        "Không có rung nào có width hoặc height lẻ (yêu cầu của yuv420p).",
        "Không có rung nào có độ phân giải vượt video nguồn.",
        "Bitrate của tất cả rung nằm trong khoảng [min_bitrate_kbps, max_bitrate_kbps].",
        "Bitrate tăng dần nghiêm ngặt qua các rung.",
        "Số rung ≥ 1 (ladder không rỗng)."
    ])
    add_body(doc,
        "Nếu có rung nào vi phạm, pipeline báo lỗi. Không tự động 'sửa' ladder mà "
        "không ghi nhận. Kết quả ladder cuối cùng được lưu cùng với tập dữ liệu kết quả."
    )

    add_heading(doc, "3.9.5. Phân biệt với phương pháp heuristic k × fixed", 3)
    add_body(doc,
        "Đề tài cũng xây dựng một ladder thứ ba theo phương pháp heuristic: nhân bitrate "
        "của fixed ladder với hệ số k (k = 0.65 nếu video 'easy', k = 1.0 nếu 'medium', "
        "k = 1.35 nếu 'hard'). Hệ số k được xác định từ complexity index CI (tính từ SI/TI). "
        "Phương pháp này được giữ để đối chiếu, không phải phương pháp đề xuất. Ladder "
        "heuristic không sử dụng VMAF và không phân tích đường cong bitrate–quality."
    )

    # ══════════════════════════════════════════════════════════════════════════
    # 3.10
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "3.10. Xây dựng bitrate ladder cố định làm baseline", 2)
    add_body(doc,
        "Để đánh giá hiệu quả của ladder đề xuất, cần một baseline rõ ràng và nhất quán. "
        "Baseline trong đề tài là fixed ladder – ladder cố định không phụ thuộc nội dung."
    )
    add_body(doc,
        "Fixed ladder được lấy từ bảng cấu hình tham khảo theo Apple HLS Authoring "
        "Specification (rút gọn). Cấu hình fixed ladder trong đề tài:"
    )
    add_table_title(doc, "Bảng 3.6. Cấu hình bitrate ladder cố định (baseline)")
    make_table(doc,
        headers=["Tên rung", "Height", "Bitrate mục tiêu (kbps)", "Ghi chú"],
        rows=[
            ["360p", "360", "365", "Rung thấp nhất"],
            ["432p", "432", "730", "Theo Apple HLS 768×432 @ 730 kbps"],
            ["720p", "720", "3 000", "Rung trung bình cao"],
            ["1080p", "1080", "6 000", "Rung cao nhất"],
        ],
        col_widths=[3.5, 3, 5.5, 5.5]
    )
    add_body(doc,
        "Tương tự candidate, các rung có height lớn hơn video nguồn bị loại tự động "
        "khỏi fixed ladder (không upscale). Do đó, nếu video nguồn là 720p, fixed ladder "
        "chỉ có 3 rung: 360p, 432p, 720p."
    )
    add_body(doc,
        "Để so sánh công bằng, các rung của fixed ladder cũng được encode và đo VMAF "
        "theo cùng quy trình FFmpeg như candidate, cùng điều kiện và cùng video nguồn. "
        "Kết quả của fixed ladder được lưu riêng với nhãn source='fixed'."
    )
    add_body(doc,
        "Mục đích của baseline: đây là cơ sở để tính toán bitrate saving và ΔVMAF. "
        "Không phải mọi hệ thống thực tế đều dùng ladder này; đây chỉ là điểm tham chiếu "
        "phù hợp với quy mô demo và mục đích minh họa nguyên lý Per-Title Encoding."
    )

    # ══════════════════════════════════════════════════════════════════════════
    # 3.11
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "3.11. Phương pháp so sánh và đánh giá", 2)
    add_body(doc,
        "Sau khi có kết quả encode và đo lường của cả hai ladder (đề xuất và baseline), "
        "phần này mô tả các phép so sánh được thực hiện để đánh giá hiệu quả tối ưu hóa."
    )

    add_heading(doc, "3.11.1. So sánh bitrate tại chất lượng tương đương", 3)
    add_body(doc,
        "Chọn một mức VMAF tham chiếu Q_ref nằm trong khoảng VMAF chung của cả hai "
        "ladder. Xác định bitrate R_baseline cần để đạt Q_ref từ fixed ladder và "
        "R_proposed cần để đạt Q_ref từ ladder đề xuất. Nếu không có rung nào có chính "
        "xác Q_ref, thực hiện nội suy tuyến tính giữa hai rung liền kề. Tính bitrate "
        "saving theo công thức (2.6). Ghi nhận rõ Q_ref và phương pháp nội suy được sử dụng."
    )

    add_heading(doc, "3.11.2. So sánh chất lượng tại bitrate tương đương", 3)
    add_body(doc,
        "Chọn một mức bitrate tham chiếu R_ref nằm trong khoảng bitrate chung của cả "
        "hai ladder. Xác định VMAF_baseline và VMAF_proposed tương ứng (dùng nội suy "
        "tuyến tính nếu cần). Tính ΔVMAF theo công thức (2.7). Ghi nhận R_ref và "
        "phương pháp được sử dụng."
    )

    add_heading(doc, "3.11.3. So sánh dung lượng và số lượng rung", 3)
    add_body(doc,
        "Với mỗi rung trong cả hai ladder, liệt kê và so sánh: kích thước file encode "
        "(bytes/MB), tổng dung lượng ladder (tổng tất cả rung), số lượng rung và "
        "khoảng VMAF bao phủ. Các so sánh này được trình bày bằng bảng và biểu đồ "
        "bar chart để dễ đọc."
    )

    add_heading(doc, "3.11.4. Phân tích trường hợp kết quả không cải thiện rõ rệt", 3)
    add_body(doc,
        "Không phải lúc nào ladder đề xuất cũng tốt hơn baseline. Một số trường hợp "
        "có thể xảy ra và cần được phân tích trung thực:"
    )
    add_bullet(doc, [
        "Candidate không đủ dày: nếu không gian candidate quá thưa, các điểm UCH có "
        "thể không bao phủ đủ vùng bitrate–quality để tạo ladder tốt hơn baseline.",
        "Video đã tương thích với fixed ladder: nếu đặc điểm nội dung video vừa khớp "
        "với các mức bitrate của fixed ladder, ladder đề xuất sẽ gần giống baseline.",
        "Chênh lệch nhỏ không có ý nghĩa thực tế: bitrate saving < 5% hoặc ΔVMAF < 1 "
        "điểm có thể nằm trong sai số đo lường.",
        "Video ngắn gây lệch bitrate: video < 10 giây có thể cho bitrate thực tế lệch "
        "nhiều so với target, ảnh hưởng đến tính chính xác của so sánh."
    ])
    add_body(doc,
        "Không ép kết luận rằng ladder đề xuất luôn tốt hơn baseline. Kết quả thực "
        "nghiệm phải được trình bày trung thực, kể cả khi chênh lệch nhỏ hoặc không "
        "thuận lợi cho phương pháp đề xuất."
    )

    # ══════════════════════════════════════════════════════════════════════════
    # 3.12
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, "3.12. Sơ đồ quy trình nghiên cứu tổng thể", 2)
    add_body(doc,
        "Sơ đồ dưới đây tổng hợp toàn bộ quy trình nghiên cứu từ đầu vào đến đầu ra. "
        "Mỗi bước trong sơ đồ tương ứng với một mục trong chương này. Sơ đồ phân biệt "
        "rõ bước xử lý (hình chữ nhật), bước quyết định (hình thoi) và đầu ra (hình "
        "oval). Các khối màu nền khác nhau phân biệt nhóm bước chính."
    )
    add_placeholder(doc, "[HÌNH 3.1. Flowchart quy trình nghiên cứu tổng thể – CÓ THỂ NHÚNG "
                          "d:\\DPT\\per-title-encoding\\docs\\chapter23_figures\\fig_3_1_flowchart.png]")
    add_body(doc, "Diễn giải các bước trong flowchart:")
    add_table_title(doc, "Bảng 3.7. Giải thích các bước trong flowchart quy trình")
    make_table(doc,
        headers=["Bước", "Tên bước", "Mục tương ứng", "Đầu vào / Đầu ra"],
        rows=[
            ["1", "Nhập video và cấu hình", "3.1", "File video, config.yaml"],
            ["2", "Chuẩn hóa video (probe)", "3.4", "VideoMeta (W, H, fps, duration)"],
            ["3", "Phân tích SI/TI", "3.6", "ComplexityResult (SI, TI, CI, label)"],
            ["4", "Tạo danh sách candidate", "3.2.2", "Danh sách LadderRung candidate"],
            ["5", "Encode từng candidate (FFmpeg)", "3.5.1", "Các file .mp4 encode"],
            ["6", "Đo bitrate thực tế + dung lượng", "3.5.2", "actual_bitrate, size_bytes"],
            ["7", "Đo VMAF (libvmaf qua FFmpeg)", "3.5.3", "vmaf score mỗi candidate"],
            ["8", "Lưu tập dữ liệu (CSV/JSON)", "3.5.4", "RQPoint dataset"],
            ["9", "Xây dựng đường cong R–Q", "3.7", "Biểu đồ bitrate–VMAF"],
            ["10", "Pareto filtering", "3.8.1–3.8.2", "Pareto frontier points"],
            ["11", "Upper Convex Hull", "3.8.3", "Hull points"],
            ["12", "Lựa chọn ladder đề xuất", "3.9", "Hull-based per-title ladder"],
            ["13", "Xây dựng fixed ladder baseline", "3.10", "Fixed ladder rungs + encode"],
            ["14", "So sánh và tính KPI", "3.11", "Bitrate saving, ΔVMAF, file size"],
            ["15", "Xuất kết quả", "—", "CSV, JSON, biểu đồ PNG, báo cáo"],
        ],
        col_widths=[1.5, 5, 3.5, 6.5]
    )
    add_body(doc,
        "Ghi chú về quy trình: bước 3 (phân tích SI/TI) và bước 4 (tạo candidate) có "
        "thể thực hiện song song với nhau và độc lập với bước encode. Bước 13 (encode "
        "fixed ladder) cũng có thể thực hiện song song với bước 4–8 (encode candidate). "
        "Tuy nhiên, trong triển khai demo, các bước được thực hiện tuần tự để đơn giản "
        "hóa logic điều phối."
    )


# ══════════════════════════════════════════════════════════════════════════════
# Content Coverage Matrix
# ══════════════════════════════════════════════════════════════════════════════

def build_coverage_matrix(doc: Document) -> None:
    add_page_break(doc)
    add_heading(doc, "PHỤ LỤC: CONTENT COVERAGE MATRIX", 1)
    add_body(doc,
        "Bảng kiểm tra dưới đây xác nhận toàn bộ yêu cầu nội dung của đề bài (phần IV "
        "và V) đã được phản ánh trong Chương 2 và Chương 3."
    )

    add_table_title(doc, "Bảng A. Content Coverage Matrix – Chương 2 và Chương 3")
    make_table(doc,
        headers=["STT", "Yêu cầu bắt buộc", "Chương", "Mục", "Mức độ"],
        rows=[
            # Nhóm A – Video Encoding
            ["1", "Video encoding (khái niệm, mục đích)", "2", "2.1.1", "Đầy đủ"],
            ["2", "Video compression (lossless/lossy)", "2", "2.1.1", "Đầy đủ"],
            ["3", "Bitrate (khái niệm, công thức, ý nghĩa)", "2", "2.1.2", "Đầy đủ"],
            ["4", "Độ phân giải – Resolution", "2", "2.1.2", "Đầy đủ"],
            ["5", "Frame rate", "2", "2.1.2", "Đầy đủ"],
            ["6", "Codec (khái niệm chung)", "2", "2.1.3", "Đầy đủ"],
            ["7", "H.264/AVC trong phạm vi đề tài", "2", "2.1.3", "Đầy đủ"],
            ["8", "CRF (khái niệm, phân biệt)", "2", "2.1.4", "Đầy đủ"],
            ["9", "CBR, VBR, CRF (phân biệt, ý nghĩa)", "2", "2.1.4", "Đầy đủ"],
            ["10", "Bitrate control (cơ chế)", "2", "2.1.4", "Đầy đủ"],
            ["11", "Quan hệ bitrate–quality–file size", "2", "2.1.5", "Đầy đủ"],
            ["12", "Tham số cố định và thay đổi trong TN", "2", "2.1.6", "Đầy đủ"],
            # Nhóm B – Bitrate Ladder
            ["13", "Representation/rung thang ladder", "2", "2.2.1", "Đầy đủ"],
            ["14", "Quan hệ resolution–bitrate trong rung", "2", "2.2.2", "Đầy đủ"],
            ["15", "Vì sao cần nhiều mức chất lượng", "2", "2.2.3", "Đầy đủ"],
            ["16", "Fixed ladder vs per-title ladder", "2", "2.2.4", "Đầy đủ"],
            # Nhóm C – VMAF
            ["17", "Đánh giá chủ quan và khách quan", "2", "2.3.1", "Đầy đủ"],
            ["18", "VMAF: khái niệm, mục đích, thang điểm", "2", "2.3.2", "Đầy đủ"],
            ["19", "Nguyên lý hoạt động VMAF (VIF, DLM)", "2", "2.3.3", "Đầy đủ"],
            ["20", "Reference video và encoded video", "2", "2.3.3", "Đầy đủ"],
            ["21", "Điều kiện đo VMAF trong đề tài", "2", "2.3.4", "Đầy đủ"],
            ["22", "Ưu điểm VMAF", "2", "2.3.5", "Đầy đủ"],
            ["23", "Giới hạn VMAF", "2", "2.3.5", "Đầy đủ"],
            # Nhóm D – SI/TI
            ["24", "SI: khái niệm, ý nghĩa trực quan", "2", "2.4.1", "Đầy đủ"],
            ["25", "SI: công thức Sobel, giải thích biến", "2", "2.4.1", "Đầy đủ"],
            ["26", "SI: ý nghĩa cao/thấp, giới hạn", "2", "2.4.1", "Đầy đủ"],
            ["27", "TI: khái niệm, ý nghĩa, công thức", "2", "2.4.2", "Đầy đủ"],
            ["28", "TI: ý nghĩa cao/thấp, giới hạn", "2", "2.4.2", "Đầy đủ"],
            ["29", "Vai trò SI/TI trong đề tài (không sinh ladder tự động)", "2", "2.4.3", "Đầy đủ"],
            ["30", "Complexity index (công thức đề xuất)", "2", "2.4.3", "Đầy đủ"],
            # Nhóm E – Rate–Quality
            ["31", "Rate–quality curve: khái niệm, trục X/Y", "2", "2.5.1", "Đầy đủ"],
            ["32", "Xây dựng đường cong từ candidate", "2", "2.5.1", "Đầy đủ"],
            ["33", "Diminishing returns (lợi ích biên giảm dần)", "2", "2.5.2", "Đầy đủ"],
            ["34", "Vai trò đường cong trong phân tích", "2", "2.5.3", "Đầy đủ"],
            # Nhóm F – Pareto và Convex Hull
            ["35", "Pareto dominance (định nghĩa, công thức)", "2", "2.6.1", "Đầy đủ"],
            ["36", "Pareto frontier (khái niệm, cách hình thành)", "2", "2.6.1", "Đầy đủ"],
            ["37", "Upper Convex Hull / upper convex envelope", "2", "2.6.2", "Đầy đủ"],
            ["38", "Phân biệt Pareto filtering ≠ lựa chọn ladder", "2", "2.6.3", "Đầy đủ"],
            # Nhóm G – KPI
            ["39", "Bitrate saving (công thức, giải thích)", "2", "2.8.1", "Đầy đủ"],
            ["40", "ΔVMAF (công thức, điều kiện)", "2", "2.8.2", "Đầy đủ"],
            ["41", "Dung lượng file và số lượng rung", "2", "2.8.3", "Đầy đủ"],
            ["42", "Tiêu chí đánh giá ladder (quality coverage, efficiency…)", "2", "2.7", "Đầy đủ"],
            ["43", "Giới hạn của KPI", "2", "2.8.4", "Đầy đủ"],
            # Chương 3 – Problem Definition
            ["44", "Phát biểu bài toán: input/output/objective", "3", "3.1.1–3.1.2", "Đầy đủ"],
            ["45", "Giả định và giới hạn bài toán", "3", "3.1.3", "Đầy đủ"],
            # Chương 3 – Test Video
            ["46", "Video thử nghiệm chính (10–30s, thông số)", "3", "3.2.1", "Có placeholder"],
            # Chương 3 – Candidate Space
            ["47", "Candidate: định nghĩa, không gian Res×BR", "3", "3.2.2", "Đầy đủ"],
            ["48", "Bảng candidate (height, bitrate, codec)", "3", "3.2.2 / B3.2–3.3", "Đầy đủ"],
            # Chương 3 – Controlled/Variable
            ["49", "Controlled variables", "3", "3.3.1", "Đầy đủ"],
            ["50", "Experimental variables", "3", "3.3.2", "Đầy đủ"],
            ["51", "Điều kiện đo lường", "3", "3.3.3", "Đầy đủ"],
            # Chương 3 – Normalization
            ["52", "Quy trình chuẩn hóa video đầu vào", "3", "3.4", "Đầy đủ"],
            # Chương 3 – FFmpeg Pipeline
            ["53", "Cấu trúc lệnh FFmpeg encode", "3", "3.5.1", "Đầy đủ"],
            ["54", "Target bitrate vs actual bitrate (phân biệt)", "3", "3.5.2", "Đầy đủ"],
            ["55", "Đo VMAF bằng FFmpeg libvmaf", "3", "3.5.3", "Đầy đủ"],
            ["56", "Cấu trúc dữ liệu kết quả RQPoint", "3", "3.5.4 / B3.4", "Đầy đủ"],
            # Chương 3 – SI/TI
            ["57", "Quy trình tính SI/TI trong thực nghiệm", "3", "3.6.1", "Đầy đủ"],
            ["58", "Sử dụng SI/TI để mô tả đặc điểm video", "3", "3.6.2", "Đầy đủ"],
            ["59", "SI/TI không sinh ladder tự động (tái khẳng định)", "3", "3.6.2", "Đầy đủ"],
            # Chương 3 – R–Q Analysis
            ["60", "Xây dựng đường cong R–Q từ dữ liệu thực đo", "3", "3.7", "Đầy đủ"],
            ["61", "Nhóm theo độ phân giải trên biểu đồ", "3", "3.7", "Đầy đủ"],
            # Chương 3 – Pareto & Hull
            ["62", "Pareto filtering: từng bước (dominance check → frontier)", "3", "3.8.1–3.8.2", "Đầy đủ"],
            ["63", "Upper Convex Hull: thuật toán, kết quả", "3", "3.8.3", "Đầy đủ"],
            ["64", "Pareto frontier ≠ final ladder (tái khẳng định)", "3", "3.8.3", "Đầy đủ"],
            # Chương 3 – Ladder Selection
            ["65", "Hull-based per-title: mục tiêu, ràng buộc", "3", "3.9.1–3.9.2", "Đầy đủ"],
            ["66", "Quy trình lựa chọn từng bước (5 bước)", "3", "3.9.3", "Đầy đủ"],
            ["67", "Kiểm tra tính hợp lệ ladder", "3", "3.9.4", "Đầy đủ"],
            ["68", "Phân biệt heuristic k×fixed vs hull-based", "3", "3.9.5", "Đầy đủ"],
            # Chương 3 – Baseline
            ["69", "Fixed ladder baseline: cấu hình, mục đích", "3", "3.10 / B3.6", "Đầy đủ"],
            ["70", "Encode và đo baseline cùng điều kiện", "3", "3.10", "Đầy đủ"],
            # Chương 3 – Comparison
            ["71", "So sánh bitrate tại Q tương đương", "3", "3.11.1", "Đầy đủ"],
            ["72", "So sánh chất lượng tại R tương đương", "3", "3.11.2", "Đầy đủ"],
            ["73", "So sánh dung lượng và số rung", "3", "3.11.3", "Đầy đủ"],
            ["74", "Phân tích trường hợp không cải thiện rõ rệt", "3", "3.11.4", "Đầy đủ"],
            # Chương 3 – Flowchart
            ["75", "Flowchart quy trình nghiên cứu tổng thể", "3", "3.12 / B3.7", "Đầy đủ"],
        ],
        col_widths=[1, 7, 2, 2.5, 3]
    )
    add_body(doc, "Tất cả 75 mục yêu cầu đều được phản ánh. Các mục có nhãn 'Có placeholder' "
                  "cần bổ sung thông số thực nghiệm khi xác định video thực tế.")


# ══════════════════════════════════════════════════════════════════════════════
# References
# ══════════════════════════════════════════════════════════════════════════════

def build_references(doc: Document) -> None:
    add_page_break(doc)
    add_heading(doc, "DANH SÁCH TÀI LIỆU THAM KHẢO CẦN XÁC MINH / BỔ SUNG", 1)
    add_body(doc,
        "Các tài liệu dưới đây được đề cập hoặc liên quan trong Chương 2 và Chương 3. "
        "Cần xác minh thông tin trích dẫn đầy đủ (tác giả, năm, tạp chí/hội nghị, DOI) "
        "trước khi đưa vào danh mục tham khảo chính thức của báo cáo."
    )
    refs = [
        "[1] Li, Z., Aaron, A., Katsavounidis, I., Moorthy, A., Manohara, M. (2016). "
        "Toward a practical perceptual video quality metric. Netflix Tech Blog. "
        "[CẦN XÁC MINH URL VÀ NĂM CHÍNH XÁC]",
        "[2] ITU-T Recommendation P.910 (2008). Subjective video quality assessment methods "
        "for multimedia applications. International Telecommunication Union.",
        "[3] Wiegand, T., Sullivan, G. J., Bjøntegaard, G., & Luthra, A. (2003). "
        "Overview of the H.264/AVC video coding standard. IEEE Transactions on Circuits "
        "and Systems for Video Technology, 13(7), 560–576.",
        "[4] FFmpeg Documentation. libvmaf filter. https://ffmpeg.org/ffmpeg-filters.html "
        "[CẦN XÁC MINH PHIÊN BẢN FFmpeg]",
        "[5] Netflix Technology Blog. Per-Title Encode Optimization. "
        "https://netflixtechblog.com/per-title-encode-optimization-7e99442b62a2 "
        "[CẦN XÁC MINH NĂM TRUY CẬP]",
        "[6] Apple Inc. HLS Authoring Specification for Apple Devices. "
        "https://developer.apple.com/documentation/http-live-streaming "
        "[CẦN XÁC MINH PHIÊN BẢN]",
        "[7] Convex Hull Algorithm – Monotone Chain. Andrew, A. M. (1979). "
        "Another efficient algorithm for convex hulls in two dimensions. "
        "Information Processing Letters, 9(5), 216–219.",
        "[8] Björn, T. (2001). A method for improved VMAF consistency. "
        "[CẦN BỔ SUNG HOẶC XÓA NẾU KHÔNG CÓ NGUỒN CHÍNH XÁC]",
    ]
    add_bullet(doc, refs)
    add_body(doc,
        "Lưu ý: Danh sách này chỉ phục vụ kiểm tra nội bộ. Trước khi nộp báo cáo, "
        "cần xác minh từng tài liệu và định dạng theo quy định trích dẫn của cơ sở "
        "đào tạo (APA, IEEE, hoặc định dạng khác)."
    )


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    out_path = Path(__file__).parent.parent / "docs" / \
        "Chuong_2_3_Co_so_ly_thuyet_va_Phuong_phap_Per_Title_Encoding.docx"

    doc = Document()
    set_document_margins(doc)

    # Default style
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(13)

    # Heading styles
    for level, (size, bold, color_hex) in {
        1: (14, True, "1F3864"),
        2: (13, True, "2E5596"),
        3: (13, True, "1F497D"),
        4: (13, True, "17375E"),
    }.items():
        try:
            hstyle = doc.styles[f"Heading {level}"]
            hstyle.font.name = "Times New Roman"
            hstyle.font.size = Pt(size)
            hstyle.font.bold = bold
            r, g, b = int(color_hex[:2], 16), int(color_hex[2:4], 16), int(color_hex[4:], 16)
            hstyle.font.color.rgb = RGBColor(r, g, b)
        except Exception:
            pass

    add_footer_page_number(doc)
    build_cover(doc)
    build_toc(doc)
    build_chapter2(doc)
    build_chapter3(doc)
    build_coverage_matrix(doc)
    build_references(doc)

    doc.save(str(out_path))
    print(f"✓ File đã lưu: {out_path}")
    print(f"  Kích thước: {out_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
