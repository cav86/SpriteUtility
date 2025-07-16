
import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk, ImageDraw
import numpy as np
from collections import Counter
from scipy.ndimage import label, find_objects
import os

NES_PALETTE = [
    (124, 124, 124), (0, 0, 252), (0, 0, 188), (68, 40, 188), (148, 0, 132), (168, 0, 32),
    (168, 16, 0), (136, 20, 0), (80, 48, 0), (0, 120, 0), (0, 104, 0), (0, 88, 0),
    (0, 64, 88), (0, 0, 0), (0, 0, 0), (0, 0, 0), (188, 188, 188), (0, 120, 248),
    (0, 88, 248), (104, 68, 252), (216, 0, 204), (228, 0, 88), (248, 56, 0), (228, 92, 16),
    (172, 124, 0), (0, 184, 0), (0, 168, 0), (0, 168, 68), (0, 136, 136), (0, 0, 0),
    (0, 0, 0), (0, 0, 0), (248, 248, 248), (60, 188, 252), (104, 136, 252), (152, 120, 248),
    (248, 120, 248), (248, 88, 152), (248, 120, 88), (252, 160, 68), (248, 184, 0),
    (184, 248, 24), (88, 216, 84), (88, 248, 152), (0, 232, 216), (120, 120, 120),
    (0, 0, 0), (0, 0, 0), (252, 252, 252), (164, 228, 252), (184, 184, 248), (216, 184, 248),
    (248, 184, 248), (248, 164, 192), (240, 208, 176), (252, 224, 168), (248, 216, 120),
    (216, 248, 120), (184, 248, 184), (184, 248, 216), (0, 252, 252), (248, 216, 248),
    (0, 0, 0), (0, 0, 0)
]

def closest_nes_color(color):
    r, g, b = map(int, color)
    return min(NES_PALETTE, key=lambda c: (r - c[0]) ** 2 + (g - c[1]) ** 2 + (b - c[2]) ** 2)

def convert_image_to_nes(image):
    arr = np.array(image.convert("RGB"))
    h, w, _ = arr.shape
    new_arr = np.zeros_like(arr)
    for y in range(h):
        for x in range(w):
            new_arr[y, x] = closest_nes_color(arr[y, x])
    return Image.fromarray(new_arr.astype('uint8'), 'RGB')

