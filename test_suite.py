import argparse
import os
import sys
import wave
import threading
import httpx
import websockets
from time import sleep
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveOptions,
    LiveTranscriptionEvents,
    Microphone,
)

from datetime import datetime

startTime = datetime.now()

# entire transcription contents
all_transcripts = []

# constants
CHANNELS = 1
RATE = 16000
CHUNK = 8000

# Mimic sending a real-time stream by sending this many seconds of audio at a time.
# Used for file "streaming" only.
REALTIME_RESOLUTION = 0.250

subtitle_line_counter = 0


def subtitle_time_formatter(seconds, separator):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02}{separator}{millis:03}"


def subtitle_formatter(response, format):
    global subtitle_line_counter
    subtitle_line_counter += 1

    start = response.start
    end = start + response.duration
    transcript = response.channel.alternatives[0].transcript

    separator = "," if format == "srt" else "."
    prefix = "- " if format == "vtt" else ""
    subtitle_string = (
        f"{subtitle_line_counter}\n"
        f"{subtitle_time_formatter(start, separator)} --> "
        f"{subtitle_time_formatter(end, separator)}\n"
        f"{prefix}{transcript}\n\n"
    )

    return subtitle_string


def run(key, method, format, **kwargs):
    if key == "":
        print(
            "[WARNING] API Key not set... will attempt to use DEEPGRAM_API_KEY environment variable."
        )

    config = DeepgramClientOptions(url=kwargs["host"], options={"keepalive": "true"})
    deepgram = DeepgramClient(key, config)

    encoding = ""
    sample_rate = ""
    if method == "mic" or method == "wav":
        encoding = "linear16"
        sample_rate = kwargs["sample_rate"]

    options = LiveOptions(
        punctuate=True,
        language="en-US",
        encoding=encoding,
        channels=kwargs["channels"],
        sample_rate=sample_rate,
        model=kwargs["model"],
        tier=kwargs["tier"],
    )

    def on_message(self, result, **kwargs):
        if result is None:
            return
        if self.first_message:
            print(
                "🟢 (3/5) Successfully receiving Deepgram messages, waiting for finalized transcription..."
            )
            self.first_message = False

        transcript = result.channel.alternatives[0].transcript
        if kwargs["timestamps"]:
            words = result.channel.alternatives[0].words
            start = words[0]["start"] if words else None
            end = words[-1]["end"] if words else None
            transcript += " [{} - {}]".format(start, end) if (start and end) else ""
        if transcript != "":
            if self.first_transcript:
                print("🟢 (4/5) Began receiving transcription")
                # if using webvtt, print out header
                if format == "vtt":
                    print("WEBVTT\n")
                self.first_transcript = False
            if format == "vtt" or format == "srt":
                transcript = subtitle_formatter(result, format)
            transcript = subtitle_formatter(result, format == "srt")
            print(transcript)

            all_transcripts.append(transcript)

    def on_metadata(self, metadata, **kwargs):
        if metadata is None:
            return
        print(f"\n{metadata}\n")

    def on_error(self, error, **kwargs):
        if error is None:
            return
        print(f"\n{error}\n")

    dg_connection = deepgram.listen.live.v("1")

    dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
    # dg_connection.on(LiveTranscriptionEvents.Metadata, on_metadata)
    dg_connection.on(LiveTranscriptionEvents.Error, on_error)

    dg_connection.start(
        options=options,
        members=dict(first_message=True, first_transcript=True),
        **dict(kwargs),
    )

    print("\n\nPress Enter to stop recording...\n\n")
    print("🟢 (1/5) Successfully opened Deepgram streaming connection")
    print(
        f'🟢 (2/5) Ready to stream {method if (method == "mic" or method == "url") else kwargs["filepath"]} audio to Deepgram{". Speak into your microphone to transcribe." if method == "mic" else ""}'
    )

    if method == "mic":
        # create microphone
        microphone = Microphone(dg_connection.send)

        # start microphone
        microphone.start()

        # signal finished
        input("")

        # stop microphone
        microphone.finish()
    elif method == "url":
        lock_exit = threading.Lock()
        exit = False

        # define a worker thread
        def httpThread():
            with httpx.stream("GET", kwargs["url"]) as r:
                for data in r.iter_bytes():
                    lock_exit.acquire()
                    if exit:
                        break
                    lock_exit.release()

                    dg_connection.send(data)

        # start the worker thread
        myHttp = threading.Thread(target=httpThread)
        myHttp.start()

        # signal finished
        input("")

        lock_exit.acquire()
        exit = True
        lock_exit.release()

        # Wait for the HTTP thread to close and join
        myHttp.join()
    elif method == "wav":
        # wav data
        data = kwargs["data"]

        lock_exit = threading.Lock()
        exit = False

        def wavThread():
            nonlocal data

            # How many bytes are contained in one second of audio?
            byte_rate = (
                kwargs["sample_width"] * kwargs["sample_rate"] * kwargs["channels"]
            )
            # How many bytes are in `REALTIME_RESOLUTION` seconds of audio?
            chunk_size = int(byte_rate * REALTIME_RESOLUTION)

            try:
                while len(data):
                    lock_exit.acquire()
                    if exit:
                        break
                    lock_exit.release()

                    chunk, data = data[:chunk_size], data[chunk_size:]
                    # Mimic real-time by waiting `REALTIME_RESOLUTION` seconds
                    # before the next packet.
                    sleep(REALTIME_RESOLUTION)
                    # Send the data
                    dg_connection.send(chunk)
            except Exception as e:
                print(f"🔴 ERROR: Something happened while sending, {e}")
                raise e

        # start the worker thread
        myWav = threading.Thread(target=wavThread)
        myWav.start()

        # signal finished
        input("")

        lock_exit.acquire()
        exit = True
        lock_exit.release()

        # Wait for the HTTP thread to close and join
        myWav.join()

    dg_connection.finish()
    print(
        "🟢 (5/5) Successfully closed Deepgram connection, waiting for final transcripts if necessary"
    )


