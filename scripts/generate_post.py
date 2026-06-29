import feedparser
import os
import re
from datetime import datetime
from google import genai
from google.genai import types

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
    """Generates an AI image using Imagen 3 and saves it locally."""
    # Ensure the images directory exists
    os.makedirs("posts/images", exist_ok=True)
    
    image_path = f"posts/images/{file_slug}.jpg"
    
    # Prompt for a consistent, clean blog aesthetic
    image_prompt = f"A simple, minimalist, flat vector illustration representing technology news about: {title}. Clean lines, professional tech blog style, dark blue and vibrant accent colors."
    
    try:
        result = client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=image_prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                output_mime_type="image/jpeg",
                aspect_ratio="16:9"
            )
        )
        
        # Save the generated image bytes directly to a file
        with open(image_path, "wb") as f:
            f.write(result.generated_images[0].image.image_bytes)
            
        # Return the relative path for the HTML to use
        return f"images/{file_slug}.jpg"
        
    except Exception as e:
        print(f"Image generation failed: {e}")
        # Fallback to a placeholder if the image generation fails for any reason
        return "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=800&q=80"

def slugify(text):
    return re.sub(r'[\W_]+', '-', text.lower()).strip('-')

def main():
    title, link, description = fetch_top_news()
    file_slug = slugify(title)
    
    html_content = generate_article(title, description)
    img_url = generate_thumbnail(title, file_slug) # Call the image generator
    
    date_str = datetime.now().strftime("%B %d, %Y")
    file_name = file_slug + ".html"
    
    # 1. Generate the Post File
    with open("posts/template.html", "r", encoding="utf-8") as f:
        template = f.read()
    
    post_html = template.replace("{{TITLE}}", title)\
                        .replace("{{DATE}}", date_str)\
                        .replace("{{IMAGE_URL}}", img_url)\
                        .replace("{{CONTENT}}", html_content)
    
    with open(f"posts/{file_name}", "w", encoding="utf-8") as f:
        f.write(post_html)
        
    # 2. Update the Posts Index
    with open("posts/index.html", "r", encoding="utf-8") as f:
        index_html = f.read()
        
    new_list_item = f'''
    <li class="post-item">
      <img src="{img_url}" alt="Thumbnail" class="post-thumb" onerror="this.style.display='none'">
      <div class="post-info">
        <a href="{file_name}">{title}</a>
        <span class="post-date">{date_str}</span>
      </div>
    </li>
    '''
    
    index_html = index_html.replace('', new_list_item.strip())
    
    with open("posts/index.html", "w", encoding="utf-8") as f:
        f.write(index_html)

    print(f"Successfully generated post: {file_name} with AI image: {img_url}")

if __name__ == "__main__":
    main()