class SpriteExtractor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sprite Converter NES")
        self.original_image = None
        self.converted_image = None
        self.sprites = []
        self.zoom = 1
        self.selected_sprite = None

        self.create_widgets()

    def create_widgets(self):
        self.info_label = tk.Label(self, text="Consola estimada: -")
        self.info_label.pack()

        self.canvas_frame = tk.Frame(self)
        self.canvas_frame.pack()

        self.scroll_x = tk.Scrollbar(self.canvas_frame, orient="horizontal")
        self.scroll_y = tk.Scrollbar(self.canvas_frame, orient="vertical")
        self.canvas_original = tk.Canvas(self.canvas_frame, xscrollcommand=self.scroll_x.set, yscrollcommand=self.scroll_y.set)
        self.canvas_converted = tk.Canvas(self.canvas_frame)
        self.scroll_x.config(command=self.canvas_original.xview)
        self.scroll_y.config(command=self.canvas_original.yview)

        self.canvas_original.grid(row=0, column=0)
        self.canvas_converted.grid(row=0, column=1)
        self.scroll_x.grid(row=1, column=0, sticky="ew")
        self.scroll_y.grid(row=0, column=2, sticky="ns")

        control_frame = tk.Frame(self)
        control_frame.pack(pady=5)

        self.load_btn = tk.Button(control_frame, text="Cargar SpriteSheet", command=self.load_image)
        self.load_btn.grid(row=0, column=0, padx=2)

        self.detect_btn = tk.Button(control_frame, text="Detectar Sprites", command=self.detect_sprites, state=tk.DISABLED)
        self.detect_btn.grid(row=0, column=1, padx=2)

        self.export_orig_btn = tk.Button(control_frame, text="Exportar Sprites Originales", command=self.export_original_sprites, state=tk.DISABLED)
        self.export_orig_btn.grid(row=0, column=2, padx=2)

        self.export_nes_btn = tk.Button(control_frame, text="Exportar Sprites NES", command=self.export_nes_sprites, state=tk.DISABLED)
        self.export_nes_btn.grid(row=0, column=3, padx=2)

        self.export_sheet_btn = tk.Button(control_frame, text="Exportar Spritesheet NES", command=self.export_nes_sheet, state=tk.DISABLED)
        self.export_sheet_btn.grid(row=0, column=4, padx=2)

        self.zoom_var = tk.StringVar(value="Zoom x1")
        self.zoom_menu = ttk.Combobox(control_frame, textvariable=self.zoom_var, values=["Zoom x1", "Zoom x2", "Zoom x3", "Zoom x4"], state="readonly", width=10)
        self.zoom_menu.bind("<<ComboboxSelected>>", lambda e: self.display_images())
        self.zoom_menu.grid(row=0, column=5, padx=2)

        self.canvas_original.bind("<Button-1>", self.select_sprite)

    def load_image(self):
        path = filedialog.askopenfilename()
        if not path:
            return
        self.original_image = Image.open(path).convert("RGBA")
        self.converted_image = convert_image_to_nes(self.original_image)
        self.sprites = []
        self.selected_sprite = None
        self.display_images()
        self.detect_btn.config(state=tk.NORMAL)
        self.export_orig_btn.config(state=tk.DISABLED)
        self.export_nes_btn.config(state=tk.DISABLED)
        self.export_sheet_btn.config(state=tk.NORMAL)
        self.estimate_console()

    def display_images(self):
        self.zoom = int(self.zoom_var.get().replace("Zoom x", ""))
        if self.original_image:
            self.tk_original = ImageTk.PhotoImage(self.original_image.resize((self.original_image.width * self.zoom, self.original_image.height * self.zoom), Image.NEAREST))
            self.canvas_original.config(scrollregion=(0, 0, self.tk_original.width(), self.tk_original.height()))
            self.canvas_original.delete("all")
            self.canvas_original.create_image(0, 0, anchor="nw", image=self.tk_original)
        if self.converted_image:
            display = self.converted_image.copy()
            draw = ImageDraw.Draw(display)
            for i, (x1, y1, x2, y2) in enumerate(self.sprites):
                color = "blue" if i == self.selected_sprite else "red"
                draw.rectangle([x1, y1, x2, y2], outline=color, width=1)
            self.tk_converted = ImageTk.PhotoImage(display.resize((display.width * self.zoom, display.height * self.zoom), Image.NEAREST))
            self.canvas_converted.config(width=self.tk_converted.width(), height=self.tk_converted.height())
            self.canvas_converted.delete("all")
            self.canvas_converted.create_image(0, 0, anchor="nw", image=self.tk_converted)

    def estimate_console(self):
        arr = np.array(self.original_image.convert("RGB"))
        pixels = arr.reshape(-1, 3)
        color_count = len(set(map(tuple, pixels)))
        consola = "Desconocida"
        if color_count <= 4:
            consola = "NES / Game Boy"
        elif color_count <= 16:
            consola = "SNES / GBA"
        elif color_count <= 64:
            consola = "Sega Genesis / Neo Geo"
        else:
            consola = "Nintendo DS / Otro"
        self.info_label.config(text=f"Consola estimada: {consola} ({color_count} colores)")

    def detect_sprites(self):
        arr = np.array(self.original_image)
        background = Counter(map(tuple, arr[:, :, :3].reshape(-1, 3))).most_common(1)[0][0]
        mask = np.any(arr[:, :, :3] != background, axis=2)
        labeled, _ = label(mask)
        slices = find_objects(labeled)
        self.sprites = [(s[1].start, s[0].start, s[1].stop, s[0].stop) for s in slices if (s[1].stop - s[1].start) > 4 and (s[0].stop - s[0].start) > 4]
        self.display_images()
        self.export_orig_btn.config(state=tk.NORMAL)
        self.export_nes_btn.config(state=tk.NORMAL)

    def select_sprite(self, event):
        if not self.sprites:
            return
        x = self.canvas_original.canvasx(event.x) // self.zoom
        y = self.canvas_original.canvasy(event.y) // self.zoom
        for i, (x1, y1, x2, y2) in enumerate(self.sprites):
            if x1 <= x <= x2 and y1 <= y <= y2:
                self.selected_sprite = i
                break
        else:
            self.selected_sprite = None
        self.display_images()

    def export_original_sprites(self):
        folder = filedialog.askdirectory()
        if not folder:
            return
        for i, (x1, y1, x2, y2) in enumerate(self.sprites):
            crop = self.original_image.crop((x1, y1, x2, y2))
            crop.save(os.path.join(folder, f"sprite_original_{i+1:03}.png"))

    def export_nes_sprites(self):
        folder = filedialog.askdirectory()
        if not folder:
            return
        for i, (x1, y1, x2, y2) in enumerate(self.sprites):
            crop = self.converted_image.crop((x1, y1, x2, y2))
            crop.save(os.path.join(folder, f"sprite_nes_{i+1:03}.png"))

    def export_nes_sheet(self):
        folder = filedialog.askdirectory()
        if not folder:
            return
        out_path = os.path.join(folder, "spritesheet_convertido_nes.png")
        self.converted_image.save(out_path)

if __name__ == "__main__":
    app = SpriteExtractor()
    app.mainloop()
