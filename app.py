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
# Tên biến trên Render mày cấu hình là: GROQ_API_KEY
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Định dạng dữ liệu nhận vào từ Roblox NPC
class NPCData(BaseModel):
    trigger: str
    environment: dict
    current_state: str
    extra: str = ""

# =================================================================
# 🔥 FIX LỖI 405: CHO PHÉP NHẬN CẢ LỆNH HEAD CỦA UPTIMEROBOT MIỄN PHÍ
# =================================================================
@app.route("/ping", methods=["GET", "HEAD"])
async def ping():
    return {
        "status": "ok",
        "message": "Server đang sống nhăn răng! Kết nối thành công rồi nhé bro."
    }

# =================================================================
# ENDPOINT CHÍNH CHỨA BỘ NÃO AI CỦA NPC (POST)
# =================================================================
@app.post("/api/npc")
async def npc_control(data: NPCData):
    try:
        # Chuẩn hóa thông số cảm biến không gian 8 hướng
        env = data.environment
        env_description = (
            f"Chính diện trước: {env.get('Forward')}m, "
            f"Chéo trước-Phải (45°): {env.get('ForwardRight')}m, "
            f"Chính phải (90°): {env.get('Right')}m, "
            f"Chéo sau-Phải (135°): {env.get('BackwardRight')}m, "
            f"Chính sau (180°): {env.get('Backward')}m, "
            f"Chéo sau-Trái (225°): {env.get('BackwardLeft')}m, "
            f"Chính trái (270°): {env.get('Left')}m, "
            f"Chéo trước-Trái (315°): {env.get('ForwardLeft')}m."
        )

        # PROMPT CHUẨN: Sử dụng dấu 3 nháy kép để xuống dòng tự nhiên, KHÔNG cần dùng \n rối mắt
        # Sử dụng model llama-3.1-8b-instant mới nhất chống lỗi model_decommissioned (400)
        system_prompt = f"""Bạn là bộ não điều khiển hướng di chuyển và hành động của một NPC thông minh tên Thắng trong Roblox.
Nhiệm vụ của bạn là phân tích dữ liệu khoảng cách vách tường từ cảm biến 8 hướng xung quanh để đưa ra quyết định di chuyển tối ưu nhất.

Dữ liệu hiện tại:
- Trạng thái hiện tại của NPC: {data.current_state}
- Tình huống kích hoạt (trigger): {data.trigger}
- Bản đồ cảm biến 8 hướng: {env_description}
- Thông tin bổ sung: {data.extra}

QUY TẮC DI CHUYỂN BẮT BUỘC:
1. Nếu hướng 'Forward' thoáng (khoảng cách > 7.0m), BẮT BUỘC trả về action='Explore' và turn_direction='Forward'.
2. Tuyệt đối KHÔNG ĐƯỢC bắt NPC đổi hướng liên tục 180 độ giữa 'Forward' và 'Backward' ở hai chu kỳ liên tiếp (gây lỗi giật lên giật xuống liên tục).
3. Nếu phía trước bị chặn (Forward < 5.0m), hãy ưu tiên chọn rẽ sang các hướng thông thoáng khác có khoảng cách mét lớn nhất như 'Left', 'Right', 'ForwardLeft', hoặc 'ForwardRight'.
4. CHỈ ĐƯỢC chọn action='Escape' và turn_direction='Backward' khi phía trước bị khóa cứng VÀ các hướng bên cạnh cũng bị chặn chật hẹp (< 4.0m).
5. Câu thoại (reply) phải ngắn gọn, tự nhiên, mang tính chất của một NPC đang tự sinh tồn.

BẮT BUỘC trả về kết quả duy nhất dưới định dạng JSON mẫu sau (TUYỆT ĐỐI không viết thêm chữ thừa hay ký hiệu markdown như ```json):
{{
    "reply": "Câu nói ngắn gọn của NPC",
    "action": "Explore",
    "turn_direction": "Forward"
}}"""

        user_content = f"Hãy xử lý hành động tiếp theo dựa trên trigger: {data.trigger}."

        # Gọi API của Groq (Dùng Llama 3.1 mượt mà ổn định)
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",  
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.3, 
            response_format={"type": "json_object"} 
        )

        # Lấy kết quả text từ AI và parse ngược lại thành Dictionary gửi về cho Roblox
        ai_response_text = completion.choices[0].message.content
        response_data = json.loads(ai_response_text)
        
        return response_data

    except Exception as e:
        print(f"Lỗi: {str(e)}")
        # Dự phòng tự vệ local nếu hệ thống API của Groq lỗi để NPC không đứng hình
        return {
            "reply": "Có gì đó không ổn, để tao tự mò đường...",
            "action": "Explore",
            "turn_direction": "Forward"
        }

# Chạy server cục bộ bằng lệnh: uvicorn app:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
