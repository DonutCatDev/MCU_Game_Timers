"""
MCU Game Timers by donutcat
Primary file, timerbox, last updated 2025-10-01
"""

"""
Imports
"""
# region
import espnow  # type: ignore
from binascii import unhexlify
from os import getenv
from time import monotonic
from asyncio import sleep, create_task, gather, run, Event
from gc import enable, mem_free  # type: ignore
from random import randint, randrange
from hardware import (
    DISPLAY,
    ENCODER,
    ENCB,
)


# endregion
"""
Setting initial variables for use
"""
# region
MODES = []
BUCKET_IDS = ["A", "B", "C", "D", "E", "F"]
EXTRAS = [
    "You're a nerd",
    "Weiners",
    "Ooh, a piece of candy",
    "Oatmeal",
    "Poggers in the \nchat",
    "Anything is a \nhammer once",
    "Watch out for \nthem pointy bits",
    "This bucket \nkills fascists",
    "Taco Tuesday",
    "Amongus",
    "Dino nuggies",
    "Bumper cars",
]
# endregion
"""
Important state management
"""
# region


class Game_States:
    """
    Captures all needed state variables for a game mode

    Attributes:
        menu_index (int): The current menu index.
        restart_index (int): The current restart index.
        lives_count (int): The number of lives remaining.
        team (str): The team name: "Red", "Blue", or "Green".
        game_length (int): The duration of the game in seconds.
        cap_length (int): The capture point length in seconds.
        checkpoint (int): The checkpoint value.
        timer_state (bool): The state of the timer (True for running, False for paused).
        cap_state (bool): The state of the capture.
        red_time (int): The remaining time for the red team.
        blue_time (int): The remaining time for the blue team.
    """

    def __init__(self):
        self.menu_index = 0
        self.restart_index = 0
        self.lives_count = 0
        self.id_index = 5
        self.bucket_count = 3
        self.team = "Green"
        self.game_length = 0
        self.cap_length = 0
        self.checkpoint = 1
        self.dd_loop = 2
        self.timer_state = True
        self.cap_state = False
        self.red_time = 0
        self.blue_time = 0

    @property
    def bucket_id(self):
        """The current bucket ID"""
        return BUCKET_IDS[self.id_index]

    @property
    def bucket_interval(self):
        interval = self.game_length // (self.bucket_count * self.dd_loop)
        return interval

    @property
    def bucket_interval_upper(self):
        """The upper interval for the current bucket"""
        start = self.bucket_interval * (
            self.bucket_count * self.dd_loop - self.id_index
        )
        stop = self.bucket_interval * (
            self.bucket_count * self.dd_loop - (self.id_index + 1)
        )
        return (start, stop, -1)

    @property
    def bucket_interval_lower(self):
        """The lower interval for the current bucket"""
        start = self.bucket_interval * (self.bucket_count - self.id_index)
        stop = self.bucket_interval * (self.bucket_count - (self.id_index + 1))
        return (start, stop, -1)

    @property
    def game_length_str(self):
        """A formatted string representation of game length"""
        return time_string(self.game_length)

    @property
    def cap_length_str(self):
        """A formatted string representation of cap length"""
        return time_string(self.cap_length)

    @property
    def red_time_str(self):
        """A formatted string representation of red team time"""
        return time_string(self.red_time)

    @property
    def blue_time_str(self):
        """A formatted string representation of blue team time"""
        return time_string(self.blue_time)

    def shallow_copy(self):
        """Returns a shallow copy of an object"""
        new_instance = self.__class__()
        for key, value in self.__dict__.items():
            setattr(new_instance, key, value)
        return new_instance

    def update_team(
        self,
        team="Green",
        pattern="chase",
        delay=0.005,
        hold=False,
    ):
        """Updates button LED and RGB state based on team"""
        self.team = team

    def reset(self):
        """Resets all state variables to their initial values"""
        self.menu_index = 0
        self.restart_index = 0
        self.lives_count = 0
        self.id_index = 5
        self.bucket_count = 3
        self.team = "Green"
        self.game_length = 0
        self.cap_length = 0
        self.checkpoint = 1
        self.dd_loop = 2
        self.timer_state = True
        self.cap_state = False
        self.red_time = 0
        self.blue_time = 0


class ENC_States:
    """Manages encoder rotation"""

    def __init__(self, encoder=ENCODER):
        self.encoder = encoder
        self.last_position = self.encoder.position
        self._was_rotated = Event()

    async def update(self):
        """Updates the pressed state of the encoder"""
        while True:
            if (
                self.encoder.position != self.last_position
                and not self._was_rotated.is_set()
            ):
                self._was_rotated.set()
            await sleep(0)

    def encoder_handler(self, x, y):
        """Handles encoder rotation"""
        while True:
            if self.encoder.position > self.last_position:
                self.last_position = self.encoder.position
                self._was_rotated.clear()
                return x + y
            elif self.encoder.position < self.last_position:
                self.last_position = self.encoder.position
                self._was_rotated.clear()
                return x - y


