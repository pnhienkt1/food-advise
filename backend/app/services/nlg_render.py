from jinja2 import Template


def render_template(template_str: str, context: dict) -> str:
    if not template_str:
        return ""
    template = Template(template_str)
    return template.render(**context)
