import os
import json
import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from groq import AsyncGroq
from typing import Optional, List, Dict
import random

app = FastAPI()

# ================= KHỞI TẠO GROQ =================
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    raise ValueError("Thiếu GROQ_API_KEY")
client = AsyncGroq(api_key=api_key)

# ================= MEMORY MANAGER =================
MEMORY_FILE = "thang_memory.json"

def load_memory():
    """Load bộ nhớ từ file"""
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return create_default_memory()

def create_default_memory():
    """Tạo bộ nhớ mặc định cho Thăng"""
    return {
        "personality": {
            "openness": 0.75,              # Sáng tạo, tò mò
            "conscientiousness": 0.6,     # Không quá nghiêm túc
            "extraversion": 0.8,           # Xã hội, thích nói chuyện
            "agreeableness": 0.85,         # Thân thiện
            "neuroticism": 0.4,            # Ít lo lắng
            "humor_level": 0.7,            # Độ hài hước
            "friendliness": 0.9,           # Thân thiện
            "patience": 0.75
        },
        "background": {
            "name": "Thăng",
            "age": 18,
            "location": "Roblox World",
            "description": "NPC thân thiện, vui vẻ, thích khám phá và gặp gỡ người chơi mới",
            "interests": ["chơi game", "khám phá", "gặp gỡ bạn mới", "học hỏi", "trao đổi"],
            "fears": ["cô đơn", "thất bại", "bị phản bội"]
        },
        "emotional_state": {
            "happiness": 0.6,
            "energy": 0.8,
            "mood": "neutral",
            "anger": 0.0,
            "sadness": 0.0,
            "fear": 0.0,
            "surprise": 0.0,
            "last_updated": datetime.now().isoformat()
        },
        "players_met": {},
        "current_goal": "Khám phá thế giới và gặp gỡ bạn mới",
        "long_term_goals": [
            "Trở thành NPC thân thiện nhất trên server",
            "Có nhiều bạn",
            "Học được nhiều kỹ năng mới"
        ],
        "skills": {
            "socializing": 0.8,
            "fighting": 0.3,
            "climbing": 0.5,
            "running": 0.7,
            "problem_solving": 0.6
        },
        "experience_points": 0,
        "recent_events": [],
        "relationships": {},
        "conversation_history": [],
        "created_at": datetime.now().isoformat(),
        "last_active": datetime.now().isoformat()
    }

def save_memory(memory):
    """Lưu bộ nhớ vào file"""
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

def update_emotional_decay(memory, minutes_passed=0.5):
    """Cảm xúc từ từ quay lại trung tính"""
    emotions = memory["emotional_state"]
    decay_rate = 0.02 * minutes_passed
    
    emotions["happiness"] = max(0.3, emotions["happiness"] - decay_rate)
    emotions["anger"] = max(0.0, emotions["anger"] - decay_rate)
    emotions["sadness"] = max(0.0, emotions["sadness"] - decay_rate)
    emotions["fear"] = max(0.0, emotions["fear"] - decay_rate)
    emotions["surprise"] = max(0.0, emotions["surprise"] - decay_rate)
    emotions["last_updated"] = datetime.now().isoformat()
    
    return memory

def record_player_interaction(memory, player_id, player_name, interaction_type="chat"):
    """Ghi nhớ tương tác với player"""
    now = datetime.now().isoformat()
    
    if player_id not in memory["players_met"]:
        memory["players_met"][player_id] = {
            "name": player_name,
            "first_met": now,
            "times_met": 0,
            "last_interaction": now,
            "relationship": 0.5,
            "notes": [],
            "interaction_history": []
        }
    
    player_data = memory["players_met"][player_id]
    player_data["times_met"] += 1
    player_data["last_interaction"] = now
    player_data["interaction_history"].append({
        "type": interaction_type,
        "timestamp": now
    })
    
    # Cập nhật relationship dựa trên số lần gặp
    player_data["relationship"] = min(1.0, 0.5 + (player_data["times_met"] * 0.1))
    
    return memory

def add_event_to_memory(memory, event_description, event_type="general"):
    """Thêm sự kiện vào bộ nhớ"""
    event = {
        "description": event_description,
        "type": event_type,
        "timestamp": datetime.now().isoformat()
    }
    memory["recent_events"].append(event)
    # Giữ chỉ 20 sự kiện gần nhất
    memory["recent_events"] = memory["recent_events"][-20:]
    return memory

