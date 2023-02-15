import asyncio
import websockets
import time
from urllib.parse import parse_qs
import pydub
import tempfile
import json
from io import BytesIO

def save_audio(encoding, sample_rate, channels, data):
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


    CODEC_EXTENSION_MAP = {
        'linear16': 'wav',
        'flac': 'flac',
        'mulaw': 'mulaw',
        'amr-nb': 'amr',
        'amr-wb': 'amr',
        'opus': 'opus',
        'speex': 'spx'
    }

    codec = codec_map.get(encoding)
    extension = CODEC_EXTENSION_MAP.get(encoding)
    print(codec)

    filename = f'tmp.{extension}'
    raw_audio = pydub.AudioSegment.from_raw(BytesIO(data), sample_width=2, channels=channels, frame_rate=sample_rate)
    raw_audio.export(filename)
    # create a temporary file
    #temp = tempfile.NamedTemporaryFile(mode="wb", delete=False)
    #filename = temp.name
    #temp.close()

    print(filename)
    # write the data to the temporary file
    #with open(filename, 'wb') as f:
    #    f.write(data)

    #import ipdb; ipdb.set_trace()

    
    # create an audio segment from the file
    #audio = pydub.AudioSegment.from_file(filename, format=extension)

    # set the sample rate
    #audio = audio.set_frame_rate(sample_rate)

    # save the audio to a file
    #audio.export(filename)

async def audio_handler(websocket, path):
    parsed_path = parse_qs(path)
    # extract encoding and sample rate from the query string
    encoding = parsed_path.get('encoding', [''])[0]
    sample_rate = int(parsed_path.get('sample_rate', [0])[0])
    channels = int(parsed_path.get('channels', [1])[0])

    print(sample_rate)

    sample_width = 2 # assuming 16-bit encoding
    # How many bytes are contained in one second of audio?
    expected_bytes_per_second = sample_width * sample_rate * channels
    
    start_time = time.time()
    bytes_received = 0
    audio_data = bytearray(b'')

    async for message in websocket:
        #print(message)
        # handle text messages
        if not isinstance(message, bytes):
            json_message = json.loads(message)
            if json_message.get('type') == 'CloseStream':
                # save the audio data to a file
                save_audio(encoding, sample_rate, channels, audio_data)
                await websocket.close(code=1000, reason="Connection closed")
                return
            else:
                await websocket.close(code=1011, reason='Invalid frame sent')
                return

        # process the audio data received from the client
        bytes_received += len(message)
        
        audio_data += message
        
        # calculate the elapsed time
        elapsed_time = time.time() - start_time
        
        # validate the data rate
        if bytes_received / elapsed_time > expected_bytes_per_second:
            await websocket.close(code=1011, reason="Data rate too high")
            return

    await websocket.close(code=1000, reason="Connection closed")

if __name__ == '__main__':
    start_server = websockets.serve(audio_handler, 'localhost', 5000)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
