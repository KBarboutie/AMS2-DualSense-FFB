"""
Author: Konrad Barboutie
Date: 2025-01-15
"""

import ctypes
import mmap
import time
import json
import numpy as np
from multiprocessing import shared_memory
from shared_memory_struct import SharedMemory
from dualsense_controller import DualSenseController

# 1 front left
# 2 front right
# 3 rear left
# 4 rear right

# list availabe devices and throw exception when tzhere is no device detected
device_infos = DualSenseController.enumerate_devices()
if len(device_infos) < 1:
    raise Exception('No DualSense Controller available.')

# flag, which keeps program alive
is_running = True

# create an instance, use fiŕst available device
controller = DualSenseController()


# switches the keep alive flag, which stops the below loop
def stop():
    global is_running
    is_running = False

# callback, when cross button is pressed, which enables rumble
def on_cross_btn_pressed():

    controller.left_rumble.set(100)
    controller.right_rumble.set(100)

def on_cross_btn_released():

    controller.left_rumble.set(0)
    controller.right_rumble.set(0)

def on_square_btn_pressed():
    controller.left_rumble.set(100)
    controller.right_rumble.set(100)

def on_square_btn_released():

    controller.left_rumble.set(0)
    controller.right_rumble.set(0)


def on_error(error):
    print(f'Opps! an error occured: {error}')
    stop()


controller.lightbar.set_color_green()
# register the button callbacks
controller.btn_cross.on_down(on_cross_btn_pressed)
controller.btn_cross.on_up(on_cross_btn_released)
controller.btn_square.on_down(on_square_btn_pressed)
controller.btn_square.on_up(on_square_btn_released)

# register the error callback
controller.on_error(on_error)

# enable/connect the device
controller.activate()

UDP_PORT = 5606

def read_shared_memory():
    try:
        # Open the memory-mapped file
        file_handle = mmap.mmap(-1, ctypes.sizeof(SharedMemory), "$pcars2$", access=mmap.ACCESS_READ)

        # Create an instance of the shared memory structure
        data = SharedMemory()

        # Read the shared memory into the structure
        file_handle.seek(0)
        ctypes.memmove(ctypes.addressof(data), file_handle.read(ctypes.sizeof(data)), ctypes.sizeof(data))

        return data
    except Exception as e:
        print(f"Error reading shared memory: {e}")
        return None


def repeat_process(frequency_hz):
    interval = 1 / frequency_hz  # Time between iterations in seconds
    while True:
        start_time = time.time()

        # Your process
        data = read_shared_memory()
        #if data:
            #print(f"mTyreSlipSpeed: {data.mUnfilteredThrottle}")

        # Traction Control System FFB

        if np.max(data.mTyreSlipSpeed)<5:
            controller.right_trigger.effect.off()
            controller.left_trigger.effect.off()

        elif data.mUnfilteredThrottle > 0.1 and np.max(data.mTyreSlipSpeed) > 5 and data.mSpeed<40:
            controller.right_trigger.effect.machine(
                start_position=1,
                end_position=9,
                amplitude_a=3,
                amplitude_b=3,
                frequency=40,
                period=1
            )
        elif data.mUnfilteredBrake > 0.1 and np.max(data.mTyreSlipSpeed) > 5:
            controller.left_trigger.effect.machine(
                start_position=1,
                end_position=9,
                amplitude_a=5,
                amplitude_b=5,
                frequency=40,
                period=1
            )






    # start keep alive loop, controller inputs and callbacks are handled in a second thread
    while is_running:
        time.sleep(0.001)


repeat_process(60)

# disable/disconnect controller device
controller.deactivate()