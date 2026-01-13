# TBD
Need to generate video using Gemini. Grok(Imagine) animal rendering is not good.

# Workflow
Grok Case: Scenario generation without image -> Run auto video generation script -> Youtube upload <br>

# Need to be done manually

## Scenario generation
Submit prompt to Gemini

## Video merging
https://new.express.adobe.com/home/tools/merge-videos

# Automation

## Grok Imagine app video creation within day limit
```
source /Users/vhehf/Desktop/"Personal materials"/StartUp/YoutubeShortsGeneration/shorts-generation/bin/activate 
cd /Users/vhehf/Desktop/"Personal materials"/StartUp/YoutubeShortsGeneration/youtube-short-generation/automation/
python text_to_video_generation.py --mode grok
```

### Disclaimer
I used video creation through Grok app rather than Grok API because of costs.
I didn’t schedule the script as a CronJob because my personal laptop isn’t suitable for running 24/7.

# Reference
```
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="$HOME/gemini-bot"
```
