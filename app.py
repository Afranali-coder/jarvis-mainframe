import os
import re
import time
import json
import asyncio
import threading
import subprocess
import webbrowser
from urllib.request import urlopen

import eel
import psutil
import keyboard
import edge_tts
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
import wavio
import numpy as np

eel.init('web')
class JarvisCore:
    """The central manager coordinating the UI states and system processes."""
    def __init__(self):
        self.ai = AIEngine()
        self.system = SystemController()

    async def _run_speech_engine(self, text):
        """Streams text payload directly into local speakers with zero disk delay."""
        try:
            clean_text = re.sub(r'[\*\-\_\[\]\(\)\#\+\`]', '', text)
            communicator = edge_tts.Communicate(clean_text, "en-IN-NeerjaNeural")
            
            audio_bytes = b""
            async for chunk in communicator.stream():
                if chunk["type"] == "audio":
                    audio_bytes += chunk["data"]
            
            if audio_bytes:
                import io
                audio_stream = io.BytesIO(audio_bytes)
                data, sample_rate = sf.read(audio_stream)
                sd.play(data, sample_rate)
                sd.wait()
        except Exception as e:
            print(f"Speech audio stream exception: {e}")
    def speak(self, text):
        """Dispatches text speech generation safely using clean asyncio execution."""
        try:
            eel.set_status_display("JARVIS: SPEAKING...")()
        except Exception:
            pass
            
        try:
            asyncio.run(self._run_speech_engine(text))
        except Exception as e:
            print(f"Async loop recovery triggered: {e}")
        
        try:
            eel.set_status_display("SYSTEM: READY")()
        except Exception:
            pass
import ollama

class AIEngine:
    """Manages local LLM inference, conversation history, and persona behaviors."""
    def __init__(self, model_name='llama3.2:1b'):
        self.model_name = model_name
        self.persona = "jarvis"
        self.custom_instructions = ""
        self.history = []

    def set_persona(self, mode, custom_text=""):
        self.persona = mode
        self.custom_instructions = custom_text
        self.history = []
    def get_system_prompt(self, language="hinglish"):
        """Generates dynamic instructions depending on current language layout."""
        if language == "english":
            rules = " CRITICAL RULE: The user is a 15-year old student. Reply strictly in clean, professional English language. Do not use Hindi words. Keep it very short and high-yield."
        else:
            rules = " CRITICAL RULE: The user is a 15-year old student. Reply strictly in short Hinglish (Hindi language using English script characters). Keep it ultra-short and clear."

        if self.persona == "jee_mentor":
            return f"You are an elite IIT-JEE Mentor and Academic Expert AI Core. Provide accurate formula insights, concept definitions, or strategy tips. Prioritize absolute speed and structural breakdowns.{rules}"
        elif self.persona == "pa":
            return f"You are a helpful and efficient Personal Assistant. Keep responses quick and direct.{rules}"
        elif self.persona == "coder":
            return f"You are an elite Software Engineer. Provide well-structured code snippets.{rules}"
        elif self.persona == "custom" and self.custom_instructions:
            return f"{self.custom_instructions}.{rules}"
            
        return f"You are JARVIS, an ultra-intelligent desktop companion. Address the user as SIR.{rules}"
    def fetch_weather(self, city):
        """API Power-up: Hits a live internet data stream for instant weather updates."""
        try:
            url = f"https://wttr.in{city}?format=j1"
            response = urlopen(url, timeout=4)
            data = json.loads(response.read().decode())
            current = data['current_condition'][0]
            temp = current['temp_C']
            desc = current['weatherDesc'][0]['value']
            return f"Sir, current temperature in {city} is {temp}°C with {desc}."
        except Exception:
            return f"Sir, I could not pull the weather metrics for {city} right now."

    def fetch_web_fact(self, query):
        """API Power-up: Fetches keyless instant answers directly from web grids."""
        try:
            clean_q = query.lower().replace("what is", "").replace("define", "").replace("?", "").strip()
            url = f"https://duckduckgo.com{clean_q}&format=json&no_html=1&skip_disambig=1"
            response = urlopen(url, timeout=4)
            data = json.loads(response.read().decode())
            if data.get("AbstractText"):
                return f"Sir, according to web records: {data['AbstractText']}"
            elif data.get("Definition"):
                return f"Sir, official definition states: {data['Definition']}"
            return None
        except Exception:
            return None

    def process_chat(self, user_query):
        """Routes human query to API lookup grids or pushes it to the local LLM loop."""
        clean_query = user_query.lower().strip()
        
        if "weather in" in clean_query:
            extracted = clean_query.split("weather in")
            if len(extracted) > 1:
                target_city = extracted[1].strip().replace("?", "")
                reply = self.fetch_weather(target_city)
                self.send_response(reply)
                return

        if clean_query.startswith("what is") or clean_query.startswith("define"):
            web_reply = self.fetch_web_fact(user_query)
            if web_reply:
                self.send_response(web_reply)
                return

        try:
            hinglish_markers = ['kaise', 'karo', 'kya', 'batao', 'hai', 'hoon', 'kaha', 'ho', 'theek', 'mera', 'apna', 'chalao', 'band', 'mujhe', 'sare', 'code']
            lang = "english"
            if any(word in hinglish_markers for word in clean_query.split()):
                lang = "hinglish"

            system_instruction = self.get_system_prompt(lang)
            self.history = self.history[-3:]
            messages = [{"role": "system", "content": system_instruction}] + self.history + [{"role": "user", "content": user_query}]
            
            output = ollama.chat(model=self.model_name, messages=messages)
            bot_reply = output.get('message', {}).get('content', 'Mainframe execution loop empty, Sir.')
            
            self.history.append({"role": "user", "content": user_query})
            self.history.append({"role": "assistant", "content": bot_reply})
            self.send_response(bot_reply)
        except Exception:
            self.send_response("Apologies Sir, I encountered a local model inference exception.")

    def send_response(self, text):
        try: eel.add_ai_message_to_chat(text)()
        except Exception: pass
        threading.Thread(target=jarvis.speak, args=(text,), daemon=True).start()
