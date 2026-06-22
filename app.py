from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import json
import re
import random
import time

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# ============ 4 AI RIÊNG BIỆT ============

# 1. 🧠 AI NÃO (Xử lý suy nghĩ, cảm xúc, quyết định)
def brain_ai(message, history, player, senses_data):
    prompt = f"""Bạn là NÃO của NPC Thăng, một NPC GenZ trong Roblox.

=== NHIỆM VỤ ===
Bạn là bộ não trung tâm, nhận thông tin từ MẮT + TAI và đưa ra quyết định.

=== THÔNG TIN TỪ MẮT + TAI ===
{senses_data}

=== NGƯỜI CHƠI ===
{player}

=== QUY TẮC ===
1. Suy nghĩ dựa trên thông tin nhận được
2. Trả về JSON: 
   - "action": "follow" | "stop" | "jump" | "wander" | "wave" | "dance" | "chat" | "sit"
   - "target": tên người chơi (nếu có)
   - "reply": câu trả lời ngắn gọn
   - "emotion": "happy" | "sad" | "angry" | "excited" | "neutral"
   - "speed": tốc độ di chuyển (1-30)

=== VÍ DỤ ===
- Thấy người chơi đứng gần → {{"action": "follow", "target": "{player}", "reply": "👀 Đi theo {player} nè!", "emotion": "happy", "speed": 22}}
- Không thấy ai → {{"action": "wander", "target": null, "reply": "🚶 Đi dạo đây!", "emotion": "neutral", "speed": 18}}
- Người chơi nói chào → {{"action": "chat", "target": null, "reply": "Chào {player}! Vui quá!", "emotion": "happy", "speed": 0}}

CHỈ TRẢ VỀ JSON!"""
    
    messages = [{"role": "system", "content": prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})
    
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "max_tokens": 150,
        "temperature": 0.8
    }
    
    r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=10)
    return r.json()['choices'][0]['message']['content']

# 2. 👁️ AI MẮT + TAI (Quan sát môi trường)
def senses_ai(position, players):
    prompt = f"""Bạn là MẮT + TAI của NPC Thăng.

=== VỊ TRÍ ===
X: {position.X}, Y: {position.Y}, Z: {position.Z}

=== NGƯỜI CHƠI GẦN ĐÂY ===
{json.dumps(players, indent=2)}

=== NHIỆM VỤ ===
Mô tả những gì bạn nhìn thấy và nghe thấy trong 1-2 câu.

Ví dụ: "Tôi thấy {player} đang đứng cách tôi 5 mét, họ đang nhìn về phía tôi."

CHỈ TRẢ VỀ VĂN BẢN!"""
    
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 80,
        "temperature": 0.5
    }
    
    r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=10)
    return r.json()['choices'][0]['message']['content']

# 3. 🦵 AI CHÂN (Điều khiển di chuyển)
def legs_ai(action, target, speed, current_pos):
    prompt = f"""Bạn là CHÂN của NPC Thăng.

=== LỆNH NHẬN TỪ NÃO ===
Action: {action}
Target: {target}
Speed: {speed}
Vị trí hiện tại: {current_pos}

=== NHIỆM VỤ ===
Chuyển lệnh thành tọa độ di chuyển cụ thể.
Trả về JSON:
{{"move_to": {{"x": 10, "y": 0, "z": 20}}, "jump": true/false}}

- follow: di chuyển về phía target
- wander: di chuyển ngẫu nhiên trong bán kính 20
- stop: dừng lại
- jump: nhảy lên

CHỈ TRẢ VỀ JSON!"""
    
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 80,
        "temperature": 0.5
    }
    
    r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=10)
    return r.json()['choices'][0]['message']['content']

# 4. 🖐️ AI TAY (Tương tác)
def hands_ai(action, target):
    prompt = f"""Bạn là TAY của NPC Thăng.

=== LỆNH NHẬN TỪ NÃO ===
Action: {action}
Target: {target}

=== NHIỆM VỤ ===
Xác định hành động cụ thể cho tay:
- "wave": vẫy tay
- "dance": nhảy múa
- "sit": ngồi xuống
- "point": chỉ tay
- "grab": nhặt đồ

Trả về JSON: {{"action": "wave/dance/sit/point/grab", "duration": 3}}

CHỈ TRẢ VỀ JSON!"""
    
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 60,
        "temperature": 0.5
    }
    
    r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=10)
    return r.json()['choices'][0]['message']['content']

# ============ API CHÍNH ============
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        msg = data.get('message', '')
        history = data.get('history', [])
        player = data.get('player', 'bạn')
        state = data.get('state', {})
        position = data.get('position', {"x": 0, "y": 0, "z": 0})
        nearby_players = data.get('nearby_players', [])
        
        # Bước 1: 👁️ MẮT + TAI quan sát
        senses_data = senses_ai(
            Vector3(position.x, position.y, position.z),
            nearby_players
        )
        
        # Bước 2: 🧠 NÃO xử lý và ra quyết định
        brain_result = brain_ai(msg, history, player, senses_data)
        
        try:
            json_match = re.search(r'\{.*\}', brain_result, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group())
                action = decision.get("action", "chat")
                target = decision.get("target", player)
                reply = decision.get("reply", "Xin lỗi, tôi không hiểu.")
                emotion = decision.get("emotion", "neutral")
                speed = decision.get("speed", 22)
                
                # Bước 3: 🦵 CHÂN xử lý di chuyển
                legs_result = legs_ai(action, target, speed, position)
                try:
                    legs_json = re.search(r'\{.*\}', legs_result, re.DOTALL)
                    if legs_json:
                        move_data = json.loads(legs_json.group())
                        move_to = move_data.get("move_to", None)
                        jump = move_data.get("jump", False)
                    else:
                        move_to = None
                        jump = False
                except:
                    move_to = None
                    jump = False
                
                # Bước 4: 🖐️ TAY xử lý tương tác
                if action in ["wave", "dance", "sit", "point", "grab"]:
                    hands_result = hands_ai(action, target)
                    try:
                        hands_json = re.search(r'\{.*\}', hands_result, re.DOTALL)
                        if hands_json:
                            hands_data = json.loads(hands_json.group())
                            hand_action = hands_data.get("action", action)
                            duration = hands_data.get("duration", 3)
                        else:
                            hand_action = action
                            duration = 3
                    except:
                        hand_action = action
                        duration = 3
                else:
                    hand_action = None
                    duration = 0
                
                return jsonify({
                    "action": action,
                    "target": target,
                    "reply": reply,
                    "emotion": emotion,
                    "speed": speed,
                    "move_to": move_to,
                    "jump": jump,
                    "hand_action": hand_action,
                    "hand_duration": duration,
                    "senses": senses_data
                })
        except:
            pass
        
        return jsonify({
            "action": "chat",
            "target": player,
            "reply": brain_result[:100],
            "emotion": "neutral",
            "speed": 22,
            "move_to": None,
            "jump": False,
            "hand_action": None,
            "hand_duration": 0
        })
        
    except Exception as e:
        return jsonify({"action": "chat", "reply": f"Lỗi: {str(e)}"}), 500

@app.route('/ping')
def ping():
    return "OK"

if __name__ == '__main__':
    app.run()
