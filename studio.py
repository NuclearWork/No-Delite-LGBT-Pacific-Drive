# -*- coding: utf-8 -*-
import customtkinter as ctk
from tkinter import filedialog, messagebox, Canvas
from PIL import Image, ImageTk
import os
import json
import threading
import subprocess
import zipfile
import shutil
import sys

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Координаты слотов в оригинальной текстуре-атласе 1024x1024
mapping = {
    'Flag-Abrosexual.png': (0, 0, 192, 128),
    'Flag-Agender.png': (384, 0, 192, 128),
    'Flag-Asexual.png': (192, 0, 192, 128),
    'Flag-BLM.png': (0, 768, 192, 256),
    'Flag-Bigender_Redesign.png': (576, 0, 192, 128),
    'Flag-Bisexual.png': (0, 128, 192, 128),
    'Flag-Demisexual.png': (192, 128, 192, 128),
    'Flag-Gay_Man.png': (384, 128, 192, 128),
    'Flag-Genderfluid.png': (576, 256, 192, 128),
    'Flag-Genderflux.png': (384, 384, 192, 128),
    'Flag-Genderqueer.png': (0, 256, 192, 128),
    'Flag-Intersex.png': (384, 256, 192, 128),
    'Flag-Lesbian_5_Stripe.png': (192, 512, 192, 128),
    'Flag-Lgbtq.png': (576, 128, 192, 128),
    'Flag-Lgbtq_progress.png': (192, 384, 192, 128),
    'Flag-Neutrois.png': (576, 384, 192, 128),
    'Flag-NonBinary.png': (384, 512, 192, 128),
    'Flag-Pangender.png': (192, 256, 192, 128),
    'Flag-Pansexual.png': (0, 384, 192, 128),
    'Flag-Polysexual.png': (192, 640, 192, 128),
    'Flag-Queer.png': (0, 512, 192, 128),
    'Flag-Straight_Ally.png': (0, 640, 192, 128),
    'Flag-Transgender.png': (384, 640, 192, 128),
}

SLOTS_ORDERED = sorted(mapping.keys())

def extract_default_assets():
    """Распаковывает встроенные в .exe шаблоны стикеров, если локальной папки нет."""
    is_bundle = hasattr(sys, '_MEIPASS')
    if not is_bundle:
        return
        
    bundle_dir = sys._MEIPASS
    local_pikcher = "pikcher"
    local_icon_dir = os.path.join(local_pikcher, "23icon")
    local_metadata = os.path.join(local_pikcher, "metadata.json")
    
    if not os.path.exists(local_pikcher):
        os.makedirs(local_pikcher)
    if not os.path.exists(local_icon_dir):
        os.makedirs(local_icon_dir)
        
    bundled_metadata = os.path.join(bundle_dir, "pikcher", "metadata.json")
    if not os.path.exists(local_metadata) and os.path.exists(bundled_metadata):
        try:
            shutil.copy(bundled_metadata, local_metadata)
        except Exception:
            pass
            
    bundled_icon_dir = os.path.join(bundle_dir, "pikcher", "23icon")
    if os.path.exists(bundled_icon_dir):
        for f in os.listdir(bundled_icon_dir):
            src_file = os.path.join(bundled_icon_dir, f)
            dst_file = os.path.join(local_icon_dir, f)
            if not os.path.exists(dst_file) and os.path.isfile(src_file):
                try:
                    shutil.copy(src_file, dst_file)
                except Exception:
                    pass

