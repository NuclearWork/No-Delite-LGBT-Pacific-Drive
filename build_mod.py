# -*- coding: utf-8 -*-
import os
import shutil
import glob
import subprocess
import json
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

SLOTS_ORDERED = sorted(mapping.keys())

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
    'Flag-Pansexual.png': ['Pansexual flag', 'Пансексуальный флаг', 'Флаг пансексуального сообщества.'], # Добавлено оригинальное имя на всякий случай
    'Flag-Polysexual.png': ['Полисексуальный флаг', 'Флаг полисексуального сообщества.'],
    'Flag-Queer.png': ['Квир-флаг', 'Флаг квир-сообщества.'],
    'Flag-Straight_Ally.png': ['Наклейка гетеросексуального союзника', 'Продемонстрируйте союзничество.'],
    'Flag-Transgender.png': ['Трансгендерный флаг', 'Флаг трансгендерного сообщества.']
}

# Вспомогательное сопоставление для пансексуалов (оригинальный скрипт мог содержать опечатку)
if 'Flag-Pansexual.png' not in loc_map:
    loc_map['Flag-Pansexual.png'] = ['Пансексуальный флаг', 'Флаг пансексуального сообщества.']
else:
    # Переопределяем для унификации
    loc_map['Flag-Pansexual.png'] = ['Пансексуальный флаг', 'Флаг пансексуального сообщества.']

# Пути к файлам и инструментам
original_icons_dir = r"original_icons\PenDriverPro\Content\UI\Icons\00_Item_Icons\Collectibles\Illo_-_Stickers\Flags"
extracted_icons_dir = r"extracted\PenDriverPro\Content\UI\Icons\00_Item_Icons\Collectibles\Illo_-_Stickers\Flags"
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
        print(f"Ошибка при выполнении: {' '.join(args)}", flush=True)
        print(f"Stdout: {result.stdout}", flush=True)
        print(f"Stderr: {result.stderr}", flush=True)
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

def migrate_if_needed():
    """Проводит автоматическую миграцию старых кастомных файлов, если они есть."""
    pikcher_dir = "pikcher"
    icon_dir = os.path.join(pikcher_dir, "23icon")
    metadata_path = os.path.join(pikcher_dir, "metadata.json")
    
    if not os.path.exists(pikcher_dir):
        os.makedirs(pikcher_dir)
    if not os.path.exists(icon_dir):
        os.makedirs(icon_dir)
        
    # Если метаданные уже созданы, просто загружаем их
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass

    # Сканируем папку 23icon на предмет кастомных (старых) картинок
    all_files = [f for f in os.listdir(icon_dir) if os.path.isfile(os.path.join(icon_dir, f))]
    custom_files = [f for f in all_files if not f.startswith("Flag-")]
    
    metadata = {}
    
    # Инициализация дефолтной структуры метаданных
    for i, slot in enumerate(SLOTS_ORDERED):
        letter = chr(65 + i)
        orig_vals = loc_map.get(slot, ["Стикер", "Стикер из игры."])
        orig_name = orig_vals[0]
        orig_desc = orig_vals[1] if len(orig_vals) > 1 else "Пользовательский стикер."
        metadata[slot] = {
            "slot_letter": letter,
            "custom_name": orig_name,
            "custom_desc": orig_desc,
            "is_assigned": False
        }
        
    # Если найдено ровно 23 старых файла, запускаем миграцию
    if len(custom_files) == 23:
        print("Обнаружено 23 кастомных файла в 23icon. Запуск автоматической миграции...", flush=True)
        custom_files_sorted = sorted(custom_files)
        backup_dir = os.path.join(pikcher_dir, "backup_migrated")
        os.makedirs(backup_dir, exist_ok=True)
        
        for slot, custom_file in zip(SLOTS_ORDERED, custom_files_sorted):
            src_path = os.path.join(icon_dir, custom_file)
            dst_path = os.path.join(icon_dir, slot)
            
            try:
                # Конвертируем в PNG и сохраняем по слоту
                img = Image.open(src_path).convert("RGBA")
                img.save(dst_path, "PNG")
                
                # Старое имя файла пишем как название наклейки
                name_without_ext = os.path.splitext(custom_file)[0]
                metadata[slot]["custom_name"] = name_without_ext
                metadata[slot]["custom_desc"] = "Пользовательский стикер."
                metadata[slot]["is_assigned"] = True
                
                # Перемещаем оригинал в бэкап
                shutil.move(src_path, os.path.join(backup_dir, custom_file))
            except Exception as e:
                print(f"Ошибка миграции файла {custom_file}: {e}", flush=True)
                
        print(f"Миграция успешно завершена! Оригиналы сохранены в: {backup_dir}", flush=True)
    else:
        # Проверяем, есть ли уже файлы с названиями слотов Flag-*.png
        for slot in SLOTS_ORDERED:
            path = os.path.join(icon_dir, slot)
            if os.path.exists(path):
                metadata[slot]["is_assigned"] = True

    # Сохраняем файл метаданных
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
        
    return metadata

