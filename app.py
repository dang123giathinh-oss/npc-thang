import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

# Khởi tạo ứng dụng FastAPI
app = FastAPI()

# Cấu hình CORS để Roblox kết nối mượt mà không bị chặn
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo Groq Client (Lấy API Key từ Environment Variable của Render)
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Định dạng dữ liệu nhận vào từ Roblox NPC (Giữ nguyên cấu trúc cũ để tránh lỗi liên kết)
class NPCData(BaseModel):
    trigger: str
    environment: dict
    current_state: str
    extra: str = "" # Thường dùng để truyền tin nhắn chat của người chơi đứng gần

# =================================================================
# ENDPOINT KIỂM TRA TRẠNG THÁI SERVER (GET/HEAD)
# =================================================================
@app.api_route("/ping", methods=["GET", "HEAD"])
async def ping():
    return {
        "status": "ok",
        "message": "Bộ não của Thắng đang hoạt động bình thường."
    }

# =================================================================
# ENDPOINT CHÍNH: XỬ LÝ CHAT VÀ ĐỊNH HƯỚNG DI CHUYỂN
# =================================================================
@app.post("/api/npc")
async def npc_control(data: NPCData):
    try:
        # Chuẩn hóa dữ liệu khoảng cách cảm biến từ 8 hướng
        env = data.environment
        env_description = (
            f"Trước mặt (Forward): {env.get('Forward')}m, "
            f"Chéo trước-phải (ForwardRight): {env.get('ForwardRight')}m, "
            f"Chính phải (Right): {env.get('Right')}m, "
            f"Chéo sau-phải (BackwardRight): {env.get('BackwardRight')}m, "
            f"Chính sau (Backward): {env.get('Backward')}m, "
            f"Chéo sau-trái (BackwardLeft): {env.get('BackwardLeft')}m, "
            f"Chính trái (Left): {env.get('Left')}m, "
            f"Chéo trước-trái (ForwardLeft): {env.get('ForwardLeft')}m."
        )

        # SYSTEM PROMPT MỚI: Chỉ tập trung vào CHAT và ĐỊNH HƯỚNG
        system_prompt = f"""Bạn là bộ não điều khiển hướng đi và lời thoại của NPC tên Thắng trong game Roblox.
Nhiệm vụ duy nhất của bạn là xử lý hai công việc sau:

1. GIAO TIẾP (CHAT): Đưa ra câu thoại tự nhiên, ngắn gọn bằng tiếng Việt (giọng điệu ngầu, thông minh, bướng bỉnh và độc lập).
   - Nếu trong phần 'Thông tin bổ sung / Chat' có tin nhắn từ người chơi, bạn hãy tập trung trả lời hoặc phản hồi lại câu nói của họ.
   - Nếu không có ai chat xung quanh, hãy đưa ra một câu tự thoại ngắn thể hiện suy nghĩ của Thắng về việc di chuyển hoặc quan sát không gian xung quanh.

2. ĐỊNH HƯỚNG (NAVIGATION): Dựa vào bản đồ khoảng cách cảm biến 8 hướng dưới đây để chọn hướng rẽ an toàn nhất, tránh đâm sầm vào tường.

Thông số hiện tại:
- Trạng thái vật lý: {data.current_state}
- Sự kiện kích hoạt (trigger): {data.trigger}
- Bản đồ khoảng cách 8 hướng: {env_description}
- Thông tin bổ sung / Chat của người chơi: {data.extra}

QUY TẮC ĐỊNH HƯỚNG BẮT BUỘC:
- Ưu tiên chọn hướng có khoảng cách mét lớn nhất (thông thoáng nhất).
- Nếu phía trước thoáng (Forward > 7.0m), hãy giữ hướng đi thẳng (action='Move', turn_direction='Forward').
- Nếu phía trước sắp va chạm (Forward < 5.0m), hãy quét các hướng bên cạnh để chọn ra hướng rộng rãi nhất rẽ sang. Hạn chế tối đa việc xoay ngược 180 độ liên tục giữa Forward và Backward trừ khi bị chặn hoàn toàn ở các hướng bên.
- Nếu bị vây kín và kẹt cứng ở mọi phía (< 3.0m), hãy chọn đứng yên để quan sát (action='Stop', turn_direction='Forward').

BẮT BUỘC trả về kết quả duy nhất dưới định dạng JSON sau (TUYỆT ĐỐI không viết thêm chữ thừa ngoài cấu trúc JSON này):
{{
    "reply": "Câu nói ngắn gọn của Thắng",
    "action": "Move",
    "turn_direction": "Forward"
}}"""

        user_content = f"Xử lý yêu cầu dựa trên trigger: {data.trigger}."

        # Gọi API của Groq sử dụng mô hình Llama 3.1
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",  
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.4, # Tăng nhẹ độ sáng tạo cho các câu thoại thêm tự nhiên
            response_format={"type": "json_object"} 
        )

        # Lấy văn bản phản hồi và chuyển đổi thành Dictionary để phản hồi về Roblox
        ai_response_text = completion.choices[0].message.content
        response_data = json.loads(ai_response_text)
        
        return response_data

    except Exception as e:
        print(f"Lỗi hệ thống: {str(e)}")
        # Phương án dự phòng cục bộ để NPC vẫn tự hoạt động khi API Groq gặp sự cố tạm thời
        return {
            "reply": "Chờ chút, để tao tự nhìn đường đi tiếp...",
            "action": "Move",
            "turn_direction": "Forward"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
