import time
import glfw
import ctypes
from OpenGL.GL import *
import imgui
import win32api # type: ignore
import win32con # type: ignore
import win32gui # type: ignore
from imgui.integrations.glfw import GlfwRenderer
import zmq
import random
import imgui
from imgui.core import Vec4, Vec2
from ctypes import windll
from OpenGL.GL import glTexParameteri, glTexImage2D, glBindTexture, glGenTextures, GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR
from PIL import Image
import json

enabled = {
    "skele": True, 
    "box": True, 
    "snap": True, 
    "distance": True, 
    "name": True, 
    "fov": True, 
    "streamproof": True, 
    "textoutline": True, 
}

def u32_to_rgba(u32):
    r = (u32 >> 24) & 0xFF
    g = (u32 >> 16) & 0xFF
    b = (u32 >> 8) & 0xFF
    a = u32 & 0xFF
    return [r / 255.0, g / 255.0, b / 255.0, a / 255.0]

def rgba_to_u32(rgba):
    return (int(rgba[0] * 255) << 24 |
            int(rgba[1] * 255) << 16 |
            int(rgba[2] * 255) << 8 |
            int(rgba[3] * 255))

def save_settings(filename):
    settings = {
        "enabled": enabled,
        "SKELE_VISIBLE": u32_to_rgba(SKELE_VISIBLE),
        "SKELE_NON_VISIBLE": u32_to_rgba(SKELE_NON_VISIBLE),
        "BOX_VISIBLE": u32_to_rgba(BOX_VISIBLE),
        "BOX_NON_VISIBLE": u32_to_rgba(BOX_NON_VISIBLE),
        "SNAP_VISIBLE": u32_to_rgba(SNAP_VISIBLE),
        "SNAP_NON_VISIBLE": u32_to_rgba(SNAP_NON_VISIBLE),
        "FOV": u32_to_rgba(FOV),
        "IGN": u32_to_rgba(IGN),
        "DISTANCE": u32_to_rgba(DISTANCE),
        "OUTLINE": u32_to_rgba(OUTLINE),
        "skele_visible_rgba": skele_visible_rgba,
        "skele_non_visible_rgba": skele_non_visible_rgba,
        "box_visible_rgba": box_visible_rgba,
        "box_non_visible_rgba": box_non_visible_rgba,
        "snap_visible_rgba": snap_visible_rgba,
        "snap_non_visible_rgba": snap_non_visible_rgba,
        "fov_rgba": fov_rgba,
        "ign_rgba": ign_rgba,
        "distance_rgba": distance_rgba,
        "outline_rgba": outline_rgba
    }
    with open(filename, 'w') as file:
        json.dump(settings, file, indent=4)

def load_settings(filename):
    global enabled, SKELE_VISIBLE, SKELE_NON_VISIBLE
    global BOX_VISIBLE, BOX_NON_VISIBLE, SNAP_VISIBLE
    global SNAP_NON_VISIBLE, FOV, IGN, DISTANCE, OUTLINE
    global skele_visible_rgba, skele_non_visible_rgba
    global box_visible_rgba, box_non_visible_rgba
    global snap_visible_rgba, snap_non_visible_rgba
    global fov_rgba, ign_rgba, distance_rgba, outline_rgba

    try:
        with open(filename, 'r') as file:
            settings = json.load(file)
            enabled = settings["enabled"]
            SKELE_VISIBLE = rgba_to_u32(settings["SKELE_VISIBLE"])
            SKELE_NON_VISIBLE = rgba_to_u32(settings["SKELE_NON_VISIBLE"])
            BOX_VISIBLE = rgba_to_u32(settings["BOX_VISIBLE"])
            BOX_NON_VISIBLE = rgba_to_u32(settings["BOX_NON_VISIBLE"])
            SNAP_VISIBLE = rgba_to_u32(settings["SNAP_VISIBLE"])
            SNAP_NON_VISIBLE = rgba_to_u32(settings["SNAP_NON_VISIBLE"])
            FOV = rgba_to_u32(settings["FOV"])
            IGN = rgba_to_u32(settings["IGN"])
            DISTANCE = rgba_to_u32(settings["DISTANCE"])
            OUTLINE = rgba_to_u32(settings["OUTLINE"])
            skele_visible_rgba[:] = settings["skele_visible_rgba"]
            skele_non_visible_rgba[:] = settings["skele_non_visible_rgba"]
            box_visible_rgba[:] = settings["box_visible_rgba"]
            box_non_visible_rgba[:] = settings["box_non_visible_rgba"]
            snap_visible_rgba[:] = settings["snap_visible_rgba"]
            snap_non_visible_rgba[:] = settings["snap_non_visible_rgba"]
            fov_rgba[:] = settings["fov_rgba"]
            ign_rgba[:] = settings["ign_rgba"]
            distance_rgba[:] = settings["distance_rgba"]
            outline_rgba[:] = settings["outline_rgba"]
    except FileNotFoundError:
        print(f"No settings file found. Using default values.")
    except json.JSONDecodeError:
        print(f"Settings file is corrupted. Using default values.")

