# Need to be done manually

## Scenario generation
Submit prompt with sample fruit cutting image

## Google flow video generation 
Upload generated scenarios and generate video on Google flow

## Video merging
TBD

# Automation

## Google Gemini app video creation within day limit
```
source /Users/vhehf/Desktop/"Personal materials"/StartUp/YoutubeShortsGeneration/shorts-generation/bin/activate 
cd /Users/vhehf/Desktop/"Personal materials"/StartUp/YoutubeShortsGeneration/youtube-short-generation/automation/fruit_cutting/
python video_generator.py
```

### Disclaimer
I used video creation through Gemini app rather than Google API because of costs.
I didn’t schedule the script as a CronJob because my personal laptop isn’t suitable for running 24/7.

# Reference
```
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="$HOME/gemini-bot"
```
