from md2pdf_cli.diagram_renderers import render_ascii_block
from md2pdf_cli.parser import DiagramBlock


def test_ascii_rendering_escapes_html_characters() -> None:
    block = DiagramBlock(
        kind="ascii",
        code="<api> & <worker>\n",
        index=0,
        source_line=1,
    )

    html = render_ascii_block(block)

    assert "<pre class=\"ascii-diagram\">" in html
    assert "&lt;api&gt; &amp; &lt;worker&gt;" in html
    assert html.endswith("</pre>")