def load_texture(image_path):
    # Load the image with PIL
    image = Image.open(image_path)
    # image = image.transpose(Image.FLIP_TOP_BOTTOM)  # Flip the image vertically

    # Convert the image to raw data
    image_data = image.convert("RGBA").tobytes()

    # Generate a texture ID
    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)

    # Set texture parameters
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)

    # Load the texture data
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, image.width, image.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, image_data)

    return texture_id, image.width, image.height

def display_image(texture_id, width, height):
    imgui.image(texture_id, width, height)

import math
def lerp(a, b, t):
    return a + (b - a) * t

def lerp_vec4(vec_a, vec_b, t):
    return Vec4(
        lerp(vec_a.x, vec_b.x, t),
        lerp(vec_a.y, vec_b.y, t),
        lerp(vec_a.z, vec_b.z, t),
        lerp(vec_a.w, vec_b.w, t)
    )

context = zmq.Context()
socket = context.socket(zmq.PULL)
socket.bind("tcp://*:12345")

POS = []
fov = 420
# higher = better performance more gpu usage
SLEEP_DELAY = 0.005

imgui.create_context()
glfw.init()
glfw.window_hint(glfw.FLOATING, True)
glfw.window_hint(glfw.RESIZABLE, False)
glfw.window_hint(glfw.DECORATED, False)
glfw.window_hint(glfw.TRANSPARENT_FRAMEBUFFER, True)

window = glfw.create_window(1920, 1079, "hyzr", None, None)
if not window:
    glfw.terminate()

from ctypes import wintypes

WDA_NONE = 0x00000000
WDA_MONITOR = 0x00000001
WDA_EXCLUDEFROMCAPTURE = 0x00000011

user32 = ctypes.WinDLL('user32', use_last_error=True)

user32.SetWindowDisplayAffinity.restype = wintypes.BOOL
user32.SetWindowDisplayAffinity.argtypes = [wintypes.HWND, wintypes.DWORD]

def set_window_display_affinity(hwnd, affinity):
    result = user32.SetWindowDisplayAffinity(hwnd, affinity)
    if not result:
        raise ctypes.WinError(ctypes.get_last_error())
    return result


glfw.make_context_current(window)
glfw.swap_interval(0)

hwnd = glfw.get_win32_window(window)
exstyle = ctypes.windll.user32.GetWindowLongW(hwnd, -20)  # GWL_EXSTYLE
exstyle |= 0x80000  # WS_EX_LAYERED
exstyle |= 0x20  # WS_EX_TRANSPARENT
# ctypes.windll.user32.SetWindowLongW(
#     hwnd, -20, exstyle
# )  # Set extended style
ctypes.windll.user32.SetLayeredWindowAttributes(
    hwnd, 0, 255, 0
)  # Set transparency
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
io = imgui.get_io()

# verdanab = io.fonts.add_font_from_file_ttf(
#     "./BurbankBigRegular-Black.ttf",
#     14,
# )
# verdanab2 = io.fonts.add_font_from_file_ttf(
#     "./BurbankBigRegular-Black.ttf",
#     24,
# )

verdanab = io.fonts.add_font_from_file_ttf(
    "./verdanab.ttf",
    14,
)
verdanab2 = io.fonts.add_font_from_file_ttf(
    "./verdanab.ttf",
    20,
)

fortnite = io.fonts.add_font_from_file_ttf(
    "./fortnite.ttf",
    14,
)
fortnite2 = io.fonts.add_font_from_file_ttf(
    "./fortnite.ttf",
    24,
)

SKELE_VISIBLE = imgui.get_color_u32_rgba(0, 1, 0, 1)
SKELE_NON_VISIBLE = imgui.get_color_u32_rgba(1, 0, 0, 1)

BOX_VISIBLE = imgui.get_color_u32_rgba(1, 1, 0, 1)
BOX_NON_VISIBLE = imgui.get_color_u32_rgba(1, 0, 1, 1)

SNAP_VISIBLE = imgui.get_color_u32_rgba(1, 0, 1, 1)
SNAP_NON_VISIBLE = imgui.get_color_u32_rgba(0, 1, 0, 1)

FOV = imgui.get_color_u32_rgba(0, 0, 0, 1)

IGN = imgui.get_color_u32_rgba(1, 1, 1, 1)
DISTANCE = imgui.get_color_u32_rgba(1, 1, 1, 1)

OUTLINE = imgui.get_color_u32_rgba(0, 0, 0, 0.5)

# RGBA values for editing
skele_visible_rgba = [0, 1, 0, 1]
skele_non_visible_rgba = [1, 0, 0, 1]

box_visible_rgba = [1, 1, 0, 1]
box_non_visible_rgba = [1, 0, 1, 1]

snap_visible_rgba = [1, 0, 1, 1]
snap_non_visible_rgba = [0, 1, 0, 1]

fov_rgba = [0, 0, 0, 1]

ign_rgba = [1, 1, 1, 1]
distance_rgba = [1, 1, 1, 1]

outline_rgba = [0, 0, 0, 0.5]

SKELE_THICKNESS = 4
SKELE_THICKNESS2 = 1
impl.refresh_font_texture()

