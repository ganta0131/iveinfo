from flask import Flask, render_template, request, jsonify
import os
import traceback
import google.generativeai as genai
from dotenv import load_dotenv
import re

load_dotenv()

app = Flask(__name__)

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
        people = int(data.get('people', 1))
        days = int(data.get('days', 7))
        japanese = int(data.get('japanese', 0))
        western = int(data.get('western', 0))
        chinese = int(data.get('chinese', 0))

        # 入力値のバリデーション
        if not all([people, days, japanese, western, chinese]):
            raise ValueError("全ての入力値が必要です")
        if days < 1 or days > 7:
            raise ValueError("日数は1〜7日の間で指定してください")
        if japanese + western + chinese != days:
            raise ValueError("和食・洋食・中華の合計日数が指定された日数と一致しません")

        # プロンプトの作成
        prompt = f"""以下の条件に基づいて、1週間分の夕食レシピ（主菜＋副菜）を生成してください。

条件：
- 人数：{people}人
- 献立日数：{days}日
- 和食：{japanese}日
- 洋食：{western}日
- 中華：{chinese}日
- 1日あたりの材料費は1人当たり150円以内
- 使用食材は週内で共通化（少なめに）
- 分量は人数に応じて自動調整
- 作り方は簡潔・一般向け
- 買い物リストには調味料（塩、こしょう、醤油、みりん、酒、酢、砂糖など）を含めない

各日のレシピは以下の形式で出力してください：
1日目
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

最後に、同じ食材を合算して買い物リストを作成してください。ただし、調味料は除外してください：
- 材料名：合算分量
- 材料名：合算分量
"""

        # AIによるレシピ生成
        try:
            response = model.generate_content(prompt)
            meal_plan = response.text
            print("=== Raw Meal Plan ===")
            print(meal_plan)
            print("=== End of Raw Meal Plan ===")
            
            # レシピと買い物リストをHTML形式に変換
            try:
                paragraphs = meal_plan.split('\n')
                recipes_html = '<div class="recipes">'
                shopping_list_html = '<div class="shopping-list">'
                
                is_shopping_list = False
                current_day = None
                current_recipe = None
                current_section = None
                
                for para in paragraphs:
                    if not para.strip():
                        continue
                    
                    # 日付の検出
                    day_match = re.match(r'^\d+日目$', para.strip())
                    if day_match:
                        if current_day:
                            recipes_html += '</div>'
                        current_day = day_match.group(1)
                        recipes_html += f'<div class="recipe-day">'
                        recipes_html += f'<h3>{para.strip()}</h3>'
                        continue
                    
                    # 買い物リストの開始
                    if '買い物リスト' in para.strip() or '材料リスト' in para.strip():
                        is_shopping_list = True
                        continue
                    
                    # レシピタイプの検出
                    if para.strip().startswith('- 主菜：') or para.strip().startswith('- 副菜：'):
                        if current_recipe:
                            recipes_html += '</div>'
                        current_recipe = para.strip()
                        recipes_html += f'<div class="recipe-item">{para.strip()}</div>'
                        current_section = None
                        continue
                    
                    # セクションの検出
                    if para.strip().startswith('材料：') or para.strip().startswith('作り方：'):
                        current_section = para.strip()
                        recipes_html += f'<div class="recipe-section">'
                        recipes_html += f'<h4>{para.strip()}</h4>'
                        continue
                    
                    if is_shopping_list:
                        # 買い物リストの項目を処理
                        if para.strip().startswith('- '):
                            item = para.strip().replace('-', '').strip()
                            if item:
                                shopping_list_html += f'<div class="shopping-item">{item}</div>'
                    else:
                        # レシピの項目を処理
                        if current_recipe:
                            if current_section:
                                # 材料や作り方の項目を処理
                                if para.strip().startswith('- '):
                                    item = para.strip().replace('-', '').strip()
                                    if item:
                                        recipes_html += f'<div class="recipe-content">{item}</div>'
                                else:
                                    recipes_html += f'<div class="recipe-content">{para.strip()}</div>'
                            else:
                                # レシピ名の下の説明を処理
                                recipes_html += f'<div class="recipe-content">{para.strip()}</div>'
                
                if current_recipe:
                    recipes_html += '</div>'
                if current_day:
                    recipes_html += '</div>'
                
                recipes_html += '</div>'
                shopping_list_html += '</div>'
                
                print(f"Generated recipes HTML: {recipes_html}")  # デバッグ用
                print(f"Generated shopping list HTML: {shopping_list_html}")  # デバッグ用
                
                return jsonify({
                    'success': True,
                    'recipes': recipes_html,
                    'shoppingList': shopping_list_html
                })
            except Exception as e:
                print(f"Error processing response: {str(e)}")
                print(f"Full traceback: {traceback.format_exc()}")
                return jsonify({
                    'success': False,
                    'error': f'Error processing response: {str(e)}'
                }), 500
        except Exception as e:
            print(f"Error generating meal plan: {str(e)}")
            print(f"Full traceback: {traceback.format_exc()}")
            return jsonify({
                'success': False,
                'error': f'Error generating meal plan: {str(e)}'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
