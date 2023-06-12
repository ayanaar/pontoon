"""
Parser for the xliff translation format.
"""
from lxml import etree
from translate.storage import xliff
import copy

from pontoon.sync.exceptions import ParseError, SyncError
from pontoon.sync.formats.base import ParsedResource
from pontoon.sync.vcs.models import VCSTranslation


class XLIFFEntity(VCSTranslation):
    """
    Interface for modifying a single entity in an xliff file.
    """

    def __init__(
        self,
        key,
        context,
        source_string,
        source_string_plural,
        strings,
        comments=None,
        order=None,
    ):
        super().__init__(
            key=key,
            context=context,
            source_string=source_string,
            source_string_plural=source_string_plural,
            strings=strings,
            comments=comments or [],
            fuzzy=False,
            order=order,
        )

    def __repr__(self):
        return f"<XLIFFEntity {self.key}>"


class XLIFFResource(ParsedResource):
    def __init__(self, path, locale, source_resource=None):
        self.path = path
        self.locale = locale
        self.source_resource = source_resource
        self.entities = {}

        # Copy entities from the source_resource if it's available.
        if source_resource:
            for key, entity in source_resource.entities.items():
                self.entities[key] = XLIFFEntity(
                    entity.key, "", "", "", {}, copy.copy(entity.comments), entity.order
                )

        # Open the file at the provided path
        with open(path) as f:
            # Read the contents of the file and encode it
            xml = f.read().encode("utf-8")

            try:
                # Parse the xml content of the file into an XLIFF file object
                self.xliff_file = xliff.xlifffile(xml)
            except etree.XMLSyntaxError as err:
                # If there is an error parsing the file, raise a ParseError
                raise ParseError(f"Failed to parse {path}: {err}")

            # Loop through each unit in the XLIFF file
            for order, unit in enumerate(self.xliff_file.units):
                # Get the unit's ID and source string
                key = unit.getid()
                context = unit.xmlelement.get("id")
                source_string = str(unit.rich_source[0])
                source_string_plural = ""

                # Get the translated string for the unit. If there's no target string, this will be an empty dictionary
                target_string = (
                    str(unit.get_rich_target()[0]) if unit.get_rich_target() else None
                )
                strings = {None: target_string} if target_string else {}

                # Get the unit's comments, split by newline characters
                comments = unit.getnotes().split("\n") if unit.getnotes() else []

                # Create a new XLIFFEntity from the unit
                entity = XLIFFEntity(
                    key,
                    context,
                    source_string,
                    source_string_plural,
                    strings,
                    comments,
                    order,
                )
                # Add the entity to the entities dictionary using its key as the dictionary key
                self.entities[entity.key] = entity

    @property
    def translations(self):
        return sorted(self.entities.values(), key=lambda e: e.order)

    def save(self, locale):
        if not self.source_resource:
            raise SyncError(
                "Cannot save XLIFF resource {}: No source resource given.".format(
                    self.path
                )
            )
        # Open the file at the provided path
        with open(self.source_resource.path) as f:
            # Read the contents of the file and encode it
            xml = f.read().encode("utf-8")

            try:
                # Parse the xml content of the file into an XLIFF file object
                self.xliff_file = xliff.xlifffile(xml)
            except etree.XMLSyntaxError as err:
                # If there is an error parsing the file, raise a ParseError
                raise ParseError(f"Failed to parse {self.source_resource.path}: {err}")

            # Loop through each unit in the XLIFF file
            for order, unit in enumerate(self.xliff_file.units):
                # Apply any changes made to this object to the backing unit in the xliff file.
                key = unit.getid()
                entity = self.entities.get(key)
                if None in entity.strings:
                    # Store updated nodes
                    xml = unit.xmlelement
                    target = xml.find(unit.namespaced("target"))

                    # If there's no existing target, create a new one
                    if target is None:
                        target = etree.SubElement(xml, unit.namespaced("target"))
                    unit.settarget(entity.strings[None])

                else:
                    # Read stored nodes
                    xml = unit.xmlelement
                    target = xml.find(unit.namespaced("target"))
                    if target is not None:
                        xml.remove(target)

                # Clear unused approved tag
                if "approved" in xml.attrib:
                    del xml.attrib["approved"]

                # Clear unused state tag
                if target is not None and "state" in target.attrib:
                    del target.attrib["state"]

        locale_mapping = {
            "bn-IN": "bn",
            "ga-IE": "ga",
            "nb-NO": "nb",
            "nn-NO": "nn",
            "sv-SE": "sv",
        }
        locale_code = locale.code
        if locale_code in locale_mapping:
            locale_code = locale_mapping[locale_code]

        # Set target-language if not set
        file_node = self.xliff_file.namespaced("file")
        for node in self.xliff_file.document.getroot().iterchildren(file_node):
            if not node.get("target-language"):
                node.set("target-language", locale_code)

        # Serialize and save the updated XLIFF file.
        with open(self.path, "wb") as f:
            f.write(bytes(self.xliff_file))


def parse(path, source_path=None, locale=None):
    if source_path is not None:
        source_resource = XLIFFResource(source_path, locale)
    else:
        source_resource = None

    return XLIFFResource(path, locale, source_resource)
