"""This module contains the Script class, which represents a script."""

import os
from pkg_resources import get_distribution  # type: ignore
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML  # type: ignore
from botcpdf.role import Role, RoleData  # type: ignore


class Script:
    """Represents a script."""

    char_types: dict[str, list[Role]] = {
        "townsfolk": [],
        "outsider": [],
        "minion": [],
        "demon": [],
    }
    first_night: dict[float, Role] = {}
    other_nights: dict[float, Role] = {}

    role_data: RoleData = RoleData()

    def __init__(self, title: str, script_data: dict):
        """Initialize a script."""
        self.title = title

        # we want to preserve the order of the characters
        # so we'll use a list instead of a set
        for char in script_data:
            self.add_char(char)

        # add meta roles to night instructions
        self.add_meta_roles()

    def add_meta_roles(self) -> None:
        """Add meta roles to the night instructions."""
        for role in self.role_data.get_first_night_meta_roles():
            self.first_night[role.first_night] = role

        for role in self.role_data.get_other_night_meta_roles():
            self.other_nights[role.other_night] = role

    def __repr__(self):
        repr_str = ""
        for char_type in self.char_types.items():
            repr_str += char_type
            for char in self.char_types[char_type]:
                repr_str += f"\t{char}"

        repr_str += f"first night: {self.sorted_first_night()}"
        repr_str += f"other nights: {self.sorted_other_nights()}"

        return repr_str

    def cleanup_id(self, char: dict) -> dict:
        """Cleanup the character ID."""

        # looking at other projects it seems that the ID in the script data is
        # _close_ to the ID in the role data
        # so we'll just do some cleanup to make it match
        char["id"] = char["id"].replace("_", "")
        char["id"] = char["id"].replace("-", "")  # just the pit-hag... why

        return char

    def sorted_first_night(self) -> list[Role]:
        """Return the first night characters in order."""
        return [self.first_night[i] for i in sorted(self.first_night.keys())]

    def sorted_other_nights(self) -> list[Role]:
        """Return the other night characters in order."""
        return [self.other_nights[i] for i in sorted(self.other_nights.keys())]

    def add_char(self, char: dict):
        """Add a character to the script."""
        char = self.cleanup_id(char)
        role = self.role_data.get_role(char["id"])

        # add to the appropriate list
        self.char_types[role.team].append(role)
        # if it's a first night character, add it to the first night list
        if role.first_night != 0:
            # if there's already a character in the slot, raise an error
            if role.first_night in self.first_night:
                raise ValueError(f"Duplicate first night character: {role.first_night}")

            self.first_night[role.first_night] = role

        # if it's an other night character, add it to the other night list
        if role.other_night != 0:
            # if there's already a character in the slot, raise an error
            if role.other_night in self.other_nights:
                raise ValueError(f"Duplicate other night character: {role.other_night}")

            self.other_nights[role.other_night] = role

    def render(self):
        """Render the script to PDF"""
        env = Environment(loader=FileSystemLoader("templates"))
        template = env.get_template("script.jinja")

        # so we can actually use images in the PDF
        this_folder = os.path.dirname(os.path.abspath(__file__))
        # use this_folder to get the path to the icons and templates folders
        icon_folder = os.path.abspath(os.path.join(this_folder, "..", "icons"))
        template_folder = os.path.abspath(os.path.join(this_folder, "..", "templates"))

        template_vars = {
            "_project": get_distribution("botc-json2pdf").__dict__,
            "title": self.title,
            "characters": self.char_types,
            "first_night": self.sorted_first_night(),
            "other_nights": self.sorted_other_nights(),
            "icon_folder": icon_folder,
            "template_folder": template_folder,
        }
        html_out = template.render(template_vars)

        # if we have BOTC_DEUG set...
        if os.environ.get("BOTC_DEBUG"):
            # write the rendered HTML to a file
            with open(f"{self.title}.html", "w", encoding="utf-8") as fhandle:
                fhandle.write(html_out)

        # convert the HTML to PDF
        pdf_folder = os.path.abspath(os.path.join(this_folder, "..", "pdfs"))
        # if pdf_folder doesn't exist, create it
        if not os.path.exists(pdf_folder):
            os.makedirs(pdf_folder)
        # save the PDF in the pdfs folder
        HTML(string=html_out).write_pdf(
            os.path.join(pdf_folder, f"{self.title}.pdf"),
            stylesheets=["templates/style.css"],
            optimize_size=(),
        )
