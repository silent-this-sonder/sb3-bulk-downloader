import tkinter as tk

# Main Window
root = tk.Tk()
root.title("SB3 Bulk Downloader")
root.geometry("960x720")

# Widgets
user_label = tk.Label(root, text="Username:")
user_entry = tk.Entry(root)
pw_label = tk.Label(root, text="Password:")
pw_entry = tk.Entry(root)
login_button = tk.Button(root, text="Login")

# Geometry Manager
user_label.pack()
user_entry.pack()
pw_label.pack()
pw_entry.pack()
login_button.pack()

# Application Event Loop
root.mainloop()