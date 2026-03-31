import os
import markdown
from datetime import datetime
from slugify import slugify  # Let's add this to requirements if needed, or use a basic function

def sanitize_filename(filename: str) -> str:
    """Basic slugify function to remove invalid path characters without external dependency."""
    keepcharacters = (' ', '.', '_', '-')
    sanitized = "".join(c for c in filename if c.isalnum() or c in keepcharacters).rstrip()
    return sanitized.replace(" ", "_").lower()

def export_as_html(markdown_content: str, topic: str):
    """
    Task 8: Converts the final approved Markdown into an HTML file ready for upload.
    Saves it into a folder divided weekly based on current date.
    """
    # Strip code block wrappers if the LLM wrapped the whole response
    markdown_content = markdown_content.strip()
    if markdown_content.startswith("```markdown"):
        markdown_content = markdown_content[11:]
    elif markdown_content.startswith("```html"):
        markdown_content = markdown_content[7:]
    elif markdown_content.startswith("```"):
        markdown_content = markdown_content[3:]
        
    if markdown_content.endswith("```"):
        markdown_content = markdown_content[:-3]
        
    markdown_content = markdown_content.strip()
    
    # Convert MD to HTML using the built-in python-markdown package
    html_content = markdown.markdown(markdown_content, extensions=['extra', 'toc'])
    
    # Calculate weekly folder
    now = datetime.now()
    year, week, _ = now.isocalendar()
    weekly_folder_name = f"Week_{week}_{year}"
    
    # Set the export directory relative to project root
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    export_dir = os.path.join(base_dir, "exports", weekly_folder_name)
    os.makedirs(export_dir, exist_ok=True)
    
    # Save the file
    safe_topic = sanitize_filename(topic)
    file_path = os.path.join(export_dir, f"{safe_topic}.html")
    
    # Prepend basic HTML boilerplate
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{topic}</title>
</head>
<body>
    {html_content}
</body>
</html>
"""
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(full_html)
        
    return file_path
