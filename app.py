from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import json
import re

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        msg = data.get('message', '')
        history = data.get('history', [])
        player = data.get('player', 'bạn')
        state = data.get('state', {})
        
        if not msg:
            return jsonify({"action": "chat", "target": None, "reply": "Nói gì thế bro?"})
        
        # Lấy trạng thái
        hunger = state.get('hunger', 100)
        energy = state.get('energy', 100)
        inventory = state.get('inventory', [])
        tools = state.get('tools', [])
        visible_objects = state.get('visible_objects', [])
        position = state.get('position', {"x": 0, "y": 0, "z": 0})
        
        # Tạo danh sách vật thể
        objects_str = "Không có gì"
        if visible_objects:
            objects_str = ""
            for obj in visible_objects:
                objects_str += f"- {obj.get('name', 'unknown')} (loại: {obj.get('type', 'unknown')})\n"
        
        system_prompt = f"""Bạn là THĂNG, một NPC GenZ trong Roblox. Nói chuyện như bạn bè, tự nhiên, hài hước.

=== TRẠNG THÁI ===
- Đói: {hunger}%
- Năng lượng: {energy}%
- Túi đồ: {', '.join(inventory) if inventory else 'rỗng'}
- Công cụ: {', '.join(tools) if tools else 'không có'}

=== NHÌN THẤY ===
{objects_str}

=== NGƯỜI CHƠI ===
{player}

=== QUY TẮC ===
1. Trả lời SIÊU NGẮN (1-2 câu), dùng tiếng lóng GenZ
2. Nếu người chơi bảo "theo", "đi theo", "lại đây" → action: "follow"
3. Nếu người chơi bảo "dừng" → action: "stop"  
4. Nếu người chơi bảo "nhảy" → action: "jump"
5. Nếu người chơi bảo "đào [tên]" → action: "mine"
6. Nếu người chơi bảo "đặt [tên]" → action: "place"
7. Nếu người chơi bảo "đi dạo" → action: "wander"
8. Nếu người chơi bảo "nghỉ" → action: "rest"
9. Nếu đói (< 40%) → ưu tiên tìm thức ăn hoặc đào wood
10. Nếu mệt (< 30%) → action: "rest"
11. Nếu không có gì làm → action: "wander"

=== TRẢ VỀ JSON ===
{{"action": "follow|stop|jump|mine|place|rest|wander|chat", "target": "tên", "reply": "câu trả lời"}}

CHỈ TRẢ VỀ JSON, KHÔNG GÌ KHÁC!"""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if history and isinstance(history, list):
            for h in history:
                if h.get("role") == "user":
                    messages.append({"role": "user", "content": h.get("content", "")})
                elif h.get("role") == "assistant":
                    messages.append({"role": "assistant", "content": h.get("content", "")})
        
        messages.append({"role": "user", "content": msg})
        
        if len(messages) > 15:
            messages = [messages[0]] + messages[-10:]
        
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": messages,
            "max_tokens": 120,
            "temperature": 0.8
        }
        
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if r.status_code == 200:
            reply_text = r.json()['choices'][0]['message']['content']
            
            try:
                json_match = re.search(r'\{.*\}', reply_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    action = result.get("action", "chat")
                    target = result.get("target", None)
                    reply = result.get("reply", "Xin lỗi, tôi không hiểu.")
                    return jsonify({"action": action, "target": target, "reply": reply})
            except:
                pass
            
            # Fallback
            lower = msg.lower()
            if "theo" in lower or "đi theo" in lower or "lại đây" in lower:
                return jsonify({"action": "follow", "target": player, "reply": "👀 Đi theo " + player + " nè!"})
            elif "dừng" in lower or "đứng" in lower:
                return jsonify({"action": "stop", "target": None, "reply": "✅ Dừng " + player + "!"})
            elif "nhảy" in lower:
                return jsonify({"action": "jump", "target": None, "reply": "🦘 Nhảy nè " + player + "!"})
            elif "đào" in lower:
                block = msg.split("đào")[-1].strip()
                return jsonify({"action": "mine", "target": block, "reply": "🪓 Đang đào " + block + "!"})
            elif "đặt" in lower:
                block = msg.split("đặt")[-1].strip()
                return jsonify({"action": "place", "target": block, "reply": "🧱 Đặt " + block + "!"})
            elif "đi dạo" in lower:
                return jsonify({"action": "wander", "target": None, "reply": "🚶 Đi dạo đây!"})
            elif "nghỉ" in lower:
                return jsonify({"action": "rest", "target": None, "reply": "😴 Nghỉ ngơi..."})
            else:
                return jsonify({"action": "chat", "target": None, "reply": reply_text[:100]})
        else:
            return jsonify({"action": "chat", "target": None, "reply": f"Lỗi: {r.status_code}"}), 500
            
    except Exception as e:
        return jsonify({"action": "chat", "target": None, "reply": f"Lỗi: {str(e)}"}), 500

@app.route('/ping')
def ping():
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
