"""MilkLab Caption Generator (S1).

Usage:
    python caption_generator.py --menu "นมหมีฮอกไกโด" --n 3

Reads GOOGLE_API_KEY from env. Generates Thai captions for milk menu items.
"""

import argparse
import json
import os
import sys
from typing import Any

from dotenv import load_dotenv
from google import genai


PROMPT_TEMPLATE = """\
คุณคือ social media manager ของร้าน MilkLab° ร้านนมสดกลางคืน

ข้อมูลเมนู:
{menu_context}

จงเขียนแคปชั่นภาษาไทย 2 ถึง 3 ประโยคเพื่อโปรโมตเมนูนี้ โดยเป็นสไตล์ {style}

เงื่อนไข:
- โทนสนุก ใช้คำง่าย ใส่ emoji ได้
- ต้องมี call-to-action ปิดท้าย เช่น สั่งเลย หรือ ทักแชท
- ห้ามใช้ em dash
- คำแคปชั่นต้องไม่เกิน 280 ตัวอักษร
- ถ้าเป็นสไตล์ cute ให้หวานและน่ารัก
- ถ้าเป็นสไตล์ minimal ให้สั้นและเรียบง่าย
- ถ้าเป็นสไตล์ gen-z ให้เท่และคูลแบบเท่ๆ
"""


def _parse_menu_input(menu: str | dict[str, Any] | None) -> str | dict[str, Any]:
    """Parse CLI menu input, allowing either plain text or JSON objects."""
    if menu is None:
        return ""
    if isinstance(menu, dict):
        return menu
    if isinstance(menu, str):
        text = menu.strip()
        if not text:
            return ""
        if text.startswith("{") or text.startswith("["):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text
        return text
    return menu


def _build_menu_context(menu: str | dict[str, Any] | None) -> str:
    """Create a compact menu context block for the prompt."""
    parsed_menu = _parse_menu_input(menu)
    if isinstance(parsed_menu, dict):
        menu_data = parsed_menu.get("menu", parsed_menu)
        if not isinstance(menu_data, dict):
            return f"ชื่อเมนู: {parsed_menu}"

        name = menu_data.get("name") or menu_data.get(
            "title") or menu_data.get("menu")
        price = menu_data.get("price")
        ingredients = menu_data.get("ingredients", [])
        if isinstance(ingredients, str):
            ingredients = [ingredients]

        parts: list[str] = []
        if name:
            parts.append(f"ชื่อเมนู: {name}")
        if price is not None:
            parts.append(f"ราคา: {price} บาท")
        if ingredients:
            parts.append("ส่วนผสม: " + ", ".join(str(item)
                         for item in ingredients))
        return "\n".join(parts) if parts else "ชื่อเมนู: ไม่ระบุ"

    return f"ชื่อเมนู: {parsed_menu}" if parsed_menu else "ชื่อเมนู: ไม่ระบุ"


def generate_caption(
    menu: str | dict[str, Any] | None,
    api_key: str | None = None,
    max_attempts: int = 3,
    style: str = "cute",
) -> str:
    """Generate a Thai caption for the given milk menu item."""
    key = api_key or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("GOOGLE_API_KEY not set in env or argument")

    menu_context = _build_menu_context(menu)
    client = genai.Client(api_key=key)

    for _ in range(max_attempts):
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=PROMPT_TEMPLATE.format(
                menu_context=menu_context, style=style),
        )
        caption = (getattr(response, "text", None) or "").strip()
        if len(caption) <= 280:
            return caption

    return caption


def generate_captions(
    menu: str | dict[str, Any] | None,
    n: int = 1,
    api_key: str | None = None,
    styles: list[str] | None = None,
) -> list[str]:
    """Generate multiple captions for the same menu."""
    if n <= 0:
        return []

    count = max(n, len(styles or [])) if styles is not None else n
    style_list = styles or ["cute"] * count
    if len(style_list) < count:
        style_list = style_list + ["cute"] * (count - len(style_list))

    return [generate_caption(menu, api_key=api_key, style=style_list[index]) for index in range(count)]


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate Thai captions for MilkLab menu items")
    parser.add_argument(
        "--menu", help="Menu name or JSON object with name, price and ingredients")
    parser.add_argument("--n", type=int, default=3,
                        help="Number of captions to generate")
    return parser


def main() -> int:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args()

    menu = args.menu
    if not menu:
        menu = input("เมนูที่จะโปรโมต: ").strip()

    if not menu:
        print("กรุณาใส่ชื่อเมนู")
        return 1

    captions = generate_captions(menu, n=args.n, styles=[
                                 "cute", "minimal", "gen-z"][: args.n])
    print()
    for index, caption in enumerate(captions, start=1):
        if args.n > 1:
            print(f"[{index}] {caption}")
        else:
            print(caption)
    return 0


if __name__ == "__main__":
    sys.exit(main())
