import json
from google import genai
from google.genai import types
from flask import Flask, request, jsonify
from math import ceil
import re
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import json_util
import requests

load_dotenv()

# Cấu hình Gemini API
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
database = client["CO3109"]
client_AI = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)

# Danh sách động cơ từ database (Bạn có thể lấy từ MongoDB)

def get_best_motor(cong_suat_can_tim, van_toc_quay_can_tim, dong_co_list):
    """
    Gửi yêu cầu đến Gemini API để chọn động cơ phù hợp nhất.
    """
    prompt = f"""
            Bạn là chuyên gia trong việc lựa chọn động cơ điện. Hãy tìm động cơ phù hợp nhất từ danh sách dưới đây.

            ### **Danh sách động cơ:**
            {json.dumps(dong_co_list, indent=2, ensure_ascii=False)}

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
    response = client_AI.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt])

    def extract_json_from_response(text):
        try:
            # Dò tìm đoạn JSON đầu tiên
            json_str = re.search(r"{.*}", text, flags=re.DOTALL).group(0)
            return json.loads(json_str)
        except:
            return {"best_motor_id": None, "reason": "Lỗi khi xử lý kết quả từ AI"}
    result = extract_json_from_response(response.text)
    return result

def get_material(sH, z, v):
    image_url = os.getenv("IMAGE_URL")
    image = requests.get(image_url)
    response = client_AI.models.generate_content(
    model="gemini-2.0-flash",
    contents=[f"""Tôi có một bảng vật liệu trong ảnh. Dựa vào bảng này, hãy chọn một vật liệu thích hợp nhất và chỉ giải thích trong json dựa trên các điều kiện sau:
                    1**Ứng suất tiếp xúc** ({sH}) phải **trong** khoảng ứng suất tiếp xúc trong bảng.  
                    2**Số răng bánh răng** ({z}) và **vận tốc xích** ({v}).  
                    3Trả kết quả dưới dạng **JSON** với các trường sau:
                    - `"vat_lieu"`: Tên vật liệu  
                    - `"nhiet_luyen"`: Nhiệt luyện  
                    - `"do_ran_be_mat"`: Độ rắn bề mặt
                    - `"giai_thich"`: Giải thích lý do chọn

                    Ví dụ:  
                    ```json
                    {{
                        "vat_lieu": "Thép 45",
                        "nhiet_luyen": "Tôi cải thiện",
                        "do_ran_be_mat": "HB170...210",
                        "giai_thich": "Vì này phù hợp nhất"
                    }}""",
              types.Part.from_bytes(data=image.content, mime_type="image/jpeg")])
    response_text = response.text.strip()

    try:
        json_match = re.search(r"```json\n(.*?)\n```", response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)
        result = json.loads(response_text)
        return result

    except json.JSONDecodeError:
        return {"error": "Lỗi khi xử lý JSON từ AI!"}
    except Exception as e:
        return {"error": f"Lỗi không xác định: {str(e)}"}

def extract_fields_from_image(images_bytes):
    prompt = """
    Bạn là chuyên gia trích xuất dữ liệu từ biểu mẫu kỹ thuật. Ảnh đầu vào là một form có nhãn tiếng Việt và các ô nhập liệu giá trị số.

    Dựa vào nội dung ảnh, hãy đọc và trích xuất các trường thông số kỹ thuật sau (nếu có), và trả về dưới dạng JSON chính xác với cấu trúc sau:

    - F: Lực vòng băng tải (N)
    - v: Vận tốc băng tải (m/s)
    - D: Đường kính tang dẫn (mm)
    - L: Thời gian phục vụ (năm)
    - t1: Thời gian t1 (s)
    - t2: Thời gian t2 (s)
    - T1: Thời gian T1 (s)
    - T2: Thời gian T2 (s)
    - nol: Hiệu suất Ổ lăn
    - nbr: Hiệu suất Bánh răng
    - nx: Hiệu suất Xích
    - uh: Hệ số Truyền động hộp
    - u1: Hệ số Truyền cấp nhanh
    - u2: Hệ số Truyền cấp chậm
    - ux: Hệ số Truyền xích

    ### Đầu ra yêu cầu:
    ```json
    {{
        "F": {Giá trị},
        "v": {Giá trị},
        "D": {Giá trị},
        "L": {Giá trị},
        "t1": {Giá trị},
        "t2": {Giá trị},
        "T1": {Giá trị},
        "T2": {Giá trị},
        "nol": {Giá trị},
        "nbr": {Giá trị},
        "nx": {Giá trị},
        "uh": {Giá trị},
        "u1": {Giá trị},
        "u2": {Giá trị},
        "ux": {Giá trị}
    }}
    (Chỉ trả JSON, không thêm mô tả)
    """

    response = client_AI.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            prompt,
            types.Part.from_bytes(data=images_bytes, mime_type="image/png")
        ]
    )
    response_text = response.text.strip()
    try:
        # Tìm và tách phần JSON chính xác nếu Gemini trả về có đánh dấu
        json_match = re.search(r"```json\n(.*?)\n```", response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)

        result = json.loads(response_text)
        return result
    except json.JSONDecodeError:
        return {"error": "Lỗi khi xử lý JSON từ AI"}
    except Exception as e:
        return {"error": f"Lỗi không xác định: {str(e)}"}

@app.route("/api-ai/find-engine", methods=["POST"])
def findBestEngine():
    
    collection = database["dong_co_dien"]
    try:
        data = request.json
        cong_suat_can_tim = int(ceil(float(data.get("cong_suat_can_tim", 0))))
        van_toc_quay_can_tim = int(ceil(float(data.get("van_toc_quay_can_tim", 0))))
        if cong_suat_can_tim == 0 or van_toc_quay_can_tim == 0:
            return jsonify({"error": "Thiếu thông số đầu vào"}), 400
        dong_co_list = list(collection.find({
            "cong_suat": {"$gte": cong_suat_can_tim},
            "van_toc_vong_quay": {"$gte": van_toc_quay_can_tim}
        }))
        dong_co_list = json.loads(json_util.dumps(dong_co_list))
        best_motor_id = get_best_motor(cong_suat_can_tim, van_toc_quay_can_tim, dong_co_list)
        return jsonify(best_motor_id), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api-ai/find-material", methods=["POST"])
def findMaterial():
    try:
        data = request.json
        sH = float(data["sH"]) if "sH" in data else None
        z = float(data["z"]) if "z" in data else None
        v = float(data["v"]) if "v" in data else None
        material = get_material(sH, z, v)
        return jsonify(material), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api-ai/extract-input-image", methods=["POST"])
def extract_input():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    try:
        image_bytes = file.read()
        result = extract_fields_from_image(image_bytes)
        required_fields = ["F", "v", "D", "L", "t1", "t2", "T1", "T2", "nol", "nbr", "nx", "uh", "u1", "u2", "ux"]
        missing_fields = [field for field in required_fields if field not in result or result[field] is None]

        if missing_fields:
            return jsonify({
                "error": f"Thiếu các trường bắt buộc: {', '.join(missing_fields)}",
                "data": result
            }), 400

        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Render cấp PORT động
    app.run(host="0.0.0.0", port=port)
