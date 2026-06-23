import os
import json
import random
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY")
)

# Từ điển cảm xúc và hành động
emotion_map = {
    "vui vẻ": "happy",
    "buồn bã": "sad",
    "sợ hãi": "scared",
    "tức giận": "angry",
    "ngạc nhiên": "surprised",
    "tò mò": "curious",
    "chán nản": "bored"
}

action_map = {
    "happy": "wave",
    "sad": "cry",
    "scared": "cower",
    "angry": "stomp",
    "surprised": "jump",
    "curious": "scratch_head",
    "bored": "yawn"
}

@app.route("/api/npc", methods=["POST"])
def npc_chat():
    try:
        data = request.json
        messages = data.get("messages", [])
        current_mood = data.get("mood", "vui vẻ")

        system_prompt = f"""Bạn là Thăng, một NPC trong game Roblox.
Tính cách: thân thiện, hài hước, nói chuyện tự nhiên như bạn bè.
Trạng thái cảm xúc hiện tại: {current_mood}.

QUAN TRỌNG: Bạn phải trả lời bằng JSON theo format sau:
{{
    "reply": "câu trả lời ngắn gọn (1-2 câu), dùng mày-tao",
    "emotion": "happy/sad/scared/angry/surprised/curious/bored",
    "action": "wave/cry/cower/stomp/jump/scratch_head/yawn/none"
}}

Luôn trả về JSON hợp lệ. Không thêm text ngoài JSON."""

        full_messages = [{"role": "system", "content": system_prompt}] + messages

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=full_messages,
            temperature=0.9,
            max_tokens=200
        )

        bot_reply = response.choices[0].message.content
        
        # Parse JSON từ AI
        try:
            result = json.loads(bot_reply)
        except:
            # Fallback nếu AI không trả JSON đúng
            result = {
                "reply": bot_reply,
                "emotion": "curious",
                "action": "none"
            }

        # Gán action dựa trên emotion nếu chưa có
        if result.get("action") == "none":
            result["action"] = action_map.get(result.get("emotion", "curious"), "none")

        return jsonify(result)

    except Exception as e:
        print("LOI:", str(e))
        return jsonify({
            "reply": "Thang hơi lag...",
            "emotion": "bored",
            "action": "yawn"
        })

@app.route("/test")
def test():
    return "Server OK"