outline_global = 3

outline_color = imgui.get_color_u32_rgba(0, 0, 0, 1)
outline_thickness = 1
dl = None

def draw_smooth_outlined_text(x, y, text):
    steps = 80  # Number of steps for creating a smoother outline
    step_size = outline_thickness / steps

    for step in range(steps):
        outline_offset = (step + 1) * step_size

        # Draw outline texts with gradually increasing offsets
        dl.add_text(x + outline_offset, y + outline_offset, outline_color, text)
        dl.add_text(x - outline_offset, y - outline_offset, outline_color, text)
        dl.add_text(x + outline_offset, y - outline_offset, outline_color, text)
        dl.add_text(x - outline_offset, y + outline_offset, outline_color, text)

def sleep(duration, get_now=time.perf_counter):
    if duration == 0:
        return
    now = get_now()
    end = now + duration
    while now < end:
        now = get_now()

style = imgui.get_style()
style.window_rounding = 5.0  # WINDOW ROUNDING
style.frame_rounding = 5.0  # FRAME ROUNDING FOR ALL ITEMS
style.window_border_size = 0.0  # WINDOW BORDER SIZE
style.window_padding = (40.0, 40.0)  # WINDOW PADDING
# style.frame_padding = (0.5, 0.5)  # WINDOW PADDING

primary_color = (0.102, 0.874, 0.980, 1)

style.colors[imgui.COLOR_BUTTON] = primary_color  # Button color
style.colors[imgui.COLOR_BUTTON_HOVERED] = (0.346, 0.072, 1.0, 1.0)  # Slightly lighter for hovered buttons
style.colors[imgui.COLOR_BUTTON_ACTIVE] = (0.226, 0.002, 0.928, 1.0)  # Slightly darker for active buttons
style.colors[imgui.COLOR_BORDER_SHADOW] = (1, 0.1, 0.1, 1.0)  # Slightly darker for active buttons
style.colors[imgui.COLOR_BORDER] = (0.1, 0.1, 0.1, 1.0)  # Slightly darker for active buttons
style.colors[imgui.COLOR_POPUP_BACKGROUND] = (0.1, 0.1, 0.1, 1.0)  # Slightly darker for active buttons
style.colors[imgui.COLOR_SCROLLBAR_BACKGROUND] = (0.2, 0.2, 0.2, 1.0)  # Slightly darker for active buttons

style.colors[imgui.COLOR_SLIDER_GRAB] = primary_color  # Slider grab color
style.colors[imgui.COLOR_SLIDER_GRAB_ACTIVE] = primary_color  # Active slider grab color, not transparent

style.colors[imgui.COLOR_CHECK_MARK] = primary_color  # Checkbox check mark color

style.colors[imgui.COLOR_HEADER] = primary_color  # Header (e.g., in menus) color
style.colors[imgui.COLOR_HEADER_HOVERED] = (0.346, 0.072, 1.0, 1.0)  # Hovered header color
style.colors[imgui.COLOR_HEADER_ACTIVE] = (0.226, 0.002, 0.928, 1.0)  # Active header color

# Change the title bar color
style.colors[imgui.COLOR_TITLE_BACKGROUND_ACTIVE] = (0.1, 0.1, 0.1, 1.0)  # Title bar background color

# Optionally, you can set other colors to match the black background
style.colors[imgui.COLOR_FRAME_BACKGROUND] = (0.3, 0.3, 0.3, 1.0)  # Dark gray for frame background
style.colors[imgui.COLOR_FRAME_BACKGROUND_ACTIVE] = (0.3, 0.3, 0.3, 1.0)  # Dark gray for frame background
style.colors[imgui.COLOR_FRAME_BACKGROUND_HOVERED] = (0.35, 0.35, 0.35, 1.0)  # Dark gray for frame background
style.colors[imgui.COLOR_TEXT] = (1.0, 1.0, 1.0, 1.0)  # White for text
style.colors[imgui.COLOR_BUTTON] = (0.1, 0.1, 0.1, 1.0)  # Dark gray for buttons
style.colors[imgui.COLOR_BUTTON_HOVERED] = (0.3, 0.3, 0.3, 1.0)  # Lighter gray for hovered buttons
imgui.push_style_color(imgui.COLOR_WINDOW_BACKGROUND, 0.02, 0.02, 0.02, 0.97)

