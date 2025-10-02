"""
MCU Game Timers by donutcat
Primary file, speakerbox, last updated 2025-10-01
"""

import espnow  # type: ignore
from asyncio import sleep, run
from hardware import AUDIO_OUT
from audio_commands import Sound_Control

e = espnow.ESPNow(buffer_size=1024)

sounds = Sound_Control(AUDIO_OUT)
sounds.set_vol(30)


async def main():
    print("Starting main")
    message = b"empty"
    msg_dec = message.decode()
    while True:
        if e:
            msg = e.read()
            if msg != None and msg.msg != message:
                print(msg.msg)
                message = msg.msg
                msg_dec = message.decode()
                if msg_dec == "Start":
                    sounds.play_track(28)
                    await sleep(0.1)
                elif msg_dec == "60":
                    sounds.play_track(27)
                    await sleep(0.1)
                elif msg_dec == "30":
                    sounds.play_track(26)
                    await sleep(0.1)
                elif msg_dec == "10":
                    for i in range(10, -1, -1):
                        sounds.play_track(i + 15)
                        await sleep(1)
                elif msg_dec in ["Pause", "Resume"]:
                    sounds.play_track(35)
                    await sleep(0.1)
                else:
                    pass


if __name__ == "__main__":
    run(main())
