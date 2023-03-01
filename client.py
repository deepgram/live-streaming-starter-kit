import asyncio
import websockets
import json

# Mimic sending a real-time stream by sending this many seconds of audio at a time.
# Used for file "streaming" only.
REALTIME_RESOLUTION = 0.250

encoding_samplewidth_map = {
    'linear16': 2,
    'flac': 0,
    'mulaw': 1,
    'amr-nb': 0,
    'amr-wb': 0,
    'opus': 0,
    'speex': 0
}

async def audio_stream():
    # TODO consider changing these to CLI variables
    data = open("preamble.raw", "rb").read()
    encoding = "linear16"
    sample_rate = 8000
    channels = 1
    expected_bytes = len(data)

    url = f"ws://localhost:5000?encoding={encoding}&sample_rate={sample_rate}&channels={channels}"

    async with websockets.connect(url) as ws:
        print('🟢 (1/5) Successfully opened streaming connection')

        async def sender(ws):
            print(f'🟢 (2/5) Ready to stream data')
            nonlocal data
            # TODO make variable
            sample_width = encoding_samplewidth_map[encoding]
            # How many bytes are contained in one second of audio?
            byte_rate = sample_width * sample_rate * channels
            # How many bytes are in `REALTIME_RESOLUTION` seconds of audio?
            chunk_size = int(byte_rate * REALTIME_RESOLUTION)

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
                    print(f"🟢 (5/5) Sent data was containerized and saved in {res.get('filename')}")
                    print(f"🟢 (5/5) Raw data was stored in {raw_filename}")

                # TODO consider if this functionality should be removed
                # Since it only applies to file streaming and not true real-time caes 
                if res.get('total_bytes'):
                    bytes_received = res.get('total_bytes')
                    if bytes_received == expected_bytes:
                        print(f"Server expected {expected_bytes} bytes of data and received all bytes")
                    else:
                        print(f"Error! Expected to send {expected_bytes} bytes of data, but server only received {bytes_received} bytes")
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