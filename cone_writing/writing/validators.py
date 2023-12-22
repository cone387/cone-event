import re

from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

COLOR_HEX_RE = "^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"
color_hex_validator = RegexValidator(
    re.compile(COLOR_HEX_RE),
    _("Enter a valid hex color, eg. #000000"),
    "invalid",
)


COLOR_HEXA_RE = "#([A-Fa-f0-9]{8}|[A-Fa-f0-9]{4})$"
color_hexa_validator = RegexValidator(
    re.compile(COLOR_HEXA_RE),
    _("Enter a valid hexa color, eg. #00000000"),
    "invalid",
)

COLOR_RGB_PATTERN = (
    # prefix and opening parenthesis
    r"^rgb\("
    # first number: red channel
    r"(\d{1,3})"
    # comma and optional space
    r",\s?"
    # second number: green channel
    r"(\d{1,3})"
    # comma and optional space
    r",\s?"
    # third number: blue channel
    r"(\d{1,3})"
    # closing parenthesis
    r"\)$"
)

color_rgb_validator = RegexValidator(
    re.compile(COLOR_RGB_PATTERN),
    _("Enter a valid rgb color, eg. rgb(128, 128, 128)"),
    "invalid",
)

COLOR_NAME_PATTERN = r"(red|green|blue|yellow|orange|black|white|gray|grey|purple|pink)"

color_name_validator = RegexValidator(
    re.compile(COLOR_NAME_PATTERN),
    _("Enter a valid color name, eg. red, green, blue, yellow, orange, black, white, gray, grey, purple, pink"),
    "invalid",
)


color_validator = RegexValidator(
    re.compile('(%s|%s|%s|%s)' % (COLOR_HEX_RE, COLOR_HEXA_RE, COLOR_RGB_PATTERN, COLOR_NAME_PATTERN)),
    _("Enter a valid color, eg. #000000, #00000000, rgb(128, 128, 128) or red etc."),
    "invalid",
)
