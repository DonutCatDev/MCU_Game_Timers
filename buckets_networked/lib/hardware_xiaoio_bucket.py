# type: ignore
"""
Hardware declarations for the timer project.
Used to easily change pin connections without changing the primary code.
This file is for the Bucket components.
Last updated 2025-10-01
"""
import board
from busio import I2C  # , UART
from digitalio import DigitalInOut, Pull, DriveMode
from rotaryio import IncrementalEncoder
from neopixel import NeoPixel
from adafruit_debouncer import Button
from lcd_i2c8574_m import I2cLcd


class DisplayWrapper:
    """Wrapper for I2C LCD display"""

    def __init__(
        self,
        sda_pin,
        scl_pin,
        lcd_addresses=[0x27, 0x3F],
        rows=2,
        cols=16,
    ):
        self.i2c = I2C(scl_pin, sda_pin)
        self.display = None
        self.lcd_addresses = lcd_addresses
        self.dimensions = (cols, rows)
        self.init_lcd()

    def init_lcd(self):
        while not self.i2c.try_lock():
            pass
        addresses = self.i2c.scan()
        for addr in self.lcd_addresses:
            if addr in addresses:
                address = addr
        try:
            self.display = I2cLcd(self.i2c, address, self.dimensions)
        except Exception:
            print("Failed to initialize LCD")
            self.display = None

    def write(self, text):
        if self.display is not None:
            self.display.write(text)

    def clear(self):
        if self.display is not None:
            self.display.clear()


# UART audio output
"""try:
    AUDIO_OUT = UART(board.IO43, board.IO44, baudrate=9600)
except Exception:
    print("AUDIO_OUT failed")
    pass"""

# I2C display creation
try:
    DISPLAY = DisplayWrapper(board.IO5, board.IO6, rows=2, cols=16)
except Exception:
    print("DISPLAY failed")
    pass


# Initialize RGB and inputs
iopins = (
    board.IO43,  # RGB data pin
    board.IO9,  # Encoder pin 1
    board.IO8,  # Encoder pin 2
    board.IO7,  # Encoder button
    board.IO1,  # Red button
    board.IO3,  # Blue button
    board.IO2,  # Red LED
    board.IO4,  # Blue LED
)
"""
iopins = (
    board.D6,  # RGB data pin
    board.D10,  # Encoder pin 1
    board.D9,  # Encoder pin 2
    board.D8,  # Encoder button
    board.D0,  # Red button
    board.D2,  # Blue button
    board.D1,  # Red LED
    board.D3,  # Blue LED
)
"""

# RGB strip setup
led_count = 58
try:
    RGB_LED = NeoPixel(iopins[0], led_count, brightness=1, auto_write=False)  # type: ignore
except Exception:
    print("RGB_LED failed")
    pass

# Encoder rotary setup
try:
    ENCODER = IncrementalEncoder(iopins[1], iopins[2])
except Exception:
    print("ENCODER failed")
    pass

# Setup button DIO objects
try:
    ENC, RED, BLUE = (DigitalInOut(pin) for pin in iopins[3:6])
    for button in [ENC, RED, BLUE]:
        button.switch_to_input(Pull.UP)
except Exception:
    print("BUTTONS failed")
    pass

# Create debouncer objects from DIO buttons
hold_ms = 1000
try:
    ENCB, REDB, BLUEB = (
        Button(ENC, long_duration_ms=hold_ms * 2),
        Button(RED, long_duration_ms=hold_ms),
        Button(BLUE, long_duration_ms=hold_ms),
    )
except Exception:
    print("DEBOUNCERS failed")
    pass

# Team button LED setup
try:
    RED_LED, BLUE_LED = (DigitalInOut(pin) for pin in iopins[6:8])
    for led in [RED_LED, BLUE_LED]:
        led.switch_to_output(False, DriveMode.PUSH_PULL)
except Exception:
    print("LEDs failed")
    pass
