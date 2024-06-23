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

# Simple rule-based system to generate a response based on keywords
def generate_response(text):
    text = text.lower()
    if 'hello' in text or 'hi' in text:
        return random.choice(['닥쳐','어쩌라고','씨발','미친놈아','닥쳐','Fuck!', 'Fucking!', 'Hello!', 'Hi there!', 'Greetings!'])
    elif 'how are you' in text:
        return random.choice(['I am fine, thank you!', 'Doing great, how about you?', 'I am good, thanks for asking!'])
    elif 'what is your name' in text:
        return 'I am your friendly assistant.'
    else:
        return "I'm sorry, I don't understand that."

# Main loop
while True:
    transcription = transcribe_directly()
    print("Transcription: ", transcription)

    response = generate_response(transcription)
    print("Response: ", response)
    make_tts(response)