def validate_input(input):
    if input.lower().startswith("mic"):
        return input

    elif input.lower().endswith("wav"):
        if os.path.exists(input):
            return input

    elif input.lower().startswith("http"):
        return input

    raise argparse.ArgumentTypeError(
        f'{input} is an invalid input. Please enter the path to a WAV file, a valid stream URL, or "mic" to stream from your microphone.'
    )


def validate_format(format):
    if (
        format.lower() == ("text")
        or format.lower() == ("vtt")
        or format.lower() == ("srt")
    ):
        return format

    raise argparse.ArgumentTypeError(
        f'{format} is invalid. Please enter "text", "vtt", or "srt".'
    )


def parse_args():
    """Parses the command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Submits data to the real-time streaming endpoint."
    )
    parser.add_argument(
        "-k", "--key", help="YOUR_DEEPGRAM_API_KEY (authorization)", default=""
    )
    parser.add_argument(
        "-i",
        "--input",
        help='Input to stream to Deepgram. Can be "mic" to stream from your microphone (requires pyaudio), the path to a WAV file, or the URL to a direct audio stream. Defaults to the included file preamble.wav',
        nargs="?",
        const=1,
        default="preamble.wav",
        type=validate_input,
    )
    parser.add_argument(
        "-m",
        "--model",
        help="Which model to make your request against. Defaults to none specified. See https://developers.deepgram.com/docs/models-overview for all model options.",
        nargs="?",
        const="",
        default="general",
    )
    parser.add_argument(
        "-t",
        "--tier",
        help="Which model tier to make your request against. Defaults to none specified. See https://developers.deepgram.com/docs/tier for all tier options.",
        nargs="?",
        const="",
        default="base",
    )
    parser.add_argument(
        "-ts",
        "--timestamps",
        help="Whether to include timestamps in the printed streaming transcript. Defaults to False.",
        nargs="?",
        const=1,
        default=False,
    )
    parser.add_argument(
        "-f",
        "--format",
        help='Format for output. Can be "text" to return plain text, "VTT", or "SRT". If set to VTT or SRT, the audio file and subtitle file will be saved to the data/ directory. Defaults to "text".',
        nargs="?",
        const=1,
        default="text",
        type=validate_format,
    )
    parser.add_argument(
        "--host",
        help='Point the test suite at a specific Deepgram URL (useful for on-prem deployments). Takes "{{wss|ws}}://hostname[:port]" as its value. Defaults to "wss://api.deepgram.com".',
        nargs="?",
        const=1,
        default="api.deepgram.com",
    )
    return parser.parse_args()


def main():
    """Entrypoint for the example."""
    # Parse the command-line arguments.
    args = parse_args()
    input = args.input
    format = args.format.lower()
    host = args.host

    try:
        if input.lower().startswith("mic"):
            run(
                args.key,
                "mic",
                format,
                model=args.model,
                tier=args.tier,
                host=host,
                channels=CHANNELS,
                sample_rate=RATE,
                timestamps=args.timestamps,
            )
        elif input.lower().endswith("wav"):
            if os.path.exists(input):
                with wave.open(input, "rb") as fh:
                    (
                        channels,
                        sample_width,
                        sample_rate,
                        num_samples,
                        _,
                        _,
                    ) = fh.getparams()
                    assert sample_width == 2, "WAV data must be 16-bit."
                    data = fh.readframes(num_samples)
                run(
                    args.key,
                    "wav",
                    format,
                    model=args.model,
                    tier=args.tier,
                    data=data,
                    channels=channels,
                    sample_width=sample_width,
                    sample_rate=sample_rate,
                    filepath=args.input,
                    host=host,
                    timestamps=args.timestamps,
                )
            else:
                raise argparse.ArgumentTypeError(
                    f"🔴 {args.input} is not a valid WAV file."
                )

        elif input.lower().startswith("http"):
            # run(args.key, "url", format, model=args.model, tier=args.tier, url=input, host=host, timestamps=args.timestamps)
            run(
                args.key,
                "url",
                format,
                model=args.model,
                tier=args.tier,
                url=input,
                host=host,
                channels=CHANNELS,
                sample_rate=RATE,
                timestamps=args.timestamps,
            )

        else:
            raise argparse.ArgumentTypeError(
                f'🔴 {input} is an invalid input. Please enter the path to a WAV file, a valid stream URL, or "mic" to stream from your microphone.'
            )

    except websockets.exceptions.InvalidStatusCode as e:
        print(f'🔴 ERROR: Could not connect to Deepgram! {e.headers.get("dg-error")}')
        print(
            f'🔴 Please contact Deepgram Support (developers@deepgram.com) with request ID {e.headers.get("dg-request-id")}'
        )
        return
    except websockets.exceptions.ConnectionClosedError as e:
        error_description = f"Unknown websocket error."
        print(
            f"🔴 ERROR: Deepgram connection unexpectedly closed with code {e.code} and payload {e.reason}"
        )

        if e.reason == "DATA-0000":
            error_description = "The payload cannot be decoded as audio. It is either not audio data or is a codec unsupported by Deepgram."
        elif e.reason == "NET-0000":
            error_description = "The service has not transmitted a Text frame to the client within the timeout window. This may indicate an issue internally in Deepgram's systems or could be due to Deepgram not receiving enough audio data to transcribe a frame."
        elif e.reason == "NET-0001":
            error_description = "The service has not received a Binary frame from the client within the timeout window. This may indicate an internal issue in Deepgram's systems, the client's systems, or the network connecting them."

        print(f"🔴 {error_description}")
        # TODO: update with link to streaming troubleshooting page once available
        # print(f'🔴 Refer to our troubleshooting suggestions: ')
        print(
            f"🔴 Please contact Deepgram Support (developers@deepgram.com) with the request ID listed above."
        )
        return

    except websockets.exceptions.ConnectionClosedOK:
        return

    except Exception as e:
        print(f"🔴 ERROR: Something went wrong! {e}")
        return


if __name__ == "__main__":
    sys.exit(main() or 0)
