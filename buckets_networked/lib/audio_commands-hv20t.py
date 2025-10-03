"""
A translation library for working with UART commands for Catalex MP3 modules.
"""
from busio import UART


class Sound_Control:
    """Sound control via UART object via Catalex protocol"""

    def __init__(self, audio: UART):
        self.audio_out = audio
        self.cmd_base = bytearray(
            [
                0xAA,
            ]
        )

    def play_track(self, track: int):
        """Plays a track based on the numerical name"""
        play_track = self.cmd_base.copy()
        play_track.append(0x07)
        play_track.append(0x02)
        play_track.append(int(hex(track)))
        play_track.append(0x00)
        sum = (0x07 + 0x02 + int(hex(track)) + 0x00) & 0xFF
        play_track.append(sum)
        self.audio_out.write(play_track)

    def vol_up(self):
        """Increments volume by one"""
        vol_up = self.cmd_base.copy()
        vol_up.append(0x14)
        vol_up.append(0x00)
        vol_up.append(0xBE)
        self.audio_out.write(vol_up)

    def vol_down(self):
        """Decrements volume by one"""
        vol_down = self.cmd_base.copy()
        vol_down.append(0x15)
        vol_down.append(0x00)
        vol_down.append(0xBF)
        self.audio_out.write(vol_down)

    def set_vol(self, level=30):
        """Sets volume level from 0-30"""
        set_vol = self.cmd_base.copy()
        set_vol.append(0x13)
        set_vol.append(0x01)
        set_vol.append(int(hex(level)))
        sum = (0x13 + 0x01 + int(hex(level))) & 0xFF
        set_vol.append(sum)
        self.audio_out.write(set_vol)

    """def play_at_vol(self, track=1, vol=30):
        "Plays a track at a set volume"
        play_at_vol = self.cmd_base
        play_at_vol[3] = 0x22
        play_at_vol[5] = int(hex(vol))
        play_at_vol[6] = int(hex(track))
        self.audio_out.write(play_at_vol)"""
