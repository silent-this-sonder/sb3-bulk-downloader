import tkinter as tk

# Main Window
root = tk.Tk()
root.title("SB3 Bulk Downloader")
root.geometry("960x720")

# Widgets
label = tk.Label(
    root, text="Lorem ipsum dolor sit amet this window will eventually have stuff and we will be with you shortly :D"
)

# Geometry Manager
label.pack(pady=10)

# Application Event Loop
root.mainloop()