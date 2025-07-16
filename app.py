from flask import Flask, render_template, request, jsonify
import os
import json
from google.generativeai import get_model, Model
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Google Cloudの認証情報設定
try:
    credentials = os.getenv('GOOGLE_SERVICE_ACCOUNT_INFO')
    if credentials:
        # JSON文字列を辞書に変換
        try:
            credentials_dict = json.loads(credentials)
            # 一時ファイルに認証情報を保存
            with open('/tmp/credentials.json', 'w') as f:
                json.dump(credentials_dict, f)
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/tmp/credentials.json'
            print("Credentials set successfully")
        except json.JSONDecodeError:
            print("Invalid JSON format in credentials")
            raise ValueError("Invalid JSON format in GOOGLE_SERVICE_ACCOUNT_INFO")
    else:
        print("No credentials found in environment variable")
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_INFO not found")
except Exception as e:
    print(f"Error setting up credentials: {str(e)}")
    raise  # エラーを再スローしてアプリケーションの起動を防ぐ

# Gemini APIの設定
try:
    # モデルの初期化前にAPIクライアントを設定
    from google.ai.generativelanguage_v1beta import GenerativeLanguageClient
    client = GenerativeLanguageClient()
    
    # モデルのリストを取得して確認
    models = client.list_models()
    print(f"Available models: {models}")
    
    # 指定のモデルが存在するか確認
    model_id = 'models/gemini-pro-vision-flash'
    model = client.get_model(name=model_id)
    print(f"Model {model_id} found and initialized successfully")
    
except Exception as e:
    print(f"Error initializing Gemini API: {str(e)}")
    import traceback
    print(f"Full traceback: {traceback.format_exc()}")
    raise  # エラーを再スローしてアプリケーションの起動を防ぐ

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
        response = model.generate(prompt)
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
