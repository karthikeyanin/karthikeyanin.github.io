import feedparser
import os
import re
from datetime import datetime
from google import genai

# The new SDK automatically detects the GEMINI_API_KEY environment variable
client = genai.Client()

def fetch_top_news():
    # Using TechCrunch as an example RSS feed
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
    
    # Using the current standard model
    response = client.models.generate_content(
        model='gemini-1.5-flash',
        contents=prompt
    )
    return response.text

def slugify(text):
    return re.sub(r'[\W_]+', '-', text.lower()).strip('-')

def main():
    title, link, description = fetch_top_news()
    html_content = generate_article(title, description)
    date_str = datetime.now().strftime("%B %d, %Y")
    file_slug = slugify(title) + ".html"
    
    # 1. Generate the Post File
    with open("posts/template.html", "r", encoding="utf-8") as f:
        template = f.read()
    
    post_html = template.replace("{{TITLE}}", title).replace("{{DATE}}", date_str).replace("{{CONTENT}}", html_content)
    
    with open(f"posts/{file_slug}", "w", encoding="utf-8") as f:
        f.write(post_html)
        
    # 2. Update the Posts Index
    with open("posts/index.html", "r", encoding="utf-8") as f:
        index_html = f.read()
        
    new_list_item = f'<li><a href="{file_slug}">{title}</a><br><span class="post-date">{date_str}</span></li>\n    '
    index_html = index_html.replace('', new_list_item)
    
    with open("posts/index.html", "w", encoding="utf-8") as f:
        f.write(index_html)

    print(f"Successfully generated post: {file_slug}")

if __name__ == "__main__":
    main()
