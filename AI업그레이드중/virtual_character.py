from flask import Flask, request, jsonify, render_template
import os
import platform
import pyaudio
import wave
from gtts import gTTS
from transformers import GPT2LMHeadModel, GPT2Tokenizer
import webbrowser
from threading import Timer
import pyvts
import asyncio
import threading

# Flask app initialization
app = Flask(__name__)

# VTube Studio API 연결 설정
vts = pyvts.vts()

# 비동기 VTube Studio 연결 함수
async def connect_vts():
    while True:
        try:
            await vts.connect()
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

            response = await vts.request(auth_data)
            
            if 'data' in response and 'authenticationToken' in response['data']:
                api_key = response['data']['authenticationToken']
                print(f"Authenticated with API key: {api_key}")
            else:
                print("Failed to authenticate")
            
            print("Authenticated and connected to VTube Studio")
            break  # 연결 성공 시 루프 종료
        except Exception as e:
            print(f"Connection failed: {e}")
            await asyncio.sleep(5)  # 5초 후에 다시 시도

# 별도의 스레드에서 asyncio 이벤트 루프 실행
def start_async_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(connect_vts())

new_loop = asyncio.new_event_loop()
threading.Thread(target=start_async_loop, args=(new_loop,)).start()

def get_model_and_tokenizer():
    global model, tokenizer
    if model is None or tokenizer is None:
        model = GPT2LMHeadModel.from_pretrained(model_name)
        tokenizer = GPT2Tokenizer.from_pretrained(model_name)
    return model, tokenizer

def generate_gpt_response(text):
    model, tokenizer = get_model_and_tokenizer()
    input_ids = tokenizer.encode(text, return_tensors='pt')
    attention_mask = [1] * len(input_ids[0])  # attention_mask 설정
    output_ids = model.generate(input_ids, max_length=50, num_return_sequences=1, pad_token_id=tokenizer.eos_token_id, attention_mask=attention_mask)
    response_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    return response_text

def make_tts(content):
    tts = gTTS(text=content, lang='ko')  # 한국어 설정
    tts.save('response.wav')

async def play_wav_file(file_path):
    try:
        wf = await asyncio.to_thread(wave.open, file_path, 'rb')
        p = pyaudio.PyAudio()

        stream = await asyncio.to_thread(p.open, format=p.get_format_from_width(wf.getsampwidth()),
                                        channels=wf.getnchannels(),
                                        rate=wf.getframerate(),
                                        output=True)
        data = await asyncio.to_thread(wf.readframes, 1024)
        while data:
            await asyncio.to_thread(stream.write, data)
            data = await asyncio.to_thread(wf.readframes, 1024)

        await asyncio.to_thread(stream.stop_stream)
        await asyncio.to_thread(stream.close)
        await asyncio.to_thread(p.terminate)
    except wave.Error as e:
        print(f"Error playing WAV file: {e}")

async def send_to_vts(text):
    message_payload = {
        "apiName": "VTubeStudioPublicAPI",
        "apiVersion": "1.0",
        "requestID": "SendMessageRequest",
        "messageType": "SendMessage",
        "data": {
            "message": text
        }
    }
    response = await vts.request(message_payload)
    print("Sent text to VTube Studio:", response)

async def chat_handler(input_text):
    response = generate_gpt_response(input_text)
    print("Response from GPT model: ", response)
    make_tts(response)
    await play_wav_file('response.wav')
    await send_to_vts(response)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    input_text = request.json.get('text')
    if not input_text:
        return jsonify({'error': "No 'text' field found in JSON request."}), 400

    print("User input: ", input_text)

    # 새로운 스레드에서 비동기 작업 실행
    asyncio.run_coroutine_threadsafe(chat_handler(input_text), new_loop)

    return jsonify({'response': 'Processing...'}), 200

def play_on_macos(filename):
    system_name = platform.system()
    if system_name == 'Darwin':
        os.system(f'afplay {filename}')
    else:
        print("Unsupported OS for audio playback.")

def open_browser():
    webbrowser.open('http://127.0.0.1:5000/')

if __name__ == '__main__':
    model_name = 'gpt2-xl'
    model = None
    tokenizer = None

    Timer(1, open_browser).start()
    app.run(port=5000)