class SystemController:
    """Manages physical hardware functions, shortcuts, and display adjustments."""
    @staticmethod
    def get_battery_status():
        try:
            battery = psutil.sensors_battery()
            if not battery:
                return "Sir, I cannot read battery sensors on this system."
            status = "charging" if battery.power_plugged else "unplugged"
            return f"Sir, battery level is at {battery.percent}%. The system power grid is currently {status}."
        except Exception:
            return "Unable to access hardware telemetry metrics, Sir."

    @staticmethod
    def run_desktop_macros(command):
        if "volume up" in command or "awaaz badhao" in command:
            for _ in range(5): keyboard.send("volume up")
            return "System sound metrics amplified."
        elif "volume down" in command or "awaaz kam karo" in command:
            for _ in range(5): keyboard.send("volume down")
            return "System sound levels lowered."
        elif "open notepad" in command:
            subprocess.Popen(["notepad.exe"])
            return "Notepad instance activated."
        elif "close chrome" in command:
            os.system("taskkill /f /im chrome.exe >nul 2>&1")
            return "Google Chrome background threads killed."
        return None

jarvis = JarvisCore()

@eel.expose
def change_ai_persona_type(mode, override_prompt=""):
    jarvis.ai.set_persona(mode, override_prompt)

@eel.expose
def get_system_telemetry():
    try:
        return {"cpu": int(psutil.cpu_percent(interval=None)), "ram": int(psutil.virtual_memory().percent), "status": "STABLE" if psutil.cpu_percent(interval=None) < 80 else "OVERLOAD"}
    except Exception: return {"cpu": 0, "ram": 0, "status": "ERROR"}