def particles():
    screen_size = Vec2(float(windll.user32.GetSystemMetrics(0)), float(windll.user32.GetSystemMetrics(1)))

    # Initialize static variables
    if not hasattr(particles, "particle_pos"):
        particles.particle_pos = [Vec2(0, 0) for _ in range(500)]
        particles.particle_target_pos = [Vec2(0, 0) for _ in range(500)]
        particles.particle_speed = [0] * 500
        particles.particle_radius = [0.8] * 500

    for i in range(1, 500):
        if particles.particle_pos[i].x == 0 or particles.particle_pos[i].y == 0:
            particles.particle_pos[i] = Vec2(random.randint(0, int(screen_size.x)),
                                             random.randint(0, int(screen_size.y)))
            particles.particle_speed[i] = 4
            particles.particle_radius[i] = 1

            particles.particle_target_pos[i] = Vec2(particles.particle_pos[i].x, -screen_size.y)

        # Perform interpolation using the custom lerp function
        particles.particle_pos[i] = Vec2(
            lerp(particles.particle_pos[i].x, particles.particle_target_pos[i].x,
                 imgui.get_io().delta_time * (particles.particle_speed[i] / 60)),
            lerp(particles.particle_pos[i].y, particles.particle_target_pos[i].y,
                 imgui.get_io().delta_time * (particles.particle_speed[i] / 60))
        )

        if particles.particle_pos[i].y < 0:
            particles.particle_pos[i] = Vec2(random.randint(0, int(screen_size.x)),
                                             random.randint(0, int(screen_size.y)))

        if particles.particle_pos[i].x == 0:
            continue

        imgui.get_window_draw_list().add_circle_filled(
            particles.particle_pos[i].x, particles.particle_pos[i].y, particles.particle_radius[i], imgui.get_color_u32_rgba(1.0, 1.0, 1.0, 1)
        )

WS_EX_LAYERED = 0x80000
WS_EX_TRANSPARENT = 0x20
WS_EX_TOPMOST = 0x00000008
def set_clickthrough(window):
    """
    Set the specified GLFW window to be click-through (transparent to mouse clicks).
    """
    hwnd = glfw.get_win32_window(window)
    exstyle = ctypes.windll.user32.GetWindowLongW(hwnd, -20)  # GWL_EXSTYLE
    exstyle |= WS_EX_LAYERED
    exstyle |= WS_EX_TRANSPARENT
    ctypes.windll.user32.SetWindowLongW(hwnd, -20, exstyle)

def remove_clickthrough(window):
    """
    Remove click-through property from the specified GLFW window.
    """
    hwnd = glfw.get_win32_window(window)
    exstyle = ctypes.windll.user32.GetWindowLongW(hwnd, -20)  # GWL_EXSTYLE
    exstyle &= ~WS_EX_LAYERED
    exstyle &= ~WS_EX_TRANSPARENT
    ctypes.windll.user32.SetWindowLongW(hwnd, -20, exstyle)

def set_window_topmost(window):
    """
    Set the specified GLFW window to always stay on top.
    """
    hwnd = glfw.get_win32_window(window)
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0,0,0,0,
    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)

def draw_blue_border():
    pos = (imgui.get_window_position()[0] + 2, imgui.get_window_position()[1] + 2)
    size = (596, 396)

    draw_list = imgui.get_window_draw_list()

    start_color = Vec4(26/255, 223/255, 250/255, 1.0)
    end_color = Vec4(0/255, 81/255, 255/255, 1.0)

    border_thickness = 3.0

    time = imgui.get_time()
    transition_speed = 1.0
    transition_amount = math.sin(time * transition_speed) * 0.5 + 0.5

    interpolated_color = lerp_vec4(start_color, end_color, transition_amount)
    border_color = imgui.get_color_u32_rgba(interpolated_color.x, interpolated_color.y, interpolated_color.z, interpolated_color.w)

    draw_list.add_rect(
        pos[0] + border_thickness, pos[1] + border_thickness,
        pos[0] + size[0] - border_thickness, pos[1] + size[1] - border_thickness,
        border_color, 5.0, 0, border_thickness
    )

window_width = 600
window_height = 400

WDA_NONE = 0x00000000
WDA_MONITOR = 0x00000001
WDA_EXCLUDEFROMCAPTURE = 0x00000011
GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_APPWINDOW = 0x00040000

# Get the handle to the window

# Change the window style
ex_style = win32gui.GetWindowLong(hwnd, GWL_EXSTYLE)
ex_style = ex_style & ~WS_EX_APPWINDOW  # Remove from Alt+Tab
ex_style = ex_style | WS_EX_TOOLWINDOW   # Add to tool window list
win32gui.SetWindowLong(hwnd, GWL_EXSTYLE, ex_style)

user32 = ctypes.WinDLL('user32', use_last_error=True)

# Define the SetWindowDisplayAffinity function prototype
user32.SetWindowDisplayAffinity.restype = wintypes.BOOL
user32.SetWindowDisplayAffinity.argtypes = [wintypes.HWND, wintypes.DWORD]

def set_window_display_affinity(hwnd, affinity):
    result = user32.SetWindowDisplayAffinity(hwnd, affinity)
    if not result:
        raise ctypes.WinError(ctypes.get_last_error())
    return result

