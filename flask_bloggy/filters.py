import markdown
import markupsafe


def md_to_html(md):
    return markupsafe.Markup(markdown.markdown(md))


def first_para(html):
    return markupsafe.Markup(html[:html.find('</p>') + 4])
