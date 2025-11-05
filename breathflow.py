# breatheflow_modern_gui_final.py
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import sounddevice as sd
from collections import deque
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# ---------------- CONFIG ----------------
SAMPLE_RATE = 16000
WINDOW_DURATION = 2.0
BPM_SMOOTH = 0.9
QUEUE_MAXLEN = 10

# ---------------- GLOBALS ----------------
running = False
audio_q = deque(maxlen=QUEUE_MAXLEN)
bpm_est = 0

# ---------------- FUNCTIONS ----------------
def compute_bpm(signal):
    try:
        signal = signal[:,0] if signal.ndim>1 else signal
        signal -= np.mean(signal)
        corr = np.correlate(signal, signal, mode="full")
        corr = corr[len(corr)//2:]
        peaks = np.diff(np.sign(np.diff(corr))) < 0
        peak_indices = np.where(peaks)[0]
        if len(peak_indices) > 1:
            period = np.mean(np.diff(peak_indices)) / SAMPLE_RATE
            bpm = 60.0 / period if period > 0 else 0
            return bpm
    except:
        return 0
    return 0

def classify_breath(bpm):
    if bpm==0: return ("⚪ No sound detected", "gray")
    elif bpm<20: return ("🟢 Normal", "green")
    elif bpm<30: return ("🟡 Abnormal", "orange")
    else: return ("🔴 Dangerous", "red")

def audio_callback(indata, frames, time_info, status):
    audio_q.append(indata.copy())

def start_audio():
    global running, stream
    if running: return
    running = True
    stream = sd.InputStream(callback=audio_callback,
                            channels=1,
                            samplerate=SAMPLE_RATE,
                            blocksize=int(SAMPLE_RATE*WINDOW_DURATION))
    stream.start()
    update_gui()

def stop_audio():
    global running, stream
    running = False
    try:
        stream.stop()
    except:
        pass
    test_frame.status_label.config(text="Stopped", fg="white")
    test_frame.bpm_label.config(text="BPM: --", fg="white")

def show_info():
    messagebox.showinfo("ℹ️ How to use BreatheFlow AI",
                        "1. Press ▶️ Start to begin breathing test.\n"
                        "2. Breathe normally into your microphone.\n"
                        "3. Watch your BPM and status update live.\n"
                        "4. Press ⏹ Stop to end the test.")

def update_gui():
    global bpm_est
    if running:
        if audio_q:
            block = audio_q.popleft()
            bpm = compute_bpm(block)
            bpm_est = BPM_SMOOTH*bpm_est + (1-BPM_SMOOTH)*bpm
            status_text, color = classify_breath(bpm_est)

            # Update labels
            test_frame.status_label.config(text=status_text, fg=color)
            test_frame.bpm_label.config(text=f"BPM: {bpm_est:.1f}", fg=color)

            # Update waveform
            signal = block[:,0] if block.ndim>1 else block
            test_frame.line.set_data(range(len(signal)), signal)
            test_frame.ax.set_xlim(0, len(signal))
            test_frame.canvas.draw()
        
        root.after(50, update_gui)

def show_frame(frame):
    frame.tkraise()

# ---------------- GUI ----------------
root = tk.Tk()
root.title("🎤 BreatheFlow AI")
root.geometry("650x450")
root.configure(bg="#0f1115")
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

# ---------------- LANDING FRAME ----------------
landing_frame = tk.Frame(root, bg="#0f1115")
landing_frame.grid(row=0, column=0, sticky="nsew")

heading = tk.Label(landing_frame, text="Welcome to BreatheFlow AI",
                   font=("Arial",28,"bold"), fg="#00bfa5", bg="#0f1115")
heading.pack(pady=30)

description = tk.Label(landing_frame, text="Measure your breathing rate in real-time using your microphone.\n"
                                           "Breathe normally and see your BPM and waveform live.",
                       font=("Arial",14), fg="white", bg="#0f1115", justify="center")
description.pack(pady=20)

start_test_btn = ttk.Button(landing_frame, text="Analyse Your Breath",
                            command=lambda: show_frame(test_frame))
start_test_btn.pack(pady=20)

# ---------------- TEST FRAME ----------------
test_frame = tk.Frame(root, bg="#0f1115")
test_frame.grid(row=0, column=0, sticky="nsew")

# Status Label
test_frame.status_label = tk.Label(test_frame, text="Press ▶️ Start", font=("Arial",16), bg="#0f1115", fg="white")
test_frame.status_label.pack(pady=10)

# BPM Label
test_frame.bpm_label = tk.Label(test_frame, text="BPM: --", font=("Arial",14), bg="#0f1115", fg="white")
test_frame.bpm_label.pack(pady=5)

# Waveform Figure
fig, ax = plt.subplots(figsize=(6,2))
line, = ax.plot([], [], color="#00bfa5")
ax.set_ylim([-1,1])
ax.set_xticks([])
ax.set_yticks([])
ax.set_facecolor("#0f1115")
fig.patch.set_facecolor("#0f1115")

canvas = FigureCanvasTkAgg(fig, master=test_frame)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack(pady=10, fill="both", expand=True)

# Save references
test_frame.canvas = canvas
test_frame.ax = ax
test_frame.line = line

# Buttons
button_frame = tk.Frame(test_frame, bg="#0f1115")
button_frame.pack(pady=10)
style = ttk.Style()
style.configure("TButton", font=("Arial",12), padding=6)
start_btn = ttk.Button(button_frame, text="▶️ Start", command=start_audio)
start_btn.grid(row=0, column=0, padx=10)
stop_btn = ttk.Button(button_frame, text="⏹ Stop", command=stop_audio)
stop_btn.grid(row=0, column=1, padx=10)
info_btn = ttk.Button(button_frame, text="ℹ️ Info", command=show_info)
info_btn.grid(row=0, column=2, padx=10)

back_btn = ttk.Button(test_frame, text="⬅️ Back", command=lambda: show_frame(landing_frame))
back_btn.pack(pady=10)

# ---------------- RUN APP ----------------
show_frame(landing_frame)
root.mainloop()
