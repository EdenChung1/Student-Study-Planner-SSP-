import customtkinter as ctk
import json
import hashlib
import threading
import os
import calendar
import requests
from datetime import datetime, timedelta
from tkinter import messagebox

DATA_FILE = "users.json"
USERDATA_DIR = "user_data"
API_KEY = "holiday-API-key"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "users.json")
USERDATA_PATH = os.path.join(BASE_DIR, USERDATA_DIR)
OPENAI_API_KEY = 'openAI-API-key'
API_URL = 'https://api.openai.com/v1/chat/completions'

def ensure_userdata_dir():
    """Ensure the user_data directory exists."""
    if not os.path.exists(USERDATA_PATH):
        os.makedirs(USERDATA_PATH)

def user_data_path(username):
    """Get the per-user task file path."""
    if username.lower() == "guest":
        return os.path.join(USERDATA_PATH, "guest.json")
    username_hash = hashlib.sha256(username.encode()).hexdigest()
    return os.path.join(USERDATA_PATH, f"{username_hash}.json")

def load_user_tasks(username):
    """Load tasks for a user from their file."""
    if username.lower() == "guest":
        return {}
    ensure_userdata_dir()
    path = user_data_path(username)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_user_tasks(username, tasks):
    """Save tasks for a user to their file."""
    if username.lower() == "guest":
        return
    ensure_userdata_dir()
    path = user_data_path(username)
    with open(path, "w") as f:
        json.dump(tasks, f, indent=2)

def load_users():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as file:
        return json.load(file)

