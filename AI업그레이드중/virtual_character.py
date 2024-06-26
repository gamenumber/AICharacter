import pyaudio
import wave
import requests
import re
import json
import time
import random
import speech_recognition as sr
from gtts import gTTS
from playsound import playsound
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from flask import Flask, request, jsonify

# Initialize GPT model and tokenizer
model_name = 'gpt2'
model = GPT2LMHeadModel.from_pretrained(model_name)
tokenizer = GPT2Tokenizer.from_pretrained(model_name)

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

# Function to convert text to speech using gTTS and play the result
def make_tts(content):
    tts = gTTS(text=content, lang='en')
    tts.save('response.mp3')
    playsound('response.mp3')

# Function to transcribe audio directly using SpeechRecognition
def transcribe_directly():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Press Enter to start recording...")
        input()
        print("Recording...")
        audio = recognizer.listen(source)
        print("Press Enter to stop recording...")
        input()
    
    try:
        print("Transcribing...")
        text = recognizer.recognize_google(audio, language='ko-KR')
        return text
    except sr.UnknownValueError:
        return "Sorry, I could not understand the audio."
    except sr.RequestError as e:
        return f"Could not request results; {e}"

# Function to generate response using GPT model
def generate_gpt_response(text):
    input_ids = tokenizer.encode(text, return_tensors='pt')
    output_ids = model.generate(input_ids, max_length=50, num_return_sequences=1)
    response_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    return response_text

# Flask app initialization
app = Flask(__name__)

@app.route('/chat', methods=['POST'])
def chat():
    input_text = request.json.get('text')
    
    # Convert speech to text
    transcription = transcribe_directly()
    print("Transcription: ", transcription)
    
    # Generate response using GPT model
    response = generate_gpt_response(transcription)
    print("Response from GPT model: ", response)
    
    # Convert response text to speech and play
    make_tts(response)
    
    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(port=5000)