async def button_monitor():
    """Async function for monitoring button presses"""
    while True:
        ENCB.update()
        await sleep(0)


initial_state = Game_States()
ENCS = ENC_States()

# endregion
"""
Simple helper functions
"""
# region


def time_string(seconds):
    """Returns a formatted string representation of time in seconds"""
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def display_message(message):
    """
    Displays a string to the 1602 LCD

    Note: if a line is already 16chars when a n\\ is added, it will skip the next line
    """
    DISPLAY.clear()
    DISPLAY.write(message)


# endregion
"""
Primary function to select GameMode instance, then pass control to it
"""
# region


async def main_menu():
    """Main menu for scrolling and displaying game options"""
    display_message(EXTRAS[randint(0, len(EXTRAS) - 1)])
    await sleep(0.5)
    display_message(f"Select a game:\n{MODES[initial_state.menu_index].name}")
    while True:
        if ENCS._was_rotated.is_set():
            initial_state.menu_index = ENCS.encoder_handler(
                initial_state.menu_index, 1
            ) % len(MODES)
            display_message(f"Select a game:\n{MODES[initial_state.menu_index].name}")
        if ENCB.short_count > 0:
            break
        await sleep(0)
    await sleep(0.1)
    display_message(f"Running:\n{MODES[initial_state.menu_index].name}")
    await MODES[initial_state.menu_index].game_setup()


# endregion
"""
Per game mode functions
"""
# region


async def start_basictimer(game_mode):
    """Function for Basic Timer mode"""
    local_state = initial_state.shallow_copy()
    await sleep(0.5)
    display_message(local_state.game_length_str)
    e.send("Start")
    await sleep(6)
    clock = monotonic()
    while local_state.game_length > 0:
        if local_state.timer_state:
            if monotonic() - clock >= 1:
                local_state.game_length -= 1
                if local_state.game_length == 10:
                    try:
                        e.send("10")
                    except:
                        pass
                display_message(local_state.game_length_str)
                clock = monotonic()
            if local_state.game_length == 60:
                try:
                    e.send("60")
                except:
                    pass
            if local_state.game_length == 30:
                try:
                    e.send("30")
                except:
                    pass
        if ENCB.short_count > 1:
            if local_state.timer_state == True:
                local_state.timer_state = False
                try:
                    e.send("Pause")
                except:
                    pass
            elif local_state.timer_state == False:
                local_state.timer_state = True
                try:
                    e.send("Resume")
                except:
                    pass
        if ENCB.long_press:
            display_message("exiting...")
            await sleep(0.5)
            break
        await sleep(0)
    try:
        e.send("End")
        await sleep(0)
    except:
        pass
    await sleep(0.1)
    await game_mode.restart()


