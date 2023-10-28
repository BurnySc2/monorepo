from typing import overload

from fastapi.templating import Jinja2Templates


@overload
# pyre-fixme[43]
def render(templates: Jinja2Templates, template_file_name: str, contexts: dict) -> str:
    ...


@overload
# pyre-fixme[43]
def render(templates: Jinja2Templates, template_file_name: str, contexts: list[dict]) -> str:
    ...


def render(templates: Jinja2Templates, template_file_name: str, context: dict | list[dict]) -> str:
    """
    Render a single template with the given context. 
    If context is a list, render multiple times using the same template.
    """
    t = templates.get_template(template_file_name)
    if isinstance(context, dict):
        return t.render(context)
    elif isinstance(context, list):
        return "".join(t.render(c) for c in context)
    else:
        raise TypeError(f"Expected dict or list[dict], got {type(context)}")
