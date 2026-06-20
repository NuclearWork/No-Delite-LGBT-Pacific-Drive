import customtkinter as ctk
from tkinter import filedialog, messagebox, Canvas
from PIL import Image, ImageTk
import os

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

SLOTS = ["Flag-Abrosexual.png", "Flag-Agender.png", "Flag-Asexual.png", "Flag-BLM.png",
    "Flag-Bigender_Redesign.png", "Flag-Bisexual.png", "Flag-Demisexual.png",
    "Flag-Gay_Man.png", "Flag-Genderfluid.png", "Flag-Genderflux.png",
    "Flag-Genderqueer.png", "Flag-Intersex.png", "Flag-Lesbian_5_Stripe.png",
    "Flag-Lgbtq.png", "Flag-Lgbtq_progress.png", "Flag-Neutrois.png",
    "Flag-NonBinary.png", "Flag-Pangender.png", "Flag-Pansexual.png",
    "Flag-Polysexual.png", "Flag-Queer.png", "Flag-Straight_Ally.png",
    "Flag-Transgender.png"]

class StickerStudio(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("No Pride Studio - Редактор стикеров")
        self.geometry("1000x700")
        self.current_slot = ctk.StringVar(value=SLOTS[0])
        self.target_w, self.target_h, self.crop_scale = 192, 128, 2.0
        self.original_image, self.photo_image = None, None
        self.img_scale, self.img_x, self.img_y = 1.0, 0, 0
        self.setup_ui()
        self.update_crop_frame()

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.sidebar = ctk.CTkFrame(self, width=250)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.sidebar, text="No Pride Studio", font=("Arial", 20, "bold")).pack(pady=20)
        ctk.CTkOptionMenu(self.sidebar, values=SLOTS, variable=self.current_slot, command=self.on_slot_change).pack(pady=10, padx=20)
        ctk.CTkButton(self.sidebar, text="Загрузить картинку", command=self.load_image).pack(pady=10, padx=20)
        ctk.CTkButton(self.sidebar, text="Сохранить", command=self.save_image, fg_color="green").pack(pady=10, padx=20)

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.canvas = Canvas(self.main_frame, bg="#2b2b2b", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.canvas.bind("<ButtonPress-1>", self.on_drag_start)
        self.canvas.bind("<B1-Motion>", self.on_drag_motion)
        self.canvas.bind("<MouseWheel>", self.on_zoom)
        self.canvas.bind("<Configure>", self.on_canvas_resize)

        self.zoom_slider = ctk.CTkSlider(self.main_frame, from_=0.1, to=5.0, command=self.on_slider_zoom)
        self.zoom_slider.set(1.0)
        self.zoom_slider.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

    def on_slot_change(self, choice):
        self.target_w, self.target_h = (192, 256) if choice == "Flag-BLM.png" else (192, 128)
        self.update_crop_frame()

    def update_crop_frame(self):
        self.draw_canvas()

    def on_canvas_resize(self, event):
        if not self.original_image:
            self.img_x, self.img_y = event.width / 2, event.height / 2
        self.draw_canvas()

    def load_image(self):
        path = filedialog.askopenfilename()
        if not path: return
        self.original_image = Image.open(path).convert("RGBA")
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        self.img_x, self.img_y = cw / 2, ch / 2
        scale_w = (self.target_w * self.crop_scale) / self.original_image.width
        scale_h = (self.target_h * self.crop_scale) / self.original_image.height
        self.img_scale = max(scale_w, scale_h)
        self.zoom_slider.set(self.img_scale)
        self.draw_canvas()

    def draw_canvas(self):
        self.canvas.delete("all")
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        fw, fh = self.target_w * self.crop_scale, self.target_h * self.crop_scale
        fx, fy = (cw - fw) / 2, (ch - fh) / 2

        if self.original_image:
            w, h = int(self.original_image.width * self.img_scale), int(self.original_image.height * self.img_scale)
            if w > 0 and h > 0:
                self.photo_image = ImageTk.PhotoImage(self.original_image.resize((w, h), Image.Resampling.LANCZOS))
                self.canvas.create_image(self.img_x, self.img_y, image=self.photo_image, anchor="center")

        self.canvas.create_rectangle(0, 0, cw, fy, fill="#1a1a1a", stipple="gray50", outline="")
        self.canvas.create_rectangle(0, fy + fh, cw, ch, fill="#1a1a1a", stipple="gray50", outline="")
        self.canvas.create_rectangle(0, fy, fx, fy + fh, fill="#1a1a1a", stipple="gray50", outline="")
        self.canvas.create_rectangle(fx + fw, fy, cw, fy + fh, fill="#1a1a1a", stipple="gray50", outline="")
        self.canvas.create_rectangle(fx, fy, fx + fw, fy + fh, outline="#3b8ed0", width=3)

    def on_drag_start(self, event):
        self.drag_start_x, self.drag_start_y = event.x, event.y

    def on_drag_motion(self, event):
        if not self.original_image: return
        self.img_x += event.x - self.drag_start_x
        self.img_y += event.y - self.drag_start_y
        self.drag_start_x, self.drag_start_y = event.x, event.y
        self.draw_canvas()

    def on_zoom(self, event):
        if not self.original_image: return
        new_scale = max(0.05, min(self.img_scale * (1.1 if event.delta > 0 else 0.9), 10.0))
        cw, ch = self.canvas.winfo_width() / 2, self.canvas.winfo_height() / 2
        self.img_x = cw + (self.img_x - cw) * (new_scale / self.img_scale)
        self.img_y = ch + (self.img_y - ch) * (new_scale / self.img_scale)
        self.img_scale = new_scale
        self.zoom_slider.set(self.img_scale)
        self.draw_canvas()

    def on_slider_zoom(self, value):
        if not self.original_image: return
        new_scale = float(value)
        cw, ch = self.canvas.winfo_width() / 2, self.canvas.winfo_height() / 2
        self.img_x = cw + (self.img_x - cw) * (new_scale / self.img_scale)
        self.img_y = ch + (self.img_y - ch) * (new_scale / self.img_scale)
        self.img_scale = new_scale
        self.draw_canvas()

    def save_image(self):
        if not self.original_image: return
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        fw, fh = self.target_w * self.crop_scale, self.target_h * self.crop_scale
        fx, fy = (cw - fw) / 2, (ch - fh) / 2
        img_left = self.img_x - (self.original_image.width * self.img_scale) / 2
        img_top = self.img_y - (self.original_image.height * self.img_scale) / 2
        crop_left, crop_top = (fx - img_left) / self.img_scale, (fy - img_top) / self.img_scale
        crop_right, crop_bottom = (fx + fw - img_left) / self.img_scale, (fy + fh - img_top) / self.img_scale

        cropped = self.original_image.transform(
            (self.target_w, self.target_h), Image.EXTENT,
            data=(crop_left, crop_top, crop_right, crop_bottom), resample=Image.Resampling.LANCZOS
        )
        out_dir = os.path.join(os.getcwd(), "pikcher", "23icon")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, self.current_slot.get())
        cropped.save(out_path)
        messagebox.showinfo("Успех", f"Картинка сохранена в:\n{out_path}")

if __name__ == "__main__":
    app = StickerStudio()
    app.mainloop()

