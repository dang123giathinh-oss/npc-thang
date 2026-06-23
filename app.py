import os
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# ====== CẤU HÌNH GROQ ======
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY")
)

# ====== MEMORY ======
conversation_memory = {}

# ====== TRẠNG THÁI NPC ======
npc_state = {
    "mood": "vui ve",
    "personality": "than thien, hai huoc, thich kham pha",
    "energy": 100,
    "goals": ["kham pha the gioi", "ket ban"]
}

@app.route("/api/npc", methods=["POST"])
def npc_chat():
    try:
        data = request.json
        user_message = data.get("message", "")
        user_id = data.get("userId", "unknown")
        player_name = data.get("playerName", "ban")
        
        print(f"{player_name}: {user_message}")
        
        # System prompt
        system_prompt = f"""Ban la Thang, mot NPC trong game Roblox.
Tinh cach: {npc_state['personality']}.
Trang thai: {npc_state['mood']}.
Muc tieu: {', '.join(npc_state['goals'])}.
Tra loi ngan gon (1-2 cau), tu nhien, giong nguoi thang.
Co the dung tieng long, noi chuyen kieu ban be."""

        # Goi Groq
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.9,
            max_tokens=150
        )
        
        bot_reply = response.choices[0].message.content
        print(f"Thang: {bot_reply}")
        
        return jsonify({
            "reply": bot_reply,
            "action": "talk",
            "mood": npc_state["mood"]
        })
        
    except Exception as e:
        print("LOI:", str(e))
        return jsonify({
            "reply": "Thang dang suy nghi...",
            "action": "idle",
            "mood": npc_state["mood"]
        })

@app.route("/test")
def test():
    return "Server Groq OK"

if __name__ == "__main__":
    print("Server Thang da san sang!")
    app.run(host="0.0.0.0", port=10000)
