# -*- coding: utf-8 -*-
import os
import shutil
import glob
import subprocess
from PIL import Image

# Словарь координат в оригинальной текстуре-атласе (ширина ячейки 192px, высота 128px/256px)
# Ключ: имя оригинального PNG-файла -> Значение: (x, y, w, h)
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

# Карта строк локализации для замены (оригинальный русский текст -> новые стикеры)
loc_map = {
    'Flag-Abrosexual.png': ['Абросексуальный флаг', 'Флаг абросексуального сообщества.'],
    'Flag-Agender.png': ['Агендерный флаг', 'Флаг агендерного сообщества.'],
    'Flag-Asexual.png': ['Асексуальный флаг', 'Флаг асексуального сообщества.'],
    'Flag-BLM.png': ['Наклейка BLM'],
    'Flag-Bigender_Redesign.png': ['Бигендерный флаг', 'Флаг бигендерного сообщества.'],
    'Flag-Bisexual.png': ['Бисексуальный флаг', 'Флаг бисексуального сообщества.'],
    'Flag-Demisexual.png': ['Демисексуальный флаг', 'Флаг демисексуального сообщества.'],
    'Flag-Gay_Man.png': ['Флаг геев', 'Флаг сообщества транс-инклюзивных геев.'],
    'Flag-Genderfluid.png': ['Гендерфлюидный флаг', 'Флаг гендерфлюидного сообщества.'],
    'Flag-Genderflux.png': ['Флаг гендерфлакс', 'Флаг сообщества гендерфлакс.'],
    'Flag-Genderqueer.png': ['Флаг гендерквиров', 'Флаг гендерквирного сообщества.'],
    'Flag-Intersex.png': ['Интерсексуальный флаг', 'Флаг интерсексуального сообщества.'],
    'Flag-Lesbian_5_Stripe.png': ['Лесбийский флаг', 'Пятицветный флаг лесбийского сообщества.'],
    'Flag-Lgbtq.png': ['Радужный флаг', 'Классический радужный флаг.'],
    'Flag-Lgbtq_progress.png': ['Гордость прогресса', 'Флаг гордости прогресса.'],
    'Flag-Neutrois.png': ['Флаг нейтру', 'Флаг сообщества нейтру.'],
    'Flag-NonBinary.png': ['Небинарный флаг', 'Флаг небинарного сообщества.'],
    'Flag-Pangender.png': ['Пангендерный флаг', 'Флаг пангендерного сообщества.'],
    'Flag-Pansexual.png': ['Пансексуальный флаг', 'Флаг пансексуального сообщества.'],
    'Flag-Polysexual.png': ['Полисексуальный флаг', 'Флаг полисексуального сообщества.'],
    'Flag-Queer.png': ['Квир-флаг', 'Флаг квир-сообщества.'],
    'Flag-Straight_Ally.png': ['Наклейка гетеросексуального союзника', 'Продемонстрируйте союзничество.'],
    'Flag-Transgender.png': ['Трансгендерный флаг', 'Флаг трансгендерного сообщества.']
}

# Пути к файлам и инструментам
original_icons_dir = r"original_icons\PenDriverPro\Content\UI\Icons\00_Item_Icons\Collectibles\Illo_-_Stickers\Flags"
extracted_icons_dir = r"extracted\PenDriverPro\Content\UI\Icons\00_Item_Icons\Collectibles\Illo_-_Stickers\Flags"
steam_locres_path = r"Z:\SteamLibrary\steamapps\common\Pacific Drive\PenDriverPro\Content\Paks\pakchunk0-WindowsNoEditor\PenDriverPro\Content\Localization\Game\ru\Game.locres"
extracted_locres_path = r"extracted\PenDriverPro\Content\Localization\Game\ru\Game.locres"
atlas_uasset = r"extracted\PenDriverPro\Content\Gameplay\Inventory\Items\Car\Cosmetic\Bumper_Sticker\Materials\T_Flags_01_D.uasset"

texconv_exe = r".\texconv.exe"
dds_tools_python = r".\dds_tools\python\python.exe"
dds_tools_script = r".\dds_tools\src\main.py"
repak_exe = r".\repak.exe"

