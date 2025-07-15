
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
    (0, 64, 88), (0, 0, 0), (188, 188, 188), (0, 120, 248), (0, 88, 248), (104, 68, 252),
    (216, 0, 204), (228, 0, 88), (248, 56, 0), (228, 92, 16), (172, 124, 0), (0, 184, 0),
    (0, 168, 0), (0, 168, 68), (0, 136, 136), (248, 248, 248), (60, 188, 252), (104, 136, 252),
    (152, 120, 248), (248, 120, 248), (248, 88, 152), (248, 120, 88), (252, 160, 68),
    (248, 184, 0), (184, 248, 24), (88, 216, 84), (88, 248, 152), (0, 232, 216),
    (120, 120, 120), (252, 252, 252), (164, 228, 252), (184, 184, 248), (216, 184, 248),
    (248, 184, 248), (248, 164, 192), (240, 208, 176), (252, 224, 168), (248, 216, 120),
    (216, 248, 120), (184, 248, 184), (184, 248, 216), (0, 252, 252), (248, 216, 248)
]

def closest_nes_color(color):
    r, g, b = [int(v) for v in color]
    return min(NES_PALETTE, key=lambda c: (int(r) - c[0])**2 + (int(g) - c[1])**2 + (int(b) - c[2])**2)

def convert_image_to_nes(image, sprite_boxes):
    arr = np.array(image.convert("RGB"))
    for (x1, y1, x2, y2) in sprite_boxes:
        region = arr[y1:y2, x1:x2]
        for y in range(region.shape[0]):
            for x in range(region.shape[1]):
                region[y, x] = closest_nes_color(region[y, x])
        arr[y1:y2, x1:x2] = region
    return Image.fromarray(arr.astype('uint8'), 'RGB')

class SpriteConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Conversor NES por Sprite")

        self.original_image = None
        self.converted_image = None
        self.sprites = []

        self.label_info = tk.Label(root, text="Sprites detectados: 0")
        self.label_info.pack()

        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.pack()

        self.canvas_original = tk.Canvas(self.canvas_frame, width=256, height=256, bg="gray")
        self.canvas_converted = tk.Canvas(self.canvas_frame, width=256, height=256, bg="gray")
        self.canvas_original.grid(row=0, column=0)
        self.canvas_converted.grid(row=0, column=1)

        self.controls = tk.Frame(root)
        self.controls.pack(pady=10)

        self.btn_load = tk.Button(self.controls, text="Cargar SpriteSheet", command=self.load_image)
        self.btn_load.pack(side="left", padx=5)

        self.btn_detect = tk.Button(self.controls, text="Detectar Sprites", command=self.detect_sprites, state="disabled")
        self.btn_detect.pack(side="left", padx=5)

        self.btn_export_sheet = tk.Button(self.controls, text="Exportar Spritesheet NES", command=self.export_nes_spritesheet, state="disabled")
        self.btn_export_sheet.pack(side="left", padx=5)

    def load_image(self):
        path = filedialog.askopenfilename()
        if not path:
            return
        self.original_image = Image.open(path).convert("RGBA")
        self.converted_image = self.original_image.copy()
        self.display_images()
        self.btn_detect.config(state="normal")
        self.btn_export_sheet.config(state="disabled")

    def display_images(self):
        img_o = self.original_image.copy()
        img_c = self.converted_image.copy()
        img_o.thumbnail((256, 256))
        img_c.thumbnail((256, 256))
        self.tk_o = ImageTk.PhotoImage(img_o)
        self.tk_c = ImageTk.PhotoImage(img_c)
        self.canvas_original.delete("all")
        self.canvas_converted.delete("all")
        self.canvas_original.create_image(0, 0, anchor="nw", image=self.tk_o)
        self.canvas_converted.create_image(0, 0, anchor="nw", image=self.tk_c)

    def detect_sprites(self):
        arr = np.array(self.original_image)
        background = Counter(map(tuple, arr[:, :, :3].reshape(-1, 3))).most_common(1)[0][0]
        mask = np.any(arr[:, :, :3] != background, axis=2)
        labeled, _ = label(mask)
        slices = find_objects(labeled)
        self.sprites = [(s[1].start, s[0].start, s[1].stop, s[0].stop)
                        for s in slices if (s[1].stop - s[1].start) > 4 and (s[0].stop - s[0].start) > 4]
        self.label_info.config(text=f"Sprites detectados: {len(self.sprites)}")
        self.converted_image = convert_image_to_nes(self.original_image.copy(), self.sprites)
        self.display_images()
        self.btn_export_sheet.config(state="normal")

    def export_nes_spritesheet(self):
        if not self.converted_image:
            return
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if not path:
            return
        self.converted_image.save(path)

if __name__ == "__main__":
    root = tk.Tk()
    app = SpriteConverterApp(root)
    root.mainloop()
