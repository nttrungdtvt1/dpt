"""Chapter 3 body: research method and proposed pipeline."""

from __future__ import annotations

from pathlib import Path

from docx_report_utils import add_picture, add_table, formula, heading, note, para


def write_chapter3(doc, fig_dir: Path) -> None:
    heading(doc, "CHƯƠNG 3. PHƯƠNG PHÁP NGHIÊN CỨU VÀ QUY TRÌNH ĐỀ XUẤT", 1)
    para(
        doc,
        "Chương này trả lời câu hỏi: đề tài dùng dữ liệu, công cụ, bước xử lý và tiêu chí nào để từ một "
        "video đầu vào xây được bitrate ladder đề xuất, rồi so với ladder cố định. Nội dung là phương pháp "
        "giải quyết bài toán, không lặp lại toàn bộ lý thuyết Chương 2. Các quy tắc số được gọi đúng là "
        "quy tắc lựa chọn đề xuất trong phạm vi thực nghiệm, không phải tiêu chuẩn Netflix hay tiêu chuẩn ngành.",
    )

    # 3.1
    heading(doc, "3.1. Phát biểu bài toán và mô hình đầu vào–đầu ra", 2)
    para(
        doc,
        "Cho một video nguồn ngắn và một không gian candidate gồm các cặp (độ phân giải, bitrate mục tiêu), "
        "hãy chọn một tập hữu hạn các rung tạo thành bitrate ladder theo nội dung, sao cho các rung nằm trên "
        "vùng hiệu quả của mặt bitrate–VMAF, bảo đảm tính tăng dần và giới hạn số rung, rồi so sánh với một "
        "ladder cố định được encode và đo trong cùng điều kiện.",
    )
    para(
        doc,
        "Đầu vào gồm: file video; cấu hình encode (codec, preset, GOP, pixel format, audio); lưới candidate "
        "trong file YAML; tham số đo VMAF; tham số lựa chọn ladder; cấu hình baseline. Đầu ra gồm: bảng điểm "
        "từng candidate; đường cong bitrate–VMAF; tập Pareto; tập upper convex hull; ladder đề xuất; ladder "
        "cố định; các KPI so sánh; biểu đồ và file encode.",
    )
    para(
        doc,
        "Các mục tiêu cần cân bằng: chất lượng (VMAF), bitrate, dung lượng lưu trữ và số rung. Không tồn tại "
        "một ladder “tốt nhất tuyệt đối”; chỉ tồn tại ladder thỏa ràng buộc đã chọn trên dữ liệu đã đo.",
    )

    heading(doc, "3.1.1. Giả định và giới hạn bài toán", 3)
    para(
        doc,
        "Giả định: demo chính dùng một video ngắn khoảng 10–30 giây; chỉ xét kênh video; codec H.264/AVC; "
        "đo full-reference trên toàn clip; không phát trực tiếp HLS/DASH; không tối ưu theo shot. Giới hạn: "
        "không gian candidate rời rạc và hữu hạn nên kết quả phụ thuộc lưới đã chọn; encoder một pass có thể "
        "làm bitrate thực lệch target; VMAF trung bình clip không mô tả biến thiên theo thời gian; một video "
        "không đủ để suy ra hành vi mọi thể loại. Per-Shot Encoding chỉ được nhắc để phân biệt lý thuyết, "
        "không có bước xử lý theo shot trong quy trình.",
    )

    heading(doc, "3.1.2. Luồng xử lý tổng quát", 3)
    para(
        doc,
        "Luồng phương pháp, khớp với pipeline triển khai, như sau:",
    )
    para(
        doc,
        "Video đầu vào → Chuẩn hóa/FFprobe → Phân tích SI/TI (mô tả nội dung) → Xây dựng lưới candidate → "
        "Encode từng candidate bằng FFmpeg → Đo bitrate thực, dung lượng, VMAF → Lưu dữ liệu → Xây đường cong "
        "bitrate–quality → Lọc Pareto → Phân tích upper convex envelope → Lựa chọn ladder theo quy tắc đề xuất → "
        "Xây dựng/đọc baseline cố định → So sánh KPI → Xuất kết quả.",
        indent=False,
    )

    add_picture(
        doc,
        fig_dir / "fig_3_0_io.png",
        "Hình 3.1. Mô hình đầu vào – xử lý – đầu ra của phương pháp",
        width_cm=15.5,
    )

    add_table(
        doc,
        ["Thành phần", "Nội dung"],
        [
            ["Đầu vào", "Video nguồn; config.yaml (codec, candidate, baseline, VMAF, ràng buộc ladder)"],
            ["Xử lý", "FFprobe, SI/TI, encode lưới, đo lường, Pareto, hull, chọn rung, so sánh"],
            ["Đầu ra", "Ladder đề xuất; ladder cố định; CSV/JSON; biểu đồ; file MP4 từng rung"],
            ["Không thuộc đầu ra", "Manifest HLS/DASH; ladder per-shot; tối ưu toàn cục đa video"],
        ],
        "Bảng 3.1. Dữ liệu đầu vào và đầu ra của quy trình",
    )

    # 3.2
    heading(doc, "3.2. Thiết kế video thử nghiệm và không gian candidate", 2)

    heading(doc, "3.2.1. Lựa chọn video thử nghiệm", 3)
    para(
        doc,
        "Demo chính sử dụng một video ngắn khoảng 10–30 giây để kiểm soát thời gian encode và bảo đảm mọi "
        "candidate đều được đo VMAF thật. Video phải đủ dài để tính TI (cần ít nhất hai khung phân tích) và "
        "đủ ngắn để lặp lại thí nghiệm trên máy cá nhân. Nếu có thêm clip, chúng được xem là thực nghiệm mở rộng, "
        "không được mô tả như “tập dữ liệu lớn”.",
    )
    para(
        doc,
        "Các thông số nguồn cần ghi nhận trước khi encode: định dạng container, codec nguồn, độ phân giải, "
        "frame rate, thời lượng, pixel format. Lý do lựa chọn nội dung: nên có một mức chi tiết và chuyển động "
        "đủ để đường cong bitrate–VMAF không hoàn toàn phẳng; tránh clip test pattern nếu muốn bàn về video tự nhiên. "
        "Thông số cụ thể của clip dùng trong lần chạy chính được điền sau khi chốt file:",
    )
    add_table(
        doc,
        ["Thông số", "Giá trị"],
        [
            ["Tên file", "[ĐIỀN THÔNG SỐ THỰC NGHIỆM]"],
            ["Định dạng / codec nguồn", "[ĐIỀN THÔNG SỐ THỰC NGHIỆM]"],
            ["Độ phân giải nguồn", "[ĐIỀN THÔNG SỐ THỰC NGHIỆM]"],
            ["Frame rate", "[ĐIỀN THÔNG SỐ THỰC NGHIỆM]"],
            ["Thời lượng", "khoảng 10–30 giây; giá trị đo: [ĐIỀN THÔNG SỐ THỰC NGHIỆM]"],
            ["Mô tả nội dung", "[ĐIỀN THÔNG SỐ THỰC NGHIỆM]"],
            ["Lý do chọn", "Clip ngắn, một tựa, phù hợp demo Per-Title; không pretent thư viện VOD"],
        ],
        "Bảng 3.2. Video thử nghiệm chính",
    )

    heading(doc, "3.2.2. Xây dựng không gian candidate", 3)
    para(
        doc,
        "Candidate trong đề tài là một cấu hình encode hợp lệ: một độ phân giải đầu ra (giữ tỉ lệ khung hình "
        "từ nguồn, làm tròn chẵn để tương thích yuv420p) kết hợp một bitrate mục tiêu. Tập candidate là tích "
        "Descartes có kiểm soát giữa danh sách chiều cao và danh sách bitrate, khai báo trong YAML, không sinh "
        "ngẫu nhiên lúc chạy.",
    )
    para(
        doc,
        "Nguyên tắc chọn lưới: (1) chiều cao bám các mức thường gặp trong phát đa mức, đồng thời trùng các mức "
        "baseline để so sánh công bằng; (2) mỗi chiều cao có nhiều bitrate, gồm giá trị thấp hơn, bằng và cao hơn "
        "baseline, để đường cong có điểm hai phía; (3) loại chiều cao lớn hơn nguồn (không upscale); (4) bitrate "
        "dương, không trùng trong cùng chiều cao; (5) số candidate đủ để Pareto có ý nghĩa nhưng vẫn encode được "
        "trên máy cá nhân.",
    )
    para(
        doc,
        "Cần khảo sát nhiều candidate vì không biết trước điểm nào hiệu quả với đúng video đang xét. Encode một "
        "cấu hình duy nhất không tạo được đường cong, không lọc được điểm kém, và không có cơ sở chọn ladder theo nội dung.",
    )

    add_table(
        doc,
        ["Candidate", "Chiều cao", "Bitrate mục tiêu (kbps)", "Codec", "Ghi chú"],
        [
            ["360p_250k", "360", "250", "H.264/AVC", "Thấp hơn baseline 360p"],
            ["360p_365k", "360", "365", "H.264/AVC", "Trùng baseline 360p"],
            ["360p_500k", "360", "500", "H.264/AVC", ""],
            ["360p_700k", "360", "700", "H.264/AVC", ""],
            ["432p_500k", "432", "500", "H.264/AVC", ""],
            ["432p_730k", "432", "730", "H.264/AVC", "Trùng baseline 432p"],
            ["432p_1000k", "432", "1000", "H.264/AVC", ""],
            ["432p_1500k", "432", "1500", "H.264/AVC", ""],
            ["720p_1000k", "720", "1000", "H.264/AVC", ""],
            ["720p_1500k", "720", "1500", "H.264/AVC", ""],
            ["720p_2000k", "720", "2000", "H.264/AVC", ""],
            ["720p_3000k", "720", "3000", "H.264/AVC", "Trùng baseline 720p"],
            ["1080p_2000k", "1080", "2000", "H.264/AVC", "Bị loại nếu nguồn < 1080p"],
            ["1080p_3000k", "1080", "3000", "H.264/AVC", "Bị loại nếu nguồn < 1080p"],
            ["1080p_4500k", "1080", "4500", "H.264/AVC", "Bị loại nếu nguồn < 1080p"],
            ["1080p_6000k", "1080", "6000", "H.264/AVC", "Trùng baseline 1080p nếu nguồn đủ"],
        ],
        "Bảng 3.3. Lưới candidate theo cấu hình thực nghiệm hiện tại",
    )
    note(
        doc,
        "Bảng 3.3 phản ánh file config.yaml của demo (các mức lấy cảm hứng từ bảng H.264 trong HLS Authoring Specification của Apple, đã rút gọn). "
        "Nếu cấu hình thay đổi, cập nhật bảng; không bịa thêm hàng. Chiều cao 1080 chỉ encode khi video nguồn ≥ 1080p.",
    )
    note(
        doc,
        "[CẦN BỔ SUNG NGUỒN THAM KHẢO CHO NỘI DUNG NÀY] Apple – HLS Authoring Specification for Apple devices (bảng gợi ý H.264).",
    )

    para(
        doc,
        "Tham số encoding giữ cố định trên toàn lưới đã nêu ở Bảng 2.1. Số candidate tối đa theo YAML là 16; "
        "số candidate thực tế bằng số cặp còn lại sau khi lọc upscale.",
    )

    # 3.3
    heading(doc, "3.3. Thiết lập điều kiện thực nghiệm", 2)
    para(
        doc,
        "Codec: H.264/AVC qua libx264. Công cụ encode và đo: FFmpeg. Phân tích dữ liệu và vẽ: Python. "
        "Định dạng đầu ra từng candidate: MP4, không audio. Scale khi encode: bicubic về đúng width×height của rung.",
    )

    add_table(
        doc,
        ["Nhóm", "Tham số", "Giá trị / nguyên tắc"],
        [
            ["Tạo candidate", "Độ phân giải, bitrate mục tiêu", "Theo lưới YAML; không upscale"],
            ["Tạo candidate", "Codec, preset, pix_fmt, GOP, audio, pass", "Cố định (libx264, veryfast, yuv420p, keyframe 2 s, -an, một pass mặc định)"],
            ["Tạo candidate", "-b:v, -maxrate, -bufsize", "Target; maxrate = target; bufsize = 2×target"],
            ["Đo lường", "Bitrate thực", "FFprobe; fallback từ dung lượng và thời lượng"],
            ["Đo lường", "Dung lượng", "Kích thước file (byte)"],
            ["Đo lường", "VMAF", "libvmaf, model vmaf_v0.6.1; scale bản encode về nguồn"],
            ["Đo lường", "PSNR/SSIM", "Phụ trợ, cùng điều kiện scale"],
            ["Chọn ladder", "min_vmaf, max_representations, one-per-height", "Tham số cấu hình; quy tắc đề xuất"],
            ["Chọn ladder", "Bitrate trên rung ladder", "Dùng bitrate mục tiêu (target), không dùng actual"],
        ],
        "Bảng 3.4. Phân biệt tham số tạo candidate, đo lường và lựa chọn ladder",
    )

    para(
        doc,
        "So sánh công bằng được bảo đảm bằng cách: mọi phương pháp (candidate, ladder đề xuất, baseline) dùng "
        "cùng encoder và cùng hàm đo; các rung trùng (height, target bitrate) được cache để không encode hai lần "
        "với điều kiện khác; không đổi mô hình VMAF giữa các lần đo trong cùng thí nghiệm.",
    )
    para(
        doc,
        "Mặc định two_pass = false vì thời gian demo. Nếu bật two-pass, toàn bộ candidate và baseline phải cùng bật, "
        "nếu không so sánh sẽ lệch do rate control.",
    )

    # 3.4
    heading(doc, "3.4. Quy trình chuẩn hóa video đầu vào", 2)
    para(
        doc,
        "Chuẩn hóa nhằm bảo đảm mọi candidate xuất phát từ cùng một tín hiệu nguồn đã biết metadata. "
        "Bước này không phải chuỗi filter phức tạp nếu file đã dùng được ngay.",
    )
    para(
        doc,
        "Các việc thực hiện: kiểm tra file tồn tại; FFprobe đọc width, height, fps, duration, codec nguồn, bitrate nguồn; "
        "loại video quá nhỏ hoặc quá ngắn; ghi nhận pixel format. Không đổi nội dung hình ảnh trước encode, trừ khi "
        "cần thống nhất format để encoder chạy ổn định. Các candidate luôn scale từ đúng file nguồn đó. "
        "Yếu tố giữ nhất quán: cùng crop (nếu có), cùng fps nguồn, không cắt khác nhau giữa các rung, không thêm "
        "logo hay lọc khác nhau.",
    )
    para(
        doc,
        "Demo không triển khai pipeline sửa màu, khử nhiễu hay scene cut. Những bước đó, nếu thêm sau, phải áp dụng "
        "trước khi rẽ nhánh candidate, nếu không từng rung sẽ có nguồn khác nhau.",
    )

    # 3.5
    heading(doc, "3.5. Quy trình encode và đo lường candidate bằng FFmpeg", 2)
    para(
        doc,
        "Quy trình encode–đo được thực hiện tuần tự cho từng candidate, có cache theo khóa (height, target bitrate).",
    )

    add_table(
        doc,
        ["Bước", "Hành động", "Kết quả"],
        [
            ["1", "Đọc cấu hình YAML", "Codec, lưới, tham số đo, ràng buộc ladder"],
            ["2", "Đọc video đầu vào (FFprobe)", "VideoMeta"],
            ["3", "Lọc và tạo danh sách candidate", "Danh sách rung hợp lệ"],
            ["4", "Gọi FFmpeg encode", "File MP4 từng candidate"],
            ["5", "Đo bitrate thực và dung lượng", "actual_bitrate_kbps, size_bytes"],
            ["6", "Đo VMAF (và PSNR/SSIM nếu bật)", "Điểm chất lượng"],
            ["7", "Lưu dòng kết quả", "CSV/JSON: một hàng một candidate"],
        ],
        "Bảng 3.5. Quy trình encode và đo lường candidate",
    )

    para(
        doc,
        "Pseudocode mức quy trình:",
        indent=False,
    )
    para(
        doc,
        "for each candidate c in grid(source):\n"
        "    if (c.height, c.target_bitrate) in cache: reuse\n"
        "    else encode with FFmpeg; measure actual bitrate, size, VMAF\n"
        "    append row(video, resolution, target, actual, size, VMAF, ...)",
        indent=False,
    )

    para(
        doc,
        "Bitrate cấu hình và bitrate thực tế có thể khác nhau, đặc biệt với nội dung dễ nén hoặc clip ngắn: "
        "encoder không “lấp” đủ target nếu không còn thông tin để mã. Phân tích mặt (R, Q) phải dùng bitrate thực tế, "
        "nếu không sẽ vẽ điểm sai vị trí tài nguyên. Ngược lại, khi dựng rung ladder cho ABR, đề tài gán bitrate "
        "mục tiêu (giá trị khai báo) để các mức vẫn tăng dần có chủ đích, tránh trường hợp actual gần bằng nhau "
        "làm mất thứ tự rung.",
    )
    para(
        doc,
        "Cấu trúc dữ liệu mỗi candidate gồm ít nhất: tên video, width, height, target_bitrate_kbps, actual_bitrate_kbps, "
        "vmaf, psnr, ssim, size_bytes, encode_seconds, tên rung, đường dẫn file. Tập hợp các hàng này là dataset "
        "bitrate–VMAF đầu vào cho các mục 3.7–3.9.",
    )

    # 3.6
    heading(doc, "3.6. Phương pháp phân tích đặc điểm nội dung bằng SI/TI", 2)
    para(
        doc,
        "Thời điểm: sau FFprobe, trước hoặc song song với encode lưới, trên chính video nguồn. "
        "Dữ liệu đầu vào: các khung xám lấy mẫu qua FFmpeg (giảm chiều rộng phân tích, sample fps, giới hạn số khung), "
        "không dùng OpenCV.",
    )
    para(
        doc,
        "Cách tính SI và TI theo (2.3) và (2.6): Sobel trên từng khung → độ lệch chuẩn → trung vị theo thời gian; "
        "hiệu hai khung liên tiếp → độ lệch chuẩn → trung vị. Tổng hợp thêm C theo (2.7) và nhãn dễ/trung bình/khó "
        "theo ngưỡng cấu hình. Kết quả dùng để mô tả video trong báo cáo và để giải thích vì sao đường cong nén "
        "dốc hay sớm bão hòa.",
    )
    para(
        doc,
        "Liên hệ với encode: SI/TI cao là giả thuyết “cần nhiều bit hơn để đạt cùng VMAF”, sẽ được đối chiếu với "
        "dataset đo được, không được dùng làm lệnh gán bitrate cho ladder chính. Hệ số k suy từ nhãn phức tạp chỉ "
        "nhân vào ladder cố định trong nhánh heuristic baseline. Giới hạn: mẫu khung thưa, ảnh phân tích nhỏ, "
        "trung vị thay cho max của P.910; do đó SI/TI là mô tả hỗ trợ, không phải đầu vào bắt buộc của bước 3.9.",
    )

    # 3.7
    heading(doc, "3.7. Phương pháp xây dựng đường cong bitrate–quality", 2)
    para(
        doc,
        "Dữ liệu: mỗi candidate một điểm với hoành độ = actual_bitrate_kbps, tung độ = VMAF. Có thể vẽ thêm "
        "chuỗi theo từng chiều cao để thấy việc chuyển resolution. Xu hướng được đọc bằng cách sắp điểm theo bitrate "
        "tăng dần: nếu đoạn sau gần nằm ngang, đó là vùng lợi ích biên giảm dần.",
    )
    para(
        doc,
        "Đường cong hỗ trợ bước lựa chọn theo hướng: ưu tiên điểm còn nằm trên vùng dốc có ý nghĩa; cảnh giác "
        "các điểm bitrate cao nhưng VMAF gần bằng điểm rẻ hơn. Việc nội suy tuyến tính trên đường cong (cùng một "
        "chuỗi, hoặc trên hull) chỉ dùng khi tính KPI tại Q* hoặc R* không trùng điểm đo. Không vẽ đường cong từ "
        "số liệu giả.",
    )

    # 3.8
    heading(doc, "3.8. Phương pháp Pareto filtering và phân tích Convex Hull", 2)
    para(
        doc,
        "Quy trình lọc và phân tích biên hiệu quả:",
    )
    para(
        doc,
        "1) Tập hợp mọi candidate có VMAF đo được, hữu hạn.\n"
        "2) Hai mục tiêu: minimize bitrate thực tế, maximize VMAF.\n"
        "3) Áp dụng (2.8): đánh dấu mọi điểm bị chi phối.\n"
        "4) Loại điểm bị chi phối → Pareto frontier.\n"
        "5) Trên frontier (hoặc trên tập điểm), tính upper convex hull bằng monotone chain: duyệt trái sang phải, "
        "giữ các đỉnh tạo bao phía trên, loại điểm thẳng hàng phía trong, trùng bitrate thì giữ VMAF cao hơn.\n"
        "6) Chuyển tập hull sang bước lựa chọn ladder; không xuất ladder = toàn bộ hull.",
        indent=False,
    )
    para(
        doc,
        "Pareto filtering không đồng nghĩa với chọn ladder cuối cùng. Candidate trên frontier vẫn có thể bị loại "
        "ở 3.9 vì trùng độ phân giải, vì phá monotonic bitrate, vì vượt max số rung, hoặc vì dưới ngưỡng VMAF cấu hình. "
        "Hull là công cụ hỗ trợ đọc envelope, không phải chứng minh tối ưu toàn cục trên mọi bitrate liên tục.",
    )

    # 3.9
    heading(doc, "3.9. Quy tắc lựa chọn bitrate ladder đề xuất", 2)
    para(
        doc,
        "Quy tắc lựa chọn được đề xuất trong phạm vi thực nghiệm. Quy tắc được áp dụng trên "
        "tập điểm upper convex hull đã đo, kết hợp ràng buộc YAML. Đây không phải thuật toán tối ưu toàn cục "
        "và không phải quy trình Per-Title Encoding thương mại.",
    )

    heading(doc, "3.9.1. Xác định mục tiêu lựa chọn", 3)
    para(
        doc,
        "Mục tiêu vận hành của bước này: duy trì các mức chất lượng hữu ích trên envelope; giảm các rung tốn bit "
        "mà không cải thiện VMAF đáng kể; bảo đảm độ bao phủ theo độ phân giải khi có thể; giới hạn số rung; "
        "giữ tính hợp lý không upscale và bitrate mục tiêu tăng dần.",
    )

    heading(doc, "3.9.2. Xác định các mức chất lượng mục tiêu", 3)
    para(
        doc,
        "Ngưỡng chất lượng được tham số hóa bằng min_vmaf trong cấu hình. Điểm hull có VMAF < min_vmaf bị loại "
        "trước khi chọn đại diện. Nếu sau lọc không còn điểm, thực nghiệm rơi về toàn bộ hull (hành vi an toàn "
        "trong mã) và phải ghi chú. min_vmaf là tham số cấu hình của đề tài, không được gọi là “ngưỡng chuẩn ngành”. "
        "Giá trị cụ thể lần chạy chính:",
    )
    note(doc, "min_vmaf = [ĐIỀN THÔNG SỐ THỰC NGHIỆM] (hiện mặc định trong YAML là 0, tức chưa cắt theo ngưỡng).")
    para(
        doc,
        "Đề tài không gán sẵn các mốc kiểu “VMAF 70/80/90 là chuẩn thương mại” nếu không có nguồn. "
        "Nếu người thí nghiệm muốn ép độ bao phủ theo khoảng VMAF, đó là cấu hình bổ sung, phải công bố rõ.",
    )

    heading(doc, "3.9.3. Lựa chọn candidate đại diện", 3)
    para(
        doc,
        "Với mỗi chiều cao còn lại trên tập đã lọc, quy tắc đề xuất chọn một đại diện: điểm có VMAF cao nhất; "
        "nếu hòa VMAF thì chọn bitrate mục tiêu thấp hơn. Tùy chọn này (prefer_one_per_height) nhằm tránh nhiều rung "
        "cùng một độ phân giải, vốn dễ trùng chức năng trên ladder ABR ngắn. Điểm được chọn phải thuộc tập không bị "
        "chi phối (thực tế là tập hull). Điểm không được chọn không có nghĩa là encode sai, mà là không cần thiết "
        "trong ràng buộc demo.",
    )

    heading(doc, "3.9.4. Xây dựng ladder cuối cùng", 3)
    para(
        doc,
        "Các đại diện được sắp theo chiều cao tăng dần, đồng thời kiểm tra bitrate mục tiêu tăng nghiêm ngặt: "
        "nếu một độ phân giải cao hơn lại có target bitrate không lớn hơn rung trước, rung đó bị bỏ để giữ monotonic. "
        "Nếu số rung còn lại vượt max_representations, quy tắc đề xuất lấy mẫu đều theo thứ tự (giữ các mốc trải "
        "suốt danh sách, gồm vùng thấp và vùng cao) để cắt còn đúng số lượng cho phép.",
    )
    para(
        doc,
        "Thứ tự kiểm tra sau khi có danh sách: (1) width/height chẵn; (2) không vượt nguồn; (3) bitrate trong biên "
        "cấu hình; (4) bitrate tăng dần. Ladder xuất ra gồm tên rung, kích thước, bitrate mục tiêu, nguồn gốc “hull”.",
    )

    heading(doc, "3.9.5. Kiểm tra tính hợp lý của ladder", 3)
    para(
        doc,
        "Trước khi so sánh baseline, kiểm tra định tính: có hai rung gần như cùng VMAF và gần bitrate hay không; "
        "có rung bitrate cao nhưng VMAF gần bão hòa so với rung liền trước hay không; khoảng VMAF giữa hai rung "
        "liền kề có quá lớn so với mục tiêu bao phủ hay không; số rung có phù hợp demo hay không. "
        "Các kiểm tra này có thể dẫn tới chỉnh YAML (lưới candidate hoặc max_representations) rồi chạy lại, "
        "chứ không “sửa tay” điểm VMAF.",
    )

    add_table(
        doc,
        ["Ràng buộc", "Ý nghĩa", "Ghi chú"],
        [
            ["Không upscale", "height ≤ height nguồn", "Bắt buộc"],
            ["Một điểm / chiều cao", "Tránh rung trùng chức năng", "prefer_one_per_height; quy tắc đề xuất"],
            ["Bitrate mục tiêu tăng dần", "Thứ tự ABR hợp lý", "Dùng target, không dùng actual"],
            ["max_representations", "Giới hạn số rung", "Tham số cấu hình (mặc định 4)"],
            ["min_vmaf", "Cắt chất lượng thấp", "Tham số cấu hình"],
        ],
        "Bảng 3.6. Ràng buộc của quy tắc lựa chọn đề xuất trong phạm vi thực nghiệm",
    )

    # 3.10
    heading(doc, "3.10. Xây dựng bitrate ladder cố định làm baseline", 2)
    para(
        doc,
        "Baseline là thước so sánh độc lập nội dung: cùng bảng resolution–bitrate cho mọi video (sau khi lọc "
        "upscale). Mục đích không phải tuyên bố bảng này là ladder hay nhất trên thị trường, mà là có một đối "
        "chứng cố định, công bố được, encode cùng điều kiện.",
    )
    para(
        doc,
        "Cách xác định: đọc danh sách fixed_ladder trong YAML, materialize width theo tỉ lệ nguồn, bỏ mức cao hơn nguồn. "
        "Các tham số encoder và đo VMAF giống hệt nhánh candidate. Baseline phải có trước khi so sánh KPI; không "
        "được lấy chính ladder đề xuất làm mốc rồi kết luận “tốt hơn”.",
    )
    para(
        doc,
        "Baseline không đại diện mọi hệ thống thực tế: chỉ vài mức, theo một bảng gợi ý đã rút gọn, không có audio, "
        "không có đóng gói ABR. Kết quả “thắng/thua” chỉ có nghĩa so với đúng baseline này.",
    )
    add_table(
        doc,
        ["Tên rung", "Chiều cao", "Bitrate mục tiêu (kbps)", "Nguồn thiết kế"],
        [
            ["360p", "360", "365", "Rút gọn từ bảng H.264 HLS Authoring (Apple)"],
            ["432p", "432", "730", "Hàng 768×432 @ 730 kbps; không bịa 480p"],
            ["720p", "720", "3000", "Rút gọn từ bảng H.264 HLS Authoring (Apple)"],
            ["1080p", "1080", "6000", "Chỉ dùng nếu nguồn ≥ 1080p"],
        ],
        "Bảng 3.7. Bitrate ladder cố định dùng làm baseline",
    )
    note(
        doc,
        "Nếu lần chạy chính dùng bảng khác, thay bằng [ĐIỀN CẤU HÌNH BASELINE THỰC TẾ]. Không chỉnh bitrate baseline sau khi đã nhìn VMAF của ladder đề xuất.",
    )

    para(
        doc,
        "Ngoài baseline cố định, demo còn giữ một nhánh heuristic k × fixed (k suy từ SI/TI) để đối chiếu lịch sử "
        "phương pháp. Nhánh này không phải ladder đề xuất chính và không được trộn vào kết luận Per-Title hull-based.",
    )

    # 3.11
    heading(doc, "3.11. Phương pháp so sánh và đánh giá", 2)
    para(
        doc,
        "So sánh thực hiện trên cùng video, cùng encoder, cùng quy trình đo. Các phép đo KPI dùng số liệu đã ghi, "
        "không dùng ví dụ minh họa Chương 2.",
    )

    heading(doc, "3.11.1. So sánh bitrate tại chất lượng tương đương", 3)
    para(
        doc,
        "Chọn một hoặc vài mức Q* (ví dụ VMAF tại một rung baseline, hoặc một mốc cấu hình). Với mỗi phương pháp, "
        "xây đường cong từ các điểm (R_actual, VMAF) của đúng ladder đó hoặc từ tập candidate nếu cần nội suy mịn hơn; "
        "trong báo cáo phải nêu rõ đường nào được dùng. Nếu tồn tại hai điểm kề nhau Q_i ≤ Q* ≤ Q_{i+1}:",
    )
    formula(
        doc,
        "R(Q*) = R_i + (R_{i+1} − R_i) · (Q* − Q_i) / (Q_{i+1} − Q_i)",
        "(3.1)",
    )
    para(
        doc,
        "Công thức (3.1) là nội suy tuyến tính do đề tài dùng khi cần, không phải chuẩn BD-Rate. "
        "BD-Rate không triển khai trong demo. Sau khi có R_baseline(Q*) và R_proposed(Q*), áp dụng (2.9). "
        "Nếu Q* nằm ngoài miền đo, không nội suy ngoại suy; ghi là không so sánh được tại mốc đó.",
    )

    heading(doc, "3.11.2. So sánh chất lượng tại bitrate tương đương", 3)
    para(
        doc,
        "Chọn R* nằm trong khoảng bitrate thực tế của cả hai ladder (ví dụ bitrate thực của một rung baseline). "
        "Nội suy VMAF theo bitrate tương tự (3.1) với vai trò R và Q đổi chỗ. Tính ΔVMAF theo (2.10). "
        "Không so hai rung khác độ phân giải như thể cùng bitrate nếu actual lệch xa target.",
    )

    heading(doc, "3.11.3. So sánh dung lượng và số lượng rung", 3)
    para(
        doc,
        "Tính S_total theo (2.11) cho ladder đề xuất và baseline. So sánh N_rung. Có thể báo cáo tổng bitrate "
        "mục tiêu và bitrate rung cao nhất. Ý nghĩa: giảm dung lượng giúp lưu trữ VOD; giảm số rung giảm chi phí "
        "encode; cả hai phải đọc cùng với VMAF để không kết luận sai từ một ladder “rẻ nhưng xấu” hoặc “ít rung quá mức”.",
    )

    heading(doc, "3.11.4. Phân tích trường hợp kết quả không cải thiện rõ rệt", 3)
    para(
        doc,
        "Ladder đề xuất không được kỳ vọng luôn tốt hơn baseline. Các tình huống cần phân tích thẳng thắn gồm: "
        "lưới candidate quá thưa, không có điểm nào hiệu quả hơn bảng cố định; nội dung đã dễ nén, baseline đã đủ; "
        "nội dung khó nhưng các điểm hull trùng đúng rung baseline; chênh lệch VMAF nhỏ so với nhiễu đo trên clip ngắn; "
        "ràng buộc one-per-height làm mất một rung trung gian hữu ích. Khi đó báo cáo ghi nhận “không cải thiện rõ”, "
        "chứ không ép diễn giải thành thành công.",
    )

    add_table(
        doc,
        ["KPI", "Công thức / cách tính", "Điều kiện"],
        [
            ["Bitrate saving tại Q*", "(2.9) với R nội suy (3.1)", "Q* trong miền đo của cả hai ladder"],
            ["ΔVMAF tại R*", "(2.10) với VMAF nội suy", "R* trong miền đo của cả hai ladder"],
            ["Δ dung lượng", "S_proposed − S_baseline", "Cùng số kiểu file, không audio"],
            ["Δ số rung", "N_proposed − N_baseline", "Đếm representation xuất ra"],
        ],
        "Bảng 3.8. Các KPI dùng khi so sánh ladder đề xuất và baseline",
    )

    # 3.12
    heading(doc, "3.12. Sơ đồ quy trình nghiên cứu tổng thể", 2)
    para(
        doc,
        "Hình 3.2 tóm tắt toàn bộ phương pháp đã trình bày. Khối xử lý là các bước FFprobe, encode, đo, vẽ đường cong, "
        "lọc Pareto, tính hull. Khối quyết định là quy tắc chọn ladder. Khối đầu ra là CSV/JSON, biểu đồ và bảng KPI. "
        "Không có nhánh Per-Shot, không có đóng gói HLS, không có tối ưu đa video.",
    )
    add_picture(
        doc,
        fig_dir / "fig_3_1_flowchart.png",
        "Hình 3.2. Flowchart quy trình nghiên cứu tổng thể",
        width_cm=14.8,
    )
    note(
        doc,
        "Nếu cần vẽ lại trong Word cho đồng bộ font Times New Roman: [HÌNH 3.2. FLOWCHART QUY TRÌNH NGHIÊN CỨU – CÓ THỂ VẼ LẠI TRONG WORD]. Logic khối phải giữ như hình.",
    )

    heading(doc, "3.13. Tóm tắt chương", 2)
    para(
        doc,
        "Chương 3 đã phát biểu bài toán một video – một lưới candidate – một ladder đề xuất; mô tả chuẩn hóa nguồn, "
        "encode FFmpeg, đo VMAF, dùng SI/TI chỉ để mô tả, dựng đường cong, lọc Pareto, phân tích upper envelope, "
        "áp dụng quy tắc lựa chọn đề xuất, xây baseline cố định và so sánh KPI, kèm trường hợp không cải thiện. "
        "Chương 4 sẽ triển khai các bước này trên công cụ và cấu hình cụ thể; Chương 5 mới được phép điền số liệu đo.",
    )
