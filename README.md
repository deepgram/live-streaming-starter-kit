# Deepgram Streaming Test Suite

The streaming test suite is designed to ensure you can stream basic audio to Deepgram, before you begin building custom integrations.

## Requirements
* Python version: 3.6+
* Dependencies (use `pip install X` to install a dependency):
    * websockets
    * pyaudio (if streaming from microphone)

## Usage

`python test_suite.py -k 'YOUR_DEEPGRAM_API_KEY' [-i mic|/path/to/audio.wav] [-o text|vtt|srt]`

The `-i/--input` argument is optional. It can be set to either:

* `mic` - stream from your microphone (requires pyaudio)
* `/path/to/audio.wav` - the path to a signed, 16-bit little-endian encoded WAV file

The `-o/--output` argument is optional. It can be set to:

* `text` (default) - output the transcription returned by Deepgram in plain text
* `vtt` - output transcriptions in VTT format
* `srt` - output transcriptions in SRT format

If not set, the included file `preamble.wav` will be streamed.

## Development and Contributing

Interested in contributing? We ❤️ pull requests!

## Getting Help

We love to hear from you so if you have questions, comments or find a bug in the
project, let us know! You can either:

- [Open an issue](https://github.com/deepgram/streaming-test-suite/issues/new) on this repository
- Ask a question, share the cool things you're working on, or see what else we have going on in our [Community Forum](https://github.com/orgs/deepgram/discussions/)
- Tweet at us! We're [@DeepgramAI on Twitter](https://twitter.com/DeepgramAI)

## Further Reading

Check out the Developer Documentation at [https://developers.deepgram.com/](https://developers.deepgram.com/)