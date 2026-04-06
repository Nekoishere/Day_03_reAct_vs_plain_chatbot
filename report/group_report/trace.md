# Trace Hệ Thống (Dựa trên Workflow Diagram)

Bản mô tả tiến trình xử lý của hệ thống chatbot bóng đá, tương ứng với các thành phần trong sơ đồ workflow.

### **Kịch bản mẫu: "Tối nay Việt Nam có trận nào không?"**

1.  **User Input (UI):**
    *   Người dùng nhập câu hỏi vào giao diện: "Tối nay Việt Nam có trận nào không?"
  
2.  **Preprocessing:**
    *   Hệ thống làm sạch văn bản, chuẩn hóa đầu vào (ví dụ: chuyển thành "toi nay viet nam co tran nao khong").

3.  **Identify Intent / Query Type:**
    *   Phân loại ý định của người dùng.
    *   **Kết quả:** Xác định đây là một câu hỏi về bóng đá (**Sports Query = True**).

4.  **Sports ReAct Agent (Luồng Xử Lý Nâng Cao):**
    *   Hệ thống khởi chạy Agent bóng đá.
    *   **Tool Selection:** Chọn bộ công cụ `football_tools.py` (ví dụ: `get_next_fixture`).
    *   **API Interaction:** Gửi yêu cầu tìm kiếm lịch thi đấu của Đội tuyển Việt Nam.
    *   **Process Response:** Nhận kết quả từ công cụ tìm kiếm: "Vietnam vs Indonesia, 19:00, 15/05/2026".

5.  **LLM Processing (Giai Đoạn "Loading"):**
    *   **History & Token Management:** Tính toán lịch sử hội thoại và giới hạn token.
    *   **Formatted Prompt:** Kết hợp thông tin từ Tool vào Prompt để LLM xử lý.
    *   **Cost Calculation:** Ước tính chi phí cuộc gọi API.
    *   **Final Answer:** LLM tạo ra câu trả lời tự nhiên dựa trên dữ liệu thật.

6.  **Display & Output:**
    *   Hiển thị phản hồi: "Dạ có, đội tuyển Việt Nam sẽ đá với Indonesia vào lúc 19:00 tối nay nhé!"
    *   Lưu vào lịch sử hội thoại và chờ câu hỏi tiếp theo.

---

### **Kịch bản dự phòng (Ví dụ: "Chào bạn"):**
1.  **Identify Intent:** Xác định không phải câu hỏi bóng đá (**Sports Query = False**).
2.  **Plain Chatbot Path:** Bỏ qua bước gọi Tool (Agent), chuyển thẳng đến bước tạo câu trả lời thông thường.
3.  **Output:** "Chào bạn! Tôi có thể hỗ trợ gì cho bạn về thông tin bóng đá?"
