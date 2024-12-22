from PIL import Image
import os
import concurrent.futures


def process_image(file_path: str) -> None:
    """Process a single image file by resaving it.

    Args:
        file_path (str): Path to the image file
    """
    try:
        # Open and resave image
        with Image.open(file_path) as img:
            img.save(file_path, quality=95, optimize=True)
    except Exception as e:
        print(f"Error processing {os.path.basename(file_path)}: {str(e)}")


def fix_image_size(folder_path: str, max_workers: int = 10) -> None:
    """Fix image size issue for pandoc by resaving images in the folder using multiple threads.

    Args:
        folder_path (str): Path to the folder containing images
        max_workers (int, optional): Maximum number of worker threads. Defaults to 4.
    """
    # Check if folder exists
    if not os.path.exists(folder_path):
        print(f"Error: Folder {folder_path} does not exist")
        return

    # Get all files in folder
    files = os.listdir(folder_path)

    # Common image extensions
    img_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]

    # Get list of image files to process
    image_files = [
        os.path.join(folder_path, file)
        for file in files
        if any(file.lower().endswith(ext) for ext in img_extensions)
    ]

    # Process images in parallel using ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(process_image, image_files)
