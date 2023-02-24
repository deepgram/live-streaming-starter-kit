import asyncio
import websockets
import time
from urllib.parse import parse_qs
import pydub
import tempfile
import json
from io import BytesIO

def save_audio(encoding, sample_rate, sample_width, channels, data):
    # map the encoding string to a pydub codec
    codec_map = {
        'linear16': 's16le',
        'flac': 'flac',
        'mulaw': 'mulaw',
        'amr-nb': 'amr_nb',
        'amr-wb': 'amr_wb',
        'opus': 'opus',
        'speex': 'speex'
    }


    codec_extension_map = {
        'linear16': 'wav',
        'flac': 'flac',
        'mulaw': 'mulaw',
        'amr-nb': 'amr',
        'amr-wb': 'amr',
        'opus': 'opus',
        'speex': 'spx'
    }

    try:
        extension = codec_extension_map[encoding]
    except:
        return "ERROR: Unsupported codec!"

    filename = f'tmp.{extension}'
    raw_audio = pydub.AudioSegment.from_raw(BytesIO(data), sample_width=sample_width, channels=channels, frame_rate=sample_rate)
    raw_audio.export(filename)

    return filename

# utility to send log messages to both server and client
async def logger(websocket, message):
    print(message)
    await websocket.send(json.dumps({
        "msg": message
    }))

async def audio_handler(websocket, path):
    await logger(websocket, "New websocket connection opened")

    # extract encoding and sample rate from the query string
    parsed_path = parse_qs(path.split("?")[1])
    encoding = parsed_path.get('encoding', [''])[0]
    sample_rate = int(parsed_path.get('sample_rate', [0])[0])
    channels = int(parsed_path.get('channels', [1])[0])

    await logger(websocket, f"Expecting audio data with encoding {encoding}, {sample_rate} sample rate, and {channels} channel(s)")

    sample_width = 2 # assuming 16-bit encoding
    # How many bytes are contained in one second of audio?
    expected_bytes_per_second = sample_width * sample_rate * channels
    
    start_time = time.time()
    bytes_received = 0
    audio_data = bytearray(b'')

    try:
        async for message in websocket:
            # handle binary messages (audio data)
            if isinstance(message, bytes):
                # process the audio data received from the client
                bytes_received += len(message)
                audio_data += message
                
                # calculate the elapsed time
                elapsed_time = time.time() - start_time
                # validate the data rate
                if bytes_received / elapsed_time > expected_bytes_per_second:
                    await websocket.close(code=1011, reason="Data rate too high")
                    return
                await logger(websocket, f"Received {bytes_received} bytes of data")

            # handle stream closures or other text messages
            else:
                json_message = json.loads(message)
                if json_message.get('type') == 'CloseStream':
                    # save the audio data to a file
                    filename = save_audio(encoding, sample_rate, sample_width, channels, audio_data)
                    await logger(websocket, f"Saved audio data to {filename}")
                    await websocket.send(json.dumps({ 'total_bytes': len(audio_data)}))
                    return
                else:
                    await websocket.close(code=1011, reason='Invalid frame sent')
                    return
                
    except websockets.exceptions.ConnectionClosedOK:
        print("Client closed connection")

async def run_server():
    server = await websockets.serve(audio_handler, 'localhost', 5000)
    print("Server is now listening for new connections")
    await server.wait_closed()

if __name__ == '__main__':
    asyncio.run(run_server())
