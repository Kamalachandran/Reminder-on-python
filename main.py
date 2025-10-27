import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from tkcalendar import DateEntry
import subprocess
import pandas as pd
import os
import sys

FILE_PATH = "reminders.csv"
SERVICE_FILE = "service.py"

# --- Create CSV if missing ---
if not os.path.exists(FILE_PATH):
    pd.DataFrame(columns=["Message", "Reminder Time", "Status"]).to_csv(FILE_PATH, index=False)

# --- Load reminders ---
reminders_df = pd.read_csv(FILE_PATH)
reminders_df["Reminder Time"] = pd.to_datetime(reminders_df["Reminder Time"], errors="coerce")

root = tk.Tk()
root.title("Simple Reminder App")
root.geometry("500x500")
root.resizable(False, False)
service_process = None

select_all_var = tk.BooleanVar()
selected_items = {}

def style_button(btn, bg=None, fg="white"):
    btn.configure(font=("Arial", 12, "bold"))
    if bg:
        btn.configure(bg=bg)
    if fg:
        btn.configure(fg=fg)

def save_reminders():
    global reminders_df
    reminders_df.to_csv(FILE_PATH, index=False)

def update_treeview():
    for i in tree.get_children():
        tree.delete(i)
    selected_items.clear()

    reminders_df["Reminder Time"] = pd.to_datetime(reminders_df["Reminder Time"], errors="coerce")

    for idx, row in reminders_df.iterrows():
        var = tk.BooleanVar(value=False)
        selected_items[idx] = var
        time_val = row["Reminder Time"]
        formatted_time = time_val.strftime("%d-%m-%Y %I:%M %p") if pd.notnull(time_val) else ""
        tree.insert("", "end", iid=idx, values=["☐", row["Message"], formatted_time, row["Status"]])
    update_select_all_button_color()

def toggle_checkbox(event):
    selected_item = tree.identify_row(event.y)
    column = tree.identify_column(event.x)
    if not selected_item or column != "#1":
        return
    idx = int(selected_item)
    var = selected_items[idx]
    var.set(not var.get())
    tree.set(selected_item, column="#1", value="☑" if var.get() else "☐")
    update_select_all_button_color()

def open_add_reminder_window():
    add_window = tk.Toplevel(root)
    add_window.title("Add New Reminder")
    add_window.grab_set()
    add_window.resizable(False, False)
    
    date_frame = ttk.Frame(add_window)
    date_frame.pack(pady=10, padx=10)
    ttk.Label(date_frame, text="Date:", font=("Arial", 12, "bold")).pack(side="left", padx=5)
    date_var = tk.StringVar(value=datetime.now().strftime('%d-%m-%Y'))
    date_entry = DateEntry(date_frame, textvariable=date_var, font=("Arial", 12), width=12)
    date_entry.pack(side="left", padx=5)


    time_frame = ttk.Frame(add_window)
    time_frame.pack(pady=10, padx=10)
    hour_var = tk.StringVar(value=datetime.now().strftime('%I'))
    minute_var = tk.StringVar(value=datetime.now().strftime('%M'))
    ampm_var = tk.StringVar(value=datetime.now().strftime('%p'))

    hour_spin = tk.Spinbox(time_frame, from_=1, to=12, wrap=True, width=3, textvariable=hour_var,
                           font=("Arial", 12, "bold"), justify='center')
    hour_spin.grid(row=0, column=0)
    ttk.Label(time_frame, text=":", font=("Arial", 12, "bold")).grid(row=0, column=1)
    minute_spin = tk.Spinbox(time_frame, from_=0, to=59, wrap=True, width=3, textvariable=minute_var,
                             font=("Arial", 12, "bold"), justify='center')
    minute_spin.grid(row=0, column=2)
    ampm_spin = tk.Spinbox(time_frame, values=("AM", "PM"), wrap=True, width=3, textvariable=ampm_var,
                           font=("Arial", 12, "bold"), justify='center')
    ampm_spin.grid(row=0, column=3, padx=(10, 0))

    message_entry = ttk.Entry(add_window, font=("Arial", 12), width=28)
    message_entry.insert(0, "Good Morning")
    message_entry.pack(pady=10, padx=10)

    def add_reminder():
        try:
            date_obj = date_entry.get_date()
            hour = int(hour_var.get())
            minute = int(minute_var.get())
            ampm = ampm_var.get().upper()
            msg = message_entry.get().strip()
            if not msg:
                messagebox.showerror("Error", "Reminder message cannot be empty")
                return
            if ampm == "PM" and hour != 12:
                hour += 12
            elif ampm == "AM" and hour == 12:
                hour = 0
            reminder_time = datetime(year=date_obj.year, month=date_obj.month, day=date_obj.day,
                                     hour=hour, minute=minute)
            if reminder_time < datetime.now():
                reminder_time += timedelta(days=1)

            global reminders_df
            new_row = pd.DataFrame([{
                "Message": msg,
                "Reminder Time": reminder_time,
                "Status": "Pending"
            }])
            reminders_df = pd.concat([reminders_df, new_row], ignore_index=True)
            save_reminders()
            update_treeview()
            add_window.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    add_btn = tk.Button(add_window, text="Add Reminder", command=add_reminder)
    add_btn.pack(pady=10)
    style_button(add_btn, bg="#28a745")