def start():
    menu = True
    global POS, dl, style
    global SKELE_VISIBLE, SKELE_NON_VISIBLE, BOX_VISIBLE, BOX_NON_VISIBLE
    global SNAP_VISIBLE, SNAP_NON_VISIBLE, FOV, IGN, DISTANCE, OUTLINE
    global skele_visible_rgba, skele_non_visible_rgba
    global box_visible_rgba, box_non_visible_rgba
    global snap_visible_rgba, snap_non_visible_rgba
    global fov_rgba, ign_rgba, distance_rgba, outline_rgba
    imgui.create_context()

    # Load texture
    texture_id, width, height = load_texture("logo.png")

    while not glfw.window_should_close(window):
        glfw.poll_events()
        try:
            imgui.new_frame() 
        except: 
            pass

        impl.process_inputs()

        if not win32api.GetAsyncKeyState(0x2D) == 0:
            while (not win32api.GetAsyncKeyState(0x2D) == 0): continue
            menu = not menu
            save_settings("settings.json")
        dl = imgui.get_background_draw_list()

        if menu:
            remove_clickthrough(window)
            set_window_topmost(window)
            with imgui.font(fortnite2):
                imgui.set_next_window_size(window_width, window_height)
                imgui.begin("Menu", None, (imgui.WINDOW_NO_RESIZE + imgui.WINDOW_NO_TITLE_BAR))
                style.window_padding = (.0, .0)  # WINDOW PADDING
                imgui.indent(25)
                imgui.dummy(0, 25)

                draw_blue_border()
                # mx, my = imgui.get_mouse_pos() 
                # wx, wy = imgui.get_window_position()
                # if mx > wx and mx < wx + window_width and my > wy and my < wy + window_height:
                #     remove_clickthrough(window)
                #     set_window_topmost(window)
                # else:
                #     set_clickthrough(window)
                #     set_window_topmost(window)
                display_image(texture_id, 50, 50)
                imgui.same_line(0, 0)
                textWidth = imgui.calc_text_size("Wavy V2 Private")[0]
                imgui.set_cursor_pos(((window_width - textWidth) * 0.5, 55))
                imgui.text("Wavy")
                imgui.same_line(0, 5)
                imgui.text_colored("V2", 0.102, 0.874, 0.980, 1)
                imgui.same_line(0, 5)
                imgui.text("Private")  

            with imgui.font(fortnite):
                imgui.dummy(0, 20)
                imgui.columns(3, "columns", border=False)
                imgui.COLOR_EDIT_NO_INPUTS = True
                # imgui.set_column_width(-1, 150) 
                _, enabled["skele"] = imgui.checkbox("Skeleton", enabled["skele"])
                _, enabled["distance"] = imgui.checkbox("Distance", enabled["distance"])
                _, enabled["box"] = imgui.checkbox("Box", enabled["box"])
                _, enabled["name"] = imgui.checkbox("Name", enabled["name"])
                _, enabled["snap"] = imgui.checkbox("Snapline", enabled["snap"])
                _, enabled["fov"] = imgui.checkbox("Fov Circle", enabled["fov"])
                _, enabled["streamproof"] = imgui.checkbox("Stream Proof", enabled["streamproof"])
                _, enabled["textoutline"] = imgui.checkbox("Text Outline", enabled["textoutline"])
                if enabled["streamproof"]:
                    set_window_display_affinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
                else:
                    set_window_display_affinity(hwnd, WDA_NONE)

                imgui.next_column()

                # imgui.set_column_width(-1, imgui.get_window_width() - 160)
                style.window_padding = (10.0, 10.0)  # WINDOW PADDING
                imgui.push_id("SKELE_VISIBLE")
                _, skele_visible_rgba = imgui.color_edit4("SKELE_VISIBLE", *skele_visible_rgba, 32)
                if imgui.is_item_hovered(): remove_clickthrough(window)
                imgui.pop_id()
                _, skele_non_visible_rgba = imgui.color_edit4("SKELE_NON_VISIBLE", *skele_non_visible_rgba, 32)
                if imgui.is_item_active(): remove_clickthrough(window)
                _, box_visible_rgba = imgui.color_edit4("BOX_VISIBLE", *box_visible_rgba, 32)
                if imgui.is_item_active(): remove_clickthrough(window)
                _, box_non_visible_rgba = imgui.color_edit4("BOX_NON_VISIBLE", *box_non_visible_rgba, 32)
                if imgui.is_item_active(): remove_clickthrough(window)
                _, snap_visible_rgba = imgui.color_edit4("SNAP_VISIBLE", *snap_visible_rgba, 32)
                if imgui.is_item_active(): remove_clickthrough(window)
                _, snap_non_visible_rgba = imgui.color_edit4("SNAP_NON_VISIBLE", *snap_non_visible_rgba, 32)
                if imgui.is_item_active(): remove_clickthrough(window)
                imgui.next_column() 
                # imgui.set_column_width(-1, 100)
                _, ign_rgba = imgui.color_edit4("IGN", *ign_rgba, 32)
                if imgui.is_item_active(): remove_clickthrough(window)
                _, distance_rgba = imgui.color_edit4("DISTANCE", *distance_rgba, 32)
                if imgui.is_item_active(): remove_clickthrough(window)
                _, outline_rgba = imgui.color_edit4("OUTLINE", *outline_rgba, 32)
                if imgui.is_item_active(): remove_clickthrough(window)
                _, fov_rgba = imgui.color_edit4("FOV", *fov_rgba, 32)
                if imgui.is_item_active(): remove_clickthrough(window)
                    
                SKELE_VISIBLE = imgui.get_color_u32_rgba(*skele_visible_rgba)
                SKELE_NON_VISIBLE = imgui.get_color_u32_rgba(*skele_non_visible_rgba)
                BOX_VISIBLE = imgui.get_color_u32_rgba(*box_visible_rgba)
                BOX_NON_VISIBLE = imgui.get_color_u32_rgba(*box_non_visible_rgba)
                SNAP_VISIBLE = imgui.get_color_u32_rgba(*snap_visible_rgba)
                SNAP_NON_VISIBLE = imgui.get_color_u32_rgba(*snap_non_visible_rgba)
                FOV = imgui.get_color_u32_rgba(*fov_rgba)
                IGN = imgui.get_color_u32_rgba(*ign_rgba)
                DISTANCE = imgui.get_color_u32_rgba(*distance_rgba)
                OUTLINE = imgui.get_color_u32_rgba(*outline_rgba)
                # style.window_padding = (40.0, outline_global0.0)  # WINDOW PADDING

                imgui.columns(1)

                particles()
                imgui.end()

        else:
            set_clickthrough(window)

        O = 0
        latest_message = None

        while True:
            O += 1
            if O > 5:
                break

            try:
                # Keep receiving messages until no more are available
                while True:
                    message = socket.recv(flags=zmq.NOBLOCK)
                    latest_message = message
                    O += 1
                    if O > 500:
                        break
            except zmq.Again:  # zmq.Again is raised when there are no more messages
                pass

            try:
                if latest_message:
                    data = latest_message.decode('utf-8', errors='replace').split(",")[:-1]
                    if len(data) == 0:
                        continue
                    else:   
                        coordinates = [(data[i], data[i+1]) for i in range(0, len(data), 2)]
                        POS = [coordinates[i:i+19] for i in range(0, len(coordinates), 19)]
                    break
            except zmq.Again:  # zmq.Again is raised when there are no more messages
                pass
        
        number_of_visible = 0
        number_of_close = 0

        for player in POS:
            try:
                headboxX = int(float(player[17][0]))   
                headboxY = int(float(player[17][1]))
                if int(float(player[15][0])) < 50: number_of_close += 1
                distance = "[" + str(int(float(player[15][0]))) + "m]"

                with imgui.font(fortnite):
                    x = 0
                    if int(float(player[14][1])) == -102:
                        x = headboxY + outline_thickness
                    else:
                        x = int(float(player[14][1]))
                    name = str(player[16][0])
                    text_size = imgui.calc_text_size(distance)
                    text_size2 = imgui.calc_text_size(name)
                    ch = abs(headboxY - x)
                    cw = ch * 0.50

                    if enabled["skele"]:
                        dl.add_line(int(float(player[0][0])), int(float(player[0][1])),  int(float(player[2][0])), int(float(player[2][1])), OUTLINE, outline_global)
                        dl.add_line(int(float(player[1][0])),  int(float(player[1][1])), int(float(player[2][0])), int(float(player[2][1])), OUTLINE, outline_global)
                        dl.add_line(int(float(player[3][0])),  int(float(player[3][1])), int(float(player[2][0])), int(float(player[2][1])), OUTLINE, outline_global)
                        dl.add_line(int(float(player[4][0])),  int(float(player[4][1])), int(float(player[2][0])), int(float(player[2][1])), OUTLINE, outline_global)
                        dl.add_line(int(float(player[5][0])),  int(float(player[5][1])), int(float(player[3][0])), int(float(player[3][1])), OUTLINE, outline_global)
                        dl.add_line(int(float(player[6][0])),  int(float(player[6][1])), int(float(player[4][0])), int(float(player[4][1])), OUTLINE, outline_global)
                        dl.add_line(int(float(player[5][0])),  int(float(player[5][1])), int(float(player[7][0])), int(float(player[7][1])), OUTLINE, outline_global)
                        dl.add_line(int(float(player[6][0])),  int(float(player[6][1])), int(float(player[8][0])), int(float(player[8][1])), OUTLINE, outline_global)
                        dl.add_line(int(float(player[10][0])), int(float(player[10][1])),int(float(player[1][0])), int(float(player[1][1])), OUTLINE, outline_global)
                        dl.add_line(int(float(player[9][0])),  int(float(player[9][1])), int(float(player[1][0])), int(float(player[1][1])), OUTLINE, outline_global)
                        dl.add_line(int(float(player[12][0])), int(float(player[12][1])),int(float(player[10][0])), int(float(player[10][1])), OUTLINE, outline_global)
                        dl.add_line(int(float(player[11][0])), int(float(player[11][1])),int(float(player[9][0])), int(float(player[9][1])), OUTLINE, outline_global)
                        dl.add_line(int(float(player[13][0])), int(float(player[13][1])),int(float(player[12][0])), int(float(player[12][1])), OUTLINE, outline_global)
                        dl.add_line(int(float(player[14][0])), int(float(player[14][1])),int(float(player[11][0])), int(float(player[11][1])), OUTLINE, outline_global)
                        if int(float(player[15][1])) == 0:
                            dl.add_line(int(float(player[0][0])), int(float(player[0][1])),  int(float(player[2][0])), int(float(player[2][1])), SKELE_NON_VISIBLE, SKELE_THICKNESS2)
                            dl.add_line(int(float(player[1][0])),  int(float(player[1][1])), int(float(player[2][0])), int(float(player[2][1])), SKELE_NON_VISIBLE, SKELE_THICKNESS2)
                            dl.add_line(int(float(player[3][0])),  int(float(player[3][1])), int(float(player[2][0])), int(float(player[2][1])), SKELE_NON_VISIBLE, SKELE_THICKNESS2)
                            dl.add_line(int(float(player[4][0])),  int(float(player[4][1])), int(float(player[2][0])), int(float(player[2][1])), SKELE_NON_VISIBLE, SKELE_THICKNESS2)
                            dl.add_line(int(float(player[5][0])),  int(float(player[5][1])), int(float(player[3][0])), int(float(player[3][1])), SKELE_NON_VISIBLE, SKELE_THICKNESS2)
                            dl.add_line(int(float(player[6][0])),  int(float(player[6][1])), int(float(player[4][0])), int(float(player[4][1])), SKELE_NON_VISIBLE, SKELE_THICKNESS2)
                            dl.add_line(int(float(player[5][0])),  int(float(player[5][1])), int(float(player[7][0])), int(float(player[7][1])), SKELE_NON_VISIBLE, SKELE_THICKNESS2)
                            dl.add_line(int(float(player[6][0])),  int(float(player[6][1])), int(float(player[8][0])), int(float(player[8][1])), SKELE_NON_VISIBLE, SKELE_THICKNESS2)
                            dl.add_line(int(float(player[10][0])), int(float(player[10][1])),int(float(player[1][0])), int(float(player[1][1])), SKELE_NON_VISIBLE, SKELE_THICKNESS2)
                            dl.add_line(int(float(player[9][0])),  int(float(player[9][1])), int(float(player[1][0])), int(float(player[1][1])), SKELE_NON_VISIBLE, SKELE_THICKNESS2)
                            dl.add_line(int(float(player[12][0])), int(float(player[12][1])),int(float(player[10][0])), int(float(player[10][1])), SKELE_NON_VISIBLE, SKELE_THICKNESS2)
                            dl.add_line(int(float(player[11][0])), int(float(player[11][1])),int(float(player[9][0])), int(float(player[9][1])), SKELE_NON_VISIBLE, SKELE_THICKNESS2)
                            dl.add_line(int(float(player[13][0])), int(float(player[13][1])),int(float(player[12][0])), int(float(player[12][1])), SKELE_NON_VISIBLE, SKELE_THICKNESS2)
                            dl.add_line(int(float(player[14][0])), int(float(player[14][1])),int(float(player[11][0])), int(float(player[11][1])), SKELE_NON_VISIBLE, SKELE_THICKNESS2)
                        else:
                            number_of_visible += 1
                            dl.add_line(int(float(player[0][0])), int(float(player[0][1])),  int(float(player[2][0])), int(float(player[2][1])), SKELE_VISIBLE, SKELE_THICKNESS2)
                            dl.add_line(int(float(player[1][0])),  int(float(player[1][1])), int(float(player[2][0])), int(float(player[2][1])), SKELE_VISIBLE, SKELE_THICKNESS2)
                            dl.add_line(int(float(player[3][0])),  int(float(player[3][1])), int(float(player[2][0])), int(float(player[2][1])), SKELE_VISIBLE, SKELE_THICKNESS2)
                            dl.add_line(int(float(player[4][0])),  int(float(player[4][1])), int(float(player[2][0])), int(float(player[2][1])), SKELE_VISIBLE, SKELE_THICKNESS2)
                            dl.add_line(int(float(player[5][0])),  int(float(player[5][1])), int(float(player[3][0])), int(float(player[3][1])), SKELE_VISIBLE, SKELE_THICKNESS2)
                            dl.add_line(int(float(player[6][0])),  int(float(player[6][1])), int(float(player[4][0])), int(float(player[4][1])), SKELE_VISIBLE, SKELE_THICKNESS2)
                            dl.add_line(int(float(player[5][0])),  int(float(player[5][1])), int(float(player[7][0])), int(float(player[7][1])), SKELE_VISIBLE, SKELE_THICKNESS2)
                            dl.add_line(int(float(player[6][0])),  int(float(player[6][1])), int(float(player[8][0])), int(float(player[8][1])), SKELE_VISIBLE, SKELE_THICKNESS2)
                            dl.add_line(int(float(player[10][0])), int(float(player[10][1])),int(float(player[1][0])), int(float(player[1][1])), SKELE_VISIBLE, SKELE_THICKNESS2)
                            dl.add_line(int(float(player[9][0])),  int(float(player[9][1])), int(float(player[1][0])), int(float(player[1][1])), SKELE_VISIBLE, SKELE_THICKNESS2)
                            dl.add_line(int(float(player[12][0])), int(float(player[12][1])),int(float(player[10][0])), int(float(player[10][1])), SKELE_VISIBLE, SKELE_THICKNESS2)
                            dl.add_line(int(float(player[11][0])), int(float(player[11][1])),int(float(player[9][0])), int(float(player[9][1])), SKELE_VISIBLE, SKELE_THICKNESS2)
                            dl.add_line(int(float(player[13][0])), int(float(player[13][1])),int(float(player[12][0])), int(float(player[12][1])), SKELE_VISIBLE, SKELE_THICKNESS2)
                            dl.add_line(int(float(player[14][0])), int(float(player[14][1])),int(float(player[11][0])), int(float(player[11][1])), SKELE_VISIBLE, SKELE_THICKNESS2)

                    if int(float(player[15][1])) == 0:
                        if enabled["distance"]:
                            if enabled["textoutline"]: draw_smooth_outlined_text(headboxX - (text_size[0]/2), headboxY - (text_size[1]) - (text_size[1]/2), distance)
                            dl.add_text(headboxX - (text_size[0]/2), headboxY - (text_size[1]) - (text_size[1]/2), DISTANCE, distance)
                        if enabled["name"]:
                            if enabled["textoutline"]: draw_smooth_outlined_text(headboxX - (text_size2[0]/2), x + text_size2[1]/2, name)
                            dl.add_text(headboxX - (text_size2[0]/2), x + (text_size2[1]/2), IGN, name)
                    else:
                        if enabled["distance"]:
                            if enabled["textoutline"]: draw_smooth_outlined_text(headboxX - (text_size[0]/2), headboxY - (text_size[1]) - (text_size[1]/2), distance)
                            dl.add_text(headboxX - (text_size[0]/2), headboxY - (text_size[1]) - (text_size[1]/2), DISTANCE, distance)
                        if enabled["name"]:
                            if enabled["textoutline"]: draw_smooth_outlined_text(headboxX - (text_size2[0]/2), x + text_size2[1]/2, name)
                            dl.add_text(headboxX - (text_size2[0]/2), x + (text_size2[1]/2), IGN, name)

                    if headboxX > 0 and headboxX < 1920 and headboxY > 0 and headboxY < 1080:
                        if int(float(player[15][1])) == 0:
                            if enabled["box"]:
                                dl.add_rect(headboxX - cw/2, headboxY, headboxX + cw/2, headboxY + ch, OUTLINE, 0, 0, outline_global)
                                dl.add_rect(headboxX - cw/2, headboxY, headboxX + cw/2, headboxY + ch, BOX_NON_VISIBLE, 0, 0, 1)
                        else:
                            if enabled["box"]:
                                dl.add_rect(headboxX - cw/2, headboxY, headboxX + cw/2, headboxY + ch, OUTLINE, 0, 0, outline_global)
                                dl.add_rect(headboxX - cw/2, headboxY, headboxX + cw/2, headboxY + ch, BOX_VISIBLE, 0, 0, 1)
                    if enabled["snap"]:
                        if int(float(player[15][1])) == 0:
                            dl.add_line(1920/2, 1080, headboxX, headboxY, OUTLINE, outline_global)
                            dl.add_line(1920/2, 1080, headboxX, headboxY, SNAP_NON_VISIBLE, 1)
                        else:
                            dl.add_line(1920/2, 1080, headboxX, headboxY, OUTLINE, outline_global)
                            dl.add_line(1920/2, 1080, headboxX, headboxY, SNAP_VISIBLE, 1)

                imgui.pop_font()

            except: pass
        with imgui.font(verdanab2):
            logo_text = "hyper.gg"
            text_size = imgui.calc_text_size(logo_text)
            draw_smooth_outlined_text(1920/2 - text_size[0]/2, 2, logo_text)
            dl.add_text(1920/2 - text_size[0]/2, 2, imgui.get_color_u32_rgba(0.8, 0.8, 0.8, 1), logo_text)

            # rendered = "Rendered Players | " + str(len(POS))
            # rendereds = imgui.calc_text_size(rendered)
            # draw_smooth_outlined_text(1920/2 - rendereds[0]/2, 24, rendered)
            # dl.add_text(1920/2 - rendereds[0]/2, 24, imgui.get_color_u32_rgba(0, 0.6, 0, 1), rendered)

            # close = "Close Range | " + str(number_of_close)
            # closes = imgui.calc_text_size(close)
            # draw_smooth_outlined_text(1920/2 - closes[0]/2, 46, close)
            # dl.add_text(1920/2 - closes[0]/2, 46, imgui.get_color_u32_rgba(0.6, 0, 0, 1), close)

            # vis = "Visible | " + str(number_of_visible)
            # viss = imgui.calc_text_size(vis)
            # draw_smooth_outlined_text(1920/2 - viss[0]/2, 68, vis)
            # dl.add_text(1920/2 - viss[0]/2, 68, imgui.get_color_u32_rgba(0, 0.6, 0, 1), vis)

        if enabled["fov"]:
            dl.add_circle(1920/2, 1080/2, 200, FOV, 200, 2)
        sleep(SLEEP_DELAY)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        imgui.render()
        imgui_renderer.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

if __name__ == "__main__":
    load_settings("settings.json")
    start()
