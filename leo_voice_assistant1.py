import pyaudio
import tkinter as tk
from tkinter import scrolledtext
from PIL import Image, ImageTk, ImageSequence
import os
import re
import datetime
import threading
import subprocess
import requests
import speech_recognition as sr
import pyttsx3
from fuzzywuzzy import process
import noisereduce as nr
from scipy.io import wavfile

# === TTS Setup ===
engine = pyttsx3.init()
engine.setProperty("rate", 150)

def speak(text):
    engine.say(text)
    engine.runAndWait()

# === Reminders ===
reminders = []

def set_reminder(text, time_str):
    reminders.append((text, time_str))
    return f"Reminder set: '{text}' at {time_str}"

def check_reminders():
    now = datetime.datetime.now().strftime("%H:%M")
    for reminder in reminders[:]:
        if reminder[1] == now:
            speak(f"Reminder: {reminder[0]}")
            reminders.remove(reminder)
    app.after(60000, check_reminders)

# === Joke API ===
def get_joke():
    try:
        response = requests.get("https://official-joke-api.appspot.com/random_joke")
        data = response.json()
        return f"{data['setup']} ... {data['punchline']}"
    except:
        return "Couldn't fetch a joke."

# === News API ===
def get_news():
    api_key = "your-newsapi-key"
    url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={api_key}"
    try:
        response = requests.get(url)
        articles = response.json().get("articles", [])
        headlines = [article["title"] for article in articles[:5]]
        return "Top headlines:\n" + "\n".join(headlines)
    except:
        return "Unable to fetch news at the moment."

# === Weather API ===
def get_weather(city="Hyderabad"):
    api_key = "4c7a6f571d88ce31b8dbb3dc310334fc"
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        response = requests.get(url)
        data = response.json()
        if response.status_code == 200:
            weather = data["weather"][0]["description"]
            temp = data["main"]["temp"]
            return f"Weather in {city}: {weather}, Temperature: {temp}°C"
        else:
            return f"Error: {data.get('message', 'Could not fetch weather data')}"
    except Exception as e:
        return f"Network error: {str(e)}"

# === Time ===
def get_time():
    now = datetime.datetime.now().strftime("%I:%M %p")
    return f"The current time is {now}"

# === Open Apps / Chrome Search ===
def open_application(command):
    chrome_path = r"C:\\Users\\vinay\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe"

    apps = {
        "notepad": "notepad.exe",
        "spotify": "spotify.exe",
        "calculator": "calc.exe",
        "chrome": chrome_path,
        "netflix": [r"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge_proxy.exe",
                    "--profile-directory=Default",
                    "--app-id=edhbnieanoeijlkpgkminebadpibapgm",
                    "--app-url=https://www.netflix.com/pwa",
                    "--app-launch-source=4"],
        "vscode": r"C:\\Users\\vinay\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe",
        "whatsapp": r"C:\\Users\\vinay\\AppData\\Local\\Packages\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm\\LocalCache\\Roaming\\WhatsApp\\WhatsApp.exe",
        "chatgpt": r"C:\\Users\\vinay\\AppData\\Local\\Programs\\chatgpt\\ChatGPT.exe",
        "file explorer": "explorer.exe",
    }

    if "search" in command and "chrome" in command:
        match = re.search(r"search (.+)", command)
        if match:
            query = match.group(1)
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            try:
                subprocess.Popen([chrome_path, "--new-tab", search_url], shell=True)
                return f"Searching for '{query}' on Google Chrome..."
            except Exception as e:
                return f"Failed to search on Chrome. Error: {str(e)}"

    match, score = process.extractOne(command, [f"open {app}" for app in apps])
    if score > 70:
        app_name = match.replace("open ", "")
        try:
            subprocess.Popen(apps[app_name], shell=True)
            return f"Opening {app_name}..."
        except Exception as e:
            return f"Failed to open {app_name}. Error: {str(e)}"

    return "I couldn't understand the application command."

