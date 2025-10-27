import time
import pandas as pd
from datetime import datetime
from plyer import notification
import signal
import sys
import os

FILE_PATH = "reminders.csv"
running = True

def signal_handler(sig, frame):
    global running
    running = False

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def show_reminder(message):
    """Show desktop notification only (no voice)."""
    try:
        notification.notify(
            title="Reminder",
            message=message,
            timeout=10
        )
    except Exception as e:
        print("Notification error:", e)

def check_reminders():
    global running
    if not os.path.exists(FILE_PATH):
        return
    try:
        df = pd.read_csv(FILE_PATH)
        df["Reminder Time"] = pd.to_datetime(df["Reminder Time"], errors="coerce")
        updated = False
        now = datetime.now()
        for idx, row in df.iterrows():
            if row["Status"] == "Pending" and pd.notnull(row["Reminder Time"]) and now >= row["Reminder Time"]:
                show_reminder(row["Message"])
                df.at[idx, "Status"] = "Completed"
                updated = True
        if updated:
            df.to_csv(FILE_PATH, index=False)
    except Exception as e:
        print("Error checking reminders:", e)

while running:
    check_reminders()
    time.sleep(30)

sys.exit(0)