def run_command(args):
    """Вспомогательная функция для запуска внешних утилит."""
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"Ошибка при выполнении: {' '.join(args)}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        raise RuntimeError(f"Команда завершилась с ошибкой: {result.returncode}")
    return result.stdout

def encode_and_fit(text, target_len, encoding):
    """Кодирует строку и выравнивает/обрезает её строго под байтовую длину target_len."""
    encoded = text.encode(encoding)
    if len(encoded) <= target_len:
        # Дополняем пробелами в соответствующей кодировке
        pad_char = ' '
        pad_bytes = pad_char.encode(encoding)
        while len(encoded) + len(pad_bytes) <= target_len:
            encoded += pad_bytes
        # Если остался 1 лишний байт (для utf-16), дополняем нулем
        if len(encoded) < target_len:
            encoded += b'\x00' * (target_len - len(encoded))
        return encoded
    else:
        # Обрезаем посимвольно с конца, пока байтовая длина не станет <= target_len
        temp_str = text
        while len(temp_str.encode(encoding)) > target_len:
            temp_str = temp_str[:-1]
        encoded = temp_str.encode(encoding)
        # Дополняем остаток пробелами
        pad_char = ' '
        pad_bytes = pad_char.encode(encoding)
        while len(encoded) + len(pad_bytes) <= target_len:
            encoded += pad_bytes
        if len(encoded) < target_len:
            encoded += b'\x00' * (target_len - len(encoded))
        return encoded

