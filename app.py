from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import json
import random

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Bộ nhớ của Thăng (lưu trên server)
memory = {
    "learned_actions": [],
    "known_objects": {},
    "experience": [],
    "personality": {
        "curiosity": 0.8,
        "bravery": 0.5,
        "friendliness": 0.7
    }
}

# Lưu bộ nhớ vào file (tạm thời)
def save_memory():
    try:
        with open("thang_memory.json", "w") as f:
            json.dump(memory, f)
    except:
        pass

def load_memory():
    try:
        with open("thang_memory.json", "r") as f:
            return json.load(f)
    except:
        return memory

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        msg = data.get('message', '')
        history = data.get('history', [])
        player = data.get('player', 'bạn')
        state = data.get('state', {})
        
        if not msg:
            return jsonify({"reply": "Nói gì thế bro?", "action": "chat", "target": None})
        
        # Tải bộ nhớ
        global memory
        memory = load_memory()
        
        # Lấy trạng thái hiện tại của Thăng
        visible_objects = state.get('visible_objects', [])
        hunger = state.get('hunger', 100)
        energy = state.get('energy', 100)
        inventory = state.get('inventory', [])
        tools = state.get('tools', [])
        position = state.get('position', {"x": 0, "y": 0, "z": 0})
        
        # Xây dựng prompt cho Groq (quyết định hành động)
        system_prompt = f"""Bạn là THĂNG, một NPC đang sống trong thế giới Roblox. Bạn có thể tự quyết định mọi hành động của mình.

=== TRẠNG THÁI CỦA BẠN ===
- Đói: {hunger}%
- Năng lượng: {energy}%
- Vị trí: ({position.get('x', 0)}, {position.get('y', 0)}, {position.get('z', 0)})
- Túi đồ: {', '.join(inventory) if inventory else 'trống'}
- Công cụ: {', '.join(tools) if tools else 'không có'}

=== NHỮNG GÌ BẠN NHÌN THẤY ===
{json.dumps(visible_objects, indent=2) if visible_objects else 'Không có gì xung quanh'}

=== BỘ NHỚ CỦA BẠN ===
- Hành động đã học: {json.dumps(memory.get('learned_actions', []))}
- Vật thể đã biết: {json.dumps(memory.get('known_objects', {}))}

=== TÍNH CÁCH ===
- Tò mò: {memory['personality']['curiosity']}
- Can đảm: {memory['personality']['bravery']}
- Thân thiện: {memory['personality']['friendliness']}

=== NHIỆM VỤ ===
1. Dựa trên trạng thái và những gì bạn nhìn thấy, hãy QUYẾT ĐỊNH HÀNH ĐỘNG
2. Trả về JSON với các trường:
   - "action": "move_to" | "mine" | "place" | "craft" | "chat" | "follow" | "jump" | "wander" | "rest" | "learn"
   - "target": tên vật thể hoặc người chơi (nếu có)
   - "reply": câu trả lời ngắn gọn (1-2 câu)
   - "learn": hành động mới muốn học (nếu action là "learn")
   - "reason": lý do quyết định (để tự học)

=== VÍ DỤ ===
- Thấy block gỗ và đói → {{"action": "mine", "target": "wood", "reply": "🪓 Tôi sẽ đào gỗ để làm bánh mì!", "learn": "đào gỗ"}}
- Thấy người chơi tên Thinh → {{"action": "follow", "target": "Thinh", "reply": "👋 Chào Thinh, tôi đi theo bạn nhé!", "learn": None}}
- Mệt quá → {{"action": "rest", "target": None, "reply": "😴 Tôi mệt quá, nghỉ tí!", "learn": None}}
- Nhìn thấy vật lạ → {{"action": "move_to", "target": "vật lạ", "reply": "🔍 Cái gì kia nhỉ? Tôi sẽ đến xem!", "learn": "khám phá vật lạ"}}
- Không biết làm gì → {{"action": "wander", "target": None, "reply": "🚶 Tôi sẽ đi dạo khám phá!", "learn": None}}

=== QUAN TRỌNG ===
- Luôn chọn hành động dựa trên trạng thái và môi trường
- Nếu đói (< 40), ưu tiên tìm thức ăn hoặc đào gỗ để làm bánh mì
- Nếu mệt (< 30), ưu tiên nghỉ ngơi
- Nếu thấy vật thể mới, hãy khám phá
- Nếu có người chơi, có thể tương tác
- CHỈ TRẢ VỀ JSON, KHÔNG GÌ KHÁC!"""

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
            "max_tokens": 200,
            "temperature": 0.9
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
                    learn = result.get("learn", None)
                    reason = result.get("reason", "")
                    
                    # Học hành động mới nếu có
                    if learn and learn not in memory['learned_actions']:
                        memory['learned_actions'].append(learn)
                        save_memory()
                    
                    # Cập nhật tính cách dựa trên hành động
                    if action == "explore":
                        memory['personality']['curiosity'] = min(1, memory['personality']['curiosity'] + 0.05)
                    elif action == "mine":
                        memory['personality']['bravery'] = min(1, memory['personality']['bravery'] + 0.05)
                    elif action == "follow":
                        memory['personality']['friendliness'] = min(1, memory['personality']['friendliness'] + 0.05)
                    save_memory()
                    
                    return jsonify({
                        "action": action,
                        "target": target,
                        "reply": reply,
                        "learn": learn,
                        "reason": reason
                    })
            except:
                pass
            
            # Fallback
            lower = msg.lower()
            if "theo" in lower or "đi theo" in lower:
                return jsonify({"action": "follow", "target": player, "reply": "👀 Đi theo " + player + " nè!", "learn": None})
            elif "đào" in lower:
                block = msg.split("đào")[-1].strip()
                return jsonify({"action": "mine", "target": block, "reply": "🪓 Đang đào " + block + "!", "learn": "đào " + block})
            elif "đặt" in lower:
                block = msg.split("đặt")[-1].strip()
                return jsonify({"action": "place", "target": block, "reply": "🧱 Đặt " + block + "!", "learn": "đặt " + block})
            else:
                return jsonify({"action": "chat", "target": None, "reply": reply_text, "learn": None})
        else:
            return jsonify({"action": "chat", "target": None, "reply": f"Lỗi API: {r.status_code}", "learn": None}), 500
            
    except Exception as e:
        return jsonify({"action": "chat", "target": None, "reply": f"Lỗi: {str(e)}", "learn": None}), 500

@app.route('/ping')
def ping():
    return "OK"

@app.route('/memory', methods=['GET'])
def get_memory():
    return jsonify(memory)

@app.route('/memory/reset', methods=['POST'])
def reset_memory():
    global memory
    memory = {
        "learned_actions": [],
        "known_objects": {},
        "experience": [],
        "personality": {
            "curiosity": 0.8,
            "bravery": 0.5,
            "friendliness": 0.7
        }
    }
    save_memory()
    return jsonify({"status": "reset"})

if __name__ == '__main__':
    # Thêm regex cho Python
    import re
    app.run(host='0.0.0.0', port=8000)
