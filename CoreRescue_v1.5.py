# -*- coding: utf-8 -*-
# title: CoreRescue (v1.5.2 - Final Build)
# author: TB / Gemini

import os, time, tempfile, shutil, sys, subprocess

# --- AUTOMATIC INSTALLER LOGIC ---
def check_and_install():
    try:
        from PIL import Image, ImageTk
        from pysiril.siril import Siril as pySiril
    except ImportError:
        print("CoreRescue: Libraries missing. Downloading stable versions...")
        python_exe = sys.executable
        pysiril_url = "https://gitlab.com/-/project/20510105/uploads/8224707c29669f255ad43da3b93bc5ec/pysiril-0.0.15-py3-none-any.whl"
        try:
            subprocess.check_call([python_exe, "-m", "pip", "install", "--disable-pip-version-check", pysiril_url, "Pillow"])
            print("Installation successful. Restarting CoreRescue...")
            args = [f'"{arg}"' if ' ' in arg else arg for arg in sys.argv]
            os.execv(python_exe, [python_exe] + args)
        except: sys.exit(1)

check_and_install()

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from pysiril.siril import Siril as pySiril

class CoreRescue:
    def __init__(self, root):
        self.root = root
        self.root.title("CoreRescue v1.5.2")
        self.root.geometry("1550x980")
        
        # Immediate path setup to prevent crash on load
        self.siril_home = os.getcwd()
        self.temp_dir = os.path.join(tempfile.gettempdir(), "core_rescue").replace("\\", "/")
        if not os.path.exists(self.temp_dir): os.makedirs(self.temp_dir)
            
        self.base_image = ""
        self.after_id = None 
        self.zoom_level = 1.0
        self.view_mode = tk.StringVar(value="Blend")
        self.current_img_path = ""
        self.label_widgets = {} 
        
        try:
            self.app = pySiril()
            self.app.Open()
            time.sleep(0.5)
            actual_home = self.app.get_cwd()
            if actual_home: self.siril_home = actual_home
        except: pass

        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def run_siril_cmd(self, cmd_string):
        try: self.app.Execute(cmd_string)
        except: pass

    def set_status(self, text, color="#e67e22"):
        self.status_label.config(text=text, background=color)
        self.root.update_idletasks()

    def load_image(self):
        path = filedialog.askopenfilename(initialdir=self.siril_home, title="Select Linear FITS")
        if path:
            self.base_image = path
            self.siril_home = os.path.dirname(path)
            shutil.copy2(path, f"{self.temp_dir}/raw.fits")
            self.run_siril_cmd(f'cd "{self.temp_dir}"')
            self.process_image()

    def reset_all(self):
        self.core_var.set(10.0); self.bp_var.set(0.0); self.sat_var.set(1.0)
        self.neb_var.set(0.1); self.feather_var.set(15.0)
        self.process_image()

    def process_image(self, save_mode=None):
        if not self.base_image: return
        self.set_status("● WORKING...", "#e67e22")
        
        c_str, c_bp, c_sat = self.core_var.get(), self.bp_var.get(), self.sat_var.get()
        n_str, feather = self.neb_var.get(), self.feather_var.get()
        
        cmds = [
            f'cd "{self.temp_dir}"',
            # Layer B: Core with Asinh and Saturation
            'load raw.fits', f'asinh {c_str} {c_bp}', f'satu {c_sat} 1.0', 'save b.fits',
            # Layer A: Nebula with MTF
            'load raw.fits', f'mtf 0.0 {n_str} 1.0', 'save a.fits',
            # Blending Mask from Core layer
            'load b.fits', f'gauss {feather}', 'save mask.fits',
            # HDR Blending PixelMath
            'load a.fits', 'pm "$a.fits$ * (1 - $mask.fits$) + ($b.fits$ * $mask.fits$)"'
        ]
        
        if save_mode:
            out_dir = os.path.dirname(self.base_image)
            ext = "fits" if save_mode == "fits" else "jpg"
            fname = f"HDR_Rescued.{ext}"
            cmds.append(f'save "{os.path.join(out_dir, fname).replace("\\", "/")}"' if ext=="fits" else f'savejpg "{os.path.join(out_dir, fname).replace("\\", "/")}" 95')
        else:
            cmds += ['savejpg _p_blend 95', 'load a.fits', 'savejpg _p_neb 95', 'load b.fits', 'savejpg _p_core 95', 'load mask.fits', 'savejpg _p_mask 95']

        for c in cmds: self.run_siril_cmd(c)
        if not save_mode: 
            self.update_display()
            self.set_status("✔ READY", "#27ae60")
        else: 
            self.set_status("✔ SAVE COMPLETE", "#2980b9")
            messagebox.showinfo("CoreRescue", "Saved successfully!")

    def update_display(self):
        m = {"Blend":"_p_blend.jpg", "Core Only":"_p_core.jpg", "Nebula Only":"_p_neb.jpg", "Mask Map":"_p_mask.jpg"}
        self.current_img_path = f"{self.temp_dir}/{m.get(self.view_mode.get())}"
        self.render_image()

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

    def setup_ui(self):
        sidebar = ttk.Frame(self.root, padding=15); sidebar.pack(side="left", fill="y")
        ttk.Label(sidebar, text="CoreRescue v1.5.2", font=('Helvetica', 14, 'bold')).pack(pady=(0,10))
        
        self.status_label = tk.Label(sidebar, text="✔ READY", fg="white", background="#27ae60", font=('Helvetica', 9, 'bold'), pady=5)
        self.status_label.pack(fill="x", pady=(0,10))

        ttk.Button(sidebar, text="Load Linear FITS", command=self.load_image).pack(fill="x")
        
        v_frm = ttk.LabelFrame(sidebar, text=" View Inspector ", padding=10); v_frm.pack(fill="x", pady=10)
        for mode in ["Blend", "Core Only", "Nebula Only", "Mask Map"]:
            ttk.Radiobutton(v_frm, text=mode, variable=self.view_mode, value=mode, command=self.update_display).pack(anchor="w")

        self.core_var, self.bp_var, self.sat_var = tk.DoubleVar(value=10.0), tk.DoubleVar(value=0.0), tk.DoubleVar(value=1.0)
        self.neb_var, self.feather_var = tk.DoubleVar(value=0.1), tk.DoubleVar(value=15.0)
        
