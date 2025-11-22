import os
from PIL import Image, ImageOps
import pillow_heif

# Регистрация HEIF/HEIC поддержки
pillow_heif.register_heif_opener()

# Форматы изображений, которые мы поддерживаем
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp", ".heic", ".heif"}


def is_image_file(path: str) -> bool:
    """
    Проверяем, что это именно файл с нужным расширением,
    а не папка/левый объект.
    """
    if not os.path.isfile(path):
        return False
    ext = os.path.splitext(path.lower())[1]
    return ext in IMAGE_EXTENSIONS


def load_image(path: str) -> Image.Image:
    """
    Загружаем изображение, применяем EXIF-ориентацию,
    приводим к RGB, принудительно загружаем данные
    и возвращаем независимую копию.
    """
    ext = os.path.splitext(path.lower())[1]

    if ext in {".heic", ".heif"}:
        heif_file = pillow_heif.read_heif(path)
        img = Image.frombytes(
            heif_file.mode,
            heif_file.size,
            heif_file.data,
            "raw"
        )
    else:
        img = Image.open(path)

    # 1) Исправляем ориентацию по EXIF, чтобы PDF не получался повернутым
    img = ImageOps.exif_transpose(img)

    # 2) Приводим к RGB — важно для PDF и一致ности
    if img.mode != "RGB":
        img = img.convert("RGB")

    # 3) Принудительно загружаем данные (исключаем ленивую загрузку)
    img.load()

    # 4) Делаем независимую копию, чтобы при сохранении PDF
    #    Pillow не "переиспользовал" один и тот же буфер
    return img.copy()


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

        # Используем ТОЛЬКО подпапку 'images' внутри лекции.
        # Любые другие подпапки (в т.ч. original_images) игнорируются.
        images_folder_path = os.path.join(full_path, 'images')
        if not os.path.isdir(images_folder_path):
            print(f"Пропускаем {folder}: нет папки 'images'")
            continue

        # Список изображений (только файлы, без подпапок)
        try:
            images = [
                f for f in os.listdir(images_folder_path)
                if is_image_file(os.path.join(images_folder_path, f))
            ]
        except FileNotFoundError:
            print(f"Папка images не найдена в {folder}")
            continue

        if not images:
            print(f"Пропускаем {folder}: нет изображений в папке 'images'")
            continue

        # Алфавитная сортировка (без учёта регистра)
        images.sort(key=str.lower)

        loaded_images = []
        for img_name in images:
            img_path = os.path.join(images_folder_path, img_name)
            try:
                img = load_image(img_path)
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

        first_image = loaded_images[0]

        # Сохранение PDF (первое изображение + остальные)
        if len(loaded_images) == 1:
            first_image.save(pdf_path, "PDF")
        else:
            first_image.save(
                pdf_path,
                "PDF",
                save_all=True,
                append_images=loaded_images[1:]
            )

        print(f"Создан PDF: {pdf_path} (из {len(loaded_images)} изображений)")


if __name__ == "__main__":
    main()
