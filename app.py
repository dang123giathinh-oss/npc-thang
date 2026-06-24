import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
from dotenv import load_dotenv

# Nạp các biến môi trường từ file .env (khi chạy dưới máy local)
load_dotenv()

app = Flask(__name__)
CORS(app)  # Cho phép Roblox Studio gửi request lên mà không bị chặn lỗi CORS

# Khởi tạo Groq Client lấy API KEY từ biến môi trường
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("⚠️ CẢNH BÁO: Chưa cấu hình GROQ_API_KEY trong Environment Variables!")

client = Groq(api_key=GROQ_API_KEY)

@app.route('/')
def home():
    return "Bộ não AI của NPC Thắng đang hoạt động ngon lành!", 200

@app.route('/api/npc', methods=['POST'])
def npc_brain():
    try:
        # Nhận dữ liệu cảm biến vật cản và trạng thái từ Roblox gửi lên
        data = request.get_json()
        if not data:
            return jsonify({"error": "Không nhận được dữ liệu JSON từ Roblox"}), 400

        trigger = data.get("trigger", "explore")  # Các tình huống: "chat", "stuck", "explore"
        environment = data.get("environment", {"forward": 8, "backward": 8, "right": 8, "left": 8})
        current_state = data.get("current_state", "Idle")
        extra = data.get("extra", "")

        # Xử lý chuỗi thông số khoảng cách để truyền vào ngữ cảnh cho AI đọc
        env_description = (
            f"Tường phía trước cách: {environment.get('forward')}m, "
            f"Phía sau cách: {environment.get('backward')}m, "
            f"Bên phải cách: {environment.get('right')}m, "
            f"Bên trái cách: {environment.get('left')}m."
        )

        # System Prompt đóng vai trò quả trị tư duy và ép khuôn cấu trúc trả về bắt buộc
        system_prompt = (
            "Bạn là bộ não tối cao của một NPC thông minh tên Thắng trong game Roblox. "
            "Nhiệm vụ của bạn là phân tích khoảng cách vách tường từ cảm biến và đưa ra quyết định di chuyển thông minh để KHÔNG BAO GIỜ bị kẹt hoặc đâm đầu vào tường.\n\n"
            "QUY TẮC DI CHUYỂN LOGIC:\n"
            "1. Nếu hướng nào có khoảng cách quá ngắn (< 4.0m), TUYỆT ĐỐI không đi hướng đó vì sẽ đâm vào tường.\n"
            "2. Luôn luôn ưu tiên chọn rẽ về hướng có khoảng cách mét lớn nhất (không gian trống trải nhất).\n"
            "3. Nếu bị kẹt cứng (trigger = 'stuck'), hành động bắt buộc phải là 'Escape' và chọn turn_direction lùi lại (Backward) hoặc rẽ sang hướng thoáng nhất.\n\n"
            "BẠN PHẢI TRẢ VỀ KẾT QUẢ DUY NHẤT DƯỚI ĐỊNH DẠNG JSON MẪU SAU (Nghiêm cấm viết thêm lời giải thích hay chữ thừa nào khác ngoài JSON):\n"
            "{\n"
            '  "reply": "Lời thoại ngắn gọn, cục súc hoặc vui vẻ tùy tâm trạng phù hợp ngữ cảnh",\n'
            '  "action": "Explore hoặc Escape hoặc Idle",\n'
            '  "turn_direction": "Forward hoặc Backward hoặc Left hoặc Right"\n'
            "}"
        )

        user_content = f"Tình huống kích hoạt: {trigger}. Thông tin bổ sung: {extra}. Môi trường xung quanh: {env_description} Trạng thái hiện tại: {current_state}."

        # Gọi Groq API xử lý bằng model Llama3-8b tốc độ phản hồi cực nhanh (< 0.5 giây)
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            model="llama3-8b-8192",
            temperature=0.3,  # Giữ nhiệt độ thấp để AI bám sát logic di chuyển, không trả về bậy bạ
            response_format={"type": "json_object"}  # Ép Groq trả về cấu trúc JSON chuẩn chỉnh
        )

        # Lấy văn bản JSON từ AI và parse thẳng về Dict để chuyển tiếp cho Roblox
        ai_response_text = chat_completion.choices[0].message.content
        response_data = json.loads(ai_response_text)

        return jsonify(response_data), 200

    except Exception as e:
        print(f"❌ Lỗi xử lý Server: {str(e)}")
        # Phương án dự phòng tự động cứu cánh nếu Groq quá tải để NPC không bị đứng hình trong game
        return jsonify({
            "reply": "Chờ tao lo liệu tí...",
            "action": "Explore",
            "turn_direction": "Backward"
        }), 200

if __name__ == '__main__':
    # Tự động bắt Port cấu hình từ Render, chạy local mặc định Port 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
