# Tài liệu kỹ thuật triển khai WO-020

## Cải tiến giao diện dashboard trực quan hơn

| | |
|---|---|
| **Work Order** | WO-020 |
| **Issue** | [#6](https://github.com/icarus7185/mes_mt/issues/6) |
| **Service** | `monitor` |
| **Loại thay đổi** | Frontend UI |
| **Phạm vi file được phép sửa** | `monitor/static/dashboard.js`, `monitor/static/style.css` |
| **API / Data layer** | Không thay đổi |
| **Phiên bản tài liệu** | 1.0 |
| **Ngày** | 2026-09-25 |
| **Trạng thái** | Ready for implementation |

> Mục tiêu của tài liệu là chuyển issue WO-020 thành hướng dẫn triển khai có thể kiểm tra được. Tài liệu không thay thế `monitor/docs/SPEC_MONITOR.md`; các hợp đồng API và quy tắc nghiệp vụ hiện tại vẫn giữ nguyên.

## 1. Bối cảnh và mục tiêu

### 1.1 Vấn đề

Dashboard hiện đã hiển thị các chỉ số vận hành, dự đoán năng lượng và ảnh lỗi bề mặt, nhưng người dùng phải tự suy luận:

- chỉ số nào là dữ liệu đo và chỉ số nào là kết quả do AI dự đoán;
- `Usage_kWh`, `Trend`, `Heavy load`, `NSM`, `PF`, `kVarh` có ý nghĩa gì;
- màu sắc hoặc trạng thái `Light_Load`, `Medium_Load`, `Maximum_Load` cần được ưu tiên xử lý ra sao;
- khi chưa có dữ liệu thì đây là trạng thái bình thường hay lỗi kết nối.

### 1.2 Mục tiêu triển khai

1. Làm rõ ý nghĩa của từng KPI bằng nhãn ngắn và mô tả ngữ cảnh.
2. Gắn nhận diện nhất quán cho mọi giá trị được mô hình AI tạo ra, đặc biệt là `Usage_kWh`.
3. Giúp người vận hành nhận biết nhanh mức độ tải và tình trạng dữ liệu mới nhất.
4. Giữ nguyên cấu trúc dữ liệu, chu kỳ polling 2 giây, API và logic tính toán hiện tại.
5. Duy trì khả năng sử dụng trên desktop, màn hình hẹp, light mode và dark mode.

## 2. Phạm vi và ràng buộc

### 2.1 Trong phạm vi

- Văn bản hiển thị, chú thích ngắn, tooltip và legend trên dashboard.
- Cách nhấn mạnh các vùng chứa dữ liệu AI dự đoán.
- Cải thiện hierarchy, trạng thái rỗng, màu sắc và affordance tương tác bằng CSS.
- Bổ sung thông tin hỗ trợ vào DOM bằng `dashboard.js` vì issue chỉ cho phép sửa static assets.
- Bổ sung nhãn accessible (`aria-label`, `aria-describedby`, trạng thái live) nếu cần trong hai file static.

### 2.2 Ngoài phạm vi

- Không sửa `monitor/templates/dashboard.html`.
- Không sửa bất kỳ endpoint hoặc schema nào trong `monitor/routers/`.
- Không sửa cách tính KPI, ngưỡng freshness, ngưỡng load hoặc thuật toán biểu đồ.
- Không thay đổi dữ liệu trả về từ `/api/records`, `/api/image/meta` và `/api/hist`.
- Không thêm thư viện bên thứ ba, bundler hoặc font/CDN mới.
- Không thêm cảnh báo email, SMS, WebSocket, đăng nhập hoặc phân quyền.
- Không diễn giải kết quả AI thành chẩn đoán chất lượng tuyệt đối; dashboard chỉ trình bày kết quả model đã trả về.

### 2.3 Quyết định kỹ thuật về giới hạn thư mục

Template hiện tại đã có các phần tử cần thiết cho dashboard. Do `Allowed Directory Scope` của issue là `/monitor/static`, phần nội dung bổ sung sẽ được tạo bằng JavaScript sau khi DOM load và được tạo kiểu bằng CSS. Nếu sau này cần thay đổi cấu trúc HTML cố định, phải mở rộng phạm vi issue trước khi sửa template.

## 3. Hiện trạng kỹ thuật

| Khu vực | Hiện trạng | Nhận định cho WO-020 |
|---|---|---|
| KPI | Có 4 tile: average, trend, freshness, heavy load | Cần đổi nhãn để giải thích giá trị và nguồn dữ liệu |
| Bảng record | Có cột `Power (kWh) (*predicted)` và màu riêng | Cần biến thành nhận diện AI rõ, nhất quán với chart |
| Biểu đồ | Có tiêu đề predicted, tooltip và giá trị cuối | Cần thêm legend/microcopy giải thích đây là dự đoán, không phải số đo trực tiếp |
| Load Type | Badge màu xanh/vàng/đỏ | Cần legend giải thích mức tải và không chỉ dựa vào màu |
| Ảnh lỗi | Có placeholder khi chưa có ảnh và lightbox | Cần mô tả rõ đây là ảnh bề mặt đã được AI phát hiện lỗi |
| Polling | Refresh mỗi 2 giây, dùng cùng response cho KPI và bảng | Giữ nguyên; không tạo thêm request |
| Theme | Có `prefers-color-scheme` | Giữ nguyên cơ chế, kiểm tra độ tương phản sau khi đổi CSS |

## 4. Định hướng trải nghiệm người dùng

### 4.1 Nguyên tắc thông tin

- **AI-generated:** dùng một treatment nhận diện thống nhất cho `Usage_kWh`, tiêu đề bảng và tiêu đề biểu đồ.
- **Measured/input context:** các cột sensor giữ vai trò dữ liệu đầu vào, không dùng màu AI.
- **Meaning before abbreviation:** viết rõ nghĩa ở tooltip/mô tả, vẫn giữ tên field kỹ thuật trong bảng để đối chiếu dữ liệu.
- **Status plus text:** màu sắc luôn đi cùng chữ hoặc ký hiệu, không dùng màu đơn độc.
- **Actionable priority:** `Maximum_Load` dùng nhãn "High load" và màu critical; không gọi đây là lỗi nếu bản thân record không phải lỗi.
- **Honest empty state:** trạng thái chưa có dữ liệu phải nói rõ "chưa nhận được" thay vì hiển thị giá trị 0.

### 4.2 Nội dung hiển thị đề xuất

| Thành phần hiện tại | Nội dung/diễn giải đề xuất | Mục đích |
|---|---|---|
| `Avg. Usage_kWh (last 20)` | `Average predicted energy` + mô tả `AI estimate across the latest 20 records` | Nói rõ đây là trung bình dự đoán |
| `Trend vs. previous` | `Change vs. previous prediction` + mô tả `Difference from the prior AI estimate` | Tránh hiểu là trend dài hạn |
| `Last update` | `Data freshness` + mô tả `Time since a new record reached monitor` | Phân biệt thời điểm polling với dữ liệu mới |
| `Heavy load (Maximum_Load)` | `High-load share` + mô tả `Records classified as Maximum_Load` | Giải thích mẫu số và phân loại |
| Tiêu đề bảng | `Recent energy predictions` | Ngắn và trực quan hơn |
| Cột `Power (kWh) (*predicted)` | `Predicted Usage_kWh` và badge `AI prediction` | Nhận diện rõ field do model điền |
| Tiêu đề chart | `Predicted energy trend` | Không tạo ấn tượng là công suất đo trực tiếp |
| Tiêu đề ảnh | `AI-detected surface defect` | Nêu rõ nguồn phát hiện và loại dữ liệu |
| Album | `Recent AI-detected defects` | Giải thích vì sao ảnh xuất hiện trong album |
| `Light_Load` | `Light load` | Dễ đọc nhưng vẫn giữ value gốc trong tooltip |
| `Medium_Load` | `Medium load` | Dễ đọc nhưng vẫn giữ value gốc trong tooltip |
| `Maximum_Load` | `High load` | Dễ hiểu cho operator, không gọi là defect |

Nội dung tiếng Anh được giữ nhất quán với dashboard hiện tại và các service spec. Tên field gốc như `Usage_kWh`, `NSM`, `PF`, `CO2` vẫn được giữ trong tooltip hoặc thông tin chi tiết để không mất khả năng đối chiếu kỹ thuật.

## 5. Thiết kế triển khai

### 5.1 `monitor/static/dashboard.js`

Thêm các helper frontend nhỏ, không thay đổi API contract:

- `addDashboardExplanations()` chạy một lần sau khi DOM load.
- Helper tạo phần tử chú thích với `textContent`, không dùng HTML từ dữ liệu server.
- Gắn `aria-describedby` cho từng KPI tile và các vùng chính.
- Tạo legend cho:
  - `AI prediction`;
  - `Light load` / `Medium load` / `High load`;
  - trạng thái dữ liệu freshness.
- Thêm tooltip native hoặc accessible description cho các thuật ngữ: `Usage_kWh`, `kVarh`, `PF`, `CO2`, `NSM`.
- Khi render record:
  - giữ nguyên giá trị `Usage_kWh` và phép format hiện tại;
  - thêm class/label cho ô predicted;
  - thêm accessible label cho badge load, bao gồm value gốc và nghĩa hiển thị.
- Khi render chart:
  - giữ nguyên điểm dữ liệu, tooltip và scale;
  - đảm bảo `aria-label` nói rõ chart thể hiện AI-predicted `Usage_kWh` theo thời gian.
- Khi có lỗi fetch hoặc chưa có dữ liệu, giữ nguyên cơ chế retry hiện tại nhưng hiển thị trạng thái dễ hiểu nếu DOM đã có vùng status.
- Gọi helper setup trước `refresh()` và không tạo thêm interval/request.

Không đưa nội dung từ record server vào `innerHTML`. Các nội dung động phải tiếp tục đi qua `textContent` hoặc thuộc tính DOM an toàn.

### 5.2 `monitor/static/style.css`

Bổ sung hoặc điều chỉnh CSS theo các nhóm sau:

1. **AI treatment**
   - Giữ một màu accent riêng cho predicted `Usage_kWh`.
   - Tạo treatment cho nhãn `AI prediction` có tương phản đủ trong light/dark mode.
   - Đồng bộ màu giữa KPI average, cột predicted, chart legend và chart line nhưng không phủ màu lên toàn bộ bảng.

2. **Information hierarchy**
   - Style cho `.metric-description`, `.panel-description`, `.legend`, `.ai-badge` và `.term-help`.
   - Mô tả nhỏ hơn label chính, có màu secondary, không chiếm quá nhiều chiều cao.
   - Không dùng card lồng trong card; phần giải thích là text/legend trong panel hiện tại.

3. **Load severity**
   - Giữ ba mức màu good/warning/critical hiện có.
   - Badge luôn hiển thị text, không chỉ dùng màu.
   - Cung cấp focus-visible rõ ràng cho phần tử tương tác.

4. **Responsive**
   - Ở viewport hẹp, KPI chuyển sang 2 cột rồi 1 cột.
   - Bảng tiếp tục scroll ngang trong vùng riêng, không làm vỡ toàn trang.
   - Chú thích và legend được phép wrap, không cắt chữ.
   - Không thay đổi kích thước cố định của chart theo cách làm mất tooltip hoặc label.

5. **Theme và contrast**
   - Kiểm tra cả `prefers-color-scheme: light` và `dark`.
   - Mọi trạng thái phải đạt tương phản đủ; không dựa riêng vào màu tím hoặc một màu duy nhất để truyền đạt ý nghĩa.
   - Không thêm gradient nền, ảnh nền hoặc dependency visual mới.

6. **Motion**
   - Giữ row flash cho record mới.
   - Không thêm animation liên tục ngoài live pulse hiện có; giảm motion khi `prefers-reduced-motion: reduce`.

### 5.3 Thứ tự xử lý dữ liệu

Giữ nguyên luồng hiện tại:

1. `refresh()` lấy metadata ảnh, album và records theo các endpoint hiện có.
2. Một response `/api/records` được dùng cho bảng, chart và cả bốn KPI.
3. `renderRecords()` tiếp tục cập nhật `lastTopRecordKey` và freshness.
4. Các helper giải thích chỉ chạy một lần; không chèn lại legend/description sau mỗi lần polling.
5. Các trạng thái rỗng tiếp tục dùng `--` hoặc placeholder, không tự suy diễn giá trị.

## 6. Ma trận file và thay đổi

| File | Thay đổi | Không thay đổi |
|---|---|---|
| `monitor/static/dashboard.js` | DOM enhancement, nhãn accessible, tooltip/legend, nhãn AI và load dễ hiểu | URL API, payload, công thức KPI, timer 2 giây |
| `monitor/static/style.css` | Typography hierarchy, AI badge, legend, responsive và contrast | Layout nghiệp vụ 4 vùng, lightbox behavior, retention |
| `monitor/templates/dashboard.html` | Không sửa theo constraint | Markup gốc được tái sử dụng |
| `monitor/routers/api.py` | Không sửa | API và response schema |
| `monitor/services/*` | Không sửa | Lưu trữ, tính toán server, model |

## 7. Tiêu chí nghiệm thu

### 7.1 Functional

- Người dùng nhìn vào dashboard có thể xác định ngay `Usage_kWh` là giá trị AI dự đoán.
- KPI average, trend và chart đều có diễn giải ngắn, không gây hiểu nhầm là số đo trực tiếp.
- Người dùng hiểu `Data freshness` đo thời gian từ record mới nhất đến hiện tại, không phải thời gian polling cuối cùng.
- Người dùng hiểu `High-load share` là tỷ lệ record `Maximum_Load` trong cửa sổ đang hiển thị.
- `Light_Load`, `Medium_Load`, `Maximum_Load` có chữ dễ hiểu và vẫn giữ được value gốc khi cần đối chiếu.
- Khu vực ảnh nói rõ đây là ảnh lỗi bề mặt do AI phát hiện.
- Trạng thái không có dữ liệu phân biệt được với trạng thái có giá trị bằng 0.
- Không phát sinh request API mới cho tooltip, legend hoặc KPI.

### 7.2 Accessibility

- Các mô tả quan trọng được đọc được bởi screen reader thông qua text hoặc `aria-describedby`.
- Màu không phải tín hiệu duy nhất để phân biệt mức tải hoặc trạng thái.
- Ảnh, lightbox và các phần tử đang có keyboard interaction tiếp tục hoạt động với `Enter`, `Space` và `Escape`.
- Focus-visible đủ rõ ở light mode và dark mode.
- Với `prefers-reduced-motion: reduce`, animation không gây khó chịu và không làm mất nội dung.

### 7.3 Responsive và visual

- Dashboard đọc được ở desktop và viewport hẹp mà không có text bị chồng lấp.
- Bảng có thể cuộn ngang độc lập; phần KPI không bị ép nhỏ đến mức mất nghĩa.
- Mô tả dài nhất không tràn khỏi tile/panel.
- Predicted column, AI badge, chart line và legend dùng cùng một ngữ nghĩa màu.
- Lightbox, chart tooltip và ảnh album không bị che bởi phần tử mới.

## 8. Kế hoạch kiểm thử

### 8.1 Kiểm thử tĩnh

- Kiểm tra chỉ có `monitor/static/dashboard.js` và `monitor/static/style.css` thay đổi.
- Tìm các URL API để xác nhận không có endpoint mới.
- Tìm `innerHTML` trong phần code mới; dữ liệu server không được chèn trực tiếp bằng HTML string.
- Kiểm tra không thêm package hoặc CDN.

### 8.2 Kiểm thử trình duyệt thủ công

Dùng hệ thống đang chạy tại `http://localhost:8003/`:

1. Mở dashboard khi chưa có record/ảnh và xác nhận empty state dễ hiểu.
2. Chờ record mới, xác nhận row đầu tiên flash một lần và freshness cập nhật đúng.
3. Kiểm tra average, trend, high-load share với dữ liệu hiện có.
4. Hover chart để xác nhận tooltip vẫn đúng timestamp/value.
5. Click và keyboard-activate ảnh để mở lightbox; đóng bằng nút, click nền và `Escape`.
6. Kiểm tra light mode và dark mode.
7. Kiểm tra viewport desktop, tablet và mobile; xác nhận không tràn/chồng lấp.
8. Bật reduced motion và xác nhận animation được giảm/tắt phù hợp.

### 8.3 Regression bắt buộc

- Polling vẫn chạy mỗi 2 giây và không reload toàn trang.
- `/api/records`, `/api/hist`, `/api/image/meta` vẫn được gọi như trước.
- Bảng vẫn hiển thị đủ các cột sensor và predicted `Usage_kWh`.
- Chart vẫn có line, gridline, end label, crosshair và tooltip.
- Album vẫn hiển thị tối đa số ảnh do backend trả về và lightbox vẫn dùng đúng filename.
- Không có lỗi JavaScript trong DevTools Console.

## 9. Rủi ro và cách giảm thiểu

| Rủi ro | Tác động | Cách giảm thiểu |
|---|---|---|
| Không sửa template nên DOM enhancement phụ thuộc selector hiện có | UI không xuất hiện nếu selector đổi | Dùng selector hiện hữu, fail soft khi thiếu node, kiểm tra sau mỗi lần render |
| Thêm quá nhiều chú thích làm dashboard chật | Giảm khả năng quét nhanh | Dùng microcopy một dòng, tooltip cho thuật ngữ chi tiết |
| Người dùng hiểu `Maximum_Load` là defect | Quyết định sai mức ưu tiên | Dùng nhãn `High load`, giữ panel defect riêng và không trộn hai khái niệm |
| Màu AI giảm tương phản trong dark mode | Khó đọc/không đạt accessibility | Kiểm thử hai theme và dùng text `AI prediction` đi kèm |
| DOM bị chèn lặp sau mỗi polling | Layout phình và giảm hiệu năng | Tạo marker/id và chỉ chạy enhancement một lần |
| Dữ liệu động bị chèn bằng HTML | XSS hoặc lỗi hiển thị | Dùng `textContent`, không dùng `innerHTML` cho giá trị server |

## 10. Definition of Done

- [ ] Tất cả thay đổi nằm trong `monitor/static/`.
- [ ] Nhãn và mô tả làm rõ dữ liệu AI dự đoán, input sensor và load severity.
- [ ] Không thay đổi API, backend, model hoặc công thức KPI.
- [ ] Light/dark mode và responsive layout đã được kiểm tra.
- [ ] Keyboard interaction, focus-visible và reduced motion đã được kiểm tra.
- [ ] Không có lỗi JavaScript trong console với cả empty state và populated state.
- [ ] Các tiêu chí nghiệm thu của issue WO-020 được kiểm tra trên dashboard đang chạy.
