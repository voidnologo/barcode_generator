import argparse
import base64
from io import BytesIO
from pathlib import Path

import jinja2
from PIL import Image

import barcode
from barcode.writer import ImageWriter


class NoTextImageWriter(ImageWriter):
    def draw_text(self, text, text_box):
        # Override the draw_text method to do nothing, effectively removing the text
        pass


def validate_number(number: str) -> int:
    if not (number.isdigit() and len(number) == 7):
        raise ValueError("Number must be exactly 7 digits")
    return int(number)


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


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a barcode with a label")
    parser.add_argument("--number", "-n", required=True, help="7-digit number to start the sequence for the barcodes.")
    parser.add_argument("--label", "-l", default="Demo", help="Label text to display above the barcode")
    parser.add_argument("--output", "-o", default=None, help="Output file name (default: <number>.jpg)")
    return parser.parse_args()


def render_jinja(data):
    template_loader = jinja2.FileSystemLoader(searchpath="./")
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template("barcode_template.html")
    html_output = template.render(barcodes=data)

    return html_output


def main() -> None:
    args = parse_arguments()

    try:
        number = validate_number(args.number)
        label = args.label
        data = []
        n = number
        for i in range(1, 5):
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
