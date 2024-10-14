from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urljoin
from uuid import uuid4

from reactpy import component, event, html, use_connection
from reactpy.backend.types import Location
from reactpy.core.component import Component
from reactpy.core.types import VdomDict
from reactpy.web.module import export, module_from_file

from reactpy_router.hooks import _use_route_state
from reactpy_router.types import Route

History = export(
    module_from_file("reactpy-router", file=Path(__file__).parent / "static" / "bundle.js"),
    ("History"),
)
"""Client-side portion of history handling"""

Link = export(
    module_from_file("reactpy-router", file=Path(__file__).parent / "static" / "bundle.js"),
    ("Link"),
)
"""Client-side portion of link handling"""

link_js_content = (Path(__file__).parent / "static" / "link.js").read_text(encoding="utf-8")


def link(attributes: dict[str, Any], *children: Any) -> Component:
    """Create a link with the given attributes and children."""
    return _link(attributes, *children)


@component
def _link(attributes: dict[str, Any], *children: Any) -> VdomDict:
    """A component that renders a link to the given path."""
    attributes = attributes.copy()
    uuid_string = f"link-{uuid4().hex}"
    class_name = f"{uuid_string}"
    set_location = _use_route_state().set_location
    if "className" in attributes:
        class_name = " ".join([attributes.pop("className"), class_name])
    if "class_name" in attributes:  # pragma: no cover
        # TODO: This can be removed when ReactPy stops supporting underscores in attribute names
        class_name = " ".join([attributes.pop("class_name"), class_name])
    if "href" in attributes and "to" not in attributes:
        attributes["to"] = attributes.pop("href")
    if "to" not in attributes:  # pragma: no cover
        raise ValueError("The `to` attribute is required for the `Link` component.")
    to = attributes.pop("to")

    attrs = {
        **attributes,
        "href": to,
        "className": class_name,
    }

    # FIXME: This component currently works in a "dumb" way by trusting that ReactPy's script tag \
    # properly sets the location due to bugs in ReactPy rendering.
    # https://github.com/reactive-python/reactpy/pull/1224
    current_path = use_connection().location.pathname

    @event(prevent_default=True)
    def on_click(_event: dict[str, Any]) -> None:
        pathname, search = to.split("?", 1) if "?" in to else (to, "")
        if search:
            search = f"?{search}"

        # Resolve relative paths that match `../foo`
        if pathname.startswith("../"):
            pathname = urljoin(current_path, pathname)

        # Resolve relative paths that match `foo`
        if not pathname.startswith("/"):
            pathname = urljoin(current_path, pathname)

        # Resolve relative paths that match `/foo/../bar`
        while "/../" in pathname:
            part_1, part_2 = pathname.split("/../", 1)
            pathname = urljoin(f"{part_1}/", f"../{part_2}")

        # Resolve relative paths that match `foo/./bar`
        pathname = pathname.replace("/./", "/")

        set_location(Location(pathname, search))

    attrs["onClick"] = on_click

    return html._(html.a(attrs, *children), html.script(link_js_content.replace("UUID", uuid_string)))

    # def on_click(_event: dict[str, Any]) -> None:
    #     set_location(Location(**_event))
    # return html._(html.a(attrs, *children), Link({"onClick": on_click, "linkClass": uuid_string}))


def route(path: str, element: Any | None, *routes: Route) -> Route:
    """Create a route with the given path, element, and child routes."""
    return Route(path, element, routes)