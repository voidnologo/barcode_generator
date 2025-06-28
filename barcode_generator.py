import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import barcode
from barcode.writer import ImageWriter


def validate_number(number: str) -> str:
    if not (number.isdigit() and len(number) == 6):
        raise ValueError("Number must be exactly 6 digits")
    return number


def create_barcode(number: str) -> Image.Image:
    ean = barcode.get_barcode_class("ean13")
    # Pad the number with leading zeros to a total length of 12 digits for EAN-13
    padded_number = number.zfill(12)
    padded_number = f"000000{number}"
    barcode_instance = ean(padded_number, writer=ImageWriter())
    return barcode_instance.render()


def add_label(image: Image.Image, label: str, font_size: int = 20) -> Image.Image:
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    # Calculate text size using textbbox
    text_bbox = draw.textbbox((0, 0), label, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # Create new image with space for label
    new_height = image.height + text_height + 10
    new_image = Image.new("RGB", (image.width, new_height), "white")
    new_image.paste(image, (0, 0))

    # Draw label centered below barcode
    draw = ImageDraw.Draw(new_image)
    text_x = (image.width - text_width) // 2
    text_y = image.height + 5
    draw.text((text_x, text_y), label, font=font, fill="black")

    return new_image


def save_image(image: Image.Image, output_path: Path) -> None:
    image.save(output_path, "JPEG")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a barcode with a label")
    parser.add_argument("--number", "-n", required=True, help="6-digit number for the barcode")
    parser.add_argument("--label", "-l", required=False, help="Label text to display below the barcode")
    parser.add_argument("--output", "-o", default=None, help="Output file name (default: <number>.jpg)")
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    try:
        number = validate_number(args.number)
        image = create_barcode(number)
        if args.label:
            image = add_label(image, args.label)

        output_path = Path(args.output or f"{number}.jpg")
        save_image(image, output_path)
        print(f"Barcode saved to {output_path}")

    except ValueError as e:
        print(f"Error: {e}")
        exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
