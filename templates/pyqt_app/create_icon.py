"""
Generate template app icon with single "T" letter.
Uses same Electric Coral orange color as C3 (#FF6B35).
"""

from PIL import Image, ImageDraw, ImageFont
import os


def create_template_icon(size=512, letter="T"):
    """
    Create app icon with single letter and Electric Coral accent.

    Args:
        size: Icon size in pixels (default: 512)
        letter: Letter to display (default: "T")
    """
    # Create image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Colors from C3 theme (Electric Coral)
    bg_color = (255, 107, 53, 255)  # ACCENT_500: #FF6B35
    text_color = (237, 232, 220, 255)  # LIGHT_BG: #EDE8DC
    border_color = (229, 90, 43, 255)  # ACCENT_600: #E55A2B

    # Draw rounded rectangle background
    margin = size // 10
    border_width = size // 30

    # Draw border
    draw.rounded_rectangle(
        [(margin, margin), (size - margin, size - margin)],
        radius=size // 8,
        fill=border_color
    )

    # Draw inner background
    draw.rounded_rectangle(
        [(margin + border_width, margin + border_width),
         (size - margin - border_width, size - margin - border_width)],
        radius=size // 8 - border_width,
        fill=bg_color
    )

    # Draw letter
    try:
        # Try to use a bold system font
        font_size = size // 2
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        # Fallback to default font
        font = ImageFont.load_default()

    text = letter

    # Get text bounding box for centering
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Center the text
    text_x = (size - text_width) // 2 - bbox[0]
    text_y = (size - text_height) // 2 - bbox[1]

    # Draw text
    draw.text((text_x, text_y), text, fill=text_color, font=font)

    return img


if __name__ == "__main__":
    # Create icons directory if it doesn't exist
    os.makedirs("icons", exist_ok=True)

    # Generate icons in multiple sizes
    sizes = [16, 32, 64, 128, 256, 512]

    for size in sizes:
        icon = create_template_icon(size)
        filename = f"icons/app_icon_{size}.png"
        icon.save(filename, "PNG")
        print(f"Created {filename}")

    # Create main icon (512px)
    icon = create_template_icon(512)
    icon.save("icons/app_icon.png", "PNG")
    icon.save("app_icon.png", "PNG")  # Also save in root for easy access
    print("Created icons/app_icon.png (main icon)")
    print("Created app_icon.png (template root)")

    print("\n✓ Icon generation complete!")
    print("\nTo customize for your app:")
    print("  python3 create_icon.py")
    print("  # Or generate with custom letter:")
    print("  # icon = create_template_icon(512, letter='X')")
