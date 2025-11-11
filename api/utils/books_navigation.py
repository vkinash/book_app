import re

from urllib.parse import quote


def add_navigation_buttons(html_content: str, filename: str, current_index: int, total_chapters: int) -> str:
    """Add Previous and Next navigation buttons to the top and bottom of the chapter."""

    # Determine if prev/next buttons should be enabled
    has_prev = current_index > 0
    has_next = current_index < total_chapters - 1

    # Create the navigation bar HTML
    nav_style = """
    <style>
        .chapter-nav {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 20px;
            background-color: #f5f5f5;
            border: 1px solid #ddd;
            margin: 20px 0;
            font-family: Arial, sans-serif;
        }
        .chapter-nav button {
            padding: 10px 20px;
            font-size: 16px;
            cursor: pointer;
            border: 1px solid #007bff;
            background-color: #007bff;
            color: white;
            border-radius: 4px;
            transition: background-color 0.3s;
        }
        .chapter-nav button:hover:not(:disabled) {
            background-color: #0056b3;
        }
        .chapter-nav button:disabled {
            background-color: #ccc;
            border-color: #ccc;
            cursor: not-allowed;
            opacity: 0.6;
        }
        .chapter-nav .chapter-info {
            font-size: 14px;
            color: #666;
        }
    </style>
    """

    prev_url = f"/book/chapter?filename={quote(filename)}&amp;chapter_index={current_index - 1}" if has_prev else "#"
    next_url = f"/book/chapter?filename={quote(filename)}&amp;chapter_index={current_index + 1}" if has_next else "#"

    # XHTML requires disabled="disabled" instead of just disabled
    prev_disabled = '' if has_prev else ' disabled="disabled"'
    next_disabled = '' if has_next else ' disabled="disabled"'

    nav_html = f"""
    <div class="chapter-nav">
        <button onclick="window.location.href='{prev_url}'"{prev_disabled}>
            ← Previous
        </button>
        <span class="chapter-info">Chapter {current_index + 1} of {total_chapters}</span>
        <button onclick="window.location.href='{next_url}'"{next_disabled}>
            Next →
        </button>
    </div>
    """

    # Try to insert after opening body tag, or prepend to content
    if '<body' in html_content.lower():
        # Insert style in head and nav after body opening tag
        if '<head' in html_content.lower():
            html_content = html_content.replace('</head>', f'{nav_style}</head>', 1)
        else:
            # No head tag, add style before body
            html_content = html_content.replace('<body', f'{nav_style}<body', 1)

        # Add navigation after body tag
        body_match = re.search(r'<body[^>]*>', html_content, re.IGNORECASE)
        if body_match:
            insert_pos = body_match.end()
            html_content = html_content[:insert_pos] + nav_html + html_content[insert_pos:]

        # Add navigation before closing body tag
        html_content = html_content.replace('</body>', f'{nav_html}</body>', 1)
    else:
        # No body tag found, just prepend and append
        html_content = nav_style + nav_html + html_content + nav_html

    return html_content