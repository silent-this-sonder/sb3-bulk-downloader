import tkinter as tk

class ScrollableChecklist(tk.Frame):
    '''Create a list of checkbuttons that supports scrolling'''
    def __init__(self, master, items, **kwargs):
        super().__init__(master, **kwargs)
        self.canvas = tk.Canvas(self)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.frame = tk.Frame(self.canvas)
        
        self.frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Populate with checkbuttons
        self.vars = {}
        for item in items:
            var = tk.IntVar()
            cb = tk.Checkbutton(self.frame, text=item, variable=var)
            cb.pack(anchor="w")
            self.vars[item] = var

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
project_checklist = ScrollableChecklist(root, ["example"] * 50)

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
project_checklist.pack(fill="both", expand=True)

# APPLICATION EVENT LOOP
root.mainloop()