def main():
    # Получаем отсортированные списки оригинальных иконок и картинок пользователя
    orig_pngs = sorted(glob.glob("original_pngs/*.png"))
    pics = sorted(glob.glob("pikcher/23icon/*"))

    if len(orig_pngs) != 23 or len(pics) != 23:
        print(f"Ошибка: Требуется ровно 23 файла. Найдено оригинальных: {len(orig_pngs)}, пользовательских: {len(pics)}")
        return

    # Шаг 1. Восстановление исходных файлов
    print("Восстанавливаем оригинальные UI-иконки из бэкапа...")
    if not os.path.exists(extracted_icons_dir):
        os.makedirs(extracted_icons_dir)
    for ext in ["*.uasset", "*.uexp"]:
        for f in glob.glob(os.path.join(original_icons_dir, ext)):
            shutil.copy(f, extracted_icons_dir)

    print("Копируем оригинальный Game.locres из папки игры...")
    os.makedirs(os.path.dirname(extracted_locres_path), exist_ok=True)
    shutil.copy(steam_locres_path, extracted_locres_path)

    # Шаг 2. Генерация нового полностью пустого атласа
    print("Создаем новый прозрачный атлас 1024x1024 (оригинальные флаги стерты)...")
    atlas = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))

    # Шаг 3. Обработка картинок пользователя для атласа и UI-иконок
    for orig_path, pic_path in zip(orig_pngs, pics):
        name = os.path.basename(orig_path)
        pic_name_no_ext = os.path.splitext(os.path.basename(pic_path))[0]
        
        if name not in mapping:
            print(f"Пропущено сопоставление координат для {name}")
            continue
            
        x, y, w, h = mapping[name]
        print(f"Обработка: {pic_name_no_ext} (для слота {name})...")

        # Открываем изображение пользователя
        pic = Image.open(pic_path).convert("RGBA")
        W_pic, H_pic = pic.size

        # Определяем физические размеры на кузове машины
        if name == 'Flag-BLM.png':
            W_poly, H_poly = 384, 436
            W_cell, H_cell = 192, 256
        else:
            W_poly, H_poly = 384, 229
            W_cell, H_cell = 192, 128

        # --- 3.1 Вставка в атлас ---
        # Вычисляем масштабирование на полигоне машины с сохранением пропорций
        scale_atlas = min(W_poly / W_pic, H_poly / H_pic)
        w_car = W_pic * scale_atlas
        h_car = H_pic * scale_atlas

        # Переносим размеры на сетку атласа
        w_cell_scaled = w_car * (W_cell / W_poly)
        h_cell_scaled = h_car * (H_cell / H_poly)

        # Вычисляем смещение центрирования
        offset_x_car = (W_poly - w_car) / 2
        offset_y_car = (H_poly - h_car) / 2
        offset_x_cell = offset_x_car * (W_cell / W_poly)
        offset_y_cell = offset_y_car * (H_cell / H_poly)

        new_w = int(round(w_cell_scaled))
        new_h = int(round(h_cell_scaled))
        ox = int(round(offset_x_cell))
        oy = int(round(offset_y_cell))

        # Масштабируем картинку для атласа
        pic_resized_atlas = pic.resize((new_w, new_h), Image.Resampling.LANCZOS)
        atlas.paste(pic_resized_atlas, (x + ox, y + oy), pic_resized_atlas)

        # --- 3.2 Генерация UI-иконки ---
        # Целевые размеры UI-иконки в меню
        W_target = 384
        H_target = 436 if name == 'Flag-BLM.png' else 229

        ui_img = Image.new("RGBA", (W_target, H_target), (0, 0, 0, 0))
        scale_ui = min(W_target / W_pic, H_target / H_pic)
        new_w_ui = int(round(W_pic * scale_ui))
        new_h_ui = int(round(H_pic * scale_ui))

        pic_resized_ui = pic.resize((new_w_ui, new_h_ui), Image.Resampling.LANCZOS)
        ox_ui = (W_target - new_w_ui) // 2
        oy_ui = (H_target - new_h_ui) // 2
        ui_img.paste(pic_resized_ui, (ox_ui, oy_ui), pic_resized_ui)

        # Сохраняем UI-иконку во временный файл
        temp_png = "temp.png"
        ui_img.save(temp_png)

        # Конвертируем UI-иконку в DDS
        run_command([texconv_exe, "-f", "B8G8R8A8_UNORM", "-m", "1", "-y", "-o", ".", temp_png])

        # Инжектируем DDS в uasset UI-иконки
        uasset_path = os.path.join(extracted_icons_dir, name.replace(".png", ".uasset"))
        run_command([dds_tools_python, dds_tools_script, uasset_path, "temp.dds", "--save_folder", os.path.dirname(uasset_path)])

    # Сохраняем атлас и конвертируем его
    print("Сохраняем атлас и конвертируем его в DDS...")
    atlas.save("T_Flags_01_D_mod.png")
    run_command([texconv_exe, "-f", "BC3_UNORM", "-m", "1", "-y", "-o", ".", "T_Flags_01_D_mod.png"])
    run_command([dds_tools_python, dds_tools_script, atlas_uasset, "T_Flags_01_D_mod.dds", "--save_folder", os.path.dirname(atlas_uasset)])

    # Шаг 4. Патч строк локализации в Game.locres
    print("Применяем патч локализации к Game.locres...")
    with open(extracted_locres_path, 'rb') as f:
        locres_data = f.read()

    patched_count = 0
    for orig_path, pic_path in zip(orig_pngs, pics):
        orig_name = os.path.basename(orig_path)
        pic_name = os.path.splitext(os.path.basename(pic_path))[0]
        
        if orig_name not in loc_map:
            continue
            
        for orig_str in loc_map[orig_name]:
            for encoding in ['utf-16-le', 'utf-8']:
                # Ищем оригинальную строку в разных регистрах
                for search_str in [orig_str, orig_str.upper()]:
                    search_bytes = search_str.encode(encoding)
                    if search_bytes in locres_data:
                        target_len = len(search_bytes)
                        replace_bytes = encode_and_fit(pic_name, target_len, encoding)
                        locres_data = locres_data.replace(search_bytes, replace_bytes)
                        patched_count += 1

    with open(extracted_locres_path, 'wb') as f:
        f.write(locres_data)
    print(f"Патч локализации завершен! Успешно изменено строк: {patched_count}")

    # Шаг 5. Упаковка пака с модом
    print("Упаковываем мод в NoPride_P.pak...")
    if os.path.exists("NoPride_P.pak"):
        os.remove("NoPride_P.pak")
    run_command([repak_exe, "pack", "extracted", "NoPride_P.pak"])

    # Шаг 6. Очистка временных файлов
    print("Очистка временных файлов...")
    for temp_file in ["temp.png", "temp.dds", "T_Flags_01_D_mod.png", "T_Flags_01_D_mod.dds"]:
        if os.path.exists(temp_file):
            os.remove(temp_file)

    print("Все шаги выполнены успешно! Мод собран в NoPride_P.pak.")

if __name__ == '__main__':
    main()
