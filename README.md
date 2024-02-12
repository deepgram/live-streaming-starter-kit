# Deepgram Live Streaming Starter Kit

[![Discord](https://dcbadge.vercel.app/api/server/xWRaCDBtW4?style=flat)](https://discord.gg/xWRaCDBtW4)

Deepgram's Live Streaming Starter Kit will take you step by step through the process of getting up and running with Deepgram's live streaming API.


# Documentation

Please refer to our [Documentation](https://developers.deepgram.com/docs/getting-started-with-the-streaming-test-suite) on how to use the Streaming Starter Kit.

# Getting an API Key

🔑 To access the Deepgram API you will need a [free Deepgram API Key](https://console.deepgram.com/signup?jump=keys).

# Requirements

- Python >= 3.6+
- [portaudio](http://portaudio.com/)
- A valid Deepgram API key

# Installation

1. Clone the [streaming starter kit](https://github.com/deepgram/streaming-test-suite/) repository
2. Install [portaudio](http://portaudio.com/) (if not already installed)
3. Run `pip install -r requirements.txt`

## Port Audio

If you use Homebrew or Conda, we recommend installing with `brew install portaudio` or `conda install portaudio`.

Otherwise, you can download a zip file from [portaudio.com](http://portaudio.com/), unzip it, and then consult [PortAudio's docs](http://www.portaudio.com/docs/v19-doxydocs/pages.html) as a reference for how to build the package on your operating system. For Linux and MacOS, the build command within the top-level `portaudio/` directory is `./configure && make`.

PortAudio is known to have compatibility issues on Windows. However, this dependency is only required if you plan to stream audio from your microphone.