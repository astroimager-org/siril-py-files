# -*- coding: utf-8 -*-
# title: StarRecombiner (v2.0 - Pro Interface)
# author: TB

import os, time, tempfile, shutil, sys, subprocess

# --- AUTOMATIC INSTALLER LOGIC ---
def check_and_install():
    try:
        from PIL import Image, ImageTk
        from pysiril.siril import Siril as pySiril
    except ImportError:
        print("StarRecombiner: Libraries missing. Downloading stable versions...")
        python_exe = sys.executable
        pysiril_url = "https://gitlab.com/-/project/20510105/uploads/8224707c29669f255ad43da3b93bc5ec/pysiril-0.0.15-py3-none-any.whl"
        try:
            subprocess.check_call([python_exe, "-m", "pip", "install", "--disable-pip-version-check", pysiril_url, "Pillow"])
            args = [f'"{arg}"' if ' ' in arg else arg for arg in sys.argv]
            os.execv(python_exe, [python_exe] + args)
        except: sys.exit(1)

check_and_install()

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from pysiril.siril import Siril as pySiril

class StarRecombiner:
    def __init__(self, root):
        self.root = root
        self.root.title("StarRecombiner v2.0")
        self.root.geometry("1550x980")
        
        self.temp_dir = os.path.join(tempfile.gettempdir(), "star_recombiner").replace("\\", "/")
        if not os.path.exists(self.temp_dir): os.makedirs(self.temp_dir)
            
        self.starless_orig = ""
        self.starmask_orig = ""
        self.after_id = None 
        self.zoom_level = 1.0
        self.current_img_path = ""
        self.siril_home = os.getcwd() 
        self.label_widgets = {}
        
        try:
            self.app = pySiril()
            self.app.Open()
            self.siril_home = self.app.get_cwd() 
        except: pass

        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def run_siril_cmd(self, cmd_string):
        try: self.app.Execute(cmd_string)
        except: pass

    def set_status(self, text, color="#e67e22"):
        self.status_label.config(text=text, background=color)
        self.root.update_idletasks()

    def load_starless(self):
        path = filedialog.askopenfilename(initialdir=self.siril_home, title="Select Starless Nebula")
        if path:
            self.starless_orig = path
            shutil.copy2(path, f"{self.temp_dir}/a.fits")
            self.run_siril_cmd(f'cd "{self.temp_dir}"')
            self.run_siril_cmd('load a.fits')
            self.run_siril_cmd('savejpg _base_starless 100')
            self.display_preview(f"{self.temp_dir}/_base_starless.jpg")

    def load_starmask(self):
        path = filedialog.askopenfilename(initialdir=self.siril_home, title="Select Linear Starmask")
        if path:
            self.starmask_orig = path
            shutil.copy2(path, f"{self.temp_dir}/b_orig.fits")
            self.process_image()

    def reset_defaults(self):
        self.asinh_var.set(20.0); self.bp_var.set(0.0)
        self.mid_var.set(0.5); self.sat_var.set(1.0); self.blur_var.set(0.5)
        self.process_image()

    def process_image(self, save_mode=None):
        if not self.starless_orig or not self.starmask_orig: return
        self.set_status("● WORKING...", "#e67e22")
        
        asinh_f, asinh_bp = self.asinh_var.get(), self.bp_var.get()
        midtones, blur_val, sat_val = self.mid_var.get(), self.blur_var.get(), self.sat_var.get()
        
        cmds = [
            f'cd "{self.temp_dir}"', 'load b_orig.fits',
            f'asinh {asinh_f} {asinh_bp}', f'mtf 0.0 {midtones} 1.0', 
            f'satu {sat_val} 1.0', f'gauss {blur_val}', 'save b.fits',
            'load a.fits', 'pm "1 - (1 - $b.fits$) * (1 - $a.fits$)"'
        ]
        
        out_dir = os.path.dirname(self.starless_orig)
        if save_mode == "fits":
            cmds.append(f'save "{os.path.join(out_dir, "recombined_final.fits").replace("\\", "/")}"')
        elif save_mode == "jpg":
            cmds.append(f'savejpg "{os.path.join(out_dir, "recombined_web.jpg").replace("\\", "/")}" 95')
        else:
            cmds.append('savejpg _preview 95')

        for c in cmds: self.run_siril_cmd(c)
        
        if not save_mode:
            self.display_preview(f"{self.temp_dir}/_preview.jpg")
            self.set_status("✔ READY", "#27ae60")
        else:
            self.set_status("✔ SAVE COMPLETE", "#2980b9")
            messagebox.showinfo("StarRecombiner", f"Successfully saved to:\n{out_dir}")

    def render_image(self):
        if not self.current_img_path: return
        try:
            img = Image.open(self.current_img_path)
            cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
            if cw < 10: cw, ch = 1000, 800
            iw, ih = img.size
            ratio = min(cw/iw, ch/ih)
            new_size = (int(iw * ratio * self.zoom_level), int(ih * ratio * self.zoom_level))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(img)
            self.canvas.delete("all")
            self.canvas.create_image(cw//2, ch//2, image=self.photo, anchor="center")
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
        except: pass

    def display_preview(self, path):
        self.current_img_path = path
        self.render_image()

    def setup_ui(self):
        sidebar = ttk.Frame(self.root, padding=15); sidebar.pack(side="left", fill="y")
        ttk.Label(sidebar, text="StarRecombiner v2.0", font=('Helvetica', 14, 'bold')).pack(pady=(0,10))
        
        self.status_label = tk.Label(sidebar, text="✔ READY", fg="white", background="#27ae60", font=('Helvetica', 9, 'bold'), pady=5)
        self.status_label.pack(fill="x", pady=(0,10))

        ttk.Button(sidebar, text="Load Starless Nebula", command=self.load_starless).pack(fill="x", pady=2)
        ttk.Button(sidebar, text="Load Linear Starmask", command=self.load_starmask).pack(fill="x", pady=2)
        
        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", pady=15)
        
        self.asinh_var = tk.DoubleVar(value=20.0); self.bp_var = tk.DoubleVar(value=0.0)
        self.mid_var = tk.DoubleVar(value=0.5); self.sat_var = tk.DoubleVar(value=1.0); self.blur_var = tk.DoubleVar(value=0.5)
        
        # Symmetrical Bold Labels
        self.create_slider(sidebar, "Asinh Stretch  (-) >> Brighter", self.asinh_var, (1, 1000), "{:.1f}", "asinh")
        self.create_slider(sidebar, "Black Point  (-) >> Darker", self.bp_var, (0, 0.1), "{:.4f}", "bp")
        self.create_slider(sidebar, "Midtones  Brighter << (-)", self.mid_var, (0.001, 0.999), "{:.3f}", "mid")
        self.create_slider(sidebar, "Star Saturation  (-) >> More", self.sat_var, (0, 5), "{:.2f}", "sat")
        self.create_slider(sidebar, "Star Blur (Gauss)  (-) >> Softer", self.blur_var, (0, 5), "{:.2f}", "blur")

        btn_compare = ttk.Button(sidebar, text="Hold to Compare (Starless Only)")
        btn_compare.pack(fill="x", pady=(15, 5))
        btn_compare.bind("<ButtonPress-1>", lambda e: self.display_preview(f"{self.temp_dir}/_base_starless.jpg"))
        btn_compare.bind("<ButtonRelease-1>", lambda e: self.display_preview(f"{self.temp_dir}/_preview.jpg"))

        ttk.Button(sidebar, text="Reset Defaults", command=self.reset_defaults).pack(fill="x", pady=5)
        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", pady=15)
        ttk.Button(sidebar, text="SAVE FINAL FITS", command=lambda: self.process_image("fits")).pack(fill="x", pady=2)
        ttk.Button(sidebar, text="SAVE WEB JPG", command=lambda: self.process_image("jpg")).pack(fill="x", pady=2)

        # Preview Area
        preview_frame = ttk.Frame(self.root); preview_frame.pack(side="right", expand=True, fill="both")
        toolbar = ttk.Frame(preview_frame); toolbar.pack(side="top", fill="x")
        ttk.Button(toolbar, text="Fit Screen", command=lambda: [setattr(self, 'zoom_level', 1.0), self.render_image()]).pack(side="left", padx=5)
        ttk.Label(toolbar, text="Wheel: Zoom | Drag: Pan").pack(side="left")

        self.canvas = tk.Canvas(preview_frame, bg="#111", highlightthickness=0); self.canvas.pack(expand=True, fill="both")
        self.canvas.bind("<MouseWheel>", lambda e: [setattr(self, 'zoom_level', self.zoom_level * (1.1 if e.delta > 0 else 0.9)), self.render_image()])
        self.canvas.bind("<ButtonPress-1>", lambda e: self.canvas.scan_mark(e.x, e.y))
        self.canvas.bind("<B1-Motion>", lambda e: self.canvas.scan_dragto(e.x, e.y, gain=1))

    def create_slider(self, p, l, v, r, f, key):
        fr = ttk.Frame(p); fr.pack(fill="x", pady=(5,0))
        ttk.Label(fr, text=l, font=('Helvetica', 8)).pack(side="left")
        self.label_widgets[key] = ttk.Label(fr, text=f.format(v.get()), foreground="#3498db", font=('Helvetica', 8, 'bold'))
        self.label_widgets[key].pack(side="right")
        
        def update_label(*args, k=key, fmt=f, var=v):
            if k in self.label_widgets:
                self.label_widgets[k].config(text=fmt.format(var.get()))
        v.trace_add("write", update_label)
        ttk.Scale(p, from_=r[0], to=r[1], variable=v, orient="horizontal", command=self.on_slider).pack(fill="x")

    def on_slider(self, _):
        if self.after_id: self.root.after_cancel(self.after_id)
        self.after_id = self.root.after(700, self.process_image)

    def on_closing(self):
        try: self.app.Close()
        except: pass
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk(); app = StarRecombiner(root); root.mainloop()