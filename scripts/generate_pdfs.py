import os
from PIL import Image
import pillow_heif

# Регистрация HEIF/HEIC поддержки
pillow_heif.register_heif_opener()

# Форматы изображений, которые мы поддерживаем
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp", ".heic", ".heif"}

def is_image_file(filename):
    return os.path.splitext(filename.lower())[1] in IMAGE_EXTENSIONS

def load_image(path):
    ext = os.path.splitext(path.lower())[1]
    if ext in {".heic", ".heif"}:
        heif_file = pillow_heif.read_heif(path)
        return Image.frombytes(
            heif_file.mode,
            heif_file.size,
            heif_file.data,
            "raw"
        )
    else:
        return Image.open(path)

def main():
    base_dir = os.getcwd()

    # Идём по всем папкам лекций
    for folder in os.listdir(base_dir):
        full_path = os.path.join(base_dir, folder)
        if not os.path.isdir(full_path):
            continue

        # Пропускаем служебные папки
        if folder in ['scripts', '.git'] or folder.startswith('.'):
            continue

        # Проверяем наличие папки images внутри лекции
        images_folder_path = os.path.join(full_path, 'images')
        if not os.path.isdir(images_folder_path):
            print(f"Пропускаем {folder}: нет папки 'images'")
            continue

        # Список изображений внутри папки images
        try:
            images = [
                f for f in os.listdir(images_folder_path)
                if is_image_file(f)
            ]
        except FileNotFoundError:
            print(f"Папка images не найдена в {folder}")
            continue

        if not images:
            print(f"Пропускаем {folder}: нет изображений в папке 'images'")
            continue

        images.sort()  # Алфавитная сортировка

        loaded_images = []
        for img_name in images:
            img_path = os.path.join(images_folder_path, img_name)
            try:
                img = load_image(img_path)
                # Приведение к RGB — важно для PDF
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                loaded_images.append(img)
            except Exception as e:
                print(f"Ошибка чтения {img_path}: {e}")

        if not loaded_images:
            print(f"Пропускаем {folder}: не удалось загрузить изображения")
            continue

        # Имя PDF (сохраняем в папке лекции, а не в images)
        pdf_path = os.path.join(
            full_path,
            f"{folder}.pdf"
        )

        # Сохранение PDF (первое изображение + остальные)
        first_image = loaded_images[0]
        if len(loaded_images) == 1:
            first_image.save(pdf_path, "PDF")
        else:
            first_image.save(pdf_path, "PDF", save_all=True, append_images=loaded_images[1:])

        print(f"Создан PDF: {pdf_path} (из {len(loaded_images)} изображений)")

if __name__ == "__main__":
    main()