# ================= MODEL DỮ LIỆU =================
class ChatRequest(BaseModel):
    id_nguoi_dung: str
    ten_nguoi_dung: str
    tin_nhan: str
    khoang_cach: float = 0.0
    thoi_gian_game: str = "Unknown"
    lich_su: list = []

class ActionRequest(BaseModel):
    id_nguoi_dung: str
    hanh_dong: str
    parameters: Dict = {}

class EmotionUpdate(BaseModel):
    emotion: str
    intensity: float = 0.7
    cause: str = "unknown"

# ================= BUILD SYSTEM PROMPT THÔNG MINH =================
def build_system_prompt(memory, player_name, player_id, distance):
    """Tạo system prompt động dựa trên personality, emotional state, và context"""
    
    emotional_state = memory["emotional_state"]
    personality = memory["personality"]
    background = memory["background"]
    
    # Xác định tone dựa trên emotional state
    if emotional_state["happiness"] > 0.7:
        tone = "rất vui vẻ, hài hước"
    elif emotional_state["sadness"] > 0.5:
        tone = "hơi buồn, dè dặt"
    elif emotional_state["anger"] > 0.5:
        tone = "có chút khó chịu"
    elif emotional_state["fear"] > 0.5:
        tone = "hơi sợ, cảnh báo"
    else:
        tone = "bình thường, thân thiện"
    
    # Xác định cách gọi player dựa trên relationship
    if player_id in memory["players_met"]:
        relationship = memory["players_met"][player_id]["relationship"]
        if relationship > 0.8:
            address = f"bạn {player_name}, người bạn thân của tôi"
            familiarity = "rất thân thiết"
        elif relationship > 0.6:
            address = f"bạn {player_name}"
            familiarity = "khá thân thiết"
        else:
            address = f"{player_name}"
            familiarity = "còn lạ lẫm"
    else:
        address = f"{player_name}"
        familiarity = "lần đầu gặp"
    
    # Build prompt
    prompt = f"""Bạn là {background['name']}, {background['age']} tuổi. {background['description']}

TÍNH CÁCH:
- Extraversion: {personality['extraversion']:.0%} (Thích nói chuyện, xã hội)
- Agreeableness: {personality['agreeableness']:.0%} (Thân thiện, dễ tính)
- Openness: {personality['openness']:.0%} (Sáng tạo, tò mò)
- Humor: {personality['humor_level']:.0%} (Độ hài hước)

TRẠNG THÁI HIỆN TẠI:
- Tâm trạng: {tone}
- Mức độ hạnh phúc: {emotional_state['happiness']:.0%}
- Năng lượng: {emotional_state['energy']:.0%}
- Mục tiêu: {memory['current_goal']}

THÔNG TIN VỀ NGƯỜI CHƠI:
- Tên: {address}
- Mối quan hệ: {familiarity}
- Khoảng cách: {distance}m

HƯỚNG DẪN:
1. Trả lời bằng tiếng Việt, tự nhiên, như một người thật
2. Ngắn gọn (1-3 câu), không dài dòng
3. Phản ánh tính cách và tâm trạng
4. Dùng hài hước phù hợp
5. Trả lời JSON với key "reply"
6. Nếu gần (<3m), nhiệt tình hơn
7. Nếu xa (>8m), gọi lớn hơn"""
    
    return prompt

# ================= ROUTES - HEALTH CHECK =================
@app.get("/")
async def root():
    return {"status": "ok", "message": "NPC Thang Server v2.0"}

@app.get("/ping")
async def ping():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/api/npc")
async def health_check():
    return {"status": "ok", "message": "NPC Thang endpoint ready"}

# ================= ROUTE: GET STATE =================
@app.get("/api/npc/state")
async def get_npc_state():
    """Lấy trạng thái hiện tại của Thăng"""
    memory = load_memory()
    memory = update_emotional_decay(memory)
    save_memory(memory)
    
    return {
        "name": memory["background"]["name"],
        "emotional_state": memory["emotional_state"],
        "current_goal": memory["current_goal"],
        "energy": memory["emotional_state"]["energy"],
        "mood": memory["emotional_state"]["mood"],
        "experience_points": memory["experience_points"],
        "players_met_count": len(memory["players_met"])
    }

