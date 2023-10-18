from flask import Flask, request, render_template, send_from_directory
import os
import shutil
from faster_whisper import WhisperModel

app = Flask(__name__)

# Create the 'temp' directory if it doesn't exist
if not os.path.exists('temp'):
    os.makedirs('temp')

@app.route('/')
def index():
    return render_template('index.html')

# ...

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    audio_files = request.files.getlist('audio_files')

    if not audio_files:
        return "No files provided."

    try:
        # Initialize the WhisperModel outside the if block for better efficiency
        model_size = "medium.en"
        # Run on CPU with INT8
        model = WhisperModel(model_size, device="cpu", compute_type="int8")

        # Clear the 'temp' directory if it contains any files
        temp_directory = 'temp'
        for filename in os.listdir(temp_directory):
            file_path = os.path.join(temp_directory, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Failed to remove {file_path}: {e}")

        transcription_results = []  # Store transcription results

        for audio_file in audio_files:
            # Determine the file extension
            file_extension = os.path.splitext(audio_file.filename)[1].lower()

            if file_extension in ('.mp3', '.mp4'):
                # Save the uploaded file to a temporary location
                audio_file_path = os.path.join("temp", audio_file.filename)
                audio_file.save(audio_file_path)

                segments, info = model.transcribe(audio_file_path, beam_size=5)

                print(f"Detected language '{info.language}' with probability {info.language_probability}")

                transcription_text = ""

                for segment in segments:
                    transcription_text += f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}\n"

                transcription_results.append((audio_file.filename, transcription_text))

                # Remove the temporary audio file
                os.remove(audio_file_path)
            else:
                return f"Invalid file type: {audio_file.filename}. Supported types: .mp3 and .mp4"

        # Create and save .txt files with transcription results
        for filename, transcription_text in transcription_results:
            with open(os.path.join('temp', f'{os.path.splitext(filename)[0]}.txt'), 'w') as text_file:
                text_file.write(transcription_text)

        # Send the .txt files as responses
        for filename, _ in transcription_results:
            return send_from_directory('temp', f'{os.path.splitext(filename)[0]}.txt', as_attachment=True)

    except Exception as e:
        # Handle exceptions here
        return "An error occurred during transcription: " + str(e)

# ...

if __name__ == '__main__':
    app.run(debug=True)