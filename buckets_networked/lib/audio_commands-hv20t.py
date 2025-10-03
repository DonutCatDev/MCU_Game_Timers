"""
A translation library for working with UART commands for Catalex MP3 modules.
"""
from busio import UART


class Sound_Control:
    """Sound control via UART object via Catalex protocol"""

    def __init__(self, audio: UART):
        self.audio_out = audio

    def play_track(self, track: int):
        """Plays a track based on the numerical name"""
        cmd = [0xAA, 0x07, 0x02, track >> 8, track & 0xFF]
        checksum = sum(cmd[1:]) & 0xFF
        cmd.append(checksum)
        self.audio_out.write(bytearray(cmd))

    def vol_up(self):
        """Increments volume by one"""
        cmd = [0xAA, 0x14, 0x00, 0xBE]
        self.audio_out.write(bytearray(cmd))

    def vol_down(self):
        """Decrements volume by one"""
        cmd = [0xAA, 0x15, 0x00, 0xBF]
        self.audio_out.write(bytearray(cmd))

    def set_vol(self, level=30):
        """Sets volume level from 0-30"""
        cmd = [0xAA, 0x13, 0x01, level]
        checksum = sum(cmd[1:]) & 0xFF
        cmd.append(checksum)
        self.audio_out.write(bytearray(cmd))
