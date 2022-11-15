# Deepgram Streaming Test Suite

A simple Python example demonstrating the use of Deepgram's real-time transcription API.

## Requirements
* Python version: 3.6+
* Dependencies (use `pip install X` to install a dependency):
    * websockets
    * pyaudio (if streaming from microphone)

## Usage

`python test_suite.py -k 'YOUR_DEEPGRAM_API_KEY' [-i mic|/path/to/audio.wav]`

The `-i/--input` argument is optional. It can be set to either:

* `mic` - stream from your microphone (requires pyaudio)
* `/path/to/audio.wav` - the path to a signed, 16-bit little-endian encoded WAV file

If not set, the included file `preamble.wav` will be streamed.