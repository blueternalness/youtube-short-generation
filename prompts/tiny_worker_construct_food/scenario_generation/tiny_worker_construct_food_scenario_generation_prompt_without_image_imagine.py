TINY_WORKER_CONSTRUCT_FOOD_SCENARIO_PROMPT_WITHOUT_IMAGE_IMAGINE = """
I want to create short form video content where tiny workers are constructing giant food.
The video should not include unrealistic scenes and unrealistic scene transitions.
Give me top 10 prompts with detailed scenarios for creating such video content. The scenario should be performed in 5 seconds.
The scenarios should include different types of foods being built, various construction sites, various construction machinery, various construction tools, and unique backgrounds or settings to make each video visually appealing.
New objects should not suddenly appear during the video.

For each scenario, write prompts in the following JSON format:

{
    "scenario1" : {
        "Subject": [Detailed object description including type of tiny worker, food, clothing, color, size, and any unique features.],
        "Action": [Specific construction actions, behaviors, movements, sequence, interaction patterns that can be performed in 5 seconds.],
        "Scene": [Detailed environment description including location, props, background elements, lighting setup, weather, time of day, architectural details. No unrealistic scene transitions.],
        "Style": [Camera shot type, angle, movement, lighting style, visual aesthetic, color palette, depth of field, focus techniques.],
        "Sounds": [Specific audio elements including ambient sounds, effects, background audio, music, environmental noise, equipment sounds, natural acoustics],
        "Technical(Negative Prompt)": No sudden appearance, No sudden disappearance, No hallucinations, No unrealistic scenes, and No unrealistic scene transitions.
    },
}
"""

# ASIS: "No object popping, No disappearing objects" instruction was in Sounds.
