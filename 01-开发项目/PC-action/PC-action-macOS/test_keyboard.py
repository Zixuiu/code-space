import keyboard

keyboard.add_hotkey('alt+m', lambda: print('TRIGGERED!'))

listener = keyboard._listener
print('nonblocking_hotkeys keys:')
for k in list(listener.nonblocking_hotkeys.keys())[:5]:
    print(f'  {k} (type: {type(k)})')

print('\n_pressed_events:', keyboard._pressed_events)

print('\nWaiting 5 seconds... Press Alt+M to test')
import time
time.sleep(5)