def save_users(users):
    with open(DATA_FILE, "w") as file:
        json.dump(users, file, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def is_password_strong(password):
    return (
        len(password) >= 8 and
        any(c.isupper() for c in password) and
        any(c.islower() for c in password) and
        any(c.isdigit() for c in password) and
        any(c in "!@#$%^&*()_+-=[]{}|;':\",.<>?/" for c in password)
    )

class AuthApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Modern Sign Up & Login")
        self.geometry("600x650")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.users = load_users()
        self.is_login = False
        self.show_password_var = ctk.BooleanVar()

        self.create_widgets()

    def create_widgets(self):
        self.container = ctk.CTkFrame(self)
        self.container.pack(expand=True)

        self.title_label = ctk.CTkLabel(self.container, text="Student Study Planner", font=ctk.CTkFont(size=30, weight="bold"))
        self.title_label.pack(pady=20)

        self.subtitle_label = ctk.CTkLabel(self.container, text="Sign Up", font=ctk.CTkFont(size=24, slant="roman", underline=True))
        self.subtitle_label.pack(pady=20)

        self.username_entry = ctk.CTkEntry(self.container, placeholder_text="Username")
        self.username_entry.pack(pady=10)

        self.password_entry = ctk.CTkEntry(self.container, placeholder_text="Password", show="*")
        self.password_entry.pack(pady=10)

        self.show_password_checkbox = ctk.CTkCheckBox(
            self.container,
            text="Show Password",
            variable=self.show_password_var,
            command=self.toggle_password_visibility
        )
        self.show_password_checkbox.pack(pady=5)

        self.error_label = ctk.CTkLabel(self.container, text="", text_color="red", font=ctk.CTkFont(size=14))
        self.error_label.pack(pady=5)

        self.main_button = ctk.CTkButton(self.container, text="Sign Up", command=self.handle_main_action)
        self.main_button.pack(pady=10)

        self.switch_mode_button = ctk.CTkButton(self.container, text="Switch to Login", command=self.switch_mode)
        self.switch_mode_button.pack(pady=5)

        self.guest_button = ctk.CTkButton(self.container, text="Continue as Guest", command=self.continue_as_guest)
        self.guest_button.pack(pady=5)

    def toggle_password_visibility(self):
        if self.show_password_var.get():
            self.password_entry.configure(show="")
        else:
            self.password_entry.configure(show="*")

    def show_error(self, message):
        self.error_label.configure(text=message)
        self.after(3000, lambda: self.error_label.configure(text=""))

    def handle_main_action(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        self.error_label.configure(text="")

        if not username or not password:
            self.show_error("Username and password cannot be empty.")
            return

        if self.is_login:
            if username not in self.users:
                self.show_error("User not found.")
                return
            if self.users[username] != hash_password(password):
                self.show_error("Incorrect username or password.")
                return
            messagebox.showinfo("Success", f"Welcome back, {username}!")
            self.open_main_app(username)
        else:
            if username in self.users:
                self.show_error("Username already exists.")
                return
            if not is_password_strong(password):
                self.show_error("Password must be 8+ chars incl. upper, lower, digit, and symbol.")
                return
            self.users[username] = hash_password(password)
            save_users(self.users)
            messagebox.showinfo("Success", "Account created successfully!")
            self.switch_mode()

    def switch_mode(self):
        self.is_login = not self.is_login
        self.error_label.configure(text="")
        if self.is_login:
            self.subtitle_label.configure(text="Login")
            self.main_button.configure(text="Login")
            self.switch_mode_button.configure(text="Switch to Sign Up")
        else:
            self.subtitle_label.configure(text="Sign Up")
            self.main_button.configure(text="Sign Up")
            self.switch_mode_button.configure(text="Switch to Login")

    def continue_as_guest(self):
        messagebox.showinfo("Guest Mode", "Continuing as guest...")
        self.open_main_app("Guest")

    def open_main_app(self, username):
        self.destroy()
        root = ctk.CTk()
        calendar_app = CustomCalendar(root, username)
        root.mainloop()


class CustomCalendar:
    def __init__(self, root, username):
        self.root = root
        self.root.title(f"{username}'s Study Planner Calendar")
        self.root.geometry("900x800")
        self.username = username

        self.today = datetime.today()
        self.current_year = self.today.year
        self.current_month = self.today.month
        self.current_day = self.today.day
        self.current_week_start = self.today - timedelta(days=self.today.weekday())

        self.tasks = load_user_tasks(self.username)
        self.holidays = {}

        self.public_holidays(self.current_year)
        self.create_widgets()

    def save_tasks(self):
        save_user_tasks(self.username, self.tasks)

    def public_holidays(self, year, country_code="AU"):
        self.holidays = {}
        try:
            url = f"https://calendarific.com/api/v2/holidays?&api_key={API_KEY}&country={country_code}&year={year}"
            response = requests.get(url)
            if response.status_code != 200:
                print("Error fetching holidays: HTTP", response.status_code)
                self.holidays = {}
                return
            data = response.json()
            if "error" in data.get("meta", {}):
                print("Calendarific API error:", data["meta"]["error_detail"])
                self.holidays = {}
                return
            for h in data.get("response", {}).get("holidays", []):
                if h["type"][0] == "National holiday":
                    d = datetime.strptime(h["date"]["iso"], "%Y-%m-%d")
                    self.holidays[(d.year, d.month, d.day)] = h["name"]
        except Exception as e:
            print("Failed to fetch holidays:", e)
            self.holidays = {}

    def create_widgets(self):
        self.outmost = ctk.CTkFrame(self.root)
        self.outmost.pack(expand=True, fill="both")

        self.sidebar = ctk.CTkFrame(self.outmost, width=230, fg_color="#f1f5f9")
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        ctk.CTkLabel(self.sidebar, text="📋 Saved Tasks", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=12)
        self.sidebar_taskbox = ctk.CTkTextbox(self.sidebar, width=210, height=600, state="disabled", wrap="word")
        self.sidebar_taskbox.pack(fill="both", expand=True, padx=8, pady=5)

        self.main_area = ctk.CTkFrame(self.outmost)
        self.main_area.pack(side="left", fill="both", expand=True)

        self.title_label = ctk.CTkLabel(self.main_area, text="📅 Study Planner Calendar 📅", font=ctk.CTkFont(size=28, weight="bold"))
        self.title_label.pack(pady=16)

        self.ai_offline_warning = ctk.CTkLabel(
            self.main_area,
            text="⚠️AI assistant will NOT work offline!⚠️",
            text_color="red",
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="center"
        )
        self.ai_offline_warning.pack(pady=4)

        if self.username.lower() == "guest":
            self.guest_warning = ctk.CTkLabel(
                self.main_area,
                text="⚠️ Guest Mode: Tasks will NOT save!⚠️",
                text_color="red",
                font=ctk.CTkFont(size=16, weight="bold"),
                anchor="center"
            )
            self.guest_warning.pack(pady=6)

        self.ai_btn = ctk.CTkButton(self.main_area, text="💬 AI Assistant", fg_color="#6366f1", text_color="white", command=self.open_ai_chat)
        self.ai_btn.pack(pady=4)

        self.header = ctk.CTkLabel(self.main_area, text="", font=ctk.CTkFont(size=20))
        self.header.pack(pady=8)

        nav_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        nav_frame.pack(pady=8)

        ctk.CTkButton(nav_frame, text="← Prev", command=self.prev_month).pack(side="left", padx=10)
        ctk.CTkButton(nav_frame, text="Next →", command=self.next_month).pack(side="left", padx=10)

        self.view_mode = ctk.StringVar(value="Month")
        self.view_selector = ctk.CTkOptionMenu(
            self.main_area,
            values=["Day", "Week", "Month"],
            variable=self.view_mode,
            command=lambda _: self.redraw_calendar_grid()
        )
        self.view_selector.pack(pady=5)

        self.calendar_frame = ctk.CTkFrame(self.main_area)
        self.calendar_frame.pack(pady=13, expand=True, fill="both")

        self.redraw_calendar_grid()
        self.update_sidebar_tasks()

    def update_sidebar_tasks(self):
        self.sidebar_taskbox.configure(state="normal")
        self.sidebar_taskbox.delete("1.0", "end")

        month_keys = []
        for key in self.tasks:
            parts = key.split('-')
            if len(parts) == 3:
                y, m, d = map(int, parts)
                if y == self.current_year and m == self.current_month:
                    month_keys.append((d, key))
        for d, key in sorted(month_keys):
            tasks = self.tasks[key]
            if tasks:
                self.sidebar_taskbox.insert("end", f"{key}:\n")
                for t in tasks:
                    self.sidebar_taskbox.insert("end", f"  • {t}\n")
        self.sidebar_taskbox.configure(state="disabled")

    def open_ai_chat(self):
        AIChatDialog(self.root)

    def get_day_task_count(self, year, month, day):
        day_tasks = len(self.tasks.get(f"{year}-{month}-{day}", []))
        hourly_tasks = sum(len(self.tasks.get(f"{year}-{month}-{day}-{h}", [])) for h in range(24))
        return day_tasks + hourly_tasks

    def redraw_calendar_grid(self):
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()

        view = self.view_mode.get()

        if view == "Month":
            self.header.configure(text=f"{calendar.month_name[self.current_month]} {self.current_year}")
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            for i, day in enumerate(days):
                lbl = ctk.CTkLabel(self.calendar_frame, text=day, font=ctk.CTkFont(size=15, weight="bold"), width=12)
                lbl.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")

            cal = calendar.Calendar(firstweekday=0)
            month_days = cal.monthdayscalendar(self.current_year, self.current_month)

            for row, week in enumerate(month_days, start=1):
                for col, day in enumerate(week):
                    if day == 0:
                        continue
                    task_count = self.get_day_task_count(self.current_year, self.current_month, day)
                    key = (self.current_year, self.current_month, day)
                    holiday_name = self.holidays.get(key)
                    is_today = (
                        self.current_year == self.today.year
                        and self.current_month == self.today.month
                        and day == self.today.day
                    )
                    btn_text = f"{day}\n🎉" if holiday_name else f"{day}\n{task_count} tasks" if task_count else str(day)

                    if is_today:
                        btn_color = "#00c896"
                    elif holiday_name:
                        btn_color = "#f9c74f"
                    elif task_count:
                        btn_color = "#8bc6ec"
                    else:
                        btn_color = "#f0f4f8"

                    btn = ctk.CTkButton(
                        self.calendar_frame,
                        text=btn_text,
                        width=85,
                        height=64,
                        fg_color=btn_color,
                        hover_color="#60a5fa",
                        text_color="black",
                        font=ctk.CTkFont(size=14),
                        command=lambda d=day: self.on_day_click(d)
                    )
                    btn.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")

        elif view == "Week":
            week_start = self.current_week_start
            self.header.configure(text=f"Week of {week_start.strftime('%d %b %Y')}")
            for i in range(7):
                current_day = week_start + timedelta(days=i)
                task_count = self.get_day_task_count(current_day.year, current_day.month, current_day.day)
                key = (current_day.year, current_day.month, current_day.day)
                holiday_name = self.holidays.get(key)
                is_today = (
                    current_day.year == self.today.year
                    and current_day.month == self.today.month
                    and current_day.day == self.today.day
                )
                label_text = current_day.strftime("%a\n%d %b")
                if holiday_name:
                    label_text += "\n🎉"
                label = ctk.CTkLabel(self.calendar_frame, text=label_text, font=ctk.CTkFont(size=13, weight="bold"))
                label.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")

                text = f"{task_count} tasks" if task_count else "No tasks"

                if is_today:
                    btn_color = "#00c896"
                elif holiday_name:
                    btn_color = "#f9c74f"
                elif task_count:
                    btn_color = "#8bc6ec"
                else:
                    btn_color = "#f0f4f8"

                btn = ctk.CTkButton(
                    self.calendar_frame,
                    text=text,
                    command=lambda d=current_day: self.show_day_tasks_dialog(d.year, d.month, d.day),
                    width=100,
                    fg_color=btn_color,
                )
                btn.grid(row=1, column=i, padx=5, pady=5, sticky="nsew")

        elif view == "Day":
            day_dt = datetime(self.current_year, self.current_month, self.current_day)
            self.header.configure(text=day_dt.strftime("Day View - %A, %d %B %Y"))

            scroll_frame = ctk.CTkScrollableFrame(self.calendar_frame, width=800, height=600)
            scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

            day_key = f"{self.current_year}-{self.current_month}-{self.current_day}"
            day_tasks = self.tasks.get(day_key, [])
            day_task_str = f"{len(day_tasks)} task(s)" if day_tasks else "No tasks"
            ctk.CTkLabel(scroll_frame, text="Day Notes", font=ctk.CTkFont(size=15, weight="bold")).grid(row=0, column=0, sticky="w", padx=5)
            daynote_btn = ctk.CTkButton(scroll_frame, text=day_task_str, width=400,
                                        command=lambda: self.show_day_tasks_dialog(self.current_year, self.current_month, self.current_day))
            daynote_btn.grid(row=0, column=1, padx=5, pady=2, sticky="ew")

            is_today = (
                self.current_year == self.today.year
                and self.current_month == self.today.month
                and self.current_day == self.today.day
            )
            if is_today:
                ctk.CTkLabel(scroll_frame, text="Today", font=ctk.CTkFont(size=13, weight="bold"), text_color="#00c896").grid(row=0, column=2, sticky="w", padx=5)

            for hour in range(0, 24):
                time_str = f"{hour:02d}:00"
                time_label = ctk.CTkLabel(scroll_frame, text=time_str, width=10, anchor="w")
                time_label.grid(row=hour+1, column=0, sticky="w", padx=5, pady=2)

                key = f"{self.current_year}-{self.current_month}-{self.current_day}-{hour}"
                hourly_tasks = self.tasks.get(key, [])
                task_count = len(hourly_tasks)
                summary = f"📝 {task_count} tasks" if task_count else "Add task"

                if task_count:
                    btn_color = "#60a5fa"
                else:
                    btn_color = "#f0f4f8"

                slot_btn = ctk.CTkButton(
                    scroll_frame,
                    text=summary,
                    width=400,
                    height=30,
                    anchor="w",
                    fg_color=btn_color,
                    text_color="black",
                    command=lambda h=hour: self.show_hourly_tasks_dialog(h)
                )
                slot_btn.grid(row=hour+1, column=1, padx=5, pady=2, sticky="ew")

    def prev_month(self):
        view = self.view_mode.get()
        if view == "Month":
            if self.current_month == 1:
                self.current_month = 12
                self.current_year -= 1
            else:
                self.current_month -= 1
            self.public_holidays(self.current_year)
            self.redraw_calendar_grid()
            self.update_sidebar_tasks()
        elif view == "Week":
            self.current_week_start -= timedelta(weeks=1)
            self.current_year = self.current_week_start.year
            self.current_month = self.current_week_start.month
            self.current_day = self.current_week_start.day
            self.public_holidays(self.current_year)
            self.redraw_calendar_grid()
            self.update_sidebar_tasks()
        elif view == "Day":
            new_date = datetime(self.current_year, self.current_month, self.current_day) - timedelta(days=1)
            self.current_year, self.current_month, self.current_day = new_date.year, new_date.month, new_date.day
            self.current_week_start = new_date - timedelta(days=new_date.weekday())
            self.public_holidays(self.current_year)
            self.redraw_calendar_grid()
            self.update_sidebar_tasks()

    def next_month(self):
        view = self.view_mode.get()
        if view == "Month":
            if self.current_month == 12:
                self.current_month = 1
                self.current_year += 1
            else:
                self.current_month += 1
            self.public_holidays(self.current_year)
            self.redraw_calendar_grid()
            self.update_sidebar_tasks()
        elif view == "Week":
            self.current_week_start += timedelta(weeks=1)
            self.current_year = self.current_week_start.year
            self.current_month = self.current_week_start.month
            self.current_day = self.current_week_start.day
            self.public_holidays(self.current_year)
            self.redraw_calendar_grid()
            self.update_sidebar_tasks()
        elif view == "Day":
            new_date = datetime(self.current_year, self.current_month, self.current_day) + timedelta(days=1)
            self.current_year, self.current_month, self.current_day = new_date.year, new_date.month, new_date.day
            self.current_week_start = new_date - timedelta(days=new_date.weekday())
            self.public_holidays(self.current_year)
            self.redraw_calendar_grid()
            self.update_sidebar_tasks()

    def on_day_click(self, day):
        self.show_day_tasks_dialog(self.current_year, self.current_month, day)

    def show_day_tasks_dialog(self, year, month, day):
        key = f"{year}-{month}-{day}"
        tasks = list(self.tasks.get(key, []))
        hourly_tasks = []
        for hour in range(24):
            hour_key = f"{year}-{month}-{day}-{hour}"
            for t in self.tasks.get(hour_key, []):
                hourly_tasks.append((hour, t))
        holiday_name = self.holidays.get((year, month, day))
        dialog = TaskDialog(self.root, f"Tasks for {day} {calendar.month_name[month]} {year}",
                            tasks, hourly_tasks, allow_add=True, holiday_name=holiday_name)
        if dialog.result is not None:
            self.tasks[key] = dialog.result
            for h in range(24):
                hour_key = f"{year}-{month}-{day}-{h}"
                self.tasks.pop(hour_key, None)
            for h, t in getattr(dialog, "result_hourly", []):
                self.tasks.setdefault(f"{year}-{month}-{day}-{h}", []).append(t)
            self.save_tasks()
            self.redraw_calendar_grid()
            self.update_sidebar_tasks()

    def show_hourly_tasks_dialog(self, hour):
        key = f"{self.current_year}-{self.current_month}-{self.current_day}-{hour}"
        tasks = list(self.tasks.get(key, []))
        dialog = TaskDialog(self.root, f"Tasks at {hour:02d}:00 on {self.current_day} {calendar.month_name[self.current_month]}",
                            tasks, [], allow_add=True)
        if dialog.result is not None:
            self.tasks[key] = dialog.result
            self.save_tasks()
            self.redraw_calendar_grid()
            self.update_sidebar_tasks()

class TaskDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, tasks, hourly_tasks, allow_add=True, hourly_only=False, holiday_name=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("480x450")
        self.resizable(False, False)
        self.result = None
        self.result_hourly = None
        self.tasks = list(tasks)
        self.hourly_tasks = list(hourly_tasks)
        self.allow_add = allow_add
        self.hourly_only = hourly_only
        self.holiday_name = holiday_name

        self.build_ui()
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.close_and_return)
        self.wait_window(self)

    def build_ui(self):
        for widget in self.winfo_children():
            widget.destroy()
        ctk.CTkLabel(self, text=self.title(), font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

        if self.holiday_name:
            holiday_frame = ctk.CTkFrame(self, fg_color="#f9c74f")
            holiday_frame.pack(pady=5, padx=10, fill="x")
            ctk.CTkLabel(
                holiday_frame,
                text=f"🎉 Public Holiday: {self.holiday_name} 🎉",
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color="#b45309"
            ).pack(padx=10, pady=4, anchor="w")

        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True, padx=10, pady=5)

        if not self.hourly_only:
            ctk.CTkLabel(self.container, text="All-Day Tasks:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
            self.day_task_frame = ctk.CTkFrame(self.container)
            self.day_task_frame.pack(fill="x", pady=4)
            for idx, task in enumerate(self.tasks):
                frame = ctk.CTkFrame(self.day_task_frame)
                frame.pack(fill="x", pady=2, padx=0)
                ctk.CTkLabel(frame, text=f"{idx+1}. {task}", anchor="w").pack(side="left", padx=5, expand=True, fill="x")
                btn = ctk.CTkButton(frame, text="Remove", width=60, fg_color="#ef4444", text_color="white",
                                    command=lambda i=idx: self.remove_task(i))
                btn.pack(side="right", padx=5)
        if self.hourly_tasks and not self.hourly_only:
            ctk.CTkLabel(self.container, text="Hourly Tasks:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10,2))
            self.hourly_task_frame = ctk.CTkFrame(self.container)
            self.hourly_task_frame.pack(fill="x", pady=2)
            by_hour = {}
            for h, t in self.hourly_tasks:
                by_hour.setdefault(h, []).append(t)
            for h in sorted(by_hour):
                for i, t in enumerate(by_hour[h]):
                    frame = ctk.CTkFrame(self.hourly_task_frame)
                    frame.pack(fill="x", pady=2, padx=0)
                    ctk.CTkLabel(frame, text=f"{h:02d}:00 - {t}", anchor="w").pack(side="left", padx=5, expand=True, fill="x")
                    btn = ctk.CTkButton(frame, text="Remove", width=60, fg_color="#ef4444", text_color="white",
                                        command=lambda h=h, i=i: self.remove_hourly_task(h, i))
                    btn.pack(side="right", padx=5)
        if self.allow_add:
            add_frame = ctk.CTkFrame(self)
            add_frame.pack(fill="x", pady=8)
            self.entry = ctk.CTkEntry(add_frame, placeholder_text="Add new task...")
            self.entry.pack(side="left", fill="x", expand=True, padx=5)
            add_btn = ctk.CTkButton(add_frame, text="Add", fg_color="#22c55e", text_color="white",
                                    command=self.add_task)
            add_btn.pack(side="left", padx=5)
            self.entry.bind('<Return>', lambda e: self.add_task())

        close_btn = ctk.CTkButton(self, text="Close", command=self.close_and_return)
        close_btn.pack(pady=10)

    def add_task(self):
        task = self.entry.get().strip()
        if task:
            if self.hourly_only:
                self.tasks.append(task)
            else:
                self.tasks.append(task)
            self.entry.delete(0, 'end')
            self.build_ui()

    def remove_task(self, idx):
        if 0 <= idx < len(self.tasks):
            del self.tasks[idx]
            self.build_ui()

    def remove_hourly_task(self, hour, task_idx):
        count = 0
        for i, (h, t) in enumerate(self.hourly_tasks):
            if h == hour:
                if count == task_idx:
                    del self.hourly_tasks[i]
                    break
                count += 1
        self.build_ui()

    def close_and_return(self):
        self.result = self.tasks
        self.result_hourly = self.hourly_tasks
        self.destroy()

class AIChatDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("AI Assistant")
        self.geometry("500x500")
        self.resizable(True, True)

        ctk.CTkLabel(self, text="AI Assistant (Type your inquiry below)", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=8)

        self.chat_frame = ctk.CTkFrame(self)
        self.chat_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.textbox = ctk.CTkTextbox(self.chat_frame, width=480, height=350, state="disabled", wrap="word")
        self.textbox.pack(fill="both", expand=True, padx=5, pady=5)

        input_frame = ctk.CTkFrame(self)
        input_frame.pack(fill="x", padx=10, pady=10)

        self.entry = ctk.CTkEntry(input_frame, placeholder_text="Ask me anything about study planning...")
        self.entry.pack(side="left", fill="x", expand=True, padx=5)
        self.entry.bind('<Return>', lambda e: self.send_message())

        send_btn = ctk.CTkButton(input_frame, text="Send", fg_color="#22c55e", text_color="white", command=self.send_message)
        send_btn.pack(side="left", padx=5)

        close_btn = ctk.CTkButton(self, text="Close", command=self.destroy)
        close_btn.pack(pady=5)

        self.after(200, self.greet)

    def greet(self):
        self.append_text("AI: Hi! I'm your AI assistant. How can I help you with your study planning?\n")

    def send_message(self):
        question = self.entry.get().strip()
        if not question:
            return
        self.append_text(f"You: {question}\n")
        self.entry.delete(0, "end")
        self.append_text("AI: ...thinking...\n")
        threading.Thread(target=self.ask_openai, args=(question,), daemon=True).start()

    def ask_openai(self, question):
        try:
            url = API_URL
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "gpt-3.5-turbo", 
                "messages": [
                    {"role": "system", "content": "You are a helpful study planning assistant."},
                    {"role": "user", "content": question}
                ],
                "max_tokens": 500,
                "temperature": 0.7,
            }
            response = requests.post(url, headers=headers, json=data, timeout=20)
            if response.status_code == 200:
                resp = response.json()
                msg = resp["choices"][0]["message"]["content"].strip()
                self.after(0, lambda: self.replace_last_response(f"AI: {msg}\n"))
            else:
                error_msg = f"AI: [API error {response.status_code}] {response.text}\n"
                self.after(0, lambda: self.replace_last_response(error_msg))
        except Exception as e:
            self.after(0, lambda: self.replace_last_response(f"AI: [Error: {str(e)}]\n"))

    def append_text(self, text):
        self.textbox.configure(state="normal")
        self.textbox.insert("end", text)
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def replace_last_response(self, new_text):
        self.textbox.configure(state="normal")
        current_text = self.textbox.get("1.0", "end-1c")
        if current_text.endswith("AI: ...thinking...\n"):
            current_text = current_text.rsplit("AI: ...thinking...\n", 1)[0]
            self.textbox.delete("1.0", "end")
            self.textbox.insert("1.0", current_text + new_text)
        else:
            self.textbox.insert("end", new_text)
        self.textbox.see("end")
        self.textbox.configure(state="disabled")


if __name__ == "__main__":
    ensure_userdata_dir()  
    app = AuthApp()
    app.mainloop()