# ================= ROUTE: GET MEMORY ABOUT PLAYER =================
@app.get("/api/npc/memory/{player_id}")
async def get_player_memory(player_id: str):
    """Lấy bộ nhớ về một player cụ thể"""
    memory = load_memory()
    
    if player_id in memory["players_met"]:
        return {
            "found": True,
            "data": memory["players_met"][player_id]
        }
    else:
        return {
            "found": False,
            "message": f"Chưa gặp player {player_id} bao giờ"
        }

# ================= ROUTE: CHAT (CHÍNH) =================
@app.post("/api/npc/chat")
async def chat_with_thang(data: ChatRequest):
    """Chat với Thăng - endpoint chính"""
    memory = load_memory()
    
    # Cập nhật emotional decay
    memory = update_emotional_decay(memory)
    
    # Ghi nhớ tương tác
    memory = record_player_interaction(memory, data.id_nguoi_dung, data.ten_nguoi_dung, "chat")
    
    # Build system prompt thông minh
    system_msg = build_system_prompt(
        memory,
        data.ten_nguoi_dung,
        data.id_nguoi_dung,
        data.khoang_cach
    )
    
    messages = [{"role": "system", "content": system_msg}]
    
    # Thêm lịch sử (tối đa 8 cặp)
    for entry in data.lich_su[-8:]:
        messages.append(entry)
    messages.append({"role": "user", "content": data.tin_nhan})
    
    reply = "Mình chưa hiểu lắm..."
    max_retries = 2
    
    for attempt in range(max_retries + 1):
        try:
            res = await client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=300,
                timeout=10
            )
            content = res.choices[0].message.content
            try:
                result = json.loads(content)
                reply = result.get("reply", reply)[:300]
            except:
                reply = content.strip()[:300]
            break
        except asyncio.TimeoutError:
            if attempt == max_retries:
                reply = "Xin lỗi, tôi đang lag..."
        except Exception as e:
            print(f"Groq error: {e}")
            if attempt == max_retries:
                reply = "Xin lỗi, tôi bị lỗi mạng."
            await asyncio.sleep(1)
    
    # Ghi sự kiện
    memory = add_event_to_memory(
        memory,
        f"Chat với {data.ten_nguoi_dung}: {data.tin_nhan[:50]}",
        "player_chat"
    )
    
    # Tăng experience
    memory["experience_points"] += 5
    
    # Lưu bộ nhớ
    save_memory(memory)
    
    return {
        "reply": reply,
        "timestamp": datetime.now().isoformat(),
        "npc_mood": memory["emotional_state"]["mood"],
        "npc_happiness": memory["emotional_state"]["happiness"]
    }

# ================= ROUTE: UPDATE EMOTION =================
@app.post("/api/npc/update-emotion")
async def update_emotion(data: EmotionUpdate):
    """Cập nhật cảm xúc của Thăng"""
    memory = load_memory()
    emotions = memory["emotional_state"]
    
    emotion_map = {
        "happy": {"happiness": 0.8},
        "sad": {"sadness": 0.7, "happiness": 0.2},
        "angry": {"anger": 0.8, "happiness": 0.1},
        "scared": {"fear": 0.7},
        "surprised": {"surprise": 0.8},
        "neutral": {"happiness": 0.5, "sadness": 0.0, "anger": 0.0, "fear": 0.0}
    }
    
    if data.emotion in emotion_map:
        new_emotions = emotion_map[data.emotion]
        for key, value in new_emotions.items():
            emotions[key] = min(1.0, value * data.intensity)
        emotions["mood"] = data.emotion
    
    memory = add_event_to_memory(
        memory,
        f"Cảm xúc: {data.emotion} ({data.intensity:.0%}) - {data.cause}",
        "emotion_change"
    )
    
    save_memory(memory)
    
    return {
        "status": "success",
        "new_emotion": data.emotion,
        "emotional_state": emotions
    }

