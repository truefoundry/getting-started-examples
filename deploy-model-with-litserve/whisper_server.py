import os
import litserve as ls
from fastapi import UploadFile
from faster_whisper import WhisperModel


def _get_model_dir():
    if "MODEL_DIR" not in os.environ:
        raise Exception(
            "MODEL_DIR environment variable is not set. Please set it to the directory containing the model."
        )
    return os.environ["MODEL_DIR"]


MODEL_DIR = _get_model_dir()


class WhisperLitAPI(ls.LitAPI):
    def setup(self, device):
        # Load the OpenAI Whisper model. You can specify other models like "base", "small", etc.
        self.model = WhisperModel(MODEL_DIR, device="cpu")

    def decode_request(self, request: UploadFile):
        # Assuming the request sends the path to the audio file
        # In a more robust implementation, you would handle audio data directly.
        return request.file

    def predict(self, audio_stream):
        # Process the audio file and return the transcription result
        output = []
        segments, _ = self.model.transcribe(audio_stream)
        for segment in segments:
            output.append({"start": segment.start, "end": segment.end, "text": segment.text})
        return output

    def encode_response(self, output):
        # Return the transcription text
        return output


if __name__ == "__main__":
    api = WhisperLitAPI()
    server = ls.LitServer(api, fast_queue=True, accelerator="cpu", timeout=1000, workers_per_device=1)
    server.run(port=8000)
