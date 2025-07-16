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

@app.route('/get_events', methods=['POST'])
def get_events():
    try:
        # プロンプトを読み込む
        with open('プロンプト.txt', 'r', encoding='utf-8') as f:
            prompt = f.read()
            
        # AIによるイベント情報生成
        response = model.generate_content(prompt)
        events_info = response.text
        
        # テキストをHTMLの段落に変換
        paragraphs = events_info.split('\n')
        formatted_html = '<div class="events-container">'
        for para in paragraphs:
            formatted_html += f'<p>{para}</p>'
        formatted_html += '</div>'
        
        return jsonify({
            'success': True,
            'events': formatted_html
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
