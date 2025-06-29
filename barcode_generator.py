import argparse
import base64
import json
import random
from io import BytesIO
from pathlib import Path

import barcode
import jinja2
from barcode.writer import ImageWriter
from PIL import Image

DATA_STORE_LOCATION = 'data_store.json'


def validate_number(number: str | None, customer_id: str) -> int:
    used_numbers = used_numbers_by_customer_id(customer_id)
    smallest = min(used_numbers) if used_numbers else None
    if number is None:
        if smallest is None:
            return random.randint(4444444, 9999999)
        return smallest - 1
    if not (number.isdigit() and len(number) == 7):
        raise ValueError("Number must be exactly 7 digits")
    number = int(number)
    if number in used_numbers:
        raise ValueError(f"Number has already been used. Choose a number smaller than {smallest}.")
    return number


def create_barcode(number: str) -> Image.Image:
    ean = barcode.get_barcode_class("ean13")
    # Pad the number with leading zeros to a total length of 12 digits for EAN-13
    padded_number = str(number).zfill(12)
    barcode_instance = ean(padded_number, writer=ImageWriter())
    barcode_img = barcode_instance.render()
    return _remove_rendered_number(barcode_img)


def _remove_rendered_number(barcode_img):
    # Crop the image to remove the text underneath
    # Assuming the barcode bars are in the top portion and text is below
    # Adjust the crop box (left, top, right, bottom) based on your image
    # This is an estimate; you may need to adjust these values
    barcode_height = barcode_img.height
    barcode_width = barcode_img.width
    # Crop to keep only the top portion (barcode bars)
    crop_box = (0, 0, barcode_width, barcode_height * 0.7)  # Adjust 0.7 to fit your barcode height
    cropped_img = barcode_img.crop(crop_box)
    return cropped_img


def save_image(rendered_template: str, output_path: Path) -> None:
    with open(output_path, "w") as f:
        f.write(rendered_template)


def render_jinja(data):
    template_loader = jinja2.FileSystemLoader(searchpath="./")
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template("barcode_template.html")
    html_output = template.render(barcodes=data)

    return html_output


def get_data_store():
    try:
        with open(Path(DATA_STORE_LOCATION)) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def used_numbers_by_customer_id(customer_id):
    data = get_data_store()
    return set(data.get(customer_id, []))


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a barcode with a label")
    parser.add_argument("--number", "-n", default=None, help="7-digit number to start the sequence for the barcodes.")
    parser.add_argument("--label", "-l", default="Demo", help="Label text to display above the barcode")
    parser.add_argument("--output", "-o", default=None, help="Output file name (default: <number>.jpg)")
    parser.add_argument("--customer-id", "-c", required=True, help="Customer ID")
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    try:
        number = validate_number(args.number, args.customer_id)
        label = args.label
        data = []
        n = number
        for i in (1, 2, 2, 3):
            barcode_image = create_barcode(n)
            image_io = BytesIO()
            barcode_image.save(image_io, format="PNG")
            image_data = base64.b64encode(image_io.getvalue()).decode("utf-8")
            data.append((f"{label} {i}", n, image_data))
            n -= 1

        rendered = render_jinja(data)

        output_path = Path(args.output or f"{number}.html")
        save_image(rendered, output_path)
        print(f"Barcode saved to {output_path}")

    except ValueError as e:
        print(f"Error: {e}")
        exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
