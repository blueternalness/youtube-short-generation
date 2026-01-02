# Need to pass this prompt with sample fruit cutting image to LLM

FRUIT_CUTTING_SCENARIO_PROMPT_WITHOUT_IMAGE = """
I want to create short form video content where various fruit models are being cut. A fruit model made of various materials.
Give me 10 prompts with detailed scenarios for creating such video content.
The scenarios should include different types of fruits being cut, various cutting tools, and unique backgrounds or settings to make each video visually appealing.
The cutting sounds should be emphasized in the scenarios to enhance the sensory experience for viewers.

For each scenario, write prompts in the following JSON format:

{
    "scenario1" : {
        "Subject": [Detailed object description including type of fruit, color, size, texture, material and any unique features.],
        "Action": [Specific cutting actions, movements, timing, sequence, interaction patterns that can be performed in 8 seconds.],
        "Scene": [Detailed environment description including location, props, background elements, lighting setup, weather, time of day, architectural details. No unrealistic scene transitions. No unrealistic scenes.],
        "Style": [Camera shot type, angle, movement, lighting style, visual aesthetic, film grade, color palette, depth of field, focus techniques.],
        "Sounds": [Specific ASMR audio elements with minimal silent moments, including cutting sounds based on the subject, equipment, and action.],
        "Technical(Negative Prompt)": No silent moments, No unrealistic actions, and No unrealistic scene transitions.
    },
}
"""
