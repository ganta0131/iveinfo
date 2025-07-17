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
主菜：レシピ名
  材料：
  - 材料1：分量
  - 材料2：分量
  作り方：
  1. 手順1
  2. 手順2
副菜：レシピ名
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
                # テキストをクリーニング
                cleaned_text = meal_plan.strip()
                print(f"=== Cleaned Text ===")
                print(cleaned_text)
                print("=== End of Cleaned Text ===")
                
                # 買い物リストの開始位置を特定
                shopping_start = cleaned_text.find('買い物リスト')
                if shopping_start == -1:
                    shopping_start = cleaned_text.find('材料リスト')
                
                if shopping_start != -1:
                    # 買い物リストとそれ以前のテキストに分割
                    recipes_text = cleaned_text[:shopping_start].strip()
                    shopping_text = cleaned_text[shopping_start:].strip()
                else:
                    recipes_text = cleaned_text
                    shopping_text = ""
                
                # レシピのHTML生成
                recipes_html = '<div class="recipes">'
                
                # 日別のレシピを処理
                # 和食、洋食、中華の順番で割り当てる
                genre_order = ['和食'] * japanese + ['洋食'] * western + ['中華'] * chinese
                
                # テキストを分割して日別のレシピを処理
                day_texts = [f"{d}日目" for d in range(1, days + 1)]
                day_contents = []
                current_start = 0
                
                # まず全ての日付の内容を取得
                for i, day_text in enumerate(day_texts):
                    next_text = f"{i + 2}日目" if i < len(day_texts) - 1 else None
                    day_start = recipes_text.find(day_text, current_start)
                    
                    if day_start != -1:
                        day_end = recipes_text.find(next_text, day_start) if next_text else len(recipes_text)
                        day_content = recipes_text[day_start:day_end].strip()
                        day_contents.append(day_content)
                        current_start = day_end
                    else:
                        day_contents.append("")
                
                # レシピを表示
                for day in range(1, days + 1):
                    day_text = f"{day}日目"
                    day_content = day_contents[day-1]
                    genre = genre_order[day-1]  # ジャンルを取得
                    
                    recipes_html += f'<div class="recipe-day">'
                    recipes_html += f'<h3>{day_text}({genre})</h3>'
                    
                    # レシピの内容を表示
                    if day_content:
                        # 主菜を処理
                        main_dish_start = day_content.find('- 主菜：')
                        if main_dish_start != -1:
                            main_dish_end = day_content.find('- 副菜：', main_dish_start)
                            if main_dish_end == -1:
                                main_dish_end = len(day_content)
                            main_content = day_content[main_dish_start:main_dish_end].strip()
                            if main_content:
                                recipes_html += f'<div class="recipe-item"><u>{main_content}</u></div>'
                        
                        # 副菜を処理
                        side_dish_start = day_content.find('- 副菜：')
                        if side_dish_start != -1:
                            side_content = day_content[side_dish_start:].strip()
                            if side_content:
                                recipes_html += f'<div class="recipe-item"><u>{side_content}</u></div>'
                    
                    recipes_html += '</div>'
                            
                            # 主菜と副菜を処理
                            main_dish = day_content.find('- 主菜：')
                            side_dish = day_content.find('- 副菜：')
                            
                            if main_dish != -1:
                                main_content = day_content[main_dish:].split('- 副菜：')[0].strip()
                                recipes_html += f'<div class="recipe-item"><u>{main_content}</u></div>'
                            
                            if side_dish != -1:
                                side_content = day_content[side_dish:].strip()
                                recipes_html += f'<div class="recipe-item"><u>{side_content}</u></div>'
                            
                            recipes_html += '</div>'
                
                recipes_html += '</div>'
                
                # 買い物リストのHTML生成
                shopping_list_html = '<div class="shopping-list">'
                
                if shopping_text:
                    # 買い物リストの項目を処理
                    items = shopping_text.split('\n')
                    for item in items:
                        if item.strip().startswith('- '):
                            clean_item = item.strip().replace('-', '').strip()
                            if clean_item:
                                shopping_list_html += f'<div class="shopping-item">{clean_item}</div>'
                
                shopping_list_html += '</div>'
                
                print(f"Generated recipes HTML: {recipes_html}")  # デバッグ用
                print(f"Generated shopping list HTML: {shopping_list_html}")  # デバッグ用
                
                return jsonify({
                    'success': True,
                    'recipes': recipes_html,
                    'shoppingList': shopping_list_html
                })
            except Exception as e:
                error_msg = f"Error processing response: {str(e)}"
                print(error_msg)
                print(f"Full traceback: {traceback.format_exc()}")
                return jsonify({
                    'success': False,
                    'error': error_msg
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
