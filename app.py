import os
import google.generativeai as genai
from flask import Flask, request, jsonify

app = Flask(__name__)

# Cấu hình Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))  # Đổi tên biến môi trường

# Chọn model Gemini 1.5 Flash (nhanh, miễn phí)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- Phần trí nhớ và trạng thái giữ nguyên như cũ ---
conversation_memory = {}
npc_state = {
    "mood": "vui vẻ",
    "personality": "thân thiện, hài hước, thích khám phá",
    "energy": 100,
    "trust_to_player": {},
    "goals": ["khám phá thế giới", "kết bạn với người chơi"]
}

@app.route("/api/npc", methods=["POST"])
def npc_chat():
    data = request.json
    user_message = data.get("message", "")
    user_id = data.get("userId", "unknown")
    player_name = data.get("playerName", "bạn")
    npc_current_mood = data.get("mood", npc_state["mood"])

    # Cập nhật cảm xúc đơn giản (giữ nguyên hàm analyze_sentiment của bạn)

    if user_id not in conversation_memory:
        conversation_memory[user_id] = []
    memory = conversation_memory[user_id]
    memory.append({"role": "user", "parts": [f"{player_name}: {user_message}"]})
    if len(memory) > 10:
        memory = memory[-10:]

    # Tạo system prompt
    system_prompt = f"""Bạn là Thăng, một NPC trong game Roblox. Tính cách: {npc_state['personality']}.
Trạng thái hiện tại: {npc_state['mood']}. Năng lượng: {npc_state['energy']}.
Mục tiêu: {', '.join(npc_state['goals'])}.
Bạn có cảm xúc như con người, biết đùa, biết sợ, biết tò mò. 
Trả lời ngắn gọn, tự nhiên. Có thể kèm hành động trong ngoặc vuông, ví dụ: [cười], [nhảy], [sợ hãi].
Hãy nhớ bạn đang ở trong thế giới Roblox, có thể tương tác với người chơi."""
    
    # Gemini không có system role như OpenAI, ta sẽ đặt system prompt vào lịch sử như 1 tin nhắn của "user" mô phỏng
    chat_history = [
        {"role": "user", "parts": [system_prompt]},
        {"role": "model", "parts": ["Đã hiểu, tôi sẽ nhập vai Thăng."]}
    ] + memory

    try:
        # Gửi toàn bộ lịch sử, Gemini tự hiểu
        response = model.generate_content(
            chat_history,
            generation_config=genai.types.GenerationConfig(
                temperature=0.9,
                max_output_tokens=150
            )
        )
        bot_reply = response.text
        memory.append({"role": "model", "parts": [bot_reply]})
        conversation_memory[user_id] = memory

        # Trích xuất action (giữ nguyên code cũ)
        action = "talk"
        if "[cười]" in bot_reply:
            action = "laugh"
        elif "[nhảy]" in bot_reply:
            action = "jump"
        # ...

        return jsonify({"reply": bot_reply, "action": action, "mood": npc_state["mood"]})
    except Exception as e:
        print("Lỗi Gemini:", e)
        return jsonify({"reply": "Thăng đang suy nghĩ...", "action": "idle", "mood": npc_state["mood"]})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
