# Need to pass this prompt with sample cooking animal image to LLM

COOKING_ANIMAL_SCENARIO_PROMPT_WITH_IMAGE_GEMINI = """
This image was captured from short form video content where various animals are cooking food. I want to create similar content.
Give me 10 prompts with detailed scenarios for creating such video content.
The scenarios should include different types of foods being cooked, various animals cooking, various cooking tools, and unique backgrounds or settings to make each video visually appealing.

For each scenario, write prompts in the following JSON format:

{
    "scenario1" : {
        "Subject": [Detailed object description including type of animal, food, clothing, color, size, and any unique features.],
        "Action": [Specific cooking actions, behaviors, movements, sequence, interaction patterns that can be performed in 8 seconds.],
        "Scene": [Detailed environment description including location, props, background elements, lighting setup, weather, time of day, architectural details. No unrealistic scene transitions.],
        "Style": [Camera shot type, angle, movement, lighting style, visual aesthetic, color palette, depth of field, focus techniques.],
        "Sounds": [Specific audio elements including ambient sounds, effects, background audio, music, environmental noise, equipment sounds, natural acoustics],
        "Technical(Negative Prompt)": No subtitles, No captions, and No unrealistic scene transitions.
    },
}
"""
