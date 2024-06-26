import os
import platform
import pyaudio
import wave
from gtts import gTTS
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from flask import Flask, request, jsonify, render_template
import webbrowser
from threading import Timer
import pyvts
import asyncio

# Initialize GPT model and tokenizer
model_name = 'gpt2-xl'  # gpt2-xl 모델 선택
model = GPT2LMHeadModel.from_pretrained(model_name)
tokenizer = GPT2Tokenizer.from_pretrained(model_name)

# Flask app initialization
app = Flask(__name__)

# VTube Studio API 연결 설정
vts = pyvts.vts()

async def connect_vts():
    await vts.connect()

    # API 인증 데이터
    auth_data = {
        "apiName": "VTubeStudioPublicAPI",
        "apiVersion": "1.0",
        "requestID": "SomeID",
        "messageType": "AuthenticationTokenRequest",
        "data": {
            "pluginName": "My Cool Plugin",
            "pluginDeveloper": "My Name",
            "pluginIcon": "iVBORw0.........KGgoA="
        }
    }

    # 인증 요청
    response = await vts.request(auth_data)
    
    # API 키가 제공되면 저장
    if 'data' in response and 'authenticationToken' in response['data']:
        api_key = response['data']['authenticationToken']
        print(f"Authenticated with API key: {api_key}")
    else:
        print("Failed to authenticate")
    
    # 예제: 캐릭터 상태 변경
    # await vts.some_method_to_change_state()

    print("Authenticated and connected to VTube Studio")

asyncio.run(connect_vts())

# Function to play a .wav file using PyAudio
def play_wav_file(filename):
    wav_file = wave.open(filename, 'rb')
    p = pyaudio.PyAudio()

    stream = p.open(format=p.get_format_from_width(wav_file.getsampwidth()),
                    channels=wav_file.getnchannels(),
                    rate=wav_file.getframerate(),
                    output=True)

    data = wav_file.readframes(1024)
    while data:
        stream.write(data)
        data = wav_file.readframes(1024)

    stream.stop_stream()
    stream.close()
    p.terminate()

# Function to convert text to speech using gTTS and save the result
def make_tts(content):
    tts = gTTS(text=content, lang='en')
    tts.save('response.wav')

# Function to generate response using GPT model
def generate_gpt_response(text):
    input_ids = tokenizer.encode(text, return_tensors='pt')
    output_ids = model.generate(input_ids, max_length=50, num_return_sequences=1)
    response_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    return response_text

# Route to serve the index.html page
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle chat functionality
@app.route('/chat', methods=['POST'])
def chat():
    input_text = request.json.get('text')
    if not input_text:
        return jsonify({'error': "No 'text' field found in JSON request."}), 400

    print("User input: ", input_text)

    # Generate response using GPT model
    response = generate_gpt_response(input_text)
    print("Response from GPT model: ", response)

    # Convert response text to speech
    make_tts(response)

    # Play the generated response (macOS)
    play_on_macos('response.wav')

    # VTube Studio와 상호작용
    asyncio.run(send_to_vts(response))

    # Return AI response in the JSON
    return jsonify({'response': response}), 200

# VTube Studio로 텍스트를 전송하는 함수
async def send_to_vts(text):
    # 여기에 VTube Studio API와 상호작용하는 코드를 추가
    # 예시: 텍스트를 캐릭터의 말풍선으로 표시
    await vts.send_text(text)
    print("Sent text to VTube Studio")

# macOS에서 WAV 파일 재생 함수
def play_on_macos(filename):
    system_name = platform.system()
    if system_name == 'Darwin':  # macOS인 경우
        os.system(f'afplay {filename}')
    else:
        print("Unsupported OS for audio playback.")

def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

# Flask 애플리케이션 실행 부분
if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run(port=5000)