# --- Bold Text Symmetrical Labels ---
        self.create_slider(sidebar, "Core Stretch  (-) >> Brighter", self.core_var, (1, 1000), "{:.1f}", "core")
        self.create_slider(sidebar, "Core Saturation  (-) >> More", self.sat_var, (0, 5), "{:.2f}", "sat")
        self.create_slider(sidebar, "Background BP  (-) >> Darker", self.bp_var, (0, 0.05), "{:.5f}", "bp")
        self.create_slider(sidebar, "Nebula Stretch  Brighter << (-)", self.neb_var, (0.001, 0.5), "{:.4f}", "neb")
        self.create_slider(sidebar, "Blend Feathering  (-) >> Softer", self.feather_var, (1, 200), "{:.1f}", "feat")

        ttk.Button(sidebar, text="Reset All Settings", command=self.reset_all).pack(fill="x", pady=(15, 0))
        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", pady=15)
        ttk.Button(sidebar, text="SAVE HDR FITS", command=lambda: self.process_image("fits")).pack(fill="x", pady=2)
        ttk.Button(sidebar, text="SAVE WEB JPG", command=lambda: self.process_image("jpg")).pack(fill="x")

        # Preview Area
        preview_frame = ttk.Frame(self.root); preview_frame.pack(side="right", expand=True, fill="both")
        toolbar = ttk.Frame(preview_frame); toolbar.pack(side="top", fill="x")
        ttk.Button(toolbar, text="Fit View", command=lambda: [setattr(self, 'zoom_level', 1.0), self.render_image()]).pack(side="left", padx=5)
        ttk.Label(toolbar, text="Wheel: Zoom | Drag: Pan").pack(side="left", padx=10)

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
    root = tk.Tk(); app = CoreRescue(root); root.mainloop()