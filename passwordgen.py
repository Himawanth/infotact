import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import random
import string
import sqlite3
from cryptography.fernet import Fernet
import os

# Ensure encryption key exists
if not os.path.exists("secret.key"):
    key = Fernet.generate_key()
    with open("secret.key", "wb") as key_file:
        key_file.write(key)

def load_key():
    return open("secret.key", "rb").read()

encryption_key = load_key()
cipher = Fernet(encryption_key)

# Initialize Database
def init_db():
    conn = sqlite3.connect("passwords.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT,
            encrypted_password BLOB
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Password Generator
def generate_password(length, use_digits=True, use_special=True):
    chars = string.ascii_letters
    if use_digits:
        chars += string.digits
    if use_special:
        chars += string.punctuation
    return ''.join(random.choice(chars) for _ in range(length))

# Save Password
def save_password(service, password):
    if not service or not password:
        messagebox.showerror("Error", "Service and password cannot be empty!")
        return
    encrypted_password = cipher.encrypt(password.encode())
    conn = sqlite3.connect("passwords.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO passwords (service, encrypted_password) VALUES (?, ?)", (service, encrypted_password))
    conn.commit()
    conn.close()
    messagebox.showinfo("Success", "Password saved securely!")

# Save Text from Editor
def save_text(text_editor):
    file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                             filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if file_path:
        with open(file_path, "w") as file:
            file.write(text_editor.get("1.0", tk.END))
        messagebox.showinfo("Success", "File saved successfully!")

# Registration Window
def register():
    def save_user():
        username = reg_user_entry.get()
        password = reg_pass_entry.get()
        if not username or not password:
            messagebox.showerror("Error", "All fields are required")
            return
        conn = sqlite3.connect("passwords.db")
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            messagebox.showinfo("Success", "Registration successful! Please login.")
            reg_window.destroy()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists")
        conn.close()
    
    reg_window = tk.Toplevel()
    reg_window.title("Register")
    reg_window.geometry("300x200")
    
    tk.Label(reg_window, text="Username:").pack()
    reg_user_entry = tk.Entry(reg_window)
    reg_user_entry.pack()
    
    tk.Label(reg_window, text="Password:").pack()
    reg_pass_entry = tk.Entry(reg_window, show="*")
    reg_pass_entry.pack()
    
    reg_btn = tk.Button(reg_window, text="Register", command=save_user)
    reg_btn.pack()
    
    reg_window.mainloop()

# Login Page
def login():
    def check_login():
        username = user_entry.get()
        password = pass_entry.get()
        conn = sqlite3.connect("passwords.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            login_window.destroy()
            main_app()
        else:
            messagebox.showerror("Error", "Invalid credentials")
    
    login_window = tk.Tk()
    login_window.title("Login")
    login_window.geometry("300x250")
    
    tk.Label(login_window, text="Username:").pack()
    user_entry = tk.Entry(login_window)
    user_entry.pack()
    
    tk.Label(login_window, text="Password:").pack()
    pass_entry = tk.Entry(login_window, show="*")
    pass_entry.pack()
    
    login_btn = tk.Button(login_window, text="Login", command=check_login)
    login_btn.pack()
    
    register_btn = tk.Button(login_window, text="Register", command=register)
    register_btn.pack()
    
    login_window.mainloop()

# Main Application
def main_app():
    root = tk.Tk()
    root.title("Password Generator & Text Editor")
    root.geometry("600x500")
    
    # Logout function
    def logout():
        root.destroy()
        login()
    
    # Notebook (Tabs)
    tabs = ttk.Notebook(root)
    password_tab = ttk.Frame(tabs)
    editor_tab = ttk.Frame(tabs)
    tabs.add(password_tab, text="Password Generator")
    tabs.add(editor_tab, text="Text Editor")
    tabs.pack(expand=1, fill="both")
    
    # Password Generator UI
    frame = ttk.Frame(password_tab)
    frame.pack(pady=20)
    
    tk.Label(frame, text="Service Name:").grid(row=0, column=0, padx=5, pady=5)
    service_entry = tk.Entry(frame)
    service_entry.grid(row=0, column=1, padx=5, pady=5)
    
    tk.Label(frame, text="Password Length:").grid(row=1, column=0, padx=5, pady=5)
    length_entry = tk.Entry(frame)
    length_entry.grid(row=1, column=1, padx=5, pady=5)
    
    digit_var = tk.BooleanVar(value=True)
    special_var = tk.BooleanVar(value=True)
    tk.Checkbutton(frame, text="Include Digits", variable=digit_var).grid(row=2, column=0)
    tk.Checkbutton(frame, text="Include Special Characters", variable=special_var).grid(row=2, column=1)
    
    password_output = tk.Entry(frame, width=30)
    password_output.grid(row=3, column=1, padx=5, pady=5)
    
    def generate_and_display():
        try:
            length = int(length_entry.get())
            password = generate_password(length, digit_var.get(), special_var.get())
            password_output.delete(0, tk.END)
            password_output.insert(0, password)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")
    
    generate_btn = tk.Button(frame, text="Generate", command=generate_and_display)
    generate_btn.grid(row=4, column=0, pady=5)
    
    save_btn = tk.Button(frame, text="Save Password", command=lambda: save_password(service_entry.get(), password_output.get()))
    save_btn.grid(row=4, column=1, pady=5)
    
    # Text Editor UI
    text_editor = scrolledtext.ScrolledText(editor_tab, wrap=tk.WORD, width=60, height=20, font=("Arial", 12))
    text_editor.pack(pady=10)
    
    save_text_btn = tk.Button(editor_tab, text="Save", command=lambda: save_text(text_editor))
    save_text_btn.pack()
    
    logout_btn = tk.Button(root, text="Logout", command=logout)
    logout_btn.pack(pady=10)
    
    root.mainloop()

# Start with login
login()
