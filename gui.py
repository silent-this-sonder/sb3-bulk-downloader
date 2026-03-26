import tkinter as tk

# MAIN WINDOW
root = tk.Tk()
root.title("SB3 Bulk Downloader")
root.geometry("960x720")

# WIDGETS

# Login Screen
user_label = tk.Label(root, text="Username:")
user_entry = tk.Entry(root)
pw_label = tk.Label(root, text="Password:")
pw_entry = tk.Entry(root)
login_button = tk.Button(root, text="Login")

# Project Filtering
project_opts = ["all", "shared", "unshared"]
project_label = tk.Label(root, text="Projects to Download")
project_optmenu = tk.OptionMenu(root, tk.StringVar(value="all"), *project_opts)
project_listbox = tk.Listbox(root)
project_scroll = tk.Scrollbar(root)

# so that the scrollbar affects the list
project_listbox.config(yscrollcommand=project_scroll.set)
project_scroll.config(command=project_listbox.yview)

for values in range(100):
    project_listbox.insert(tk.END, values)

# GEOMETRY MANAGER

# Login Screen
user_label.pack()
user_entry.pack()
pw_label.pack()
pw_entry.pack()
login_button.pack()

# Project Filtering
project_label.pack()
project_optmenu.pack()
project_scroll.pack(side="right", fill="both")
project_listbox.pack(side="right", fill="both")

# APPLICATION EVENT LOOP
root.mainloop()