# === Noise Reduction (Optional) ===
def reduce_noise(audio_file):
    try:
        rate, data = wavfile.read(audio_file)
        reduced_noise = nr.reduce_noise(y=data, sr=rate, prop_decrease=0.9)
        return reduced_noise
    except Exception as e:
        print(f"Noise reduction error: {e}")
        return None

# === Fuzzy Match Commands ===
def parse_command(command):
    predefined_commands = [
        "what time is it",
        "what is the weather",
        "open chrome",
        "search on chrome",
        "open notepad",
        "tell me a joke",
        "latest news"
    ]
    match = process.extractOne(command, predefined_commands)
    if match:
        best_match, score = match
        return best_match if score > 70 else None
    return None

# === Execute Commands ===
def execute_command(command):
    print(f"Recognized Command: {command}")
    command = command.lower()

    if "time" in command:
        response = get_time()
    elif "weather" in command:
        response = get_weather()
    elif "search" in command or "open" in command:
        response = open_application(command)
    elif "news" in command:
        response = get_news()
    elif "joke" in command:
        response = get_joke()
    else:
        response = "Sorry, I didn't understand that."

    print(f"Response: {response}")
    speak(response)
    return response

# === Wake Word Listener ===
def listen_for_command():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            print("Listening for wake word...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=6)
            text = recognizer.recognize_google(audio).lower()
            print(f"Heard: {text}")

            if "leo" in text:
                speak("Yes?")
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=5)
                command = recognizer.recognize_google(audio)
                print(f"Command: {command}")
                return command
            else:
                print("Wake word not detected.")
        except sr.UnknownValueError:
            print("Could not understand audio.")
        except sr.WaitTimeoutError:
            print("Listening timed out.")
        except Exception as e:
            print(f"Error: {e}")
    return None

# === GUI Setup ===
app = tk.Tk()
app.title("Leo Voice Assistant")
app.geometry("600x500")
app.resizable(False, False)

chat_box = scrolledtext.ScrolledText(app, wrap=tk.WORD, width=60, height=20, font=("Arial", 12))
chat_box.pack(padx=10, pady=10)

status_label = tk.Label(app, text="Leo is ready to help you.", font=("Arial", 12))
status_label.pack()

# === Theme Toggle ===
dark_mode = False

def toggle_theme():
    global dark_mode
    dark_mode = not dark_mode
    if dark_mode:
        app.configure(bg="#1e1e1e")
        chat_box.configure(bg="#2e2e2e", fg="white")
        status_label.configure(bg="#1e1e1e", fg="white")
        speak_button.configure(bg="#444", fg="white")
        theme_btn.configure(text="🌞 Light Mode")
    else:
        app.configure(bg="white")
        chat_box.configure(bg="white", fg="black")
        status_label.configure(bg="white", fg="black")
        speak_button.configure(bg="#007BFF", fg="white")
        theme_btn.configure(text="🌙 Dark Mode")

def on_speak_button_click():
    status_label.config(text="Listening...")
    app.after(1000, lambda: status_label.config(text="Leo is ready to help you."))

# === Listen Command ===
def start_listening():
    status_label.config(text="Listening...")
    command = listen_for_command()
    if command:
        chat_box.insert(tk.END, f"You: {command}\n")
        response = execute_command(command)
        chat_box.insert(tk.END, f"Leo: {response}\n\n")
    else:
        chat_box.insert(tk.END, "Leo: No valid command detected.\n")
    status_label.config(text="Leo is ready to help you.")

def threaded_listen():
    threading.Thread(target=start_listening).start()

# === Buttons ===
speak_button = tk.Button(app, text="🎤 Speak", command=on_speak_button_click, bg="#007BFF", fg="white", font=("Helvetica", 12))
speak_button.pack(pady=10)

listen_button = tk.Button(app, text="Start Listening", command=threaded_listen, font=("Arial", 12))
listen_button.pack(pady=10)

theme_btn = tk.Button(app, text="🌙 Dark Mode", command=toggle_theme, font=("Arial", 12))
theme_btn.pack(pady=5)

# === Start ===
check_reminders()
app.mainloop()
