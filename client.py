import asyncio
import websockets
import json

# Mimic sending a real-time stream by sending this many seconds of audio at a time.
# Used for file "streaming" only.
REALTIME_RESOLUTION = 0.250

async def audio_stream():
    data = open("out.opus", "rb").read()
    expected_bytes = len(data)
    encoding = "opus"
    sample_rate = 48000
    sample_width = 1
    channels = 1
    uri = f"ws://localhost:5000?encoding={encoding}&sample_rate={sample_rate}&channels={channels}"

    async with websockets.connect(uri) as ws:
        async def sender(ws):
            nonlocal data
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
            return

        async def receiver(ws):
            async for msg in ws:
                res = json.loads(msg)
                if res.get('msg'):
                    # receive response from the server
                    print("Server message:", res.get('msg'))
                if res.get('total_bytes'):
                    bytes_received = res.get('total_bytes')
                    if bytes_received == expected_bytes:
                        print(f"Server received all {expected_bytes} expected bytes of data")
                    else:
                        print(f"Error! Expected to send {expected_bytes} bytes of data, but server only received {bytes_received} bytes")
            return
            
        functions = [
            asyncio.ensure_future(sender(ws)),
            asyncio.ensure_future(receiver(ws))
        ]
        await asyncio.gather(*functions)

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(audio_stream())
