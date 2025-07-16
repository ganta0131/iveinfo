from flask import Flask, render_template, request, jsonify
import os
from google.generativeai import AIModel, Model
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Gemini APIの設定
model = Model('gemini-1.5-flash', api_key=os.getenv('GOOGLE_SERVICE_ACCOUNT_INFO'))

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
        
        return jsonify({
            'success': True,
            'events': events_info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True)
