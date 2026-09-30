"""Chapter 2 body: theory and evaluation metrics."""

from __future__ import annotations

from pathlib import Path

from docx_report_utils import add_picture, add_table, formula, heading, note, para


def write_chapter2(doc, fig_dir: Path) -> None:
    heading(doc, "CHƯƠNG 2. CƠ SỞ LÝ THUYẾT VÀ CÁC CHỈ SỐ ĐÁNH GIÁ", 1)

    para(
        doc,
        "Chương này trình bày các kiến thức cần thiết để hiểu bài toán lựa chọn bitrate ladder "
        "theo từng nội dung. Các khái niệm được định nghĩa trước khi sử dụng, kèm công thức và "
        "ý nghĩa vận hành. Chương không mô tả quy trình thực nghiệm chi tiết; phần đó thuộc Chương 3. "
        "Mọi ví dụ số liệu trong chương này là minh họa, không phải kết quả đo của đề tài.",
    )

    # 2.1
    heading(doc, "2.1. Các tham số encoding và quan hệ bitrate–dung lượng–chất lượng", 2)
    para(
        doc,
        "Mục này làm rõ các tham số quyết định cách một video được nén và vì sao chúng phải được "
        "kiểm soát khi so sánh các cặp độ phân giải/bitrate. Nếu các tham số phụ thay đổi tùy tiện "
        "giữa các candidate, sự khác biệt về chất lượng sẽ không còn phản ánh đúng bài toán ladder.",
    )

    heading(doc, "2.1.1. Video encoding và video compression", 3)
    para(
        doc,
        "Video số là chuỗi khung hình (frame) được lấy mẫu theo thời gian. Mỗi khung là một ảnh "
        "có kích thước cố định. Lượng dữ liệu thô rất lớn: một video Full HD chưa nén có thể chiếm "
        "hàng trăm megabit mỗi giây, vượt xa băng thông phổ biến của mạng truy cập. Video encoding "
        "là quá trình biến tín hiệu video nguồn thành một dòng bit tuân theo một chuẩn mã hóa. "
        "Video compression là khía cạnh then chốt của encoding: giảm lượng bit trong khi giữ mức "
        "méo hình ảnh chấp nhận được.",
    )
    para(
        doc,
        "Nén video khai thác hai dạng dư thừa chính. Dư thừa không gian xuất hiện khi các pixel "
        "lân cận trong cùng một khung có tương quan cao, ví dụ vùng trời đồng màu. Dư thừa thời gian "
        "xuất hiện khi các khung liên tiếp giống nhau, đặc biệt ở cảnh tĩnh. Bộ mã hóa dự đoán pixel "
        "từ thông tin đã có, rồi chỉ mã hóa phần sai số dự đoán. Phần không dự đoán được, hoặc được "
        "chủ động lược bỏ, tạo ra méo nén. Bài toán bitrate ladder chính là chọn mức nén phù hợp cho "
        "từng phiên bản phát, chứ không phải tìm một điểm nén duy nhất cho mọi tình huống mạng.",
    )

    heading(doc, "2.1.2. Bitrate", 3)
    para(
        doc,
        "Bitrate là tốc độ bit trung bình của dòng video sau nén, thường tính bằng kilobit mỗi giây "
        "(kbps) hoặc megabit mỗi giây (Mbps). Bitrate càng cao thì, trong cùng một codec và cùng một "
        "nội dung, bộ mã hóa có nhiều bit hơn để biểu diễn chi tiết và chuyển động. Bitrate không "
        "đồng nhất với chất lượng cảm nhận: hai video cùng bitrate có thể khác nhau rõ rệt nếu độ "
        "phức tạp nội dung khác nhau.",
    )
    para(
        doc,
        "Cần phân biệt bitrate mục tiêu (target bitrate) và bitrate thực tế (actual bitrate). "
        "Bitrate mục tiêu là giá trị cấu hình đưa vào bộ mã hóa, ví dụ tham số -b:v của FFmpeg. "
        "Bitrate thực tế là giá trị đo được trên file đầu ra, phụ thuộc nội dung, bộ điều khiển tốc độ "
        "và thời lượng clip. Khi phân tích đường cong bitrate–quality, đề tài lấy bitrate thực tế làm "
        "trục tài nguyên, vì đó mới là lượng bit thực sự đã dùng.",
    )

    heading(doc, "2.1.3. Độ phân giải", 3)
    para(
        doc,
        "Độ phân giải là số pixel theo chiều ngang và chiều dọc của khung hình, ký hiệu W×H. "
        "Trong hệ thống phát đa mức, người ta thường gọi các rung theo chiều cao, ví dụ 360p, 720p, "
        "1080p. Số pixel tỉ lệ với W×H. Khi giảm độ phân giải, lượng thông tin không gian cần mã hóa "
        "giảm, nên cùng một mức chất lượng cảm nhận có thể đạt được với bitrate thấp hơn. Ngược lại, "
        "nếu bitrate quá thấp ở độ phân giải cao, khối hóa và mất chi tiết có thể nặng hơn so với "
        "việc xuống thang độ phân giải rồi nén.",
    )
    para(
        doc,
        "Trong bài toán ladder, mỗi rung là một cặp (độ phân giải, bitrate), không phải chỉ một trong "
        "hai đại lượng. Việc tăng độ phân giải mà không cấp đủ bitrate thường không cải thiện chất lượng "
        "tương ứng. Đề tài không upscale vượt độ phân giải nguồn: chiều cao candidate lớn hơn chiều cao "
        "video gốc bị loại, vì phóng to không tạo thêm chi tiết thật.",
    )

    heading(doc, "2.1.4. Frame rate", 3)
    para(
        doc,
        "Frame rate, ký hiệu fps, là số khung hình mỗi giây. Frame rate cao hơn mô tả chuyển động mượt "
        "hơn nhưng tăng lượng dữ liệu thời gian cần nén. Trong phạm vi đề tài, frame rate được giữ cố định "
        "theo video nguồn; các candidate không khảo sát việc đổi fps. Cố định fps giúp sự khác biệt giữa "
        "các điểm dữ liệu chỉ đến từ độ phân giải và bitrate, đúng trọng tâm xây dựng ladder.",
    )

    heading(doc, "2.1.5. Codec và phạm vi H.264/AVC", 3)
    para(
        doc,
        "Codec (coder–decoder) là bộ quy tắc và thuật toán nén/giải nén. Cùng một nội dung, các codec "
        "khác nhau có hiệu suất nén khác nhau ở cùng bitrate. Nếu so sánh ladder giữa hai codec, không thể "
        "kết luận sự khác biệt đến từ việc chọn rung hay từ chính codec.",
    )
    para(
        doc,
        "Đề tài chốt codec thực nghiệm là H.264/AVC, triển khai qua encoder libx264 trong FFmpeg. "
        "H.264/AVC sử dụng dự đoán intra trong khung, ước lượng chuyển động liên khung, biến đổi phần dư "
        "và mã hóa entropy. Chuẩn này vẫn phổ biến trên thiết bị và nền tảng VOD, phù hợp demo quy mô nhỏ. "
        "Đề tài không khẳng định kết luận sẽ giữ nguyên với HEVC, AV1 hay VVC. Việc đổi codec sẽ làm thay đổi "
        "toàn bộ đường cong bitrate–quality và phải được xem là thực nghiệm khác.",
        indent=True,
    )
    note(
        doc,
        "[CẦN BỔ SUNG NGUỒN THAM KHẢO CHO NỘI DUNG NÀY] ITU-T Rec. H.264 / ISO/IEC 14496-10 – Advanced video coding.",
    )

    heading(doc, "2.1.6. Quan hệ độ phân giải–bitrate–chất lượng–dung lượng", 3)
    para(
        doc,
        "Ba đại lượng bitrate R, thời lượng T và dung lượng file S liên hệ gần đúng theo:",
    )
    formula(doc, "S ≈ (R × T) / 8", "(2.1)")
    para(
        doc,
        "Trong đó R là bitrate trung bình (bit/s), T là thời lượng (s), S là dung lượng (byte). "
        "Hệ số 8 đổi từ bit sang byte. Công thức bỏ qua overhead container ở mức chấp nhận được với clip ngắn. "
        "Ý nghĩa thực tiễn: giảm bitrate trung bình của một rung sẽ giảm dung lượng lưu trữ và giảm lưu lượng truyền, "
        "miễn là chất lượng vẫn đủ dùng.",
        indent=True,
    )
    para(
        doc,
        "Quan hệ bitrate–chất lượng không tuyến tính. Ở vùng bitrate thấp, thêm một lượng bit nhỏ có thể "
        "cải thiện rõ nét (giảm khối, giữ cạnh). Ở vùng bitrate cao, đường cong đi vào bão hòa: cùng một "
        "lượng bit tăng thêm chỉ đổi lấy ít điểm chất lượng. Đây là hiện tượng lợi ích biên giảm dần, sẽ "
        "được dùng khi loại các rung “tốn bit nhưng gần như không đẹp hơn”.",
    )
    para(
        doc,
        "Quan hệ độ phân giải–bitrate cũng không có một tỉ lệ cố định cho mọi video. Nội dung nhiều chi tiết "
        "và chuyển động mạnh thường cần nhiều bit hơn ở cùng độ phân giải. Đó là lý do ladder cố định dễ "
        "thừa bit với nội dung dễ nén và thiếu bit với nội dung khó nén.",
    )

    heading(doc, "2.1.7. Điều khiển bitrate: CBR, VBR và CRF", 3)
    para(
        doc,
        "Bộ điều khiển tốc độ quyết định bit được phân bổ theo thời gian. Ba chế độ thường gặp trong thực hành "
        "FFmpeg/x264 là CBR, VBR và CRF. Chúng không phải ba “chất lượng” khác nhau theo nghĩa cảm nhận, "
        "mà là ba cách ràng buộc tài nguyên.",
    )
    para(
        doc,
        "CBR (Constant Bitrate) giữ tốc độ bit gần như không đổi theo thời gian. Cách này dễ lập kế hoạch băng "
        "thông nhưng kém hiệu quả với cảnh lúc dễ lúc khó: cảnh tĩnh bị cấp thừa bit, cảnh phức tạp bị thiếu bit.",
    )
    para(
        doc,
        "VBR (Variable Bitrate) cho phép bitrate tức thời thay đổi, thường kèm ngưỡng trung bình hoặc đỉnh. "
        "ABR (Average Bitrate) là dạng VBR hướng tới bitrate trung bình mục tiêu. Đây là chế độ phù hợp khi "
        "đối tượng so sánh là các mức bitrate của ladder.",
    )
    para(
        doc,
        "CRF (Constant Rate Factor) không ấn định bitrate trước mà ấn định một “ngưỡng méo” tương đối. "
        "Bitrate đầu ra phụ thuộc độ khó nội dung: video dễ nén cho file nhỏ hơn ở cùng CRF. CRF hữu ích "
        "khi muốn chất lượng cảm nhận tương đối ổn định, nhưng không phải công cụ chính để dựng một bảng "
        "bitrate cố định theo từng rung. Trong đề tài, encode candidate dùng bitrate mục tiêu (-b:v), "
        "không dùng CRF làm trục khảo sát chính. CRF chỉ có thể xuất hiện như bước probe tùy chọn, không "
        "thay thế lưới candidate.",
    )
    note(
        doc,
        "[CẦN BỔ SUNG NGUỒN THAM KHẢO CHO NỘI DUNG NÀY] Tài liệu FFmpeg Encode/H.264 và các mô tả rate control của x264.",
    )

    heading(doc, "2.1.8. Tham số cần cố định khi so sánh ladder", 3)
    para(
        doc,
        "Để sự khác biệt giữa các candidate phản ánh đúng cặp (độ phân giải, bitrate), các tham số sau "
        "được giữ cố định trong thực nghiệm: codec (libx264), preset mã hóa, pixel format, khoảng keyframe "
        "(GOP liên quan đến thời gian seek), việc có/không có âm thanh, số pass, bộ lọc scale, và điều kiện "
        "đo chất lượng. Tham số thay đổi có chủ đích chỉ gồm chiều cao (kéo theo chiều rộng giữ tỉ lệ) và "
        "bitrate mục tiêu. Nếu preset bị đổi giữa các điểm, thời gian encode và cả chất lượng đều thay đổi, "
        "làm hỏng so sánh.",
    )

    add_table(
        doc,
        ["Tham số", "Vai trò", "Cách xử lý trong đề tài"],
        [
            ["Codec", "Quyết định công cụ nén", "Cố định H.264/AVC (libx264)"],
            ["Preset", "Đánh đổi tốc độ encode và hiệu suất nén", "Cố định theo cấu hình"],
            ["Pixel format", "Lấy mẫu màu, ảnh hưởng dung lượng và tương thích", "Cố định yuv420p"],
            ["GOP / keyframe", "Điểm vào ngẫu nhiên, kích thước khoảng Intra", "Cố định theo thời gian keyframe"],
            ["Audio", "Làm lệch dung lượng và bitrate tổng", "Tắt để chỉ xét video"],
            ["Độ phân giải", "Trục không gian của rung", "Thay đổi theo candidate"],
            ["Bitrate mục tiêu", "Trục tài nguyên của rung", "Thay đổi theo candidate"],
            ["Frame rate", "Mật độ khung theo thời gian", "Giữ theo nguồn"],
        ],
        "Bảng 2.1. Các tham số encoding và cách xử lý trong đề tài",
    )

    # 2.2
    heading(doc, "2.2. Bitrate ladder và các rung chất lượng", 2)
    para(
        doc,
        "Mục này chỉ nêu phần lý thuyết cần cho Chương 3, không lặp lại toàn bộ bối cảnh VOD đã thuộc Chương 1.",
    )

    heading(doc, "2.2.1. Khái niệm rung trong bitrate ladder", 3)
    para(
        doc,
        "Bitrate ladder là tập hữu hạn các phiên bản đã mã hóa của cùng một nội dung, sắp theo mức tài nguyên "
        "và chất lượng. Mỗi phần tử của ladder gọi là một rung (rung / representation). Một rung trong đề tài "
        "được xác định bởi độ phân giải (width × height) và bitrate mục tiêu, cùng codec và các tham số phụ "
        "đã cố định. Người xem (hoặc client ABR) không nhận một file duy nhất mà có thể chuyển giữa các rung "
        "khi băng thông thay đổi.",
    )
    para(
        doc,
        "Quan hệ resolution–bitrate trong một rung phải hợp lý: độ phân giải cao hơn thường đi kèm bitrate "
        "cao hơn. Nếu một rung 720p có bitrate thấp hơn rung 360p, thứ tự chất lượng và thứ tự tài nguyên "
        "bị đảo, client khó chọn đúng mức. Tính tăng dần của bitrate theo ladder là ràng buộc thiết kế, "
        "không phải hệ quả tự nhiên của encoder.",
    )

    heading(doc, "2.2.2. Vì sao ladder cần nhiều mức chất lượng", 3)
    para(
        doc,
        "Mạng và thiết bị người xem không đồng nhất. Một rung duy nhất hoặc quá cao thì máy yếu và đường truyền "
        "hẹp bị gián đoạn, hoặc quá thấp thì người dùng có băng thông tốt bị thiệt chất lượng. Nhiều rung tạo "
        "độ bao phủ: từ mức xem được trên mạng hạn chế đến mức gần bão hòa chất lượng trên mạng tốt. Số rung "
        "cũng không nên quá lớn: mỗi rung tốn chi phí encode, lưu trữ và làm phức tạp việc chuyển mức. "
        "Demo của đề tài giới hạn số rung để phù hợp thực nghiệm nhỏ, không mô phỏng ladder thương mại đầy đủ.",
    )

    heading(doc, "2.2.3. Nguyên tắc cơ bản khi xây dựng ladder", 3)
    para(
        doc,
        "Các nguyên tắc lý thuyết thường được dùng, ở mức định hướng chứ không phải tiêu chuẩn bắt buộc của đề tài, gồm: "
        "(1) không upscale nguồn; (2) bitrate tăng dần theo rung; (3) khoảng cách giữa các rung đủ lớn để việc "
        "chuyển mức có ý nghĩa; (4) tránh hai rung gần như trùng chất lượng; (5) có ít nhất một rung “xem được” "
        "ở bitrate thấp và một rung tiệm cận bão hòa. Việc cụ thể hóa thành quy tắc số thuộc Chương 3 và được "
        "gọi đúng là quy tắc đề xuất trong phạm vi thực nghiệm.",
    )

    heading(doc, "2.2.4. Ladder cố định và ladder theo nội dung", 3)
    para(
        doc,
        "Ladder cố định gán cùng bảng resolution–bitrate cho nhiều tựa phim. Ưu điểm là đơn giản, dễ vận hành. "
        "Nhược điểm là bỏ qua độ khó nén riêng của từng video. Ladder tối ưu theo nội dung (Per-Title) chọn "
        "tập rung sau khi quan sát hành vi nén của chính video đó. Per-Title khác Per-Shot: Per-Shot điều chỉnh "
        "theo từng shot/cảnh bên trong một tựa, phức tạp hơn nhiều và không được triển khai trong đề tài. "
        "Đề tài chỉ dùng Per-Title ở mức toàn clip ngắn.",
    )

    # 2.3
    heading(doc, "2.3. Đánh giá chất lượng video bằng VMAF", 2)

    heading(doc, "2.3.1. Khái niệm đánh giá chất lượng video", 3)
    para(
        doc,
        "Đánh giá chủ quan dựa trên người xem, điển hình là điểm MOS (Mean Opinion Score) thu từ thí nghiệm "
        "theo khuyến nghị của ITU. Đây là chuẩn vàng về cảm nhận nhưng tốn thời gian, khó lặp lại cho hàng "
        "chục candidate encode. Đánh giá khách quan dùng thuật toán so sánh video đã xử lý với video tham chiếu "
        "hoặc ước lượng không tham chiếu. Trong encoding, chỉ số khách quan cho phép xếp hạng nhanh các cấu hình.",
    )
    para(
        doc,
        "PSNR đo méo điểm-ảnh qua MSE, dễ tính nhưng thường lệch cảm nhận thị giác. SSIM so sánh cấu trúc, "
        "độ sáng và tương phản, gần cảm nhận hơn PSNR ở nhiều trường hợp, nhưng vẫn chưa phải thước đo chính "
        "của đề tài. Đề tài dùng VMAF làm chỉ số chất lượng chính khi so sánh candidate; PSNR/SSIM nếu được đo "
        "chỉ đóng vai trò phụ trợ, không quyết định ladder.",
    )
    note(
        doc,
        "[CẦN BỔ SUNG NGUỒN THAM KHẢO CHO NỘI DUNG NÀY] ITU-T P.910 (đánh giá chủ quan); Wang và cộng sự (SSIM, 2004).",
    )

    heading(doc, "2.3.2. Tổng quan về VMAF", 3)
    para(
        doc,
        "VMAF (Video Multimethod Assessment Fusion) là chỉ số chất lượng tham chiếu đầy đủ do Netflix phát triển "
        "nhằm dự đoán cảm nhận người xem tốt hơn các độ đo truyền thống trong ngữ cảnh streaming. Điểm VMAF "
        "thường được báo cáo trên thang khoảng 0 đến 100, trong đó giá trị cao hơn tương ứng với chất lượng dự đoán "
        "tốt hơn đối với mô hình đã chọn. VMAF không phải “điểm đẹp tuyệt đối” của video ngoài đời, mà là đầu ra "
        "của một mô hình đã huấn luyện trên dữ liệu cảm nhận nhất định.",
    )
    para(
        doc,
        "VMAF phù hợp bài toán so sánh candidate vì: cùng một video nguồn, cùng điều kiện đo, các bản encode khác "
        "nhau có thể xếp hạng tương đối tin cậy; thang điểm liên tục đủ mịn để vẽ đường cong bitrate–quality; "
        "công cụ FFmpeg (filter libvmaf) cho phép đo lặp lại được trong demo. Đề tài không dùng VMAF để tuyên bố "
        "chất lượng tuyệt đối với mọi loại màn hình hay mọi nhóm người xem.",
    )
    note(
        doc,
        "[CẦN BỔ SUNG NGUỒN THAM KHẢO CHO NỘI DUNG NÀY] Li và cộng sự, Toward A Practical Perceptual Video Quality Metric (Netflix TechBlog); kho mã VMAF.",
    )

    heading(doc, "2.3.3. Nguyên lý hoạt động ở mức khái quát", 3)
    para(
        doc,
        "VMAF thuộc nhóm full-reference: nó so sánh video đã mã hóa (distorted) với video tham chiếu (reference). "
        "Trước khi trích đặc trưng, hai tín hiệu phải cùng độ phân giải và được căn chỉnh thời gian. Trong đề tài, "
        "bản encode được scale về đúng kích thước nguồn rồi mới đo, để các rung 360p và 720p có thể so được trên "
        "cùng một lưới pixel tham chiếu.",
    )
    para(
        doc,
        "Ở mức khái quát, VMAF kết hợp nhiều đặc trưng chất lượng (ví dụ các thành phần liên quan đến độ sắc nét, "
        "méo khối, và đo lường khác trong bộ công cụ VMAF) rồi dùng mô hình học để ánh xạ vector đặc trưng sang "
        "một điểm dự đoán cảm nhận. Đề tài không đi sâu kiến trúc machine learning và không tự huấn luyện lại mô hình. "
        "Mô hình dùng trong đo lường được cấu hình sẵn, ví dụ phiên bản built-in vmaf_v0.6.1 qua libvmaf. "
        "Điều quan trọng với thực nghiệm là giữ nguyên mô hình và quy trình tiền xử lý cho mọi candidate.",
    )

    heading(doc, "2.3.4. Cách sử dụng VMAF trong đề tài", 3)
    para(
        doc,
        "Video tham chiếu là video đầu vào đã chuẩn hóa (cùng nội dung nguồn dùng để encode). Video sau encode "
        "là từng file candidate. Kết quả VMAF là một điểm trung bình trên toàn clip (giá trị parse được từ log "
        "FFmpeg). Điểm này được ghi cùng bitrate thực tế, dung lượng, độ phân giải và tên rung. Không nội suy hay "
        "bịa điểm khi libvmaf lỗi: thiếu VMAF được xem là lỗi thực nghiệm, không phải “điểm 0”.",
    )
    para(
        doc,
        "Các điều kiện cần thống nhất khi so sánh gồm: cùng video nguồn; cùng mô hình VMAF; cùng cách scale "
        "(cùng flags nội suy); cùng không gian màu/pixel format đầu vào bộ lọc; cùng cách lấy trung bình theo clip. "
        "Vi phạm một trong các điều kiện này làm mất tính so sánh giữa các candidate.",
    )

    heading(doc, "2.3.5. Ưu điểm và giới hạn của VMAF", 3)
    para(
        doc,
        "Ưu điểm: lặp lại được, tự động hóa được, nhạy với nhiều dạng méo nén thường gặp trong streaming, "
        "phù hợp xếp hạng cấu hình encode. Giới hạn: điểm phụ thuộc nội dung, độ phân giải đo, mô hình và "
        "cách căn chỉnh; clip ngắn có thể làm điểm trung bình kém ổn định; VMAF không bao hết hiện tượng "
        "như méo màu đặc thù, audio, hay trải nghiệm sống động trên mọi thiết bị. Do đó VMAF không được dùng "
        "như bằng chứng duy nhất cho “mọi khía cạnh chất lượng”. Nó là thước đo chính trong không gian so sánh "
        "mà đề tài đã chọn, kèm các chỉ số bitrate, dung lượng và số rung.",
    )

    add_table(
        doc,
        ["Chỉ số", "Loại", "Vai trò trong đề tài"],
        [
            ["VMAF", "Khách quan, full-reference", "Chỉ số chất lượng chính khi chọn và so sánh ladder"],
            ["PSNR", "Khách quan, dựa trên MSE", "Phụ trợ, không quyết định ladder"],
            ["SSIM", "Khách quan, cấu trúc", "Phụ trợ, không quyết định ladder"],
            ["MOS", "Chủ quan", "Không thu thập trong demo nhỏ"],
            ["SI/TI", "Đặc trưng nội dung", "Mô tả độ phức tạp, không thay VMAF"],
        ],
        "Bảng 2.2. Các chỉ số liên quan đến chất lượng và nội dung",
    )

    # 2.4
    heading(doc, "2.4. Spatial Information và Temporal Information", 2)
    para(
        doc,
        "SI và TI là hai đặc trưng dùng để mô tả độ phức tạp không gian và mức độ thay đổi theo thời gian "
        "của video. Chúng giúp giải thích vì sao hai clip cùng độ phân giải có đường cong nén khác nhau. "
        "Chúng không phải điểm chất lượng và không thay thế VMAF.",
    )

    heading(doc, "2.4.1. Spatial Information (SI)", 3)
    para(
        doc,
        "Spatial Information đo lượng chi tiết/kết cấu trong từng khung. Trực quan, SI cao tương ứng ảnh nhiều "
        "biên, hoa văn mịn, chữ, tán cây, nhiễu chi tiết; SI thấp tương ứng vùng phẳng, nền đồng nhất, đồ họa đơn giản. "
        "SI liên hệ với độ phức tạp không gian: nội dung nhiều biên thường khó nén intra hơn.",
    )
    para(
        doc,
        "Khuyến nghị ITU-T P.910 định nghĩa SI trên khung độ sáng sau lọc Sobel, rồi lấy độ lệch chuẩn theo không gian "
        "và cực đại theo thời gian:",
    )
    formula(doc, "SI = max_n { σ_space [ Sobel(F_n) ] }", "(2.2)")
    para(
        doc,
        "F_n là khung độ sáng thứ n; Sobel(F_n) là độ lớn gradient (biên); σ_space là độ lệch chuẩn trên các pixel "
        "của bản đồ biên; max_n lấy giá trị lớn nhất theo thời gian. Ý nghĩa: một cảnh có khung cực kỳ nhiều chi tiết "
        "sẽ đẩy SI lên, dù các khung khác đơn giản hơn.",
        indent=True,
    )
    para(
        doc,
        "Đề tài sử dụng biến thể thực nghiệm, không phải bản chứng nhận P.910. Gradient Sobel được xấp xỉ trên "
        "khung xám đã giảm mẫu. SI của từng khung là độ lệch chuẩn của biên. Thay vì max theo thời gian, đề tài "
        "lấy trung vị:",
    )
    formula(doc, "SI_n = σ( |∇Sobel F_n| ),    SI = median({SI_n})", "(2.3)")
    para(
        doc,
        "Trung vị giảm ảnh hưởng của một cú cắt cảnh hoặc một khung nhiễu. Do lấy mẫu fps thấp và giảm độ phân giải "
        "khi phân tích, SI trong đề tài là ước lượng để so sánh tương đối, không dùng làm số liệu chuẩn phòng thí nghiệm. "
        "SI cao gợi ý nội dung giàu chi tiết; SI thấp gợi ý nội dung phẳng. Giới hạn: SI không biết biên đó có phải "
        "chi tiết quan trọng với người xem hay không; SI phụ thuộc tiền xử lý (độ phân giải phân tích, lọc).",
    )
    note(
        doc,
        "[CẦN BỔ SUNG NGUỒN THAM KHẢO CHO NỘI DUNG NÀY] ITU-T P.910 – định nghĩa SI/TI gốc. Công thức (2.3) là quy tắc triển khai của đề tài.",
    )

    heading(doc, "2.4.2. Temporal Information (TI)", 3)
    para(
        doc,
        "Temporal Information đo mức độ thay đổi giữa các khung liên tiếp. Trực quan, TI cao ứng với chuyển động mạnh, "
        "rung máy, đổi cảnh nhanh; TI thấp ứng với cảnh gần như tĩnh. TI liên hệ khả năng dự đoán liên khung: chuyển động "
        "phức tạp làm phần dư lớn, bitrate cần nhiều hơn để giữ chất lượng.",
    )
    para(
        doc,
        "P.910 định nghĩa TI từ hiệu hai khung độ sáng liên tiếp:",
    )
    formula(doc, "M_n(i,j) = F_n(i,j) − F_{n−1}(i,j)", "(2.4)")
    formula(doc, "TI = max_n { σ_space [ M_n ] }", "(2.5)")
    para(
        doc,
        "M_n là ảnh hiệu; σ_space là độ lệch chuẩn không gian của ảnh hiệu; max_n lấy cực đại theo thời gian. "
        "Một cú cắt cảnh có thể tạo TI rất lớn dù phần lớn video tĩnh.",
    )
    para(
        doc,
        "Đề tài dùng biến thể:",
    )
    formula(doc, "TI_n = σ(F_n − F_{n−1}),    TI = median({TI_n})", "(2.6)")
    para(
        doc,
        "TI_n cao nghĩa là khung n khác khung trước nhiều. Trung vị lại được dùng để giảm ảnh hưởng cắt cảnh đơn lẻ. "
        "Giới hạn: TI trên ảnh hiệu không phân biệt chuyển động máy quay và chuyển động đối tượng; giảm mẫu thời gian "
        "(sample fps) có thể bỏ qua chuyển động nhanh giữa hai mẫu. TI = 0 gần như cảnh không đổi theo thời gian, "
        "encoder có thể dùng rất ít bit so với target.",
    )

    heading(doc, "2.4.3. Vai trò của SI/TI trong đề tài", 3)
    para(
        doc,
        "Phân tích SI/TI được thực hiện trên video nguồn, trước hoặc song song với việc encode lưới candidate, "
        "nhằm mô tả đặc điểm nội dung. Khi so sánh hai video, cặp (SI, TI) giúp đọc đường cong bitrate–VMAF: "
        "video SI/TI cao thường bão hòa chậm hơn, cần rung bitrate lớn hơn để đạt cùng VMAF. SI/TI không trực tiếp "
        "sinh bitrate ladder trong phương pháp chính. Việc gán hệ số k từ chỉ số phức tạp tổ hợp chỉ phục vụ "
        "nhánh heuristic (k nhân ladder cố định) để đối chiếu, không phải quy trình Per-Title chính.",
    )
    para(
        doc,
        "Chỉ số phức tạp tổ hợp dùng trong mã nguồn là quy tắc đề xuất của thực nghiệm, không phải công thức P.910:",
    )
    formula(doc, "C = clip( 0,55·(SI / SI_ref) + 0,45·(TI / TI_ref) ,  0 , 1,5 )", "(2.7)")
    para(
        doc,
        "SI_ref và TI_ref là hằng số quy đổi về cùng thang (cấu hình thực nghiệm). C được gắn nhãn dễ/trung bình/khó "
        "theo ngưỡng cấu hình, rồi cho ra hệ số k heuristic. Không được diễn giải C như “độ phức tạp chuẩn ngành”.",
    )

    # 2.5
    heading(doc, "2.5. Đường cong bitrate–quality", 2)
    para(
        doc,
        "Đường cong bitrate–quality (rate–quality curve) mô tả chất lượng đạt được khi thay đổi lượng bit, "
        "trong điều kiện codec và nội dung cố định. Đây là công cụ trung tâm để nhìn thấy candidate nào tốn bit "
        "mà không đổi lấy chất lượng tương xứng.",
    )
    para(
        doc,
        "Trục hoành là bitrate thực tế (kbps). Trục tung là chỉ số chất lượng, ở đây là VMAF. Mỗi candidate "
        "là một điểm (R_i, Q_i). Tập điểm có thể tô màu theo độ phân giải để thấy sự chuyển mức không gian. "
        "Đường cong được đọc như một xu hướng, không nhất thiết nội suy thành hàm liên tục trừ khi bước so sánh "
        "cần nội suy tại một mức VMAF mục tiêu.",
    )
    para(
        doc,
        "Ở vùng bitrate thấp, Q tăng nhanh theo R. Sau một ngưỡng, ΔQ/ΔR giảm. Đây là lợi ích biên giảm dần: "
        "tăng bitrate không luôn đem lại mức tăng chất lượng tương ứng, đặc biệt khi đã gần giới hạn do độ phân giải "
        "nguồn hoặc do chính nội dung (cảnh đơn giản đã “đẹp sẵn”). Candidate nằm trên đoạn gần phẳng của đường cong "
        "dễ trở thành rung dư thừa.",
    )

    add_picture(
        doc,
        fig_dir / "fig_2_1_bitrate_quality.png",
        "Hình 2.1. Ví dụ minh họa đường cong bitrate–VMAF và lợi ích biên giảm dần (không phải số liệu đề tài)",
    )

    add_table(
        doc,
        ["Candidate minh họa", "Bitrate (kbps)", "VMAF", "Nhận xét"],
        [
            ["A", "400", "72", "Chất lượng thấp, còn dư địa tăng"],
            ["B", "800", "84", "Tăng bitrate 400 kbps, VMAF +12"],
            ["C", "1600", "91", "Tăng thêm 800 kbps, VMAF chỉ +7"],
            ["D", "3200", "93", "Tăng gấp đôi bitrate, VMAF +2: gần bão hòa"],
        ],
        "Bảng 2.3. Ví dụ minh họa lợi ích biên giảm dần (số liệu giả định)",
    )
    note(
        doc,
        "Bảng 2.3 và Hình 2.1 chỉ để giải thích khái niệm. Không sử dụng các số này như kết quả thực nghiệm.",
    )
    para(
        doc,
        "Vai trò của đường cong trong lựa chọn candidate là cung cấp bức tranh toàn cục trước khi lọc Pareto "
        "và trước khi áp dụng quy tắc chọn rung. Người phân tích nhìn thấy nhóm điểm kém hiệu quả, nhóm điểm "
        "chuyển độ phân giải, và vùng bão hòa. Đường cong không tự chọn ladder; nó là đầu vào trực quan và "
        "định lượng cho các bước lọc.",
    )

    # 2.6
    heading(doc, "2.6. Pareto frontier và Convex Hull trong phân tích candidate", 2)
    para(
        doc,
        "Khi đã có nhiều điểm (bitrate, VMAF), cần công cụ để loại phương án kém và nhận diện đường biên hiệu quả. "
        "Hai công cụ được dùng là tập Pareto (không bị chi phối) và bao lồi phía trên (upper convex envelope). "
        "Chúng không đồng nhất.",
    )

    heading(doc, "2.6.1. Khái niệm Pareto dominance", 3)
    para(
        doc,
        "Bài toán có hai mục tiêu xung đột: tối thiểu hóa bitrate và tối đa hóa VMAF. Candidate B chi phối "
        "(dominate) candidate A khi B không tệ hơn A trên cả hai mục tiêu và tốt hơn nghiêm ngặt ở ít nhất một mục tiêu:",
    )
    formula(
        doc,
        "B ⪰ A  khi  R_B ≤ R_A  và  Q_B ≥ Q_A,  đồng thời  (R_B < R_A  hoặc  Q_B > Q_A)",
        "(2.8)",
    )
    para(
        doc,
        "R là bitrate thực tế, Q là VMAF. Nếu B dùng ít bit hơn hoặc bằng A nhưng đạt VMAF cao hơn hoặc bằng, "
        "và không trùng hoàn toàn, thì A là phương án kém hiệu quả: không có lý do kỹ thuật để giữ A nếu chỉ xét "
        "hai mục tiêu này. Candidate bị chi phối được loại ở bước lọc, chưa phải bước dựng ladder cuối.",
    )

    heading(doc, "2.6.2. Pareto frontier", 3)
    para(
        doc,
        "Tập Pareto (Pareto frontier) là tập các candidate không bị bất kỳ candidate nào khác chi phối. "
        "Mọi điểm trên frontier đều là “tốt theo một nghĩa”: muốn tăng VMAF phải chấp nhận tăng bitrate, "
        "muốn giảm bitrate phải chấp nhận giảm VMAF. Frontier hình thành bằng cách duyệt toàn bộ điểm hợp lệ "
        "và loại điểm bị dominate, rồi sắp theo bitrate tăng dần.",
    )

    add_picture(
        doc,
        fig_dir / "fig_2_2_pareto.png",
        "Hình 2.2. Ví dụ minh họa điểm bị chi phối và Pareto frontier (không phải số liệu đề tài)",
    )

    heading(doc, "2.6.3. Convex Hull hoặc upper convex envelope", 3)
    para(
        doc,
        "Bao lồi của một tập điểm trên mặt phẳng là đa giác lồi nhỏ nhất chứa mọi điểm. Trong không gian "
        "bitrate–VMAF, phần có ý nghĩa với bài toán “chất lượng tốt nhất theo bitrate” là cạnh phía trên: "
        "upper convex envelope. Đường này nối các điểm sao cho không điểm nào nằm trên đoạn nối theo nghĩa "
        "lồi, và độ dốc phản ánh hiệu suất biên.",
    )
    para(
        doc,
        "Một điểm có thể nằm trên Pareto frontier nhưng không nằm trên bao lồi: đó là điểm “lõm”, hiệu suất "
        "biên thấp hơn tổ hợp nội suy của hai điểm lân cận trên hull. Upper envelope hữu ích khi muốn đọc "
        "đường biên lồi của khả năng nén. Đề tài tính upper convex hull bằng thuật toán monotone chain trên "
        "các điểm (R, Q), loại điểm trùng bitrate (giữ VMAF cao hơn) và loại điểm thẳng hàng phía trong.",
    )
    para(
        doc,
        "Khác biệt then chốt: Pareto là khái niệm tối ưu đa mục tiêu (không bị chi phối); convex hull là khái niệm "
        "hình học (bao lồi). Mọi điểm hull (phía trên) đều không bị chi phối, nhưng không phải mọi điểm Pareto "
        "đều nằm trên hull. Không được viết “Pareto tức là convex hull”. Cả hai chỉ hỗ trợ phân tích; chúng không "
        "tự động quyết định toàn bộ bitrate ladder.",
    )

    add_picture(
        doc,
        fig_dir / "fig_2_3_convex_hull.png",
        "Hình 2.3. Minh họa Pareto frontier khác upper convex envelope (không phải số liệu đề tài)",
    )

    heading(doc, "2.6.4. Phân biệt lọc candidate và lựa chọn ladder", 3)
    para(
        doc,
        "Lọc Pareto loại candidate bị chi phối. Phân tích hull thu hẹp thêm tập “nằm trên đường biên lồi”. "
        "Lựa chọn ladder là bước khác: từ tập đã lọc, áp dụng ràng buộc số rung, mức chất lượng mục tiêu, "
        "một đại diện mỗi độ phân giải, tính tăng dần bitrate, và tính hợp lý ứng dụng. Một điểm trên frontier "
        "có thể bị bỏ vì trùng chức năng với điểm khác, vì vượt quá số rung cho phép, hoặc vì VMAF dưới ngưỡng "
        "cấu hình. Nhầm hai bước này sẽ biến mọi điểm Pareto thành ladder, thường quá nhiều rung và không ABR-friendly.",
    )

    # 2.7
    heading(doc, "2.7. Các tiêu chí đánh giá bitrate ladder", 2)
    para(
        doc,
        "Một ladder không được chấm chỉ bằng một con số. Các tiêu chí sau được dùng song song, ở mức định tính "
        "và định lượng.",
    )
    para(
        doc,
        "Chất lượng hình ảnh được đại diện chủ yếu bởi VMAF từng rung và độ bao phủ các vùng chất lượng "
        "(thấp–trung–cao). Bitrate từng rung và bitrate đại diện (ví dụ rung cao nhất, hoặc tổng bitrate các rung) "
        "phản ánh chi phí truyền tải. Dung lượng file phản ánh chi phí lưu trữ VOD: mọi rung đều chiếm chỗ trên máy chủ. "
        "Số lượng rung phản ánh độ phức tạp vận hành và chi phí encode. Độ bao phủ chất lượng xét xem có khoảng VMAF "
        "quá lớn bị bỏ trống hay không. Tính hợp lý resolution–bitrate xét thứ tự tăng dần và việc không upscale. "
        "Hiệu quả bitrate–quality xét việc có rung nằm sâu dưới envelope hay không. Tính nhất quán điều kiện so sánh "
        "là điều kiện tiên quyết: cùng codec, cùng đo VMAF, cùng nguồn.",
    )
    para(
        doc,
        "Các tiêu chí có thể xung đột: giảm số rung làm thưa độ bao phủ; giảm bitrate có thể giảm VMAF. "
        "Chương 3 sẽ biến các tiêu chí này thành quy tắc lựa chọn và thành KPI so sánh với baseline.",
    )

    add_table(
        doc,
        ["Tiêu chí", "Đại lượng điển hình", "Hướng mong muốn trong demo"],
        [
            ["Chất lượng", "VMAF từng rung", "Đủ dùng, có rung tiệm cận bão hòa hợp lý"],
            ["Bitrate", "kbps thực tế / mục tiêu", "Không cấp thừa bit khi đã bão hòa"],
            ["Dung lượng", "byte hoặc KB/MB", "Giảm khi chất lượng tương đương"],
            ["Số rung", "số representation", "Hữu hạn, không trùng chức năng"],
            ["Bao phủ", "khoảng VMAF giữa các rung", "Không để khoảng trống quá lớn"],
            ["Hợp lý R–Q", "thứ tự height/bitrate", "Tăng dần, không upscale"],
        ],
        "Bảng 2.4. Tiêu chí đánh giá bitrate ladder",
    )

    # 2.8
    heading(doc, "2.8. Các chỉ số định lượng đánh giá hiệu quả tối ưu", 2)
    para(
        doc,
        "Mục tiêu diễn đạt gọn là “giữ chất lượng phù hợp nhưng giảm bitrate không cần thiết”. Các KPI dưới đây "
        "dùng để so sánh ladder đề xuất với ladder cố định (baseline). Chúng không chứng minh tối ưu toàn cục.",
    )

    heading(doc, "2.8.1. Tiết kiệm bitrate tại chất lượng tương đương", 3)
    para(
        doc,
        "Ý tưởng: cố định một mức chất lượng Q* và so sánh bitrate cần thiết của hai ladder. Điều kiện so sánh "
        "là cùng video, cùng codec, cùng cách đo VMAF. Công thức:",
    )
    formula(doc, "Bitrate Saving (%) = (R_baseline − R_proposed) / R_baseline × 100%", "(2.9)")
    para(
        doc,
        "R_baseline là bitrate (thực tế, sau nội suy nếu cần) của baseline tại Q*; R_proposed là bitrate của "
        "ladder đề xuất tại cùng Q*. Giá trị dương nghĩa là phương án đề xuất dùng ít bit hơn để đạt cùng VMAF. "
        "Giá trị âm nghĩa là đề xuất tốn bit hơn ở mức đó.",
    )
    para(
        doc,
        "Hai ladder hiếm khi có đúng cùng một điểm VMAF. Khi đó cần nội suy trên đường cong bitrate–VMAF "
        "(thường nội suy tuyến tính giữa hai điểm lân cận, trình bày ở Chương 3). Không được chọn tùy tiện "
        "một rung của A rồi so với một rung khác độ phân giải của B nếu chưa cùng Q*. Cũng không được trung bình "
        "bitrate mọi rung rồi gọi là “cùng chất lượng”.",
    )

    heading(doc, "2.8.2. Chênh lệch chất lượng tại bitrate tương đương", 3)
    para(
        doc,
        "Ý tưởng đảo: cố định một mức bitrate R* và so sánh VMAF:",
    )
    formula(doc, "ΔVMAF = VMAF_proposed − VMAF_baseline", "(2.10)")
    para(
        doc,
        "ΔVMAF dương: tại cùng mức tài nguyên, đề xuất đạt điểm VMAF cao hơn. Điều kiện áp dụng: R* phải nằm "
        "trong miền có thể nội suy của cả hai đường cong. Chênh lệch vài điểm VMAF trên clip ngắn chưa đủ để "
        "khẳng định khác biệt cảm nhận rõ với mọi người xem; KPI này chỉ là chênh lệch mô hình.",
    )

    heading(doc, "2.8.3. So sánh dung lượng và số lượng rung", 3)
    para(
        doc,
        "Tổng dung lượng ladder:",
    )
    formula(doc, "S_total = Σ_i S_i", "(2.11)")
    para(
        doc,
        "S_i là dung lượng file rung i. Chỉ số này phản ánh chi phí lưu trữ VOD. Có thể kèm tổng bitrate mục tiêu "
        "các rung hoặc bitrate rung cao nhất như bitrate đại diện cho truyền tải đỉnh. Số rung N_rung cho biết "
        "độ phức tạp. Giảm S_total đồng thời giảm N_rung có thể là tốt về chi phí, nhưng phải kiểm tra độ bao phủ "
        "chất lượng: một ladder một rung rất “tiết kiệm” có thể không còn là ladder ABR.",
    )

    heading(doc, "2.8.4. Giới hạn của các chỉ số đánh giá", 3)
    para(
        doc,
        "Không chỉ dựa vào một KPI. Bitrate saving cao tại một Q* có thể đi kèm mất rung trung gian. ΔVMAF tại "
        "một R* có thể không đại diện toàn miền. “Tương đương chất lượng” luôn là xấp xỉ vì VMAF liên tục còn "
        "ladder thì rời rạc. Kết quả phụ thuộc video, codec, preset, lưới candidate và cách đo. Với một clip ngắn, "
        "không suy ra quy luật cho thư viện VOD. Các KPI chỉ có nghĩa trong đúng điều kiện so sánh đã công bố.",
    )

    heading(doc, "2.9. Tóm tắt chương", 2)
    para(
        doc,
        "Chương 2 đã xác định các tham số encoding cần cố định, khái niệm rung và ladder, vai trò của VMAF, "
        "cách đọc SI/TI, đường cong bitrate–quality, sự khác nhau giữa Pareto và upper convex envelope, "
        "các tiêu chí đánh giá ladder và các KPI so sánh với baseline. Chương 3 chuyển các khái niệm này "
        "thành quy trình: từ một video đầu vào đến bitrate ladder đề xuất và phép so sánh.",
    )
