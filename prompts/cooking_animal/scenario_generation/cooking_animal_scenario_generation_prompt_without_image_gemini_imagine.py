# Have to use this prompt

COOKING_ANIMAL_SCENARIO_PROMPT_WITHOUT_IMAGE_IMAGINE = """
I want to create short form video content where various adorable animals are cooking food.
The animals should act like humans while cooking.
The video should not include unrealistic scenes and unrealistic scene transitions.
Give me top 5 prompts with detailed scenarios for creating such video content. The scenario should be performed in 6 seconds.
The scenarios should include different types of foods being cooked, various animals cooking, various cooking tools, and unique backgrounds or settings to make each video visually appealing.

For each scenario, write prompts in the following JSON format:

{
    "scenario1" : {
        "Subject": [Detailed object description including type of animal, food, clothing, color, size, and any unique features.],
        "Action": [Specific cooking actions, behaviors, movements, sequence, interaction patterns that can be performed in 6 seconds.],
        "Scene": [Detailed environment description including location, props, background elements, lighting setup, weather, time of day, architectural details. No unrealistic scene transitions.],
        "Style": [Camera shot type, angle, movement, lighting style, visual aesthetic, color palette, depth of field, focus techniques.],
        "Sounds": [Specific audio elements including ambient sounds, effects, background audio, music, environmental noise, equipment sounds, natural acoustics],
        "Technical(Negative Prompt)": No captions, and No unrealistic scene transitions.
    },
}
"""
