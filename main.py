from prompts.movie_set_prompt import IMAGE_GENERATION_PROMPT, VIDEO_GENERATION_PROMPT
from google import genai
from google.genai import types
from PIL import Image

#client = genai.Client(api_key="AIzaSyBU2Ofu-RWPrWQMkfnHIHfUS1gcOqvKU30")
client = genai.Client(api_key="AIzaSyBU2Ofu-RWPrWQMkfnHIHfUS1gcOqvKU30")

prompt = (
    IMAGE_GENERATION_PROMPT
)

image = Image.open("./images/kpop_daemon_hunters.png")

response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[prompt, image],
)

for part in response.parts:
    if part.text is not None:
        print(part.text)
    elif part.inline_data is not None:
        image = part.as_image()
        image.save("generated_image.png")

