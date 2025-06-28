import argparse
from enum import StrEnum
from pathlib import Path

from PIL import Image, ImageOps
from treepoem import generate_barcode


class CodeType(StrEnum):
    BARCODE = 'barcode'
    QR_CODE = 'qr'


class BarcodeType(StrEnum):
    barcode = 'ean13'
    qr = 'qrcode'


def validate_number(number: str) -> str:
    if not (number.isdigit() and len(number) < 12):
        raise ValueError("Number must be digits only and less than 12 characters")
    return number


def validate_label(label: str) -> str:
    return label.replace(' ', '_')


def validate_image_type(image_type: str) -> str:
    if image_type not in list(CodeType):
        raise ValueError(f"ImageType must be one of: {[_.value for _ in CodeType]}.")
    return CodeType(image_type)


def create_barcode(image_type: str, number: str, label: str) -> Image.Image:
    barcode_image = generate_barcode(
        barcode_type=BarcodeType[image_type].value,
        data=number.zfill(12),  # Pad to 12 digits for EAN-13
        options=(
            {
                "includetext": True,
                "extratext": label or number,
            }
            | (
                {
                    "extratextsize": 6,
                    "extratextyalign": "below",
                }
                if image_type is CodeType.QR_CODE
                else {}
            )
        ),
        scale=2,
    )
    barcode_image = ImageOps.expand(barcode_image, border=10, fill="white")
    return barcode_image


def save_image(image: Image.Image, output_path: Path) -> None:
    image.save(output_path, "JPEG")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a barcode with a label")
    parser.add_argument("--number", "-n", required=True, help="Number for the barcode (less than 12 digits)")
    parser.add_argument("--label", "-l", default="", help="Label text to display below the barcode")
    parser.add_argument("--output", "-o", default=None, help="Output file name (default: <number>.jpg)")
    parser.add_argument("--type", "-t", default=CodeType.BARCODE, help=f"Image type ({[_.value for _ in CodeType]})")
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    try:
        number = validate_number(args.number)
        label = validate_label(args.label)
        image_type = validate_image_type(args.type)
        image = create_barcode(image_type, number, label)

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
