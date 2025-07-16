from flask import Flask, render_template, request, jsonify
import os
import json
from google.generativeai import get_model
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Google Cloudの認証情報設定
try:
    credentials = os.getenv('GOOGLE_SERVICE_ACCOUNT_INFO')
    if credentials:
        # 一時ファイルに認証情報を保存
        with open('/tmp/credentials.json', 'w') as f:
            f.write(credentials)
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/tmp/credentials.json'
        print("Credentials set successfully")
    else:
        print("No credentials found in environment variable")
except Exception as e:
    print(f"Error setting up credentials: {str(e)}")

# Gemini APIの設定
try:
    model = get_model('models/gemini-1.5-flash')
    print("Gemini API initialized successfully")
except Exception as e:
    print(f"Error initializing Gemini API: {str(e)}")
    model = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_events', methods=['POST'])
def get_events():
    try:
        if model is None:
            return jsonify({
                'success': False,
                'error': 'Gemini API initialization failed'
            }), 500

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
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
