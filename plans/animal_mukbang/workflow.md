# Caution
Need to use Gemini(veo). Grok(Imagine) animal rendering is bad.

# Workflow
Gemini App Case: Scenario generation -> generate video from Gemini app with automation program -> resize video to 1:1 or 9:16 -> merge videos -> Youtube upload <br>
Google Flow Case: Scenario generation -> generate video from Gemini flow with 9:16 size -> merge video on Google flow -> Youtube upload <br>
(scenario generation without image seems okay too)

# Need to be done manually

## Scenario generation
Submit prompt

## Google flow video generation 
Upload generated scenarios and generate video on Google flow

## Video resizing
Convert 16:9 video to 1:1 or 9:16 video <br>
https://new.express.adobe.com/home/tools/resize-video

## Video merging
https://new.express.adobe.com/home/tools/merge-videos

# Automation

## Google Gemini app video creation within day limit
```
source /Users/vhehf/Desktop/"Personal materials"/StartUp/YoutubeShortsGeneration/shorts-generation/bin/activate 
cd /Users/vhehf/Desktop/"Personal materials"/StartUp/YoutubeShortsGeneration/youtube-short-generation/automation/
python text_to_video_generation.py --mode gemini
```

### Disclaimer
I used video creation through Gemini app rather than Google API because of costs.
I didn’t schedule the script as a CronJob because my personal laptop isn’t suitable for running 24/7.

# Reference
```
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="$HOME/gemini-bot"
```
