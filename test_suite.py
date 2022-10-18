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
import sys
import wave
import websockets

from datetime import datetime
startTime = datetime.now()

# Mimic sending a real-time stream by sending this many seconds of audio at a time.
REALTIME_RESOLUTION = 0.250

async def run(data, key, channels, sample_width, sample_rate, filepath):
    # How many bytes are contained in one second of audio.
    byte_rate = sample_width * sample_rate * channels
    print('This demonstration will print all finalized results, not interim results.')

    # Connect to the real-time streaming endpoint, attaching our credentials.
    async with websockets.connect(
        f'wss://api.deepgram.com/v1/listen?punctuate=true&channels={channels}&sample_rate={sample_rate}&encoding=linear16',
        extra_headers={
            'Authorization': 'Token {}'.format(key)
        }
    ) as ws:
        print("🟢 Successfully opened Deepgram streaming connection")

        
        async def sender(ws):
            """ Sends the data, mimicking a real-time connection.
            """
            nonlocal data
            try:
                print("🎙 Sending data...")
                while len(data):
                    # How many bytes are in `REALTIME_RESOLUTION` seconds of audio?
                    i = int(byte_rate * REALTIME_RESOLUTION)
                    chunk, data = data[:i], data[i:]
                    # Send the data
                    await ws.send(chunk)
                    # Mimic real-time by waiting `REALTIME_RESOLUTION` seconds
                    # before the next packet.
                    await asyncio.sleep(REALTIME_RESOLUTION)

                # An empty binary message tells Deepgram that no more audio
                # will be sent. Deepgram will close the connection once all
                # audio has finished processing.
                await ws.send(json.dumps({                                                   
                    'type': 'CloseStream'
                }))
                print('🟢 Successfully closed Deepgram connection')
            except websockets.exceptions.ConnectionClosedError as e:
                print(f'🔴 ERROR: Deepgram connection unexpectedly closed! {e}')
                return
            except Exception as e: 
                print(f'Error while sending: {e}')
                raise e
    
        async def receiver(ws):
            """ Print out the messages received from the server.
            """
            print("💬 Waiting to receive transcript...")
            async for msg in ws:
                res = json.loads(msg)
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
                        print(f'🟢 Request finished with a duration of {res["duration"]} seconds')
                except KeyError:
                    print(f'🔴 ERROR: Received unexpected API response! {msg}')

        await asyncio.gather(*[
            asyncio.ensure_future(sender(ws)),
            asyncio.ensure_future(receiver(ws))
        ])

def parse_args():
    """ Parses the command-line arguments.
    """
    parser = argparse.ArgumentParser(description='Submits data to the real-time streaming endpoint.')
    parser.add_argument('-k', '--key', required=True, help='YOUR_DEEPGRAM_API_KEY (authorization)')
    parser.add_argument('input', help='Input file.')
    return parser.parse_args()

def main():
    """ Entrypoint for the example.
    """
    # Parse the command-line arguments.
    args = parse_args()

    # Open the audio file.
    with wave.open(args.input, 'rb') as fh:
        (channels, sample_width, sample_rate, num_samples, _, _) = fh.getparams()
        assert sample_width == 2, 'WAV data must be 16-bit.'
        data = fh.readframes(num_samples)

    # Run the example.
    try:
        asyncio.run(run(data, args.key, channels, sample_width, sample_rate, args.input))
    except websockets.exceptions.InvalidStatusCode as e:
        print(f'🔴 ERROR: Could not connect to Deepgram! {e.headers.get("dg-error")}')
        print(f'🔴 Please contact Deepgram Support with request ID {e.headers.get("dg-request-id")}')
        return
    except websockets.exceptions.ConnectionClosedError as e:
        print(f'🔴 ERROR: Deepgram connection unexpectedly closed! {e}')
        return
    except Exception as e:
        print(f'🔴 ERROR: Something went wrong! {e}')
        return


if __name__ == '__main__':
    sys.exit(main() or 0)