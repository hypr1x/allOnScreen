import glfw
import ctypes
from OpenGL.GL import *
import imgui
from imgui.integrations.glfw import GlfwRenderer
import zmq
context = zmq.Context()
socket = context.socket(zmq.PULL)
socket.bind("tcp://*:12345")

POS = []
fov = 420

imgui.create_context()
glfw.init()
glfw.window_hint(glfw.FLOATING, True)
glfw.window_hint(glfw.RESIZABLE, False)
glfw.window_hint(glfw.DECORATED, False)
glfw.window_hint(glfw.TRANSPARENT_FRAMEBUFFER, True)

window = glfw.create_window(1920, 1079, "hyzr", None, None)
if not window:
    glfw.terminate()

# Import ctypes library for calling Windows API functions
from ctypes import wintypes

# Define constants for SetWindowDisplayAffinity
WDA_NONE = 0x00000000
WDA_MONITOR = 0x00000001
WDA_EXCLUDEFROMCAPTURE = 0x00000011

# Load the user32 DLL
user32 = ctypes.WinDLL('user32', use_last_error=True)

# Define the SetWindowDisplayAffinity function prototype
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
ctypes.windll.user32.SetWindowLongW(
    hwnd, -20, exstyle
)  # Set extended style
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
# glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
impl = GlfwRenderer(window)
imgui.get_io().ini_file_name = "".encode()
imgui.create_context()
imgui_io = imgui.get_io()
imgui_renderer = GlfwRenderer(window)
io = imgui.get_io()

# set_window_display_affinity(hwnd, WDA_EXCLUDEFROMCAPTURE)

verdanab = io.fonts.add_font_from_file_ttf(
    "./BurbankBigRegular-Black.ttf",
    14,
)


# verdanab2 = io.fonts.add_font_from_file_ttf(
#     "C:/Windows/Fonts/verdanab.ttf",
#     10,
# )
# SKELE = imgui.get_color_u32_rgba(1, 0.2, 0, 1)
# WHITE = imgui.get_color_u32_rgba(1, 1, 1, 1)
# BOX = imgui.get_color_u32_rgba(1, 0, 0, 1)

SKELE = imgui.get_color_u32_rgba(0, 0, 0, 1)
WHITE = imgui.get_color_u32_rgba(1, 1, 0, 1)
BOX = imgui.get_color_u32_rgba(1, 0, 0, 1)
SNAP = imgui.get_color_u32_rgba(1, 0, 1, 1)
SNAP2 = imgui.get_color_u32_rgba(0, 1, 0, 1)
WNAME = imgui.get_color_u32_rgba(1, 0, 1, 1)
BOX2 = imgui.get_color_u32_rgba(1, 0, 1, 1)
FOV = imgui.get_color_u32_rgba(0, 0, 0, 1)
ADS = imgui.get_color_u32_rgba(0.3, 0.3, 0.3, 1)
# WHITE = imgui.get_color_u32_rgba(1, 135/255, 110/255, 1)
SKELE_THICKNESS = 4
SKELE_THICKNESS2 = 2
impl.refresh_font_texture()

IGN = imgui.get_color_u32_rgba(1, 1, 1, 1)
IGN2 = imgui.get_color_u32_rgba(1, 1, 1, 1)
SKELE3 = imgui.get_color_u32_rgba(1, 0, 0, 1)
SKELE2 = imgui.get_color_u32_rgba(0, 1, 0, 1)

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

