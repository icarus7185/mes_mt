# Bộ prompt dựng project

## A. Viết tài liệu

** Gợi ý cách viết brief**

````text
Hãy gợi ý tôi cách viết brief để triển khai ý tưởng:
3 microservice theo dõi hệ thống MES gồm: 
- collect data gửi tới trung tâm
- phân tích data bằng machine learning
- hiển thị kết quả phân tích
````

** Tài liệu yêu cầu nghiệp vụ**

````text
Tôi đang làm một bản PoC hệ thống giám sát cho dây chuyền cán thép.

Khách hàng đang gặp hai vấn đề:
- Lỗi bề mặt thép hiện được kiểm tra bằng mắt nên hay bị sót.
- Điện năng tiêu thụ chỉ biết được khi có hoá đơn cuối tháng.

Họ muốn hệ thống làm được những việc sau:
- Tự kiểm tra ảnh bề mặt từ camera bằng AI. Chỉ ảnh có lỗi mới báo lên cho người vận hành, kèm ảnh để xem lại.
- Dự đoán điện năng tiêu thụ theo thời gian thực, vẽ thành biểu đồ để thấy bất thường ngay trong ca.
- Mạng nhà máy hay chập chờn, nên lần gửi dữ liệu nào lỗi thì phải hiện ra cho người vận hành thấy. Khi lâu không có dữ liệu mới cũng phải thấy được.
- Mọi kết quả dự đoán điện năng được lưu lại để phân tích sau. Ảnh lỗi thì chỉ cần giữ vài ảnh gần nhất.
- Người phụ trách model có thể train lại model khi có dữ liệu mới.
- Mọi thứ nằm trên một dashboard đơn giản, trưởng ca nhìn là hiểu.
- Hệ thống phải gọn nhẹ, một nhóm nhỏ tự dựng và chạy được.

Giai đoạn này chưa có camera và cảm biến thật, nên cả hai nguồn dữ liệu đều được giả lập từ dữ liệu mẫu. Chưa làm các phần sau:
- kết nối thiết bị thật;
- cảnh báo qua email/SMS;
- đăng nhập, phân quyền;
- chạy nhiều dây chuyền.

Dựa vào mô tả trên, viết giúp tôi docs/BUSINESS_REQUIREMENTS.md. Người đọc là sếp và phía nhà máy, nên viết bằng ngôn ngữ nghiệp vụ, đừng đưa chi tiết kỹ thuật vào.
Tài liệu cần có: vấn đề, mục tiêu, các bên liên quan, phạm vi làm và không làm, tiêu chí thành công, rủi ro.
Tài liệu viết bằng tiếng Anh.
````

** Spec tổng thể**

````text
Viết docs/SPEC_SYSTEM_OVERVIEW.md, mô tả 3 service ghép với nhau thế nào: kiến trúc, 3 pipeline (ảnh, điện năng, giả lập lỗi), và format dữ liệu gửi qua lại giữa các service.
Chi tiết bên trong từng service để dành cho spec riêng của service đó.
Cuối tài liệu thêm hướng dẫn chạy cả hệ thống.
````

** Spec từng service**

````text
Viết spec cho service <prod_line | asst | monitor>, lưu ở <service>/docs/SPEC_<SERVICE>.md.
Mỗi yêu cầu chức năng đánh mã FR-P1, FR-A1, FR-M1... và có acceptance criteria kiểm tra được.
Ngoài ra cần có: API, bảng config kèm giá trị mặc định, và cấu trúc thư mục.
Đọc thêm SPEC_SYSTEM_OVERVIEW.md để tránh viết lặ
````

** Domain model**

````text
Viết docs/DOMAIN_MODEL.md: hệ thống có những đối tượng dữ liệu nào (ảnh, record, file model), chúng thay đổi thế nào khi đi qua 3 service, và class nào giữ chúng.
Vẽ sơ đồ class bằng Mermaid. Tên class ở đây sẽ là tên dùng khi code.
````

