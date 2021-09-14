# Image manipulation
from pathlib import Path

from PIL import Image


def mass_convert_images():
    """ Convert all .jpg images to .png """
    images_folder = Path(__file__).parent.parent.parent / 'images'
    for file_path in images_folder.iterdir():
        if file_path.suffix != '.jpg':
            continue
        file_name = file_path.stem
        output_path = file_path.parent / (file_name + '.png')

        im = Image.open(file_path)
        im.save(output_path)