def start():
    global POS, dl
    while not glfw.window_should_close(window):
        glfw.poll_events()
        try:
            imgui.new_frame() 
        except: 
            pass

        impl.process_inputs()
        dl = imgui.get_background_draw_list()
        O = 0
        while True:
            O += 1
            if O > 5000:
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                glfw.swap_buffers(window)
                break
            try:
                message = socket.recv(flags=zmq.NOBLOCK)
                data = message.decode('utf-8', errors='replace').split(",")[ : -1]
                if len(data) == 0:  continue
                else: 
                    coordinates = [(data[i], data[i+1]) for i in range(0, len(data), 2)]
                    POS = [coordinates[i:i+19] for i in range(0, len(coordinates), 19)]
                    break
            except: 
                pass

        fps = int(imgui.get_io().framerate)
        fps_text = f"FPS: {fps}"
        hyper_text = f"Hyper Private"
        with imgui.font(verdanab):
            # for i in range(-outline_thickness, outline_thickness + 1):
            #     for j in range(-outline_thickness, outline_thickness + 1):
            #         if i != 0 or j != 0:
            #             dl.add_text(7 + i, 8 + j, outline_color, hyper_text)
            
            draw_smooth_outlined_text(7, 8, hyper_text)

            dl.add_text(7, 8, imgui.get_color_u32_rgba(0, 1, 1, 255), hyper_text)
            # drawOutline(7, 8, hyper_text)
            # draw_outlined_text((7, 8), imgui.get_color_u32_rgba(0, 1, 1, 255), hyper_text)

            # for i in range(-outline_thickness, outline_thickness + 1):
            #     for j in range(-outline_thickness, outline_thickness + 1):
            #         if i != 0 or j != 0:
            #             dl.add_text(7 + i, 27 + j, outline_color, fps_text)

            draw_smooth_outlined_text(7, 27, fps_text)

            dl.add_text(7, 27, imgui.get_color_u32_rgba(1, 1, 1, 1), fps_text)

        for player in POS:
            try:
                headboxX = int(float(player[17][0]))   
                headboxY = int(float(player[17][1]))
                distance = "[" + str(int(float(player[15][0]))) + "m]"
                # if headboxX < 0 or headboxX > 1920 or headboxY > 1080 or headboxY < 0:
                # if int(float(player[15][1])) == 0:
                #     dl.add_line(headboxX, headboxY,  1920/2, 0, imgui.get_color_u32_rgba(1, 0, 0, 1), 1)
                # else:
                #     dl.add_line(headboxX, headboxY,  1920/2, 0, imgui.get_color_u32_rgba(1, 1, 1, 1), 1)

                text_size = imgui.calc_text_size(distance)
                dl.add_line(int(float(player[0][0])), int(float(player[0][1])),  int(float(player[2][0])), int(float(player[2][1])), SKELE, SKELE_THICKNESS)
                dl.add_line(int(float(player[1][0])),  int(float(player[1][1])), int(float(player[2][0])), int(float(player[2][1])), SKELE, SKELE_THICKNESS)
                dl.add_line(int(float(player[3][0])),  int(float(player[3][1])), int(float(player[2][0])), int(float(player[2][1])), SKELE, SKELE_THICKNESS)
                dl.add_line(int(float(player[4][0])),  int(float(player[4][1])), int(float(player[2][0])), int(float(player[2][1])), SKELE, SKELE_THICKNESS)
                dl.add_line(int(float(player[5][0])),  int(float(player[5][1])), int(float(player[3][0])), int(float(player[3][1])), SKELE, SKELE_THICKNESS)
                dl.add_line(int(float(player[6][0])),  int(float(player[6][1])), int(float(player[4][0])), int(float(player[4][1])), SKELE, SKELE_THICKNESS)
                dl.add_line(int(float(player[5][0])),  int(float(player[5][1])), int(float(player[7][0])), int(float(player[7][1])), SKELE, SKELE_THICKNESS)
                dl.add_line(int(float(player[6][0])),  int(float(player[6][1])), int(float(player[8][0])), int(float(player[8][1])), SKELE, SKELE_THICKNESS)
                dl.add_line(int(float(player[10][0])), int(float(player[10][1])),int(float(player[1][0])), int(float(player[1][1])), SKELE, SKELE_THICKNESS)
                dl.add_line(int(float(player[9][0])),  int(float(player[9][1])), int(float(player[1][0])), int(float(player[1][1])), SKELE, SKELE_THICKNESS)
                dl.add_line(int(float(player[12][0])), int(float(player[12][1])),int(float(player[10][0])), int(float(player[10][1])), SKELE, SKELE_THICKNESS)
                dl.add_line(int(float(player[11][0])), int(float(player[11][1])),int(float(player[9][0])), int(float(player[9][1])), SKELE, SKELE_THICKNESS)
                dl.add_line(int(float(player[13][0])), int(float(player[13][1])),int(float(player[12][0])), int(float(player[12][1])), SKELE, SKELE_THICKNESS)
                dl.add_line(int(float(player[14][0])), int(float(player[14][1])),int(float(player[11][0])), int(float(player[11][1])), SKELE, SKELE_THICKNESS)
                if int(float(player[15][1])) == 0:
                    dl.add_line(int(float(player[0][0])), int(float(player[0][1])),  int(float(player[2][0])), int(float(player[2][1])), SKELE3, SKELE_THICKNESS2)
                    dl.add_line(int(float(player[1][0])),  int(float(player[1][1])), int(float(player[2][0])), int(float(player[2][1])), SKELE3, SKELE_THICKNESS2)
                    dl.add_line(int(float(player[3][0])),  int(float(player[3][1])), int(float(player[2][0])), int(float(player[2][1])), SKELE3, SKELE_THICKNESS2)
                    dl.add_line(int(float(player[4][0])),  int(float(player[4][1])), int(float(player[2][0])), int(float(player[2][1])), SKELE3, SKELE_THICKNESS2)
                    dl.add_line(int(float(player[5][0])),  int(float(player[5][1])), int(float(player[3][0])), int(float(player[3][1])), SKELE3, SKELE_THICKNESS2)
                    dl.add_line(int(float(player[6][0])),  int(float(player[6][1])), int(float(player[4][0])), int(float(player[4][1])), SKELE3, SKELE_THICKNESS2)
                    dl.add_line(int(float(player[5][0])),  int(float(player[5][1])), int(float(player[7][0])), int(float(player[7][1])), SKELE3, SKELE_THICKNESS2)
                    dl.add_line(int(float(player[6][0])),  int(float(player[6][1])), int(float(player[8][0])), int(float(player[8][1])), SKELE3, SKELE_THICKNESS2)
                    dl.add_line(int(float(player[10][0])), int(float(player[10][1])),int(float(player[1][0])), int(float(player[1][1])), SKELE3, SKELE_THICKNESS2)
                    dl.add_line(int(float(player[9][0])),  int(float(player[9][1])), int(float(player[1][0])), int(float(player[1][1])), SKELE3, SKELE_THICKNESS2)
                    dl.add_line(int(float(player[12][0])), int(float(player[12][1])),int(float(player[10][0])), int(float(player[10][1])), SKELE3, SKELE_THICKNESS2)
                    dl.add_line(int(float(player[11][0])), int(float(player[11][1])),int(float(player[9][0])), int(float(player[9][1])), SKELE3, SKELE_THICKNESS2)
                    dl.add_line(int(float(player[13][0])), int(float(player[13][1])),int(float(player[12][0])), int(float(player[12][1])), SKELE3, SKELE_THICKNESS2)
                    dl.add_line(int(float(player[14][0])), int(float(player[14][1])),int(float(player[11][0])), int(float(player[11][1])), SKELE3, SKELE_THICKNESS2)
                else:
                    dl.add_line(int(float(player[0][0])), int(float(player[0][1])),  int(float(player[2][0])), int(float(player[2][1])), SKELE2, SKELE_THICKNESS2)
                    dl.add_line(int(float(player[1][0])),  int(float(player[1][1])), int(float(player[2][0])), int(float(player[2][1])), SKELE2, SKELE_THICKNESS2)
                    dl.add_line(int(float(player[3][0])),  int(float(player[3][1])), int(float(player[2][0])), int(float(player[2][1])), SKELE2, SKELE_THICKNESS2)
                    dl.add_line(int(float(player[4][0])),  int(float(player[4][1])), int(float(player[2][0])), int(float(player[2][1])), SKELE2, SKELE_THICKNESS2)
                    dl.add_line(int(float(player[5][0])),  int(float(player[5][1])), int(float(player[3][0])), int(float(player[3][1])), SKELE2, SKELE_THICKNESS2)
                    dl.add_line(int(float(player[6][0])),  int(float(player[6][1])), int(float(player[4][0])), int(float(player[4][1])), SKELE2, SKELE_THICKNESS2)
                    dl.add_line(int(float(player[5][0])),  int(float(player[5][1])), int(float(player[7][0])), int(float(player[7][1])), SKELE2, SKELE_THICKNESS2)
                    dl.add_line(int(float(player[6][0])),  int(float(player[6][1])), int(float(player[8][0])), int(float(player[8][1])), SKELE2, SKELE_THICKNESS2)
                    dl.add_line(int(float(player[10][0])), int(float(player[10][1])),int(float(player[1][0])), int(float(player[1][1])), SKELE2, SKELE_THICKNESS2)
                    dl.add_line(int(float(player[9][0])),  int(float(player[9][1])), int(float(player[1][0])), int(float(player[1][1])), SKELE2, SKELE_THICKNESS2)
                    dl.add_line(int(float(player[12][0])), int(float(player[12][1])),int(float(player[10][0])), int(float(player[10][1])), SKELE2, SKELE_THICKNESS2)
                    dl.add_line(int(float(player[11][0])), int(float(player[11][1])),int(float(player[9][0])), int(float(player[9][1])), SKELE2, SKELE_THICKNESS2)
                    dl.add_line(int(float(player[13][0])), int(float(player[13][1])),int(float(player[12][0])), int(float(player[12][1])), SKELE2, SKELE_THICKNESS2)
                    dl.add_line(int(float(player[14][0])), int(float(player[14][1])),int(float(player[11][0])), int(float(player[11][1])), SKELE2, SKELE_THICKNESS2)
                # dl.add_line(headboxX, headboxY,  1920/2, 1080/2, imgui.get_color_u32_rgba(0, 0, 0, 1), 4)

                # if int(float(player[15][0])) < 10:
                #     dl.add_line(headboxX, headboxY,  1920/2, 1080/2, imgui.get_color_u32_rgba(1, 0, 0, 1), 2)
                # elif int(float(player[15][0])) < 20:
                #     dl.add_line(headboxX, headboxY,  1920/2, 1080/2, imgui.get_color_u32_rgba(0.8, 0, 0, 1), 2)
                # elif int(float(player[15][0])) < 40:
                #     dl.add_line(headboxX, headboxY,  1920/2, 1080/2, imgui.get_color_u32_rgba(0.6, 0, 0, 1), 2)
                # elif int(float(player[15][0])) < 80:
                #     dl.add_line(headboxX, headboxY,  1920/2, 1080/2, imgui.get_color_u32_rgba(0.4, 0, 0, 1), 2)
                # elif int(float(player[15][0])) < 160:
                #     dl.add_line(headboxX, headboxY,  1920/2, 1080/2, imgui.get_color_u32_rgba(0.2, 0, 0, 1), 2)
                # elif int(float(player[15][0])) >= 160:
                #     dl.add_line(headboxX, headboxY,  1920/2, 1080/2, imgui.get_color_u32_rgba(0, 0, 0, 1), 2)
                with imgui.font(verdanab):
                    # for i in range(-outline_thickness - 1, outline_thickness + outline_thickness):
                    #     for j in range(-outline_thickness - 1, outline_thickness + outline_thickness):
                    #         if i != 0 or j != 0:
                    #             dl.add_text(headboxX - (text_size[0]/2) + i, headboxY + j, outline_color, distance)
                    x = 0
                    if int(float(player[14][1])) == -102:
                        x = headboxY + outline_thickness
                    else:
                        x = int(float(player[14][1]))
                    name = str(player[16][0])
                    text_size2 = imgui.calc_text_size(name)
                    # ch = abs(headboxY - x)
                    # cw = ch * 0.60
                    # if not(headboxX < 0 or headboxX > 1920 or headboxY > 1080 or headboxY < 0):
                    #     dl.add_rect(int(headboxX - cw/2), headboxY, int(headboxX + cw/2), headboxY + ch, imgui.get_color_u32_rgba(0, 0, 0, 1), 0, 0, 3)

                    #     if int(float(player[15][1])) == 0:
                    #         dl.add_rect(int(headboxX - cw/2), headboxY, int(headboxX + cw/2), headboxY + ch, imgui.get_color_u32_rgba(1, 0, 0, 1), 0, 0, 1)
                    #     else:
                    #         dl.add_rect(int(headboxX - cw/2), headboxY, int(headboxX + cw/2), headboxY + ch, imgui.get_color_u32_rgba(0, 1, 0, 1), 0, 0, 1)

                    if int(float(player[15][1])) == 0:
                        draw_smooth_outlined_text(headboxX - (text_size[0]/2), headboxY - (text_size[1]) - (text_size[1]/2), distance)
                        dl.add_text(headboxX - (text_size[0]/2), headboxY - (text_size[1]) - (text_size[1]/2), IGN, distance)
                        draw_smooth_outlined_text(headboxX - (text_size2[0]/2), x + text_size2[1]/2, name)
                        dl.add_text(headboxX - (text_size2[0]/2), x + (text_size2[1]/2), IGN, name)
                    else:
                        draw_smooth_outlined_text(headboxX - (text_size[0]/2), headboxY - (text_size[1]) - (text_size[1]/2), distance)
                        dl.add_text(headboxX - (text_size[0]/2), headboxY - (text_size[1]) - (text_size[1]/2), IGN2, distance)
                        draw_smooth_outlined_text(headboxX - (text_size2[0]/2), x + text_size2[1]/2, name)
                        dl.add_text(headboxX - (text_size2[0]/2), x + (text_size2[1]/2), IGN2, name)
                


        #         # ads = int(float(player[18][0]))
        #         # weaponName = player[18][1]
        #         # if win32api.GetAsyncKeyState(0X02) == 0:
        #         #     dl.add_line(int(float(player[0][0])), int(float(player[0][1])),  int(float(player[2][0])), int(float(player[2][1])), SKELE3, SKELE_THICKNESS2)
        #         #     dl.add_line(int(float(player[1][0])),  int(float(player[1][1])), int(float(player[2][0])), int(float(player[2][1])), SKELE3, SKELE_THICKNESS2)
        #         #     dl.add_line(int(float(player[3][0])),  int(float(player[3][1])), int(float(player[2][0])), int(float(player[2][1])), SKELE3, SKELE_THICKNESS2)
        #         #     dl.add_line(int(float(player[4][0])),  int(float(player[4][1])), int(float(player[2][0])), int(float(player[2][1])), SKELE3, SKELE_THICKNESS2)
        #         #     dl.add_line(int(float(player[5][0])),  int(float(player[5][1])), int(float(player[3][0])), int(float(player[3][1])), SKELE3, SKELE_THICKNESS2)
        #         #     dl.add_line(int(float(player[6][0])),  int(float(player[6][1])), int(float(player[4][0])), int(float(player[4][1])), SKELE3, SKELE_THICKNESS2)
        #         #     dl.add_line(int(float(player[5][0])),  int(float(player[5][1])), int(float(player[7][0])), int(float(player[7][1])), SKELE3, SKELE_THICKNESS2)
        #         #     dl.add_line(int(float(player[6][0])),  int(float(player[6][1])), int(float(player[8][0])), int(float(player[8][1])), SKELE3, SKELE_THICKNESS2)
        #         #     dl.add_line(int(float(player[10][0])), int(float(player[10][1])),int(float(player[1][0])), int(float(player[1][1])), SKELE3, SKELE_THICKNESS2)
        #         #     dl.add_line(int(float(player[9][0])),  int(float(player[9][1])), int(float(player[1][0])), int(float(player[1][1])), SKELE3, SKELE_THICKNESS2)
        #         #     dl.add_line(int(float(player[12][0])), int(float(player[12][1])),int(float(player[10][0])), int(float(player[10][1])), SKELE3, SKELE_THICKNESS2)
        #         #     dl.add_line(int(float(player[11][0])), int(float(player[11][1])),int(float(player[9][0])), int(float(player[9][1])), SKELE3, SKELE_THICKNESS2)
        #         #     dl.add_line(int(float(player[13][0])), int(float(player[13][1])),int(float(player[12][0])), int(float(player[12][1])), SKELE3, SKELE_THICKNESS2)
        #         #     dl.add_line(int(float(player[14][0])), int(float(player[14][1])),int(float(player[11][0])), int(float(player[11][1])), SKELE3, SKELE_THICKNESS2)
        #         if int(float(player[15][1])) == 1:
        #             dl.add_line(int(float(player[0][0])), int(float(player[0][1])),  int(float(player[2][0])), int(float(player[2][1])), SKELE, SKELE_THICKNESS)
        #             dl.add_line(int(float(player[1][0])),  int(float(player[1][1])), int(float(player[2][0])), int(float(player[2][1])), SKELE, SKELE_THICKNESS)
        #             dl.add_line(int(float(player[3][0])),  int(float(player[3][1])), int(float(player[2][0])), int(float(player[2][1])), SKELE, SKELE_THICKNESS)
        #             dl.add_line(int(float(player[4][0])),  int(float(player[4][1])), int(float(player[2][0])), int(float(player[2][1])), SKELE, SKELE_THICKNESS)
        #             dl.add_line(int(float(player[5][0])),  int(float(player[5][1])), int(float(player[3][0])), int(float(player[3][1])), SKELE, SKELE_THICKNESS)
        #             dl.add_line(int(float(player[6][0])),  int(float(player[6][1])), int(float(player[4][0])), int(float(player[4][1])), SKELE, SKELE_THICKNESS)
        #             dl.add_line(int(float(player[5][0])),  int(float(player[5][1])), int(float(player[7][0])), int(float(player[7][1])), SKELE, SKELE_THICKNESS)
        #             dl.add_line(int(float(player[6][0])),  int(float(player[6][1])), int(float(player[8][0])), int(float(player[8][1])), SKELE, SKELE_THICKNESS)
        #             dl.add_line(int(float(player[10][0])), int(float(player[10][1])),int(float(player[1][0])), int(float(player[1][1])), SKELE, SKELE_THICKNESS)
        #             dl.add_line(int(float(player[9][0])),  int(float(player[9][1])), int(float(player[1][0])), int(float(player[1][1])), SKELE, SKELE_THICKNESS)
        #             dl.add_line(int(float(player[12][0])), int(float(player[12][1])),int(float(player[10][0])), int(float(player[10][1])), SKELE, SKELE_THICKNESS)
        #             dl.add_line(int(float(player[11][0])), int(float(player[11][1])),int(float(player[9][0])), int(float(player[9][1])), SKELE, SKELE_THICKNESS)
        #             dl.add_line(int(float(player[13][0])), int(float(player[13][1])),int(float(player[12][0])), int(float(player[12][1])), SKELE, SKELE_THICKNESS)
        #             dl.add_line(int(float(player[14][0])), int(float(player[14][1])),int(float(player[11][0])), int(float(player[11][1])), SKELE, SKELE_THICKNESS)
        #             # dl.add_rect_filled(headboxX - (cornerWidth/2), headboxY + text_size[1]/2 + 0, headboxX - (cornerWidth/2) + cornerWidth, headboxY + cornerHeight + text_size[1]/2 + 0, BOX2, 2, 2)
        #         if int(float(player[15][1])) == 0:
        #             dl.add_line(int(float(player[0][0])), int(float(player[0][1])),  int(float(player[2][0])), int(float(player[2][1])), SKELE2, SKELE_THICKNESS)
        #             dl.add_line(int(float(player[1][0])),  int(float(player[1][1])), int(float(player[2][0])), int(float(player[2][1])), SKELE2, SKELE_THICKNESS)
        #             dl.add_line(int(float(player[3][0])),  int(float(player[3][1])), int(float(player[2][0])), int(float(player[2][1])), SKELE2, SKELE_THICKNESS)
        #             dl.add_line(int(float(player[4][0])),  int(float(player[4][1])), int(float(player[2][0])), int(float(player[2][1])), SKELE2, SKELE_THICKNESS)
        #             dl.add_line(int(float(player[5][0])),  int(float(player[5][1])), int(float(player[3][0])), int(float(player[3][1])), SKELE2, SKELE_THICKNESS)
        #             dl.add_line(int(float(player[6][0])),  int(float(player[6][1])), int(float(player[4][0])), int(float(player[4][1])), SKELE2, SKELE_THICKNESS)
        #             dl.add_line(int(float(player[5][0])),  int(float(player[5][1])), int(float(player[7][0])), int(float(player[7][1])), SKELE2, SKELE_THICKNESS)
        #             dl.add_line(int(float(player[6][0])),  int(float(player[6][1])), int(float(player[8][0])), int(float(player[8][1])), SKELE2, SKELE_THICKNESS)
        #             dl.add_line(int(float(player[10][0])), int(float(player[10][1])),int(float(player[1][0])), int(float(player[1][1])), SKELE2, SKELE_THICKNESS)
        #             dl.add_line(int(float(player[9][0])),  int(float(player[9][1])), int(float(player[1][0])), int(float(player[1][1])), SKELE2, SKELE_THICKNESS)
        #             dl.add_line(int(float(player[12][0])), int(float(player[12][1])),int(float(player[10][0])), int(float(player[10][1])), SKELE2, SKELE_THICKNESS)
        #             dl.add_line(int(float(player[11][0])), int(float(player[11][1])),int(float(player[9][0])), int(float(player[9][1])), SKELE2, SKELE_THICKNESS)
        #             dl.add_line(int(float(player[13][0])), int(float(player[13][1])),int(float(player[12][0])), int(float(player[12][1])), SKELE2, SKELE_THICKNESS)
        #             dl.add_line(int(float(player[14][0])), int(float(player[14][1])),int(float(player[11][0])), int(float(player[11][1])), SKELE2, SKELE_THICKNESS)
        #         name = str(player[16][0])


        #         distanceStr = "[" + str(int(float(player[15][0]))) + "M]"
        #         with imgui.font(verdanab):  
        #             text_size = imgui.calc_text_size(distanceStr)
        #             text_size2 = imgui.calc_text_size(name)

        #             for i in range(-outline_thickness, outline_thickness + 1):
        #                 for j in range(-outline_thickness, outline_thickness + 1):
        #                     if i != 0 or j != 0:
        #                         dl.add_text(headboxX - text_size[0]/2 + i, headboxY - text_size[1]/2 + j, outline_color, distanceStr)
        #             dl.add_text(headboxX - text_size[0]/2, headboxY - text_size[1]/2, WHITE, distanceStr)

        #             x = 0
        #             if int(float(player[14][1])) == -102:
        #                 x = headboxY + outline_thickness0
        #             else:
        #                 x = int(float(player[14][1]))
        #             for i in range(-outline_thickness, outline_thickness + 1):
        #                 for j in range(-outline_thickness, outline_thickness + 1):
        #                     if i != 0 or j != 0:
        #                         dl.add_text(headboxX - text_size2[0]/2 + i, x + text_size2[1]/2 + j, outline_color, name)
        #             dl.add_text(headboxX - text_size2[0]/2, x + text_size2[1]/2, IGN, name)

            except: pass
        # dl.add_circle(1920/2, 1080/2, 600, IGN)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        imgui.render()
        imgui_renderer.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

if __name__ == "__main__":
    # threading.Thread(target=getLoop).start()
    start()
