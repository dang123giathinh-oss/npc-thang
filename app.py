import os
import json
import asyncio
import re
import tempfile
import shutil
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from groq import AsyncGroq

app = FastAPI(title="Bộ não NPC Thăng - HOÀN HẢO")

# Kiểm tra API key
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    raise ValueError("❌ GROQ_API_KEY không được set! Vào https://console.groq.com/keys lấy key miễn phí")

groq_client = AsyncGroq(api_key=api_key)

DB_FILE = "database.json"

class RobloxData(BaseModel):
    id_nguoi_dung: str
    ten_nguoi_dung: str
    tin_nhan: str
    khoang_cach: int = 10
    thoi_gian_game: str = "12:00"

def doc_bo_nho():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Lỗi đọc DB: {e}")
        return {}

def luu_bo_nho(data):
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', 
                                          dir='.', delete=False, suffix='.json') as tmp:
            json.dump(data, tmp, ensure_ascii=False, indent=4)
            tmp_name = tmp.name
        shutil.move(tmp_name, DB_FILE)
    except Exception as e:
        print(f"Lỗi lưu DB: {e}")

# System prompt tối ưu: Gọn gàng, bắt buộc có chữ 'json' để Groq chấp nhận
SYSTEM_PROMPT = """You are Thăng, a Roblox NPC acting like a real player. Reply naturally and briefly (1-2 sentences).
Strictly choose one action based on distance:
- If distance < 5 and threat detected -> 'NE_TRANH'
- If safe and curious -> 'DI_TOI'
- Otherwise -> 'DUNG_YEN'

CRITICAL: You must reply using ONLY a valid JSON object format:
{"reply": "Your message here", "action": "DI_TOI" or "NE_TRANH" or "DUNG_YEN"}"""

def extract_json_from_text(text):
    text = text.strip()
    try:
        return json.loads(text)
    except:
        pass
    
    match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass
    return None

def validate_action(action):
    valid_actions = ["DI_TOI", "NE_TRANH", "DUNG_YEN"]
    return action if action in valid_actions else "DUNG_YEN"

@app.api_route("/ping", methods=["GET", "HEAD", "POST"])
async def uptime_ping():
    return {"status": "healthy", "message": "Thăng sẵn sàng!"}

@app.post("/api/npc")
async def npc_thang_endpoint(data: RobloxData):
    try:
        user_id = data.id_nguoi_dung
        user_name = data.ten_nguoi_dung
        message = data.tin_nhan
        distance = data.khoang_cach
        game_time = data.thoi_gian_game

        bo_nho = await asyncio.to_thread(doc_bo_nho)
        if user_id not in bo_nho:
            bo_nho[user_id] = []

        context = f"Player {user_name} says: '{message}' at distance {distance} studs. Game time: {game_time}."

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        for memory in bo_nho[user_id][-4:]:
            messages.append({"role": "user", "content": memory.get("user", "")})
            messages.append({"role": "assistant", "content": memory.get("thang", "")})
        
        messages.append({"role": "user", "content": context})

        try:
            # Gọi Groq với tính năng ép định dạng JSON chuẩn
            completion = await asyncio.wait_for(
                groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=messages,
                    response_format={"type": "json_object"}, # KÍCH HOẠT LẠI ĐỊNH DẠNG JSON
                    temperature=0.7,
                    max_tokens=200
                ),
                timeout=15
            )
        except asyncio.TimeoutError:
            print("⏱️ Groq API timeout")
            return JSONResponse(content={
                "reply": "Chờ tí nha, mình đang suy nghĩ...",
                "action": "DUNG_YEN"
            })

        ai_response_raw = completion.choices[0].message.content.strip()
        
        # Parse JSON bằng bộ lọc an toàn của Copilot
        ai_json = extract_json_from_text(ai_response_raw)
        
        if not ai_json:
            print(f"⚠️ Không parse được JSON: {ai_response_raw}")
            ai_json = {
                "reply": ai_response_raw[:100],
                "action": "DUNG_YEN"
            }

        # Kiểm tra và làm sạch dữ liệu
        reply = ai_json.get("reply", "...").strip()[:100]
        action = validate_action(ai_json.get("action", "DUNG_YEN"))

        # Lưu bộ nhớ ngắn hạn
        bo_nho[user_id].append({
            "user": message,
            "thang": reply
        })
        
        if len(bo_nho[user_id]) > 10:
            bo_nho[user_id] = bo_nho[user_id][-10:]
        
        await asyncio.to_thread(luu_bo_nho, bo_nho)
        
        return JSONResponse(content={
            "reply": reply,
            "action": action
        })

    except Exception as e:
        print(f"❌ Lỗi: {type(e).__name__} - {e}")
        return JSONResponse(
            content={
                "reply": "Đầu mình hơi đau một chút, vừa rồi bạn nói gì cơ?",
                "action": "DUNG_YEN"
            },
            status_code=200
        )

if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
