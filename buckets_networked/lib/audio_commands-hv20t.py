"""
A translation library for working with UART commands for Catalex MP3 modules.
"""
from busio import UART


class Sound_Control:
    """Sound control via UART object via Catalex protocol"""

    def __init__(self, audio: UART):
        self.audio_out = audio

    cmd_base = bytearray([0x7E, 0xFF, 0x06, 0x00, 0x00, 0x00, 0x00, 0xEF])

    def play_track(self, track: int):
        """Plays a track based on the numerical name"""
        play_track = self.cmd_base
        play_track[3] = 0x03
        play_track[6] = int(hex(track))
        self.audio_out.write(play_track)

    def vol_up(self):
        """Increments volume by one"""
        vol_up = self.cmd_base
        vol_up[3] = 0x04
        self.audio_out.write(vol_up)

    def vol_down(self):
        """Decrements volume by one"""
        vol_down = self.cmd_base
        vol_down[3] = 0x05
        self.audio_out.write(vol_down)

    def set_vol(self, level=30):
        """Sets volume level from 0-30"""
        set_vol = self.cmd_base
        set_vol[3] = 0x06
        set_vol[6] = int(hex(level))
        self.audio_out.write(set_vol)

    def play_at_vol(self, track=1, vol=30):
        """Plays a track at a set volume"""
        play_at_vol = self.cmd_base
        play_at_vol[3] = 0x22
        play_at_vol[5] = int(hex(vol))
        play_at_vol[6] = int(hex(track))
        self.audio_out.write(play_at_vol)
