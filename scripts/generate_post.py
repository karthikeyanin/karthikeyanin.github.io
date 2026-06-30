import feedparser
import os
import re
import base64
from datetime import datetime
from google import genai

client = genai.Client()

def fetch_top_news():
    feed = feedparser.parse("https://techcrunch.com/feed/")
    top_entry = feed.entries[0]
    return top_entry.title, top_entry.link, top_entry.description

def generate_article(title, description):
    prompt = f"""
    Act as a Senior Software Engineer. Read the following tech news description:
    Title: {title}
    Description: {description}
    
    Write a 3-paragraph blog post for your personal portfolio. 
    1. Summarize the news.
    2. Add a brief technical perspective or opinion on how it impacts software engineering or infrastructure.
    Format the output in pure HTML using <p> and <strong> tags only. Do not include standard html boilerplate.
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    return response.text

def generate_thumbnail(title, file_slug):
    """Generates an AI image using Gemini Image and saves it locally."""
    os.makedirs("blog/posts/images", exist_ok=True)
    image_path = f"blog/posts/images/{file_slug}.png"
    
    image_prompt = f"A simple, minimalist, flat vector illustration representing technology news about: {title}. Clean lines, professional tech blog style, dark blue and vibrant accent colors."
    
    try:
        interaction = client.interactions.create(
            model="gemini-3.1-flash-image",
            input=image_prompt
        )
        with open(image_path, "wb") as f:
            f.write(base64.b64decode(interaction.output_image.data))
        return f"images/{file_slug}.png"
    except Exception as e:
        print(f"Image generation failed: {e}")
        return "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=800&q=80"

def slugify(text):
    return re.sub(r'[\W_]+', '-', text.lower()).strip('-')

def main():
    title, link, description = fetch_top_news()
    file_slug = slugify(title)
    
    html_content = generate_article(title, description)
    img_url = generate_thumbnail(title, file_slug)
    
    date_str = datetime.now().strftime("%B %d, %Y")
    file_name = file_slug + ".html"
    
    # 1. Generate individual post page
    with open("blog/posts/template.html", "r", encoding="utf-8") as f:
        template = f.read()
    
    post_html = template.replace("{{TITLE}}", title)\
                        .replace("{{DATE}}", date_str)\
                        .replace("{{IMAGE_URL}}", img_url)\
                        .replace("{{CONTENT}}", html_content)
    
    with open(f"blog/posts/{file_name}", "w", encoding="utf-8") as f:
        f.write(post_html)
        
    # 2. Update index.html safely
    with open("blog/posts/index.html", "r", encoding="utf-8") as f:
        index_html = f.read()
        
    # Check if this exact post already exists to prevent duplication loops
    if f'href="{file_name}"' in index_html:
        print(f"Post {file_name} already exists in index.html. Skipping modification.")
        return

    # Build clean list item snippet
    new_list_item = f'''
    <li class="post-item">
      <img src="{img_url}" alt="Thumbnail" class="post-thumb" onerror="this.style.display='none'">
      <div class="post-info">
        <a href="{file_name}">{title}</a>
        <span class="post-date">{date_str}</span>
      </div>
    </li>'''

    # Strictly controlled injection logic
    if '<!-- POSTS_INJECT_MARKER -->' in index_html:
        # Standard injection path
        replacement = f"{new_list_item}\n    <!-- POSTS_INJECT_MARKER -->"
        index_html = index_html.replace('<!-- POSTS_INJECT_MARKER -->', replacement, 1)
    elif '</ul>' in index_html:
        # Safe fallback if marker was stripped by a bad PR merge
        print("Marker missing! Falling back to safe </ul> insertion tag.")
        replacement = f"{new_list_item}\n    <!-- POSTS_INJECT_MARKER -->\n  </ul>"
        index_html = index_html.replace('</ul>', replacement, 1)
    else:
        print("CRITICAL ERROR: Could not find valid target tags in blog/posts/index.html. File left untouched.")
        return
    
    with open("blog/posts/index.html", "w", encoding="utf-8") as f:
        f.write(index_html)

    print(f"Successfully generated post: {file_name}")

if __name__ == "__main__":
    main()