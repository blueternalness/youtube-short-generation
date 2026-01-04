# Have to use this prompt

ANIMAL_MUKBANG_SCENARIO_PROMPT_WITHOUT_IMAGE_GEMINI = """
I want to create mukbang short form video content where various adorable animals are eating food.
The animals should act like humans while eating food.
The video should not include unrealistic scenes and unrealistic scene transitions.
Give me top 5 prompts with detailed scenarios for creating such video content. The scenario should be performed in 8 seconds.
The scenarios should include different types of foods, various animals, and unique backgrounds or settings to make each video visually appealing.
The eating sounds should be emphasized in the scenarios to enhance the sensory experience for viewers.

For each scenario, write prompts in the following JSON format:

{
    "scenario1" : {
        "Subject": [Detailed object description including type of animal, food, clothing, color, size, and any unique features.],
        "Action": [Specific eating actions, behaviors, movements, sequence, interaction patterns that can be performed in 8 seconds.],
        "Scene": [Detailed environment description including location, props, background elements, lighting setup, weather, time of day, architectural details. No unrealistic scene transitions.],
        "Style": [Camera shot type, angle, movement, lighting style, visual aesthetic, color palette, depth of field, focus techniques.],
        "Sounds": [Specific audio elements including ambient sounds, effects, background audio, music, environmental noise, equipment sounds, natural acoustics],
        "Technical(Negative Prompt)": No captions, No unrealistic scenes, and No unrealistic scene transitions.
    },
}
"""
# if video quality is low, try change Sound section to eating sounds referring Imagine prompt
