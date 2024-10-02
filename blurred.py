import zmq
import base64
import numpy as np
import cv2
import glfw
import ctypes
from OpenGL.GL import *
import imgui
from imgui.integrations.glfw import GlfwRenderer
imgui.create_context()
glfw.init()
glfw.window_hint(glfw.FLOATING, True)
glfw.window_hint(glfw.RESIZABLE, False)
glfw.window_hint(glfw.DECORATED, False)
glfw.window_hint(glfw.TRANSPARENT_FRAMEBUFFER, True)
window = glfw.create_window(1920, 1079, "hyzr", None, None)
if not window: glfw.terminate()
from ctypes import wintypes
WDA_EXCLUDEFROMCAPTURE = 0x00000011
user32 = ctypes.WinDLL('user32', use_last_error=True)
user32.SetWindowDisplayAffinity.restype = wintypes.BOOL
user32.SetWindowDisplayAffinity.argtypes = [wintypes.HWND, wintypes.DWORD]
def set_window_display_affinity(hwnd, affinity):
    result = user32.SetWindowDisplayAffinity(hwnd, affinity)
    if not result: raise ctypes.WinError(ctypes.get_last_error())
    return result
glfw.make_context_current(window)
glfw.swap_interval(0)
hwnd = glfw.get_win32_window(window)
# set_window_display_affinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
exstyle = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
exstyle |= 0x80000
exstyle |= 0x20 
ctypes.windll.user32.SetWindowLongW(hwnd, -20, exstyle)
ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0, 255, 0)
glViewport(0, 0, 1920, 1079)
glMatrixMode(GL_PROJECTION)
glLoadIdentity()
glOrtho(0, 1920, 1079, 0, 1, -1)
glMatrixMode(GL_MODELVIEW)
glLoadIdentity()
glEnable(GL_BLEND)
impl = GlfwRenderer(window)
imgui.get_io().ini_file_name = "".encode()
imgui.create_context()
imgui_io = imgui.get_io()
imgui_renderer = GlfwRenderer(window)
style = imgui.core.get_style()
style.colors[imgui.COLOR_WINDOW_BACKGROUND] = (0, 0, 0, 0)
style.window_padding = (0, 0)
style.frame_border_size = 0
style.window_border_size = 0
context = zmq.Context()
socket = context.socket(zmq.PULL)
socket.bind("tcp://*:5553")
image_texture = glGenTextures(1)
glBindTexture(GL_TEXTURE_2D, image_texture)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
while not glfw.window_should_close(window):
    glfw.poll_events()
    imgui.new_frame()
    data = None
    try:
        old = None
        while True:
            message = socket.recv(flags=zmq.NOBLOCK)
            data = message.decode('utf-8', errors='replace')
            if (data is None):
                if old is not None:
                    data = old
                    break
                continue
            else: old = data
    except: pass
    if data is None:
        imgui.render()
        continue
    imgui.set_next_window_position(int(1920 / 2 - 450), int(1080 / 2 - 450))
    # imgui.set_next_window_position(0, 0)
    imgui.begin("blurred", flags=imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_MOVE,)
    try:
        img_data = base64.b64decode(data)
        img_array = np.frombuffer(img_data, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_UNCHANGED)
        glBindTexture(GL_TEXTURE_2D, image_texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.shape[1], img.shape[0], 0, GL_RGBA, GL_UNSIGNED_BYTE, img)
        imgui.image(image_texture, img.shape[1], img.shape[0])
    except: pass
    imgui.end()
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    imgui.render()
    imgui_renderer.render(imgui.get_draw_data())
    glfw.swap_buffers(window)
glDeleteTextures([image_texture])
glfw.terminate()