async def start_doordash(game_mode):
    """Function for DoorDash/moving KotH game mode"""
    local_state = initial_state.shallow_copy()
    await sleep(0.5)
    bucket_list = []
    while len(bucket_list) < local_state.bucket_count:
        for i in range(1, local_state.bucket_count + 1):
            bucket_list.append(i)
    if local_state.dd_loop == 2:
        while len(bucket_list) < local_state.bucket_count * 2:
            for i in range(1, local_state.bucket_count + 1):
                bucket_list.append(i)
    bucket_order = []
    while len(bucket_list) > 0:
        bucket_order.append(bucket_list.pop(randrange(len(bucket_list))))
    print(bucket_order)
    bucket_interval = initial_state.bucket_interval
    print(bucket_interval)
    display_message(local_state.game_length_str)
    e.send("Start")
    await sleep(6)
    clock = monotonic()
    while local_state.game_length > 0:
        if local_state.timer_state:
            if local_state.game_length % bucket_interval == 0:
                # If the game length is a multiple of the bucket interval, send a message to the next bucket
                interval_count = (local_state.game_length // bucket_interval) - 1
                try:
                    e.send("Inactive")
                    # deactivate all first
                    await sleep(1)
                    e.send("Active", e.peers[bucket_order[interval_count] + 1])
                    # activate peer 2-6, choosing from bucket_order via interval_count
                except:
                    print("fucky wucky")
                    pass
                print(f"bucket {bucket_order[interval_count]} active")
            if monotonic() - clock >= 1:
                local_state.game_length -= 1
                if local_state.game_length == 10:
                    try:
                        e.send("10")
                    except:
                        pass
                if local_state.game_length == 30:
                    try:
                        e.send("30")
                    except:
                        pass
                if local_state.game_length == 60:
                    try:
                        e.send("60")
                    except:
                        pass
                display_message(local_state.game_length_str)
                clock = monotonic()
        if ENCB.short_count > 1:
            if local_state.timer_state == True:
                local_state.timer_state = False
                try:
                    e.send("Pause")
                except:
                    pass
            elif local_state.timer_state == False:
                local_state.timer_state = True
                try:
                    e.send("Resume")
                except:
                    pass
        if ENCB.long_press:
            display_message("exiting...")
            await sleep(0.5)
            break
        await sleep(0)
    try:
        e.send("End")
        await sleep(0)
    except:
        pass
    await sleep(0.1)
    await game_mode.restart()


# endregion
"""
GameMode class and instantiation
"""
# region


class GameMode:
    def __init__(
        self,
        name,
        has_lives=False,
        has_id=False,
        has_team=False,
        has_game_length=False,
        has_cap_length=False,
        has_checkpoint=False,
    ):
        self.name = name
        self.has_lives = has_lives
        self.has_id = has_id
        self.has_team = has_team
        self.has_game_length = has_game_length
        self.has_cap_length = has_cap_length
        self.has_checkpoint = has_checkpoint
        self.final_func_str = f"start_{self.name.replace(' ', '').lower()}"

    def set_message(self):
        self.display_messages = {
            1: f"{self.name} Ready\nTeam lives {initial_state.lives_count}",
            2: f"{self.name}\nReady {initial_state.game_length_str}",
            3: f"{self.name} Ready\n{initial_state.team} {initial_state.game_length_str} {initial_state.cap_length_str}",
            4: f"{self.name}\nReady Team {initial_state.team}",
            5: f"{self.name} Ready\n{initial_state.game_length_str} {initial_state.bucket_id}",
        }
        message = 1
        if self.has_lives:
            message = 1
        elif self.has_id:
            message = 5
        elif self.has_team:
            if self.has_game_length:
                message = 3
            else:
                message = 4
        elif self.has_game_length:
            message = 2
        return self.display_messages[message]

    async def game_setup(self):
        if self.has_lives:
            await self.counter_screen()
        if self.has_id:
            await self.identity_screen()
        if self.has_team:
            await self.team_screen()
        if self.has_game_length:
            await self.timer_screen()
        await self.standby_screen()

    async def counter_screen(self):
        """Screen used to set lives for Attrition"""
        await sleep(0.5)
        display_message(f"{self.name} \nLives: {initial_state.lives_count}")
        while True:
            if ENCS._was_rotated.is_set():
                initial_state.lives_count = max(
                    0, ENCS.encoder_handler(initial_state.lives_count, 1)
                )
                display_message(f"{self.name}\nLives: {initial_state.lives_count}")
            if ENCB.short_count > 0:
                break
            await sleep(0)
        await sleep(0)

    async def identity_screen(self):
        """Screen to set bucket identifier for swapping-based game modes"""
        await sleep(0.5)
        display_message(f"{self.name}\nBucket ID: {initial_state.bucket_id}")
        while True:
            if ENCS._was_rotated.is_set():
                initial_state.id_index = ENCS.encoder_handler(
                    initial_state.id_index, 1
                ) % len(BUCKET_IDS)
                display_message(f"{self.name}\nBucket ID: {initial_state.bucket_id}")
            if ENCB.short_count > 0:
                break
            await sleep(0)
        display_message(f"{self.name}\nBucket Count: {initial_state.bucket_count}")
        await sleep(0)
        while True:
            if ENCS._was_rotated.is_set():
                initial_state.bucket_count = ENCS.encoder_handler(
                    initial_state.bucket_count, 1
                ) % len(BUCKET_IDS)
                display_message(
                    f"{self.name}\nBucket Count: {initial_state.bucket_count}"
                )
            if ENCB.short_count > 0:
                break
            await sleep(0)
        display_message(f"{self.name}\nLoop Count: {initial_state.dd_loop}")
        await sleep(0)
        while True:
            if ENCS._was_rotated.is_set():
                initial_state.dd_loop = max(
                    1, (ENCS.encoder_handler(initial_state.dd_loop, 1) % 3)
                )
                display_message(f"{self.name}\nLoop Count: {initial_state.dd_loop}")
            if ENCB.short_count > 0:
                break
            await sleep(0)
        await sleep(0)

    async def team_screen(self):
        """Screen for selecting team counter for Attrition and Death Clicks"""
        await sleep(0.5)
        display_message(f"{self.name}\nTeam:")
        while True:
            if ENCB.short_count > 0:
                break
            await sleep(0)
        await sleep(0)

    async def timer_screen(self):
        """Screen used to set time for game modes with built in timers"""
        await sleep(0.5)
        display_message(f"{self.name}\nTime: {initial_state.game_length_str}")
        while True:
            if ENCS._was_rotated.is_set():
                initial_state.game_length = max(
                    0, ENCS.encoder_handler(initial_state.game_length, 15)
                )
                display_message(f"{self.name}\nTime: {initial_state.game_length_str}")
            if ENCB.short_count > 0:
                break
            await sleep(0)
        if self.has_cap_length:
            display_message(f"{self.name}\nCap time: {initial_state.cap_length_str}")
            await sleep(0)
            while True:
                if ENCS._was_rotated.is_set():
                    initial_state.cap_length = max(
                        0, ENCS.encoder_handler(initial_state.cap_length, 5)
                    )
                    display_message(
                        f"{self.name}\nCap time: {initial_state.cap_length_str}"
                    )
                if ENCB.short_count > 0:
                    break
                await sleep(0)
        if self.has_checkpoint:
            display_message(f"{self.name}\nCheckpoint: {initial_state.checkpoint}s")
            await sleep(0)
            while True:
                if ENCS._was_rotated.is_set():
                    initial_state.checkpoint = max(
                        0, ENCS.encoder_handler(initial_state.checkpoint, 1)
                    )
                    display_message(
                        f"{self.name}\nCheckpoint: {initial_state.checkpoint}s"
                    )
                if ENCB.short_count > 0:
                    break
                await sleep(0)
        await sleep(0)

    async def standby_screen(self):
        """
        Pre-game confirmation screen.
        Also handles restarting or reseting the mode.
        """
        while True:
            await sleep(0.5)
            display_message(self.set_message())
            await sleep(0.5)
            while True:
                if ENCB.short_count > 0:
                    break
                await sleep(0)
            display_message(f"{self.name}\nStarting...")
            await sleep(0)
            await self.run_final_function()
            if initial_state.restart_index == 0:
                break
            elif initial_state.restart_index == 1:
                pass
        return

    async def restart(self):
        """Function for restarting the program"""
        await sleep(0.5)
        RESTART_OPTIONS = ["No", "Yes"]
        display_message(f"Restart?:\n{RESTART_OPTIONS[initial_state.restart_index]}")
        await sleep(0.5)
        while True:
            if ENCS._was_rotated.is_set():
                initial_state.restart_index = ENCS.encoder_handler(
                    initial_state.restart_index, 1
                ) % len(RESTART_OPTIONS)
                display_message(
                    f"Restart?:\n{RESTART_OPTIONS[initial_state.restart_index]}"
                )
            if ENCB.short_count > 0:
                break
            await sleep(0)
        await sleep(0.5)
        print(mem_free())
        if initial_state.restart_index == 1:
            if self.has_team:
                initial_state.update_team(
                    "Blue" if initial_state.team == "Red" else "Red"
                )
            else:
                initial_state.update_team()
        await sleep(0.5)
        return

    async def run_final_function(self):
        final_func = globals().get(self.final_func_str, None)
        if callable(final_func):
            await final_func(self)  # type: ignore
        else:
            print(f"Function {self.final_func_str} not found")


MODES = [
    GameMode("Basic Timer", has_game_length=True),
    GameMode("DoorDash", has_id=True, has_game_length=True),
]
# endregion
"""
ESP-NOW setup
"""
# region

e = espnow.ESPNow()
e.peers.append(espnow.Peer(mac=unhexlify(getenv("SOUNDBOX1_MAC")))),  # type: ignore
e.peers.append(espnow.Peer(mac=unhexlify(getenv("SOUNDBOX2_MAC")))),  # type: ignore
e.peers.append(espnow.Peer(mac=unhexlify(getenv("BUCKETA_MAC")))),  # type: ignore
e.peers.append(espnow.Peer(mac=unhexlify(getenv("BUCKETB_MAC")))),  # type: ignore
e.peers.append(espnow.Peer(mac=unhexlify(getenv("BUCKETC_MAC")))),  # type: ignore
e.peers.append(espnow.Peer(mac=unhexlify(getenv("BUCKETD_MAC")))),  # type: ignore
e.peers.append(espnow.Peer(mac=unhexlify(getenv("BUCKETE_MAC")))),  # type: ignore

# endregion
"""
Main program
"""
# region

enable()


async def game_task_chain():
    """Task chain for running the program"""
    while True:
        await main_menu()
        initial_state.reset()


async def main():
    game_task = create_task(game_task_chain())
    enc_task = create_task(ENCS.update())
    button_task = create_task(button_monitor())
    await gather(game_task, enc_task, button_task)


if __name__ == "__main__":
    run(main())
# endregion
