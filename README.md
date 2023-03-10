# Deepgram Streaming Test Suite

If you're looking to get started with Deepgram's audio streaming capabilities, our streaming test suite is the perfect place to begin. The test suite provides sample code that allows you to easily stream basic audio to Deepgram, ensuring that you have the necessary foundation to build custom integrations.

<img width="798" alt="image" src="https://user-images.githubusercontent.com/3937986/221058079-1aedc658-c5ef-4956-b529-ed7923424130.png">

Before diving into building your own integration, we highly recommend running through the steps in our test suite at least once to ensure that you can stream sample audio to Deepgram successfully. This will help you avoid many potential issues and streamline the integration process for sending your own audio to our system.

The test suite includes many ways to help diagnose problems. If you encounter issues, the test suite will provide more details on the error as well as steps to fix it.

With our streaming test suite, you can feel confident that you are laying a solid foundation for your audio streaming needs. Let's get started!

## Set Up

### Prerequisites

You must have:

- Python >= 3.6+
- [portaudio](http://portaudio.com/), if you plan to stream audio from your microphone
- A valid Deepgram API key (you can create one in our [Console](https://console.deepgram.com/))

### Installation

1. Check out the [streaming test suite](https://github.com/deepgram/streaming-test-suite/) repository
2. `pip install requirements.txt` 

## Streaming a Local Source

The first step in getting started with Deepgram's audio streaming capabilities is to learn how to stream a local audio source to Deepgram. This simple task allows you to learn the basic concepts of how Deepgram's API works without worrying about complexities that arise with other audio sources. Additionally, it ensures that you can receive results from Deepgram in your development environment.

The streaming test suite provides sample code that facilitates this process. Before building your own integration, we recommend running this code at least once to make sure that you can stream audio to Deepgram successfully. 

### Stream A File

While streaming a file isn’t our recommended way to use Deepgram’s real-time transcription service (we suggest our [pre-recorded API](https://developers.deepgram.com/documentation/getting-started/prerecorded/) for that), it’s a quick and easy way to make sure your API key and network are functioning correctly.

Just run the following command:

`python test_suite.py -k YOUR_DEEPGRAM_API_KEY`

> 💡 Make sure to replace `YOUR_DEEPGRAM_API_KEY` with an API key generated from our [Console](https://console.deepgram.com/).

This will stream the included file, `preamble.wav`, to Deepgram and print out transcripts to your terminal.

You can also stream your own WAV file by running:

`python test_suite.py -k YOUR_DEEPGRAM_API_KEY -i /path/to/audio.wav`  

To check out how this functionality is implemented, look at the conditional `elif method == 'wav'` in our `sender` function.

### Stream Your Microphone

The streaming test suite also has the ability to send audio from your microphone to Deepgram for transcription. 

First, make sure pyaudio and its portaudio dependency are installed, and you have a microphone connected to your computer. Then, run:

`python test_suite.py -k YOUR_DEEPGRAM_API_KEY -i mic` 

## Subtitle Generation

In addition to printing transcripts to the terminal, the test suite can also wrap Deepgram’s responses in two common subtitle formats, SRT or VTT. 

To generate SRT or VTT files, add the `-o/--output` parameter when running the test suite:

`python test_suite.py -k YOUR_DEEPGRAM_API_KEY [-i mic|/path/to/audio.wav] [-o text|vtt|srt]`

This parameter defaults to `text`, which outputs responses to your terminal.

---

If you were able to successfully stream local audio and receive a transcript, you’re ready to move on to more complex integrations!