class StickerStudio(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("No Pride Studio - Редактор стикеров")
        self.geometry("1200x820")
        self.resizable(False, False)
        
        self.current_slot = SLOTS_ORDERED[0]
        self.metadata = {}
        
        # Ссылки на картинки превью для карты (предотвращает garbage collection)
        self.map_photos = {}
        
        # Переменные для интерактивного кадрирования
        self.original_image = None
        self.photo_image = None
        self.img_scale = 1.0
        self.img_x = 0
        self.img_y = 0
        
        # Распаковка дефолтных ресурсов и импорт
        extract_default_assets()
        
        # Запуск миграции и чтение метаданных
        from build_mod import migrate_if_needed
        self.metadata = migrate_if_needed()

        self.setup_ui()
        self.select_slot(self.current_slot)

    def setup_ui(self):
        # Настройка сетки окна: левая колонка для карты, правая для редактора и логов
        self.grid_columnconfigure(0, weight=0, minsize=550)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ================= ЛЕВАЯ ПАНЕЛЬ: Карта атласа =================
        self.left_frame = ctk.CTkFrame(self, width=540)
        self.left_frame.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        
        ctk.CTkLabel(
            self.left_frame, 
            text="ИНТЕРАКТИВНАЯ КАРТА АТЛАСА", 
            font=("Arial", 16, "bold")
        ).pack(pady=10)
        
        # Холст карты (512x512 для сжатия 1024x1024 в 2 раза)
        self.map_canvas = Canvas(self.left_frame, bg="#1e1e1e", width=512, height=512, highlightthickness=0)
        self.map_canvas.pack(pady=5, padx=10)
        self.map_canvas.bind("<Button-1>", self.on_map_click)

        # Подсказка для карты
        ctk.CTkLabel(
            self.left_frame,
            text="Кликни по любому слоту на карте выше для его выбора.",
            font=("Arial", 12, "italic"),
            text_color="#888888"
        ).pack(pady=2)

        # Панель сборки мода (под картой)
        self.build_frame = ctk.CTkFrame(self.left_frame)
        self.build_frame.pack(fill="x", padx=15, pady=5)
        
        self.build_button = ctk.CTkButton(
            self.build_frame,
            text="СОБРАТЬ МОД В ИГРУ 🔧",
            font=("Arial", 14, "bold"),
            fg_color="#1f538d",
            hover_color="#18416e",
            command=self.start_build
        )
        self.build_button.pack(fill="x", padx=10, pady=5)

        # Панель информации о папке мода
        self.folder_info_frame = ctk.CTkFrame(self.build_frame, fg_color="transparent")
        self.folder_info_frame.pack(fill="x", padx=10, pady=2)
        self.folder_info_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            self.folder_info_frame, 
            text="Папка собранного мода: pikcher/Сам_Мод/", 
            font=("Arial", 11, "bold"),
            text_color="#aaaaaa"
        ).grid(row=0, column=0, sticky="w", padx=5)
        
        self.btn_open_folder = ctk.CTkButton(
            self.folder_info_frame, 
            text="Открыть папку мода 📂", 
            width=160,
            font=("Arial", 11),
            command=self.open_mod_folder
        )
        self.btn_open_folder.grid(row=0, column=1, sticky="e", padx=5)

        self.log_textbox = ctk.CTkTextbox(self.build_frame, height=105, font=("Courier", 10))
        self.log_textbox.pack(fill="x", padx=10, pady=5)
        self.log_textbox.insert("1.0", "Лог сборщика мода...\n")

        # ================= ПРАВАЯ ПАНЕЛЬ: Редактор выбранного слота =================
        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")
        
        self.slot_header = ctk.CTkLabel(
            self.right_frame, 
            text="РЕДАКТОР СЛОТА", 
            font=("Arial", 18, "bold"),
            text_color="#3b8ed0"
        )
        self.slot_header.pack(pady=10)

        # Текстовые поля метаданных стикера
        self.inputs_frame = ctk.CTkFrame(self.right_frame)
        self.inputs_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(self.inputs_frame, text="Название стикера в меню игры:", font=("Arial", 12, "bold")).pack(anchor="w", padx=15, pady=2)
        self.name_entry = ctk.CTkEntry(self.inputs_frame, font=("Arial", 12))
        self.name_entry.pack(fill="x", padx=15, pady=2)

        ctk.CTkLabel(self.inputs_frame, text="Описание стикера в меню игры:", font=("Arial", 12, "bold")).pack(anchor="w", padx=15, pady=2)
        self.desc_entry = ctk.CTkEntry(self.inputs_frame, font=("Arial", 12))
        self.desc_entry.pack(fill="x", padx=15, pady=2)

        # Холст кадрирования
        self.crop_frame = ctk.CTkFrame(self.right_frame)
        self.crop_frame.pack(pady=10)
        
        self.crop_canvas = Canvas(self.crop_frame, bg="#111111", width=400, height=300, highlightthickness=0)
        self.crop_canvas.pack(padx=5, pady=5)
        self.crop_canvas.bind("<ButtonPress-1>", self.on_drag_start)
        self.crop_canvas.bind("<B1-Motion>", self.on_drag_motion)
        self.crop_canvas.bind("<MouseWheel>", self.on_zoom)

        # Слайдер масштаба
        self.zoom_slider = ctk.CTkSlider(self.right_frame, from_=0.05, to=5.0, command=self.on_slider_zoom)
        self.zoom_slider.set(1.0)
        self.zoom_slider.pack(fill="x", padx=30, pady=5)

        # Кнопки действий над слотом
        self.actions_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.actions_frame.pack(pady=10)

        self.btn_load = ctk.CTkButton(
            self.actions_frame, 
            text="Выбрать картинку 📂", 
            command=self.load_image
        )
        self.btn_load.grid(row=0, column=0, padx=5)

        self.btn_save = ctk.CTkButton(
            self.actions_frame, 
            text="Сохранить слот ✔", 
            fg_color="green", 
            hover_color="#005f00", 
            command=self.save_slot
        )
        self.btn_save.grid(row=0, column=1, padx=5)

        self.btn_reset = ctk.CTkButton(
            self.actions_frame, 
            text="Очистить слот 🗑", 
            fg_color="red", 
            hover_color="#8b0000", 
            command=self.reset_slot
        )
        self.btn_reset.grid(row=0, column=2, padx=5)

        # Кнопки импорта/экспорта профилей
        self.profile_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.profile_frame.pack(pady=5)

        self.btn_export = ctk.CTkButton(
            self.profile_frame, 
            text="Экспорт набора (ZIP) 📤", 
            fg_color="#4a4a4a",
            hover_color="#333333",
            command=self.export_profile
        )
        self.btn_export.grid(row=0, column=0, padx=5)

        self.btn_import = ctk.CTkButton(
            self.profile_frame, 
            text="Импорт набора (ZIP) 📥", 
            fg_color="#4a4a4a",
            hover_color="#333333",
            command=self.import_profile
        )
        self.btn_import.grid(row=0, column=1, padx=5)

    def draw_map(self):
        """Отрисовывает сетку атласа на холсте слева."""
        self.map_canvas.delete("all")
        self.map_photos.clear()
        
        icon_dir = os.path.join("pikcher", "23icon")

        for slot_name in SLOTS_ORDERED:
            x, y, w, h = mapping[slot_name]
            # Сжатие в 2 раза для экрана
            sx, sy, sw, sh = x // 2, y // 2, w // 2, h // 2
            
            letter = self.metadata.get(slot_name, {}).get("slot_letter", "?")
            is_assigned = self.metadata.get(slot_name, {}).get("is_assigned", False)
            is_selected = (slot_name == self.current_slot)
            
            border_color = "#3b8ed0" if is_selected else "#444444"
            border_width = 3 if is_selected else 1
            
            pic_path = os.path.join(icon_dir, slot_name)
            
            if is_assigned and os.path.exists(pic_path):
                # Загружаем уменьшенное превью
                try:
                    img = Image.open(pic_path).convert("RGBA")
                    img_resized = img.resize((sw, sh), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img_resized)
                    self.map_photos[slot_name] = photo
                    
                    self.map_canvas.create_image(sx + sw // 2, sy + sh // 2, image=photo, anchor="center")
                    # Рисуем рамку поверх картинки
                    self.map_canvas.create_rectangle(sx, sy, sx + sw, sy + sh, outline=border_color, width=border_width)
                except Exception:
                    # В случае ошибки отрисовываем как пустую
                    self.map_canvas.create_rectangle(sx, sy, sx + sw, sy + sh, fill="#2b2b2b", outline=border_color, width=border_width)
                    self.map_canvas.create_text(sx + sw // 2, sy + sh // 2, text=letter, fill="#888888", font=("Arial", 14, "bold"))
            else:
                # Отрисовываем пустой слот с буквой
                # BLM слот сделаем чуть темнее
                bg_color = "#151515" if slot_name == "Flag-BLM.png" else "#252525"
                self.map_canvas.create_rectangle(sx, sy, sx + sw, sy + sh, fill=bg_color, outline=border_color, width=border_width)
                self.map_canvas.create_text(sx + sw // 2, sy + sh // 2, text=letter, fill="#666666", font=("Arial", 16, "bold"))

    def on_map_click(self, event):
        """Обрабатывает клик мыши по карте атласа."""
        mx, my = event.x * 2, event.y * 2  # Возвращаем исходный масштаб 1024x1024
        
        for slot_name, (x, y, w, h) in mapping.items():
            if x <= mx < x + w and y <= my < y + h:
                self.select_slot(slot_name)
                break

    def select_slot(self, slot_name):
        """Выбирает слот для редактирования и загружает его данные."""
        self.current_slot = slot_name
        self.draw_map()
        
        # Получаем данные о слоте
        info = self.metadata.get(slot_name, {})
        letter = info.get("slot_letter", "?")
        
        # Исключаем техническое имя файла в скобках по требованию пользователя
        self.slot_header.configure(text=f"РЕДАКТОР СЛОТА {letter}")
        
        # Обновляем текстовые поля ввода
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, info.get("custom_name", ""))
        
        self.desc_entry.delete(0, "end")
        self.desc_entry.insert(0, info.get("custom_desc", ""))

        # Размеры кадрирования в зависимости от слота
        tw, th = (192, 256) if slot_name == "Flag-BLM.png" else (192, 128)
        
        # Подбираем масштаб рамки кадрирования на холсте 400x300
        scale_w = 340 / tw
        scale_h = 240 / th
        self.crop_scale = min(scale_w, scale_h)
        self.target_w, self.target_h = tw, th

        # Очищаем редактор картинок
        self.original_image = None
        self.photo_image = None
        self.img_scale = 1.0
        
        # Если слот уже настроен, загружаем его текущую картинку в качестве основы для редактирования
        pic_path = os.path.join("pikcher", "23icon", slot_name)
        if os.path.exists(pic_path):
            try:
                self.original_image = Image.open(pic_path).convert("RGBA")
                self.img_x, self.img_y = 200, 150 # Центр холста
                
                # Масштабируем так, чтобы картинка перекрывала рамку кадрирования
                scale_fit_w = (self.target_w * self.crop_scale) / self.original_image.width
                scale_fit_h = (self.target_h * self.crop_scale) / self.original_image.height
                self.img_scale = max(scale_fit_w, scale_fit_h)
                self.zoom_slider.set(self.img_scale)
            except Exception:
                pass
                
        self.draw_crop_canvas()

    def load_image(self):
        """Загружает файл пользователя на холст кадрирования."""
        path = filedialog.askopenfilename(
            filetypes=[("Изображения", "*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.webp")]
        )
        if not path:
            return
            
        try:
            self.original_image = Image.open(path).convert("RGBA")
            self.img_x, self.img_y = 200, 150
            
            # Масштабируем под рамку
            scale_fit_w = (self.target_w * self.crop_scale) / self.original_image.width
            scale_fit_h = (self.target_h * self.crop_scale) / self.original_image.height
            self.img_scale = max(scale_fit_w, scale_fit_h)
            
            self.zoom_slider.set(self.img_scale)
            self.draw_crop_canvas()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть изображение:\n{e}")

    def draw_crop_canvas(self):
        """Отрисовывает интерактивную область обрезки."""
        self.crop_canvas.delete("all")
        cw, ch = 400, 300
        
        fw = self.target_w * self.crop_scale
        fh = self.target_h * self.crop_scale
        fx = (cw - fw) / 2
        fy = (ch - fh) / 2

        # Отрисовка изображения пользователя
        if self.original_image:
            w = int(self.original_image.width * self.img_scale)
            h = int(self.original_image.height * self.img_scale)
            if w > 0 and h > 0:
                self.photo_image = ImageTk.PhotoImage(self.original_image.resize((w, h), Image.Resampling.LANCZOS))
                self.crop_canvas.create_image(self.img_x, self.img_y, image=self.photo_image, anchor="center")

        # Полупрозрачные маски
        self.crop_canvas.create_rectangle(0, 0, cw, fy, fill="#0f0f0f", outline="")
        self.crop_canvas.create_rectangle(0, fy + fh, cw, ch, fill="#0f0f0f", outline="")
        self.crop_canvas.create_rectangle(0, fy, fx, fy + fh, fill="#0f0f0f", outline="")
        self.crop_canvas.create_rectangle(fx + fw, fy, cw, fy + fh, fill="#0f0f0f", outline="")
        
        # Синяя рамка границ
        self.crop_canvas.create_rectangle(fx, fy, fx + fw, fy + fh, outline="#3b8ed0", width=3)
        
        # Вспомогательный текст, если картинка не загружена
        if not self.original_image:
            self.crop_canvas.create_text(200, 150, text="Нажмите 'Выбрать картинку'\nдля загрузки", fill="#555555", font=("Arial", 12, "bold"), justify="center")

    def on_drag_start(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def on_drag_motion(self, event):
        if not self.original_image: return
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        self.img_x += dx
        self.img_y += dy
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.draw_crop_canvas()

    def on_zoom(self, event):
        if not self.original_image: return
        factor = 1.1 if event.delta > 0 else 0.9
        new_scale = max(0.05, min(self.img_scale * factor, 10.0))
        
        # Приближение относительно центра холста
        cx, cy = 200, 150
        self.img_x = cx + (self.img_x - cx) * (new_scale / self.img_scale)
        self.img_y = cy + (self.img_y - cy) * (new_scale / self.img_scale)
        self.img_scale = new_scale
        
        self.zoom_slider.set(self.img_scale)
        self.draw_crop_canvas()

    def on_slider_zoom(self, value):
        if not self.original_image: return
        new_scale = float(value)
        cx, cy = 200, 150
        self.img_x = cx + (self.img_x - cx) * (new_scale / self.img_scale)
        self.img_y = cy + (self.img_y - cy) * (new_scale / self.img_scale)
        self.img_scale = new_scale
        self.draw_crop_canvas()

    def save_slot(self):
        """Обрезает картинку, сохраняет её в файл слота и обновляет метаданные."""
        if not self.original_image:
            messagebox.showwarning("Внимание", "Пожалуйста, сначала загрузите изображение.")
            return
            
        custom_name = self.name_entry.get().strip()
        custom_desc = self.desc_entry.get().strip()
        
        if not custom_name:
            messagebox.showwarning("Внимание", "Пожалуйста, введите название стикера для игры.")
            return

        cw, ch = 400, 300
        fw = self.target_w * self.crop_scale
        fh = self.target_h * self.crop_scale
        fx = (cw - fw) / 2
        fy = (ch - fh) / 2

        img_left = self.img_x - (self.original_image.width * self.img_scale) / 2
        img_top = self.img_y - (self.original_image.height * self.img_scale) / 2
        
        crop_left = (fx - img_left) / self.img_scale
        crop_top = (fy - img_top) / self.img_scale
        crop_right = (fx + fw - img_left) / self.img_scale
        crop_bottom = (fy + fh - img_top) / self.img_scale

        try:
            cropped = self.original_image.transform(
                (self.target_w, self.target_h), Image.EXTENT,
                data=(crop_left, crop_top, crop_right, crop_bottom), resample=Image.Resampling.BICUBIC
            )
            
            icon_dir = os.path.join("pikcher", "23icon")
            os.makedirs(icon_dir, exist_ok=True)
            out_path = os.path.join(icon_dir, self.current_slot)
            
            cropped.save(out_path, "PNG")
            
            # Обновление метаданных
            self.metadata[self.current_slot]["custom_name"] = custom_name
            self.metadata[self.current_slot]["custom_desc"] = custom_desc
            self.metadata[self.current_slot]["is_assigned"] = True
            
            with open(os.path.join("pikcher", "metadata.json"), 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
                
            self.draw_map()
            messagebox.showinfo("Успех", f"Слот {self.metadata[self.current_slot]['slot_letter']} успешно сохранен!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить изображение:\n{e}")

    def reset_slot(self):
        """Сбрасывает слот, удаляя картинку пользователя и очищая метаданные."""
        letter = self.metadata[self.current_slot]["slot_letter"]
        if not messagebox.askyesno("Подтверждение", f"Очистить слот {letter} и удалить кастомный стикер?"):
            return
            
        pic_path = os.path.join("pikcher", "23icon", self.current_slot)
        if os.path.exists(pic_path):
            try:
                os.remove(pic_path)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить файл:\n{e}")
                return
                
        # Сброс метаданных в исходное состояние
        from build_mod import loc_map
        orig_vals = loc_map.get(self.current_slot, ["Стикер", "Стикер из игры."])
        self.metadata[self.current_slot]["custom_name"] = orig_vals[0]
        self.metadata[self.current_slot]["custom_desc"] = orig_vals[1] if len(orig_vals) > 1 else "Пользовательский стикер."
        self.metadata[self.current_slot]["is_assigned"] = False
        
        with open(os.path.join("pikcher", "metadata.json"), 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
            
        self.original_image = None
        self.photo_image = None
        self.img_scale = 1.0
        
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, self.metadata[self.current_slot]["custom_name"])
        self.desc_entry.delete(0, "end")
        self.desc_entry.insert(0, self.metadata[self.current_slot]["custom_desc"])
        
        self.draw_map()
        self.draw_crop_canvas()
        messagebox.showinfo("Успех", f"Слот {letter} успешно очищен!")

    def export_profile(self):
        """Экспортирует всю текущую конфигурацию стикеров и текстов в ZIP-архив."""
        path = filedialog.asksaveasfilename(
            defaultextension=".zip",
            filetypes=[("ZIP-архив", "*.zip")],
            title="Экспортировать набор стикеров"
        )
        if not path:
            return
            
        try:
            metadata_path = os.path.join("pikcher", "metadata.json")
            icon_dir = os.path.join("pikcher", "23icon")
            
            if not os.path.exists(metadata_path):
                messagebox.showwarning("Внимание", "У вас нет сохраненных стикеров для экспорта.")
                return
                
            with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Добавляем metadata.json в корень архива
                zipf.write(metadata_path, "metadata.json")
                
                # Добавляем все изображения слотов
                if os.path.exists(icon_dir):
                    for f in os.listdir(icon_dir):
                        if f.startswith("Flag-") and f.endswith(".png"):
                            zipf.write(os.path.join(icon_dir, f), os.path.join("23icon", f))
                            
            messagebox.showinfo("Успех", f"Набор стикеров успешно экспортирован в:\n{path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать профиль:\n{e}")

    def import_profile(self):
        """Импортирует конфигурацию стикеров и текстов из ZIP-архива с заменой."""
        path = filedialog.askopenfilename(
            filetypes=[("ZIP-архив", "*.zip")],
            title="Импортировать набор стикеров"
        )
        if not path:
            return
            
        if not messagebox.askyesno("Подтверждение", "Импорт сотрет все текущие стикеры и тексты Студии. Продолжить?"):
            return
            
        try:
            temp_extract_dir = "temp_extract"
            if os.path.exists(temp_extract_dir):
                shutil.rmtree(temp_extract_dir)
            os.makedirs(temp_extract_dir)
            
            # Распаковка во временную папку
            with zipfile.ZipFile(path, 'r') as zipf:
                zipf.extractall(temp_extract_dir)
                
            temp_metadata = os.path.join(temp_extract_dir, "metadata.json")
            if not os.path.exists(temp_metadata):
                messagebox.showerror("Ошибка", "Выбранный ZIP-архив не является корректным профилем (отсутствует metadata.json).")
                shutil.rmtree(temp_extract_dir)
                return
                
            # Перенос файлов в рабочую папку
            metadata_path = os.path.join("pikcher", "metadata.json")
            icon_dir = os.path.join("pikcher", "23icon")
            
            # Копируем metadata.json
            shutil.copy(temp_metadata, metadata_path)
            
            # Очищаем старые стикеры Flag-*.png из папки 23icon перед импортом
            if os.path.exists(icon_dir):
                for f in os.listdir(icon_dir):
                    if f.startswith("Flag-") and f.endswith(".png"):
                        try:
                            os.remove(os.path.join(icon_dir, f))
                        except Exception:
                            pass
            else:
                os.makedirs(icon_dir, exist_ok=True)
                
            # Копируем новые картинки
            temp_icon_dir = os.path.join(temp_extract_dir, "23icon")
            if os.path.exists(temp_icon_dir):
                for f in os.listdir(temp_icon_dir):
                    src_file = os.path.join(temp_icon_dir, f)
                    dst_file = os.path.join(icon_dir, f)
                    shutil.copy(src_file, dst_file)
                    
            # Очистка временной директории
            shutil.rmtree(temp_extract_dir)
            
            # Перечитываем метаданные и перерисовываем интерфейс
            with open(metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
                
            self.select_slot(self.current_slot)
            self.draw_map()
            messagebox.showinfo("Успех", "Набор стикеров успешно импортирован!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось импортировать профиль:\n{e}")

    def open_mod_folder(self):
        """Открывает в проводнике Windows папку с готовым модом."""
        try:
            target_path = os.path.abspath(os.path.join("pikcher", "Сам_Мод"))
            os.makedirs(target_path, exist_ok=True)
            os.startfile(target_path)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть папку:\n{e}")

    def start_build(self):
        """Запускает процесс сборщика мода в отдельном потоке."""
        self.build_button.configure(state="disabled")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.insert("end", "Запуск сборщика мода...\n")
        
        class TextRedirector(object):
            def __init__(self, queue_callback):
                self.queue_callback = queue_callback
            def write(self, string):
                self.queue_callback(string)
            def flush(self):
                pass
        
        def run():
            import sys
            import build_mod
            
            old_stdout = sys.stdout
            sys.stdout = TextRedirector(self.queue_log)
            
            try:
                # Запускаем сборщик напрямую
                build_mod.main()
                self.after(0, self.prompt_save_mod)
            except Exception as e:
                self.queue_log(f"\n[ОШИБКА] Сборка завершилась с ошибкой: {str(e)}\n")
                self.after(0, lambda: messagebox.showerror("Ошибка", f"Не удалось собрать мод:\n{e}"))
            finally:
                sys.stdout = old_stdout
                self.after(0, lambda: self.build_button.configure(state="normal"))
                
        threading.Thread(target=run, daemon=True).start()

    def prompt_save_mod(self):
        """Предлагает пользователю сохранить собранный мод в его папку с игрой."""
        mod_path = os.path.join("pikcher", "Сам_Мод", "ZZZZ_NOPRIDE_P.pak")
        if not os.path.exists(mod_path):
            return
            
        target_file = filedialog.asksaveasfilename(
            defaultextension=".pak",
            initialfile="ZZZZ_NOPRIDE_P.pak",
            filetypes=[("Pak моды", "*.pak")],
            title="Выбери папку ~mods в игре для сохранения мода"
        )
        if target_file:
            try:
                shutil.copy(mod_path, target_file)
                self.queue_log(f"\n[УСПЕХ] Мод успешно сохранен в:\n{target_file}\n")
                messagebox.showinfo("Успех", f"Мод сохранен!\n\nНе забудь запустить игру.")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить мод:\n{e}")

    def queue_log(self, text):
        """Безопасная вставка лога в текстовое поле из фонового потока."""
        self.after(0, lambda: self.log_textbox.insert("end", text))
        self.after(0, lambda: self.log_textbox.see("end"))

if __name__ == '__main__':
    app = StickerStudio()
    app.mainloop()
