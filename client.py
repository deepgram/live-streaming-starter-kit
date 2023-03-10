import asyncio
import websockets
import json

# Mimic sending a real-time stream by sending this many seconds of audio at a time.
# Used for file "streaming" only.
REALTIME_RESOLUTION = 0.250

encoding_samplewidth_map = {
    'linear16': 2,
    'mulaw': 1
}

async def audio_stream():
    audio_file = "preamble.flac"
    # TODO consider changing these to CLI variables
    data = open(audio_file, "rb").read()
    encoding = "flac"
    sample_rate = 8000
    channels = 1

    url = f"ws://localhost:5000?encoding={encoding}&sample_rate={sample_rate}&channels={channels}"

    async with websockets.connect(url) as ws:
        print('🟢 (1/5) Successfully opened streaming connection')

        async def sender(ws):
            print(f'🟢 (2/5) Ready to stream data')
            nonlocal data

            # For audio formats with non-variable sample widths,
            # we can do some calculations and send audio in real-time
            sample_width = encoding_samplewidth_map.get(encoding)
            if sample_width:
                # How many bytes are contained in one second of audio?
                byte_rate = sample_width * sample_rate * channels
                # How many bytes are in `REALTIME_RESOLUTION` seconds of audio?
                chunk_size = int(byte_rate * REALTIME_RESOLUTION)
            # Otherwise, we'll send an arbitrary chunk size
            else:
                chunk_size = 5000

            while len(data):
                chunk, data = data[:chunk_size], data[chunk_size:]
                # Mimic real-time by waiting `REALTIME_RESOLUTION` seconds
                # before the next packet.
                await asyncio.sleep(REALTIME_RESOLUTION)
                # Send the data
                await ws.send(chunk)
                
            await ws.send(json.dumps({ "type": "CloseStream" }))
            print('🟢 (4/5) Successfully closed connection, waiting for final messages if necessary')
            return

        async def receiver(ws):
            first_message = True
            async for msg in ws:
                if first_message:
                    print("🟢 (3/5) Successfully receiving server messages")
                    first_message = False

                res = json.loads(msg)
                if res.get('msg'):
                    # receive response from the server
                    print("Server message:", res.get('msg'))

                if res.get('filename'):
                    raw_filename = f"{res.get('filename').split('.')[0]}.raw"
                    print(f"🟢 (5/5) Sent audio data was stored in {raw_filename}")
                    if res.get('filename').split('.')[1] != 'raw':
                        print(f"🟢 (5/5) Sent audo data was also containerized and saved in {res.get('filename')}")

            return
            
        functions = [
            asyncio.ensure_future(sender(ws)),
            asyncio.ensure_future(receiver(ws))
        ]
        await asyncio.gather(*functions)

if __name__ == '__main__':
    try:
        asyncio.get_event_loop().run_until_complete(audio_stream())
    except websockets.exceptions.InvalidStatusCode as e:
        print(f'🔴 ERROR: Could not connect to server! {e}')