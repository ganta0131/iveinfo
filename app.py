from flask import Flask, render_template, request, jsonify
import os
import traceback
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Google Cloudの認証情報設定
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.getenv('GOOGLE_SERVICE_ACCOUNT_INFO')
if not os.getenv('GOOGLE_SERVICE_ACCOUNT_INFO'):
    raise ValueError("GOOGLE_SERVICE_ACCOUNT_INFO not found")

# Gemini APIの設定
try:
    genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("Gemini API initialized successfully")
except Exception as e:
    print(f"Error initializing Gemini API: {str(e)}")
    print(f"Full traceback: {traceback.format_exc()}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_meal_plan', methods=['POST'])
def get_meal_plan():
    try:
        data = request.get_json()
        people = data.get('people', 1)
        days = data.get('days', 7)
        japanese = data.get('japanese', 0)
        western = data.get('western', 0)
        chinese = data.get('chinese', 0)

        # プロンプトの作成
        prompt = f"""以下の条件に基づいて、1週間分の夕食レシピ（主菜＋副菜）を生成してください。

条件：
- 人数：{people}人
- 献立日数：{days}日
- 和食：{japanese}日
- 洋食：{western}日
- 中華：{chinese}日
- 1日あたりの材料費は300円以内
- 使用食材は週内で共通化（少なめに）
- 分量は人数に応じて自動調整
- 作り方は簡潔・一般向け

各日のレシピは以下の形式で出力してください：
1. 日付（例：1日目）
   - 主菜：レシピ名
     材料：
     - 材料1：分量
     - 材料2：分量
     作り方：
     1. 手順1
     2. 手順2
   - 副菜：レシピ名
     材料：
     - 材料1：分量
     - 材料2：分量
     作り方：
     1. 手順1
     2. 手順2

最後に、同じ食材を合算して買い物リストを作成してください：
- 材料名：合算分量
- 材料名：合算分量
"""

        # AIによるレシピ生成
        response = model.generate_content(prompt)
        meal_plan = response.text

        # レシピと買い物リストをHTML形式に変換
        paragraphs = meal_plan.split('\n')
        recipes_html = '<div class="recipes">'
        shopping_list_html = '<div class="shopping-list">'
        
        is_shopping_list = False
        for para in paragraphs:
            if para.strip() == '最後に、同じ食材を合算して買い物リストを作成してください：':
                is_shopping_list = True
                continue
            
            if not para.strip():
                continue
            
            if is_shopping_list:
                shopping_list_html += f'<p>{para}</p>'
            else:
                recipes_html += f'<div class="recipe-item">{para}</div>'
        
        recipes_html += '</div>'
        shopping_list_html += '</div>'
        
        return jsonify({
            'success': True,
            'recipes': recipes_html,
            'shoppingList': shopping_list_html
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
