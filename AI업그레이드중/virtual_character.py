import os
import platform
import pyaudio
import wave
import speech_recognition as sr
from gtts import gTTS
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from flask import Flask, request, jsonify, render_template, send_file
import webbrowser  # 웹 브라우저 모듈 추가
from threading import Timer  # 타이머 모듈 추가

# Initialize GPT model and tokenizer
model_name = 'gpt2-large'  # gpt2-large 모델 선택
model = GPT2LMHeadModel.from_pretrained(model_name)
tokenizer = GPT2Tokenizer.from_pretrained(model_name)

# Flask app initialization
app = Flask(__name__)

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
    tts = gTTS(text=content, lang='ko')
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

    # Return success message or any other response
    return jsonify({'message': 'Response played.'}), 200

# macOS에서 WAV 파일 재생 함수
def play_on_macos(filename):
    system_name = platform.system()
    if system_name == 'Darwin':  # macOS인 경우
        os.system(f'afplay {filename}')
    else:
        print("Unsupported OS for audio playback.")

# 함수로 웹 브라우저 자동 실행
def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

# Flask 애플리케이션 실행 부분
if __name__ == '__main__':
    # 타이머를 사용하여 웹 브라우저를 자동으로 엽니다.
    Timer(1, open_browser).start()
    app.run(port=5000)
