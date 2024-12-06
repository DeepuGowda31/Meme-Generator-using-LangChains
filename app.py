import os
import requests
from flask import Flask, render_template, request, send_from_directory
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import openai

app = Flask(__name__)
app.config['MEME_FOLDER'] = 'static/memes/'
app.config['UPLOAD_FOLDER'] = 'static/uploads/'

# Ensure required folders exist
os.makedirs(app.config['MEME_FOLDER'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Set your OpenAI API key
openai.api_key = ""

# Chain 1: Generate a realistic image based on context
def generate_image(context, style="realistic"):
    prompt = (
        f"A photorealistic image that reflects this context humorously: {context}. "
        "Make it vibrant and engaging, suitable for a meme. Include clear focal elements."
    )
    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="512x512"
    )
    image_url = response['data'][0]['url']
    return image_url

# Chain 2: Generate funny text for the image
def generate_text_for_image(image_description, humor_style):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[ 
           {"role": "system", "content": f"You are a professional meme caption generator. Create {humor_style}, engaging, and humorous text."},
            {"role": "user", "content": f"Generate a funny caption with emojis for this image description: {image_description}"}
        ]
    )
    return response['choices'][0]['message']['content']

# Chain 3: Combine the image and text to create a meme
def create_meme(image_url, text):
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content))

    # Set up drawing context and font
    draw = ImageDraw.Draw(image)
    font_path = "fonts/arial.ttf"  # Replace with the path to a valid .ttf font file
    font = ImageFont.truetype(font_path, size=24)

    # Word wrapping for the text
    max_width = image.size[0] - 40
    lines = []
    words = text.split()
    while words:
        line = ''
        while words and draw.textbbox((0, 0), line + words[0], font=font)[2] <= max_width:
            line += words.pop(0) + ' '
        lines.append(line.strip())

    # Calculate text placement
    text_height = sum([draw.textbbox((0, 0), line, font=font)[3] for line in lines])
    y = image.size[1] - text_height - 20
    for line in lines:
        width = draw.textbbox((0, 0), line, font=font)[2]
        x = (image.size[0] - width) // 2
        draw.text((x, y), line, font=font, fill="white", stroke_fill="black", stroke_width=2)
        y += draw.textbbox((0, 0), line, font=font)[3]

    # Save the meme
    meme_path = os.path.join(app.config['MEME_FOLDER'], 'meme.png')
    image.save(meme_path)
    return meme_path

@app.route('/', methods=['GET', 'POST'])
def index():
    humor_styles = ["Witty", "Sarcastic", "Pun-based", "Dark Humor", "Dad Jokes", "Absurd", "Dry Humor", "Self-deprecating", "Slapstick", "Cringe-worthy", "Playful", "Intellectual", "Meta", "Surreal", "Mocking", "Nerdy/Geeky", "Observational", "Parody", "Satire", "Hyperbole"]

    if request.method == 'POST':
        context = request.form['context']
        humor_style = request.form['humor_style']

        # Chain 1: Generate Image
        image_url = generate_image(context, style="realistic")

        # Chain 2: Generate Text
        funny_text = generate_text_for_image(context, humor_style)

        # Chain 3: Create Meme
        meme_path = create_meme(image_url, funny_text)

        return render_template('index.html', meme_path=meme_path, funny_text=funny_text, context=context, humor_style=humor_style)

    return render_template('index.html', humor_styles=humor_styles)


@app.route('/static/memes/<filename>')
def serve_meme(filename):
    return send_from_directory(app.config['MEME_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
