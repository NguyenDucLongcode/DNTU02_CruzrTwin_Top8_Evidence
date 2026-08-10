from gtts import gTTS

text = "CruzTwin ASEAN — closing the last meter of smart-city response."
tts = gTTS(text, lang='en', tld='com') # Default google US female voice
tts.save("outro_en_google_female.mp3")
print("Saved to outro_en_google_female.mp3")