** API spec**

````text
Viết docs/api-spec.md, liệt kê mọi endpoint của 3 service.
Mỗi endpoint ghi rõ: request, các mã trạng thái có thể trả về, và ví dụ JSON.
````

** Coding rules**

````text
Viết docs/CODING_RULES.md cho code Python của repo này. Mỗi quy tắc có mã riêng (PY-001...) và mức MUST/SHOULD để AI review theo được.
Cần bao gồm: cấu trúc module, đặt tên, type hint, logging, xử lý lỗi, async, config, test.
Cuối tài liệu thêm checklist các quy tắc MUST.
````

** Rà soát tài liệu **

````text
Đọc lại toàn bộ tài liệu vừa viết, so với brief và so chéo giữa các tài liệu với nhau. Tìm: chỗ thiếu, con số hoặc tên gọi không khớp, link sai, acceptance criteria mơ hồ.
Chỗ nào sai thì sửa luôn, rồi gửi tôi danh sách những gì đã sửa.
````


** Cập nhật tài liệu sau khi đổi code (mẫu chung)**

````text
Tôi vừa sửa <mô tả thay đổi, hoặc dán git diff / số commit>.
Tìm mọi tài liệu (docs/, */docs/, README.md) đang mô tả phần này và cập nhật cho khớp với code mới. Đừng viết lại những phần không liên quan.
Gửi tôi danh sách chỗ đã sửa.
````

** Thêm yêu cầu mới vào spec trước khi code**

````text
Tôi muốn thêm chức năng: monitor cho tải file lịch sử dự đoán dạng CSV từ dashboard.
Viết trước phần spec: thêm FR mới vào SPEC_MONITOR.md (có acceptance criteria), thêm endpoint vào api-spec.md, cập nhật DOMAIN_MODEL.md nếu cần. Chưa code gì cả.
Chỗ nào chưa rõ (tên file khi tải về, trường hợp chưa có dữ liệu...) thì hỏi tôi.
````

** Sửa đường dẫn tài liệu bị sai**

````text
Mấy tài liệu trong docs/ đang dẫn đến docs/SPEC_PROD_LINE.md, docs/SPEC_ASST.md, docs/SPEC_MONITOR.md, nhưng thật ra các spec này nằm trong <service>/docs/. Tìm hết các link sai và sửa lại cho đúng.
````

** Viết lại tài liệu từ code**

````text
Spec của service <tên service> đã cũ, không còn khớp với code. Đọc code hiện tại của service đó rồi viết lại <service>/docs/SPEC_<SERVICE>.md, giữ nguyên khung và mã FR cũ. FR nào không còn thì đánh dấu removed chứ đừng xoá mã, FR mới thì đánh mã tiếp theo.
Chỗ nào code có vẻ làm sai so với spec cũ thì đừng tự chọn bên nào đúng, ghi ra cho tôi.
````

** Cập nhật README**

````text
Cập nhật README.md:
- thêm cấu trúc thư mục đầy đủ;
- trong phần cài đặt, thêm hướng dẫn giải nén prod_line/data/from_camera/test_images.zip ngay tại thư mục đó rồi xoá file zip.
Lệnh nào cũng ghi cho cả Bash và PowerShell.
````

** Dịch tài liệu**

````text
Dịch README.md sang tiếng Anh. Giữ nguyên các lệnh, đường dẫn, tên field và thuật ngữ như kVarh, PF, NSM, Usage_kWh. Viết tự nhiên như người viết tài liệu kỹ thuật, đừng dịch sát từng chữ.
````

** Ghi lại một quyết định kỹ thuật**

````text
Chúng tôi vừa quyết định <ví dụ: giữ file model đã train trong repo thay vì bắt người dùng gọi /api/train sau khi clone>.
Viết một ghi chú ngắn vào docs/decisions/, gồm: bối cảnh, quyết định, lý do, và ảnh hưởng. Tài liệu nào đang mô tả ngược với quyết định này thì sửa luôn.
````

