import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

@app.route('/')
def home():
    return "Bộ não AI tối cao 8 hướng đang hoạt động!", 200

@app.route('/api/npc', methods=['POST'])
def npc_brain():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON payload received"}), 400

        trigger = data.get("trigger", "explore")
        environment = data.get("environment", {})
        current_state = data.get("current_state", "Idle")
        extra = data.get("extra", "")

        # Xử lý chuỗi thông số cảm biến không gian 8 hướng hoàn chỉnh (Yêu cầu 3)
        env_description = (
            f"Chính diện trước: {environment.get('forward')}m, "
            f"Chéo trước-Phải (45°): {environment.get('forward_right')}m, "
            f"Chính phải (90°): {environment.get('right')}m, "
            f"Chéo sau-Phải (135°): {environment.get('backward_right')}m, "
            f"Chính sau (180°): {environment.get('backward')}m, "
            f"Chéo sau-Trái (225°): {environment.get('backward_left')}m, "
            f"Chính trái (270°): {environment.get('left')}m, "
            f"Chéo trước-Trái (315°): {environment.get('forward_left')}m."
        )

        # Cập nhật System Prompt dạy AI tư duy không gian góc chéo nhạy bén
        system_prompt = (
            "Bạn là bộ não tối cao điều khiển một NPC thông minh tên Thắng trong game Roblox. "
            "Nhiệm vụ của bạn là phân tích dữ liệu khoảng cách vách tường từ cảm biến 8 hướng xung quanh để đưa ra quyết định di chuyển tối ưu nhất.\n\n"
            "QUY TẮC DI CHUYỂN TOÀN DIỆN:\n"
            "1. Nếu hướng nào có khoảng cách vật cản quá ngắn (< 4.0m), TUYỆT ĐỐI không cho NPC đi hướng đó.\n"
            "2. Hãy xem xét kỹ các hướng chéo (ForwardRight, ForwardLeft, BackwardRight, BackwardLeft). Đôi khi rẽ góc chéo 45 độ giúp né tường mượt mà hơn rẽ vuông góc.\n"
            "3. Luôn luôn ưu tiên chọn 'turn_direction' về hướng có khoảng cách mét lớn nhất, trống trải nhất.\n"
            "4. Nếu bị kẹt cứng (trigger = 'stuck'), hành động phải là 'Escape' và chọn turn_direction lùi lại (Backward) hoặc bẻ lái gấp sang hướng có khoảng cách thoáng nhất.\n\n"
            "BẠN PHẢI TRẢ VỀ KẾT QUẢ DUY NHẤT DƯỚI ĐỊNH DẠNG JSON SAU (Không viết lời giải thích, không thừa ký tự ngoài JSON):\n"
            "{\n"
            '  "reply": "Lời thoại ngắn gọn, cục súc hoặc hài hước phù hợp hoàn cảnh hiện tại",\n'
            '  "action": "Explore hoặc Escape hoặc Idle",\n'
            '  "turn_direction": "Forward hoặc Backward hoặc Left hoặc Right hoặc ForwardRight hoặc ForwardLeft hoặc BackwardRight hoặc BackwardLeft"\n'
            "}"
        )

        user_content = f"Tình huống kích hoạt: {trigger}. Thông tin bổ sung: {extra}. Bản đồ cảm biến 8 hướng: {env_description} Trạng thái hiện tại: {current_state}."

        if not client:
            raise Exception("Groq Client chưa cấu hình API Key")

        # Gọi mô hình tư duy nhanh Llama 3
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            model="llama3-8b-8192",
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        ai_response_text = chat_completion.choices[0].message.content
        response_data = json.loads(ai_response_text)

        return jsonify(response_data), 200

    except Exception as e:
        print(f"❌ Sự cố Server: {str(e)}")
        # Cứu cánh mặc định tại Server để tăng độ tin cậy
        return jsonify({
            "reply": "Có gì đó không ổn, để tao tự mò đường...",
            "action": "Explore",
            "turn_direction": "Backward"
        }), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
