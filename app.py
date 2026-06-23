import os
import traceback
from flask import Flask, request, jsonify

app = Flask(__name__)

# ====== CẤU HÌNH GEMINI ======
# Nếu dùng Gemini
try:
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("Gemini da san sang")
except Exception as e:
    print("Loi Gemini:", e)
    model = None

# ====== MEMORY ======
conversation_memory = {}

# ====== TRẠNG THÁI NPC ======
npc_state = {
    "mood": "vui ve",
    "personality": "than thien, hai huoc, thich kham pha",
    "energy": 100,
    "goals": ["kham pha the gioi", "ket ban voi nguoi choi"]
}

@app.route("/api/npc", methods=["POST"])
def npc_chat():
    try:
        data = request.json
        user_message = data.get("message", "")
        user_id = data.get("userId", "unknown")
        player_name = data.get("playerName", "ban")
        
        print(f"Nhan tin nhan: {user_message} tu {player_name}")
        
        # Kiểm tra model
        if model is None:
            print("LOI: Model chua duoc khoi tao")
            return jsonify({
                "reply": "Thang chua duoc cai dat AI",
                "action": "idle",
                "mood": npc_state["mood"]
            })
        
        # System prompt
        system_prompt = f"""Ban la Thang, mot NPC trong game Roblox. 
Tinh cach: {npc_state['personality']}.
Trang thai: {npc_state['mood']}.
Muc tieu: {', '.join(npc_state['goals'])}.
Tra loi ngan gon, tu nhien, nhu nguoi thang."""
        
        # Gọi Gemini
        prompt = f"{system_prompt}\n\nNguoi choi {player_name} noi: {user_message}\nThang tra loi:"
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.9,
                max_output_tokens=150
            )
        )
        
        bot_reply = response.text
        print(f"Thang tra loi: {bot_reply}")
        
        return jsonify({
            "reply": bot_reply,
            "action": "talk",
            "mood": npc_state["mood"]
        })
        
    except Exception as e:
        print("========== LỖI CHI TIẾT ==========")
        print(traceback.format_exc())
        print("==================================")
        
        return jsonify({
            "reply": "Thang dang suy nghi...",
            "action": "idle",
            "mood": npc_state["mood"]
        })

@app.route("/test")
def test():
    return "Server dang chay"

if __name__ == "__main__":
    print("Server dang khoi dong...")
    app.run(host="0.0.0.0", port=10000)