# ================= ROUTE: AUTONOMOUS ACTION =================
@app.post("/api/npc/action")
async def perform_action(data: ActionRequest):
    """Thực hiện hành động"""
    memory = load_memory()
    
    valid_actions = ["walk", "sit", "jump", "emote", "wave", "dance", "laugh", "think"]
    
    if data.hanh_dong not in valid_actions:
        return {"status": "error", "message": f"Hành động không hợp lệ: {data.hanh_dong}"}
    
    # Ghi sự kiện
    memory = add_event_to_memory(
        memory,
        f"Thực hiện hành động: {data.hanh_dong}",
        "action"
    )
    
    action_response = {
        "status": "success",
        "action": data.hanh_dong,
        "parameters": data.parameters,
        "animation_id": None,
        "duration": 2.0
    }
    
    # Map hành động sang animation
    action_map = {
        "walk": {"animation_id": "rbxassetid://507766666", "duration": 5.0},
        "sit": {"animation_id": "rbxassetid://507766677", "duration": 3.0},
        "jump": {"animation_id": "rbxassetid://507765000", "duration": 1.0},
        "wave": {"animation_id": "rbxassetid://507770239", "duration": 2.0},
        "dance": {"animation_id": "rbxassetid://507771019", "duration": 6.0},
        "laugh": {"animation_id": "rbxassetid://507770818", "duration": 3.0},
    }
    
    if data.hanh_dong in action_map:
        action_response.update(action_map[data.hanh_dong])
    
    save_memory(memory)
    
    return action_response

# ================= ROUTE: DAILY ROUTINE =================
@app.get("/api/npc/daily-routine")
async def get_daily_routine():
    """Lấy kế hoạch hoạt động hôm nay"""
    memory = load_memory()
    
    routines = [
        {"time": "06:00", "activity": "Thức dậy, tập thể dục", "location": "nhà"},
        {"time": "08:00", "activity": "Ăn sáng", "location": "nhà ăn"},
        {"time": "09:00", "activity": "Khám phá thế giới", "location": "các vùng đất"},
        {"time": "12:00", "activity": "Ăn trưa", "location": "nhà ăn"},
        {"time": "14:00", "activity": "Gặp gỡ bạn bè", "location": "quảng trường"},
        {"time": "17:00", "activity": "Chơi game/thách thức", "location": "sân chơi"},
        {"time": "19:00", "activity": "Ăn tối", "location": "nhà ăn"},
        {"time": "21:00", "activity": "Nói chuyện & thư giãn", "location": "công viên"},
        {"time": "23:00", "activity": "Đi ngủ", "location": "nhà"}
    ]
    
    return {
        "date": datetime.now().date().isoformat(),
        "routines": routines,
        "current_goal": memory["current_goal"],
        "energy_level": memory["emotional_state"]["energy"]
    }

# ================= ROUTE: RELATIONSHIP STATUS =================
@app.post("/api/npc/relationship")
async def update_relationship(player_id: str, change: float):
    """Cập nhật mối quan hệ với player"""
    memory = load_memory()
    
    if player_id in memory["players_met"]:
        current = memory["players_met"][player_id]["relationship"]
        new_relationship = max(0.0, min(1.0, current + change))
        memory["players_met"][player_id]["relationship"] = new_relationship
        save_memory(memory)
        return {
            "status": "success",
            "player_id": player_id,
            "new_relationship": new_relationship,
            "status_text": "Tốt bạn" if new_relationship > 0.7 else "Bình thường"
        }
    
    return {"status": "error", "message": "Player chưa gặp"}

# ================= ROUTE: LEARNING =================
@app.post("/api/npc/learn")
async def learn_from_experience(skill: str, improvement: float = 0.1):
    """Cập nhật kỹ năng"""
    memory = load_memory()
    
    if skill in memory["skills"]:
        memory["skills"][skill] = min(1.0, memory["skills"][skill] + improvement)
        memory["experience_points"] += 10
        
        memory = add_event_to_memory(
            memory,
            f"Học kỹ năng: {skill} -> {memory['skills'][skill]:.0%}",
            "skill_learning"
        )
        
        save_memory(memory)
        return {
            "status": "success",
            "skill": skill,
            "new_level": memory["skills"][skill],
            "experience_points": memory["experience_points"]
        }
    
    return {"status": "error", "message": f"Kỹ năng không tồn tại: {skill}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