@eel.expose
def fetch_embedded_notes(subject):
    """Zero-latency database parser mapping core JEE equations."""
    notes_db = {
        "physics": """
            <div class='note-item'><b>Electrostatics:</b> F = k·q₁q₂/r² [k ≈ 9×10⁹ N·m²/C²]<br>E = -dV/dx. Gauss Law: ∮E·dA = q_in/ε₀</div>
            <div class='note-item'><b>Current Electricity:</b> V = IR, I = nAev_d, v_d = eEτ/m.<br>Cells in parallel: E_eq = (ΣE_i/r_i)/(Σ1/r_i)</div>
            <div class='note-item'><b>Kinematics Core:</b> R = u²sin(2θ)/g, H_max = u²sin²θ/2g.<br>Trajectory: y = x·tanθ - gx²/(2u²cos²θ)</div>
        """,
        "chemistry": """
            <div class='note-item'><b>Mole Concept:</b> Molarity = Moles / Volume(L). Molality = Moles / Mass of Solvent(kg).<br>1 Mole = 6.022×10²³</div>
            <div class='note-item'><b>Chemical Kinetics:</b> 1st Order Equation: k = (2.303/t)·log(A₀/A_t).<br>Half life t_1/2 = 0.693/k (Independent of A₀)</div>
            <div class='note-item'><b>Thermodynamics:</b> ΔG = ΔH - TΔS. Spontaneous reaction if ΔG < 0. Enthalpy: ΔH = ΔU + Δn_gRT</div>
        """,
        "maths": """
            <div class='note-item'><b>Quadratic Equations:</b> Roots x = [-b ± √(b² - 4ac)] / 2a.<br>Sum = -b/a, Product = c/a. D < 0 means imaginary roots.</div>
            <div class='note-item'><b>Matrices & Adjoint:</b> A·adj(A) = |A|·I. Inverse A⁻¹ = adj(A)/|A|.<br>Properties: |adj(A)| = |A|^(n-1)</div>
            <div class='note-item'><b>Coordinate Geometry:</b> Circle: x² + y² + 2gx + 2fy + c = 0.<br>Center = (-g, -f), Radius = √(g² + f² - c)</div>
        """
    }
    return notes_db.get(subject, "No entry found.")

@eel.expose
def capture_voice_input():
    recognizer_node = sr.Recognizer()
    temp_audio_file = "temp_voice_clip.wav"
    sample_rate = 16000
    duration_seconds = 5
    try:
        eel.set_status_display("JARVIS: LISTENING...")()
        audio_data = sd.rec(int(duration_seconds * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
        sd.wait()
        wavio.write(temp_audio_file, audio_data, sample_rate, sampwidth=2)
        with sr.AudioFile(temp_audio_file) as source_file:
            audio_stream = recognizer_node.record(source_file)
        if os.path.exists(temp_audio_file): os.remove(temp_audio_file)
        eel.set_status_display("SYSTEM: COMPUTING...")()
        return recognizer_node.recognize_google(audio_stream)
    except Exception as err:
        if os.path.exists(temp_audio_file): os.remove(temp_audio_file)
        print(f"[RECOVERY]: Voice processing bypassed: {err}")
        eel.set_status_display("SYSTEM: READY")()
        return ""

@eel.expose
def process_user_input(text):
    clean_text = text.lower().strip()
    shortcut_response = jarvis.system.run_desktop_macros(clean_text)
    if shortcut_response:
        jarvis.ai.send_response(shortcut_response)
        return
    if "battery status" in clean_text or "check power" in clean_text:
        jarvis.ai.send_response(jarvis.system.get_battery_status())
        return
    elif "open browser" in clean_text:
        webbrowser.open("https://google.com")
        return
    threading.Thread(target=jarvis.ai.process_chat, args=(text,), daemon=True).start()

if __name__ == '__main__':
    eel.start('index.html', mode='chrome', size=(460, 900), position=(1450, 15))
