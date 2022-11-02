""" A simple example which prints out parsed streaming responses.
    Python version: 3.6+
    Dependencies (use `pip install X` to install a dependency):
      - websockets
    Usage:
      python deepgram_streaming.py -k 'YOUR_DEEPGRAM_API_KEY' /path/to/audio.wav
    Limitations:
      - Only parses signed, 16-bit little-endian encoded WAV files.
"""

import argparse
import asyncio
import json
import os
import sys
import wave
import websockets
import validators

from datetime import datetime
startTime = datetime.now()

# Mimic sending a real-time stream by sending this many seconds of audio at a time.
REALTIME_RESOLUTION = 0.250

async def run(data, key, channels, sample_width, sample_rate, filepath):
    # How many bytes are contained in one second of audio.
    byte_rate = sample_width * sample_rate * channels
    # print('ℹ️ This demonstration will print all finalized results, not interim results.')

    # Connect to the real-time streaming endpoint, attaching our credentials.
    async with websockets.connect(
        f'wss://api.deepgram.com/v1/listen?punctuate=true&channels={channels}&sample_rate={sample_rate}&encoding=linear16',
        extra_headers={
            'Authorization': 'Token {}'.format(key)
        }
    ) as ws:
        print(f'ℹ️  Request ID: {ws.response_headers.get("dg-request-id")}')
        print('🟢 (1/5) Successfully opened Deepgram streaming connection')

        async def sender(ws):
            """ Sends the data, mimicking a real-time connection.
            """
            nonlocal data
            try:
                print(f'🟢 (2/5) Preparing to stream {filepath} to Deepgram')
                while len(data):
                    # How many bytes are in `REALTIME_RESOLUTION` seconds of audio?
                    i = int(byte_rate * REALTIME_RESOLUTION)
                    chunk, data = data[:i], data[i:]
                    # Send the data
                    await ws.send(chunk)
                    # Mimic real-time by waiting `REALTIME_RESOLUTION` seconds
                    # before the next packet.
                    await asyncio.sleep(REALTIME_RESOLUTION)

                await ws.send(json.dumps({                                                   
                    'type': 'CloseStream'
                }))
                print('🟢 (5/5) Successfully closed Deepgram connection, waiting for final transcripts if necessary')
            except Exception as e: 
                print(f'🔴 ERROR: Something happened while sending, {e}')
                raise e
    
        async def receiver(ws):
            """ Print out the messages received from the server.
            """
            first_receive = True
            
            async for msg in ws:
                res = json.loads(msg)
                if first_receive:
                    print("🟢 (3/5) Data stream began successfully")
                    print("🟢 (4/5) Began receiving transcription")
                    first_receive = False
                try:
                    # To see interim results in this demo, remove the conditional `if res['is_final']:`.
                    if res.get('is_final'):
                        transcript = res.get('channel', {})\
                        .get('alternatives', [{}])[0]\
                        .get('transcript', '')
                        if transcript:
                            print(f'{transcript}')
                    # handle end of stream
                    if res.get('created'):
                        print(f'🟢 Request finished with a duration of {res["duration"]} seconds. Exiting!')
                except KeyError:
                    print(f'🔴 ERROR: Received unexpected API response! {msg}')

        await asyncio.gather(*[
            asyncio.ensure_future(sender(ws)),
            asyncio.ensure_future(receiver(ws))
        ])

def validate_input(input):
    if input.startswith('mic'):
        return input

    elif input.endswith('wav'):
        if os.path.exists(input):
            return input
    
    elif validators.url(input):
        return input
        
    raise argparse.ArgumentTypeError(f'{input} is an invalid input. Please enter the path to a WAV file, a stream URL, or "mic" to stream from your microphone.')

def parse_args():
    """ Parses the command-line arguments.
    """
    parser = argparse.ArgumentParser(description='Submits data to the real-time streaming endpoint.')
    parser.add_argument('-k', '--key', required=True, help='YOUR_DEEPGRAM_API_KEY (authorization)')
    parser.add_argument('-i', '--input', help='Input to stream to Deepgram. Can be the path to a WAV file, a stream URL, or "mic" to stream from your microphone. Defaults to preamble.wav', nargs='?', const=1, default='preamble.wav', type=validate_input)
    return parser.parse_args()

def main():
    """ Entrypoint for the example.
    """
    # Parse the command-line arguments.
    args = parse_args()
    input = args.input

    if input.startswith('mic'):
        # set up mic
        return

    elif input.endswith('wav'):
        if os.path.exists(input):
            # Open the audio file.
            with wave.open(input, 'rb') as fh:
                (channels, sample_width, sample_rate, num_samples, _, _) = fh.getparams()
                assert sample_width == 2, 'WAV data must be 16-bit.'
                data = fh.readframes(num_samples)
                # TODO: kick off the process
        else:
            raise argparse.ArgumentTypeError(f'🔴 {args.input} is not a valid file.')
    
    elif validators.url(input):
        return input
        
    else:
        raise argparse.ArgumentTypeError(f'🔴 {input} is an invalid input. Please enter the path to a WAV file, a stream URL, or "mic" to stream from your microphone.')


    # Run the example.
    try:
        asyncio.run(run(data, args.key, channels, sample_width, sample_rate, args.input))
    except websockets.exceptions.InvalidStatusCode as e:
        print(f'🔴 ERROR: Could not connect to Deepgram! {e.headers.get("dg-error")}')
        print(f'🔴 Please contact Deepgram Support with request ID {e.headers.get("dg-request-id")}')
        # TODO: add how to contact support
        return
    except websockets.exceptions.ConnectionClosedError as e:
        error_description = f'Unknown websocket error.'
        print(f'🔴 ERROR: Deepgram connection unexpectedly closed with code {e.code} and payload {e.reason}')
        
        if e.reason == 'DATA-0000':
            error_description = "The payload cannot be decoded as audio. It is either not audio data or is a codec unsupported by Deepgram."
        elif e.reason == 'NET-0000':
            error_description = "The service has not transmitted a Text frame to the client within the timeout window. This may indicate an issue internally in Deepgram's systems or could be due to Deepgram not receiving enough audio data to transcribe a frame."
        elif e.reason == 'NET-0001':
            error_description = "The service has not received a Binary frame from the client within the timeout window. This may indicate an internal issue in Deepgram's systems, the client's systems, or the network connecting them."
        
        print(f'🔴 {error_description}')
        print(f'🔴 Please contact Deepgram Support with the request ID listed above.')
        return
    except Exception as e:
        print(f'🔴 ERROR: Something went wrong! {e}')
        return

"""
TODO: 

* step by step tutorial?

"""


if __name__ == '__main__':
    sys.exit(main() or 0)