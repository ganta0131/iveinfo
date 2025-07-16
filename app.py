from flask import Flask, render_template, request, jsonify
import os
from google.generativeai import get_model
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Gemini APIの設定
try:
    model = get_model('gemini-1.5-flash')
    model._api_key = os.getenv('GOOGLE_SERVICE_ACCOUNT_INFO')
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