def main():
    print("[STAGE 1/6] Запуск миграции и инициализация метаданных...", flush=True)
    metadata = migrate_if_needed()
    
    # Восстановление исходных файлов
    print("[STAGE 2/6] Восстановление оригинальных UI-иконки из бэкапа...", flush=True)
    if not os.path.exists(extracted_icons_dir):
        os.makedirs(extracted_icons_dir)
    for ext in ["*.uasset", "*.uexp"]:
        for f in glob.glob(os.path.join(original_icons_dir, ext)):
            shutil.copy(f, extracted_icons_dir)

    # Восстанавливаем Game.locres из Game_original.locres (если есть, иначе оставляем текущий)
    print("Восстанавливаем оригинальный Game.locres...", flush=True)
    orig_locres = extracted_locres_path.replace("Game.locres", "Game_original.locres")
    if os.path.exists(orig_locres):
        shutil.copy(orig_locres, extracted_locres_path)
    else:
        print("Внимание: Game_original.locres не найден. Если это первый запуск, то всё ОК, но если вы уже собирали мод, строки могут не обновиться.", flush=True)

    # Генерация нового пустого прозрачного атласа
    print("[STAGE 3/6] Создаем прозрачный атлас 1024x1024 (оригинальные pride-флаги удалены)...", flush=True)
    atlas = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))

    icon_dir = os.path.join("pikcher", "23icon")

    # Обработка картинок пользователя для атласа и UI-иконок
    print("[STAGE 4/6] Обработка слотов стикеров...", flush=True)
    for slot_name in SLOTS_ORDERED:
        x, y, w, h = mapping[slot_name]
        pic_path = os.path.join(icon_dir, slot_name)
        is_assigned = metadata.get(slot_name, {}).get("is_assigned", False) and os.path.exists(pic_path)
        
        # Размеры ячейки
        if slot_name == 'Flag-BLM.png':
            W_cell, H_cell = 192, 256
        else:
            W_cell, H_cell = 192, 128

        # Целевые размеры UI-иконки в меню игры
        W_target = 384
        H_target = 436 if slot_name == 'Flag-BLM.png' else 229

        ui_img = Image.new("RGBA", (W_target, H_target), (0, 0, 0, 0))

        if is_assigned:
            print(f"Обработка слота {metadata[slot_name]['slot_letter']} ({slot_name})...", flush=True)
            pic = Image.open(pic_path).convert("RGBA")
            W_pic, H_pic = pic.size

            # 1. Вставка в атлас
            if W_pic == W_cell and H_pic == H_cell:
                # Если картинка подготовлена студией с точным разрешением
                atlas.paste(pic, (x, y), pic)
            else:
                # Автоматический кроп для неидеальных размеров
                padding_x = int(W_cell * 0.05)
                padding_y = int(H_cell * 0.05)
                target_w = W_cell - padding_x * 2
                target_h = H_cell - padding_y * 2
                
                scale_to_fill = max(target_w / W_pic, target_h / H_pic)
                w_scaled = int(round(W_pic * scale_to_fill))
                h_scaled = int(round(H_pic * scale_to_fill))
                
                pic_scaled = pic.resize((w_scaled, h_scaled), Image.Resampling.LANCZOS)
                
                left = (w_scaled - target_w) / 2
                top = (h_scaled - target_h) / 2
                right = (w_scaled + target_w) / 2
                bottom = (h_scaled + target_h) / 2
                
                pic_cropped = pic_scaled.crop((left, top, right, bottom))
                atlas.paste(pic_cropped, (x + padding_x, y + padding_y), pic_cropped)

            # 2. Вставка в UI-иконку
            scale_ui = min(W_target / W_pic, H_target / H_pic)
            new_w_ui = int(round(W_pic * scale_ui))
            new_h_ui = int(round(H_pic * scale_ui))
            pic_resized_ui = pic.resize((new_w_ui, new_h_ui), Image.Resampling.LANCZOS)
            ox_ui = (W_target - new_w_ui) // 2
            oy_ui = (H_target - new_h_ui) // 2
            ui_img.paste(pic_resized_ui, (ox_ui, oy_ui), pic_resized_ui)
        else:
            # Слот пуст. Оставляем его прозрачным в атласе.
            # UI-иконка также останется пустой (прозрачной)
            pass

        # Сохраняем UI-иконку
        temp_png = "temp.png"
        ui_img.save(temp_png)

        # Конвертируем UI-иконку в DDS
        run_command([texconv_exe, "-f", "B8G8R8A8_UNORM", "-m", "1", "-y", "-o", ".", temp_png])

        # Инжектируем DDS в uasset UI-иконки
        uasset_path = os.path.join(extracted_icons_dir, slot_name.replace(".png", ".uasset"))
        run_command([dds_tools_python, dds_tools_script, uasset_path, "temp.dds", "--save_folder", os.path.dirname(uasset_path)])

    # Сохраняем атлас и конвертируем его
    print("Сохраняем новый атлас и конвертируем в DDS...", flush=True)
    atlas.save("T_Flags_01_D_mod.png")
    run_command([texconv_exe, "-f", "BC3_UNORM", "-y", "-o", ".", "T_Flags_01_D_mod.png"])
    run_command([dds_tools_python, dds_tools_script, atlas_uasset, "T_Flags_01_D_mod.dds", "--save_folder", os.path.dirname(atlas_uasset)])

    # Шаг 4. Патч строк локализации в Game.locres
    print("[STAGE 5/6] Применяем патч локализации к Game.locres...", flush=True)
    with open(extracted_locres_path, 'rb') as f:
        locres_data = f.read()

    patched_count = 0
    for slot_name in SLOTS_ORDERED:
        if slot_name not in loc_map:
            continue
            
        is_assigned = metadata.get(slot_name, {}).get("is_assigned", False)
        
        # Получаем новые строки локализации
        if is_assigned:
            new_name = metadata[slot_name].get("custom_name", "Стикер")
            new_desc = metadata[slot_name].get("custom_desc", "Пользовательский стикер.")
        else:
            new_name = "Пустой слот"
            new_desc = "Стикер удален."

        orig_strs = loc_map[slot_name]
        
        for idx, orig_str in enumerate(orig_strs):
            new_val = new_name if idx == 0 else new_desc
            
            for encoding in ['utf-16-le', 'utf-8']:
                for search_str in [orig_str, orig_str.upper()]:
                    search_bytes = search_str.encode(encoding)
                    if search_bytes in locres_data:
                        target_len = len(search_bytes)
                        replace_bytes = encode_and_fit(new_val, target_len, encoding)
                        locres_data = locres_data.replace(search_bytes, replace_bytes)
                        patched_count += 1

    with open(extracted_locres_path, 'wb') as f:
        f.write(locres_data)
    print(f"Патч локализации завершен! Успешно изменено строк: {patched_count}", flush=True)

    # Шаг 5. Упаковка пака с модом
    mod_name = "ZZZZ_NOPRIDE_P.pak"
    print(f"[STAGE 6/6] Упаковываем мод в {mod_name}...", flush=True)
    if os.path.exists(mod_name):
        os.remove(mod_name)
    
    ubulk_path = atlas_uasset.replace(".uasset", ".ubulk")
    if os.path.exists(ubulk_path):
        os.remove(ubulk_path)
        print("Удален неиспользуемый файл ubulk перед упаковкой.", flush=True)

    run_command([repak_exe, "pack", "extracted", mod_name])

    # Копирование собранного пака в папку "Сам_Мод" для релиза/гитхаба
    sam_mod_dir = "Сам_Мод"
    if os.path.exists(sam_mod_dir):
        shutil.copy(mod_name, os.path.join(sam_mod_dir, mod_name))
        print(f"Копия мода сохранена в папку {sam_mod_dir}", flush=True)

    # Очищаем старые файлы в локальной папке перед завершением
    pass
    # Генерация документации для GitHub
    print("Генерация документации для GitHub...", flush=True)
    docs_dir = "docs"
    os.makedirs(docs_dir, exist_ok=True)
    
    readme_content = """# Pacific Drive: No Pride Mod (Custom Stickers)

Этот мод заменяет все 23 радужных стикера и наклейки (LGBTQ+) в игре Pacific Drive на пользовательские мемы и картинки.

## Особенности
- Полностью удаляет оригинальные текстуры ЛГБТ-флагов из атласа игры (используется чистый холст).
- Заменяет UI-иконки в меню кастомизации на ваши собственные картинки.
- Изменяет локализацию (русские названия и описания) в меню кастомизации под названия ваших файлов.
- Автоматически собирает мод в формате `.pak` с наивысшим приоритетом (`zzzz_NoPride_P.pak`), чтобы предотвратить конфликты с другими модами.

## Как использовать мод
1. Скачайте файл `zzzz_NoPride_P.pak` из релизов.
2. Переместите его в папку модов игры:
   `[Папка_Steam]\\steamapps\\common\\Pacific Drive\\PenDriverPro\\Content\\Paks\\~mods\\`
3. Запустите игру и наслаждайтесь новыми наклейками в меню кастомизации автомобиля!

## Для разработчиков (Как собрать мод самому)
Если вы хотите использовать свои собственные картинки:
1. Используйте `NoPrideStudio.exe` для загрузки картинок по слотам (от A до W).
2. Запустите сборку прямо из Студии или с помощью `python build_mod.py`.
3. Скрипт автоматически обновит локализацию, атлас и упакует в готовый пак модов!
"""
    with open(os.path.join(docs_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    print("Документация сгенерирована (README.md).", flush=True)

    # Очистка временных файлов
    print("Очистка временных файлов...", flush=True)
    for temp_file in ["temp.png", "temp.dds", "T_Flags_01_D_mod.png", "T_Flags_01_D_mod.dds"]:
        if os.path.exists(temp_file):
            os.remove(temp_file)

    print("Все шаги выполнены успешно! Мод собран в ZZZZ_NOPRIDE_P.pak.", flush=True)

if __name__ == '__main__':
    main()
