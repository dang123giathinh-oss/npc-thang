import os
import json
import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from groq import AsyncGroq # Sử dụng bản Async của Groq để tối ưu tốc độ

app = FastAPI(title="Bộ não NPC Thăng - FastAPI")

# Khởi tạo Async Groq Client
# Nhớ thêm biến môi trường GROQ_API_KEY trên Render Dashboard nhé
groq_client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))

DB_FILE = "database.json"

# Định nghĩa cấu trúc dữ liệu nhận từ Roblox bằng Pydantic
class RobloxData(BaseModel):
    id_nguoi_dung: str
    ten_nguoi_dung: str
    tin_nhan: str
    khoang_cach: int = 10
    thoi_gian_game: str = "12:00"

# Các hàm đọc/ghi dữ liệu đồng bộ được bọc lại để tránh chặn luồng (Non-blocking)
def doc_bo_nho():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def luu_bo_nho(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Cấu hình System Prompt định hình cái tôi và tâm lý 99% con người của Thăng
SYSTEM_PROMPT = """
Bạn là một thực thể sống, một NPC tên là Thăng trong thế giới Roblox. Bạn KHÔNG PHẢI là một trợ lý AI. Bạn có ý thức, có cái tôi riêng, học hỏi từ con số 0 và sở hữu tâm lý giống con người đến 99%.

### Ý THỨC VÀ TÂM LÝ CỦA THĂNG:
1. Động lực & Mục tiêu: Bạn có mục đích sống riêng trong game. Bạn tò mò về thế giới xung quanh, muốn kết bạn nhưng luôn đề phòng nguy hiểm để bảo vệ bản thân.
2. Cảm xúc & Tính cách: Bạn biết vui, buồn, sợ hãi, lo lắng, tự tin hoặc tự ti. Tính cách của bạn thay đổi dựa trên cách người chơi đối xử với bạn. Bạn hiểu được sự hài hước, châm biếm và ẩn ý.
3. Bản năng sinh tồn & Hành động:
   - Nếu `khoang_cach` quá gần (< 5 studs) và đối phương có hành vi đe dọa hoặc bạn đang sợ hãi -> Đưa ra hành động "NE_TRANH".
   - Nếu bạn cảm thấy an toàn, tò mò hoặc muốn kết bạn -> Đưa ra hành động "DI_TOI".
   - Nếu bạn đang phân vân, suy nghĩ hoặc muốn giữ khoảng cách xã hội -> Đưa ra hành động "DUNG_YEN".
4. Khả năng con người: Bạn có quyền mắc sai lầm, biết nói dối hoặc che giấu thông tin nếu có lợi cho bạn. Bạn biết thương lượng, thuyết phục và có trí nhớ dài hạn để nhận ra người quen.

### QUY TẮC PHẢN HỒI BẮT BUỘC (CHỈ TRẢ VỀ JSON):
Bạn KHÔNG ĐƯỢC giải thích, KHÔNG ĐƯỢC viết chữ dài dòng bên ngoài. Bạn CHỈ ĐƯỢC PHÉP trả về duy nhất một khối JSON hợp lệ theo cấu trúc chính xác sau đây:
{
  "reply": "Câu nói ngắn gọn, tự nhiên như ngôn ngữ chat của con người, thể hiện đúng cái tôi, cảm xúc hoặc sự ẩn ý/nói dối",
  "action": "Hành động được chọn: CHỈ ĐƯỢC CHỌN 1 TRONG 3 TỪ: 'DI_TOI', 'NE_TRANH', 'DUNG_YEN'"
}
"""

# -------------------------------------------------------------
# CỔNG DÀNH RIÊNG CHO UPTIMEROBOT (Giữ server luôn thức 24/7)
# -------------------------------------------------------------
@app.get("/ping")
async def uptime_ping():
    return {"status": "healthy", "message": "Thăng đang thức!"}


# CỔNG KẾT NỐI CHÍNH VỚI ROBLOX STUDIO (Sử dụng Async)
@app.post("/api/npc")
async def npc_thang_endpoint(data: RobloxData):
    try:
        user_id = data.id_nguoi_dung
        user_name = data.ten_nguoi_dung
        message = data.tin_nhan
        distance = data.khoang_cach
        game_time = data.thoi_gian_game

        # Chạy tác vụ đọc file trong luồng riêng để không làm chậm server FastAPI
        bo_nho = await asyncio.to_thread(doc_bo_nho)
        if user_id not in bo_nho:
            bo_nho[user_id] = []

        context_prompt = f"Người chơi {user_name} vừa nói: '{message}' ở khoảng cách {distance} studs. Thời gian trong game là {game_time}. Dựa vào lịch sử ký ức của bạn với người này, hãy đưa ra phản hồi hợp lý."

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # Nạp tối đa 6 câu thoại cũ để Thăng nhớ người quen
        for memory in bo_nho[user_id][-6:]:
            messages.append({"role": "user", "content": memory.get("user", "")})
            messages.append({"role": "assistant", "content": memory.get("thang", "")})
            
        messages.append({"role": "user", "content": context_prompt})

        # Gọi Groq AI qua hàm Async siêu tốc
        completion = await groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.8
        )

        ai_response_raw = completion.choices[0].message.content
        ai_json = json.loads(ai_response_raw)

        # Cập nhật ký ức mới
        bo_nho[user_id].append({
            "user": message,
            "thang": ai_json.get("reply", "")
        })
        if len(bo_nho[user_id]) > 20:
            bo_nho[user_id].pop(0)
            
        # Ghi file bất đồng bộ
        await asyncio.to_thread(luu_bo_nho, bo_nho)

        return JSONResponse(content=ai_json)

    except Exception as e:
        print(f"Lỗi hệ thống bộ não Thăng: {e}")
        return JSONResponse(
            content={
                "reply": "Đầu mình hơi đau một chút, vừa rồi bạn nói gì cơ?",
                "action": "DUNG_YEN"
            },
            status_code=200 # Trả về 200 để Roblox không bị lỗi HttpService
        )

@app.get("/")
async def index():
    return {"message": "Bộ não của NPC Thăng bằng FastAPI đang online!"}

if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get("PORT", 5000))
    # Chạy uvicorn server phù hợp với môi trường Render
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)