def delete_selected_reminders():
    global reminders_df
    checked = [idx for idx, var in selected_items.items() if var.get()]
    if not checked:
        messagebox.showinfo("No selection", "Please select reminders to delete.")
        return
    confirm = messagebox.askyesno("Delete", f"Delete {len(checked)} selected reminders?")
    if confirm:
        reminders_df = reminders_df.drop(checked).reset_index(drop=True)
        save_reminders()
        update_treeview()

def toggle_select_all():
    new_state = select_all_var.get()
    for idx, var in selected_items.items():
        var.set(new_state)
        tree.set(idx, column="#1", value="☑" if new_state else "☐")
    update_select_all_button_color()

def update_select_all_button_color():
    if all(var.get() for var in selected_items.values()) and selected_items:
        select_all_btn.config(bg="green", fg="white")
        select_all_var.set(True)
    elif any(var.get() for var in selected_items.values()):
        select_all_btn.config(bg="orange", fg="white")
        select_all_var.set(False)
    else:
        select_all_btn.config(bg="red", fg="white")
        select_all_var.set(False)

def start_service():
    global service_process
    if service_process is None:
        service_process = subprocess.Popen([sys.executable, SERVICE_FILE], creationflags=subprocess.CREATE_NO_WINDOW)
        
button_frame = tk.Frame(root)
button_frame.grid(row=1, column=0, columnspan=5, pady=10, sticky='ew')

select_all_btn = tk.Button(button_frame, text="Select All",
                           command=lambda: [select_all_var.set(not select_all_var.get()), toggle_select_all()])
select_all_btn.grid(row=0, column=0, padx=10)
style_button(select_all_btn)

button_frame.grid(row=0, column=3)

add_btn = tk.Button(button_frame, text="Add Reminder", command=open_add_reminder_window,width=20)
add_btn.grid(row=0, column=5,pady=10)
style_button(add_btn, bg="#28a745")

delete_btn = tk.Button(button_frame, text="Delete Reminders", command=delete_selected_reminders,width=20)
delete_btn.grid(row=1, column=5, padx=10)
style_button(delete_btn, bg="#dc3545")


table_frame = tk.Frame(root)
table_frame.grid(row=4, column=0, columnspan=4, padx=10, pady=10, sticky='nsew')
columns = (" ", "Message", "Reminder Time", "Status")
tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor='center', width=150)

tree.column(columns[0], anchor='center', width=10)
tree.pack(fill='both', expand=True)
tree.bind("<Button-1>", toggle_checkbox)

def auto_refresh():
    global reminders_df
    try:
        if os.path.exists(FILE_PATH):
            new_df = pd.read_csv(FILE_PATH)
            new_df["Reminder Time"] = pd.to_datetime(new_df["Reminder Time"], errors="coerce")
            reminders_df = new_df
            update_treeview()
    except Exception as e:
        print("Auto-refresh error:", e)
    root.after(10000, auto_refresh)

update_treeview()
start_service()
auto_refresh()
root.mainloop()
