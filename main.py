import time
import azure.cognitiveservices.speech as speechsdk
import os
from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import ftransc.core as ft

load_dotenv()
key = os.getenv('SPEECH_KEY')

# def recognize_from_microphone():
#     speech_config = speechsdk.SpeechConfig(subscription=key, region="eastus")
#     speech_config.speech_recognition_language="en-US"
#     speech_config.enable_dictation()

#     audio_config = speechsdk.audio.AudioConfig(filename="audio.wav")
#     speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

#     print("Transcribing...")
#     # speech_recognition_result = speech_recognizer.recognize_once_async().get()

#     done = False
#     def stop_cb(evt):
#         print('CLOSING on {}'.format(evt))
#         speech_recognizer.stop_continuous_recognition()
#         nonlocal done
#         done = True

#     def write_cb(evt):
#         with open('transcribe.txt', 'a') as f:
#             f.write(evt.result.text + ' ')

#     # speech_recognizer.recognizing.connect(lambda evt: print('RECOGNIZING: {}'.format(evt)))
#     # speech_recognizer.recognized.connect(lambda evt: print(evt.result.text))
#     speech_recognizer.recognized.connect(write_cb)
#     speech_recognizer.session_started.connect(lambda evt: print('SESSION STARTED: {}'.format(evt.session_id)))
#     speech_recognizer.session_stopped.connect(lambda evt: print('SESSION STOPPED {}'.format(evt)))
#     speech_recognizer.canceled.connect(lambda evt: print('CANCELED {}'.format(evt)))

#     speech_recognizer.session_stopped.connect(stop_cb)
#     speech_recognizer.canceled.connect(stop_cb)

#     speech_recognizer.start_continuous_recognition()
#     while not done:
#         time.sleep(.5)



#     # if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
#     #     print("Recognized:\n{}".format(speech_recognition_result.text))
#     # elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
#     #     print("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))
#     # elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
#     #     cancellation_details = speech_recognition_result.cancellation_details
#     #     print("Speech Recognition canceled: {}".format(cancellation_details.reason))
#     #     if cancellation_details.reason == speechsdk.CancellationReason.Error:
#     #         print("Error details: {}".format(cancellation_details.error_details))
#     #         print("Did you set the speech resource key and region values?")

# recognize_from_microphone()

# bot start
PORT = int(os.environ.get('PORT', '8443'))
TOKEN = os.getenv('BOT_TOKEN')

print("Starting bot...")

def start_command(update, context):
    update.message.reply_text("Hello there, I'm your transcriber. Send me any audio of wav format and I'll try to transcribe it. You can also record it from telegram itself.")

def help_command(update, context):
    update.message.reply_text("Send me any audio and I'll try to transcribe it.")




speech_config = speechsdk.SpeechConfig(subscription=key, region="eastus")
speech_config.speech_recognition_language="en-US"
speech_config.enable_dictation()
speech_config.set_profanity(profanity_option=speechsdk.ProfanityOption.Raw)

def handle_message(update, context):
    update.message.reply_text("Send me any audio and I'll try to transcribe it.")

def handle_audio(update, context):
    if update.message.voice:
        audio_file = update.message.voice.file_id
        audio = update.message.voice
    else:
        audio_file = update.message.audio.file_id
        audio = update.message.audio

    if audio.file_size > 40 * 1024 * 1024 or audio.duration > 360:
        update.message.reply_text("Audio is too long or too big. Please send a smaller audio.")
        return

    msg = update.message.reply_text("I'm transcribing your audio...")
    chat_id = update.message.chat_id
    
    file_data = context.bot.getFile(audio_file)
    file_data.download(audio_file)
    ft.transcode(file_data.download(audio_file), 'wav')

    print(file_data.file_path)

    audio_config = speechsdk.audio.AudioConfig(filename=audio_file+".wav")
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    print("Transcribing...")
    result = ''

    done = False
    def stop_cb(evt):
        print('CLOSING on {}'.format(evt))
        speech_recognizer.stop_continuous_recognition()
        nonlocal done
        done = True
        update.message.reply_text("I'm done transcribing your audio.")
        os.remove(audio_file+".wav")
        os.remove(audio_file)

    def write_cb(evt):
        nonlocal result
        result += evt.result.text + ' '
        context.bot.edit_message_text(chat_id=chat_id, message_id=msg.message_id, text=result)

    speech_recognizer.recognized.connect(write_cb)
    speech_recognizer.session_started.connect(lambda evt: print('SESSION STARTED: {}'.format(evt.session_id)))
    speech_recognizer.session_stopped.connect(lambda evt: print('SESSION STOPPED {}'.format(evt)))
    speech_recognizer.canceled.connect(lambda evt: print('CANCELED {}'.format(evt)))

    speech_recognizer.session_stopped.connect(stop_cb)

    speech_recognizer.start_continuous_recognition()
    while not done:
        time.sleep(.5)

def error(update, context):
    # print(f'Update {update} caused error {context.error}')
    print('Update', update, 'caused error', context.error)
    update.message.reply_text("Something bad happened.")

if __name__ == '__main__':
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Add handlers
    dp.add_handler(CommandHandler('start', start_command))
    dp.add_handler(CommandHandler('help', help_command))

    # handle messages
    dp.add_handler(MessageHandler(Filters.text, handle_message))
    dp.add_handler(MessageHandler(Filters.audio, handle_audio))
    dp.add_handler(MessageHandler(Filters.voice, handle_audio))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    # updater.start_polling()
    updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN, webhook_url=os.getenv('BASE_URL') + TOKEN)

    updater.idle()


'''
Bot commands:

start - Start the bot
help - Show help
'''
