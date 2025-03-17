import json
import google.generativeai as genai
from flask import Flask, request, jsonify
from math import ceil
import requests
import re
import os
from dotenv import load_dotenv

load_dotenv()

# Cấu hình Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)

# Danh sách động cơ từ database (Bạn có thể lấy từ MongoDB)


def fetch_database_data(url):
    response = requests.get(url)
    return response.json()

dong_co_list = []
dong_co_list = fetch_database_data("http://localhost:5165/api/dong_co_4a")
dong_co_list += fetch_database_data("http://localhost:5165/api/dong_co_dk")
dong_co_list += fetch_database_data("http://localhost:5165/api/dong_co_k")

def get_best_motor(cong_suat_can_tim, van_toc_quay_can_tim):
    filter_dong_co = list(filter(lambda x: x['cong_suat'] >= cong_suat_can_tim, dong_co_list))
    """
    Gửi yêu cầu đến Gemini API để chọn động cơ phù hợp nhất.
    """
    prompt = f"""
            Bạn là chuyên gia trong việc lựa chọn động cơ điện. Hãy tìm động cơ phù hợp nhất từ danh sách dưới đây.

            ### **Danh sách động cơ:**
            {json.dumps(filter_dong_co, indent=2, ensure_ascii=False)}

            ### **Tiêu chí lựa chọn:**
            1. **Công suất (`cong_suat` kW)** phải lớn hơn hoặc bằng giá trị yêu cầu.
            2. **Vận tốc vòng quay (`van_toc_vong_quay` vòng/phút) gần nhất** lớn hơn hoặc bằng với giá trị yêu cầu.

            ### **Thông số yêu cầu:**
            - **Công suất tối thiểu:** {cong_suat_can_tim} kW
            - **Vận tốc vòng quay:** {van_toc_quay_can_tim} RPM

            ### **Yêu cầu đầu ra:**
            - Chỉ trả về duy nhất một **Id** của động cơ phù hợp nhất.
            - Giải thích lý do chọn động cơ đó và nếu được thì tìm tài liệu và link để người dùng biết thêm về động cơ này.
            - Bắt buộc trả về dưới dạng JSON **chính xác**, không thêm giải thích.

            ### **Định dạng JSON chính xác (bắt buộc làm theo):**
            ```json
            {{
                "best_motor_id": "id của động cơ phù hợp nhất",
                "reason": "Lý do chọn động cơ"
            }}
    """

    model = genai.GenerativeModel("gemini-2.0-pro-exp-02-05")
    response = model.generate_content(prompt)

    response_text = response.text.strip()
    response_text = re.sub(r"```json\n(.*?)\n```", r"\1", response_text, flags=re.DOTALL)

    try:
        # Parse lại JSON đúng định dạng
        result = json.loads(response_text)
        return result
    except json.JSONDecodeError:
        return {"best_motor_id": None, "reason": "Lỗi khi xử lý kết quả từ AI"}

@app.route("/api-ai/find-engine", methods=["POST"])
def findBestEngine():
    try:
        data = request.json
        cong_suat_can_tim = ceil(float(data.get("cong_suat_can_tim", 0)))
        van_toc_quay_can_tim = ceil(float(data.get("van_toc_quay_can_tim", 0)))

        if cong_suat_can_tim == 0 or van_toc_quay_can_tim == 0:
            return jsonify({"error": "Thiếu thông số đầu vào"}), 400
        best_motor_id = get_best_motor(cong_suat_can_tim, van_toc_quay_can_tim)
        print(best_motor_id)
        return jsonify({"best_motor_id": best_motor_id})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
