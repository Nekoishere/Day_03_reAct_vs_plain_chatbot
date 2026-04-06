# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Công Nhật Tân
- **Student ID**: 2A202600141
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implementated**: `src/api/api.py`, `src/core/openai_provider.py`, `trace.md`, 
- **Code Highlights**: 
    - Triển khai **FastAPI Server** để bọc Agent/Chatbot thành một REST API chuyên nghiệp.
    - Thiết lập cơ chế **Auto-Fallback** giữa OpenAI và Gemini trong `openai_provider.py`: Nếu OpenAI bị Rate Limit (429), hệ thống tự động đổi sang dùng Gemini để không ngắt quãng trải nghiệm người dùng.
    - Cấu hình **Threading Lock** trong API để xử lý tuần tự các request LLM, tránh tình trạng spam API gây lỗi đồng thời.
- **Documentation**: Viết file `API_SETUP_GUIDE.md` hướng dẫn chi tiết cách deploy và test các endpoint bằng Swagger UI và Postman.

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: Lỗi trùng lặp lệnh gọi API sau khi giải quyết Conflict Git (`git pull`).
- **Log Source**: `logs/2026-04-06.log` cho thấy độ trễ tăng đột biến và Agent bị treo không phản hồi.
- **Diagnosis**: Trong file `openai_provider.py`, do quá trình merge code thủ công bị lỗi, hàm `self.client.chat.completions.create` bị gọi lặp lại 2 lần liên tiếp. Kèm theo cơ chế `threading.Lock`, request đầu tiên bị kẹt khiến tất cả các request sau đó đều phải xếp hàng chờ vô hạn.
- **Solution**: Xoá bỏ dòng code thừa, gộp logic gọi API vào duy nhất một khối `try-except` xử lý Rate Limit.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: Vòng lặp ReAct giúp Model có khả năng "chia để trị", bẻ nhỏ một câu hỏi phức tạp thành các bước suy luận (*Thought*) và hành động (*Action*). Điều này giúp Agent có thể giải quyết các bài toán yêu cầu logic nhiều bước mà Chatbot thông thường thường xuyên bị "quên" hoặc "loạn" thông tin.
2.  **Reliability**: Agent cực kỳ đáng tin cậy vì nó "biết những gì nó không biết". Thay vì bịa ra tỉ số trận đấu (Hallucination) như Chatbot, Agent sẽ chủ động gọi Tool Search để lấy dữ liệu thực và chỉ trả lời dựa trên những gì nó quan sát được (*Observation*).
3.  **Observation**: Dữ liệu từ Observation đóng vai trò là "Ground Truth". Nó không chỉ cung cấp thông tin mới mà còn giúp Agent tự điều chỉnh hướng suy luận nếu bước trước đó chưa mang lại kết quả mong muốn.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: Sử dụng **Redis Queue** hoặc **Celery** để quản lý hàng đợi Request Agent thay vì chỉ dùng Threading Lock đơn giản, giúp hệ thống chịu tải được hàng ngàn người dùng cùng lúc.
- **Safety**: Tích hợp các lớp **Guardrails** (như NeMo Guardrails) để kiểm duyệt câu trả lời của Agent, tránh trường hợp Agent thực thi các tool có tính chất phá hoại hoặc trả lời các nội dung nhạy cảm.
- **Performance**: Áp dụng **Semantic Caching** (như GPTCache) để lưu trữ các câu trả lời trùng lặp, giúp giảm chi phí API và tăng tốc độ phản hồi cho những câu hỏi phổ biến.

---
