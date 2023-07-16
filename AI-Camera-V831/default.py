from maix import camera,display,image,gpio
import serial,time

# UART1
UART1 = serial.Serial("/dev/ttyS1",115200,timeout=0.2)    # 连接串口
tmp = UART1.readline()
array_str = "{V831:Ready! }\n"
UART1.write(array_str.encode("utf-8"))

# LED
class LED:
    def __init__(self, line, bank, chip=1):
        self.led = gpio.gpio(line, bank, chip)
    def on(self):
        self.led.set_value(0)
    def off(self):
        self.led.set_value(1)
    def value(self):
        return self.led.get_value()
    def __del__(self):
        self.led.release()

blink = LED(14, "H")
blink.on()  #默认开

# KEY
class BUTTON:
    def __init__(self, line, bank, chip=1, mode=2):
        self.button = gpio.gpio(line, bank, chip, mode)
    def is_pressed(self):
        if self.button.get_value() != 1:
            return True
    def __del__(self):
        self.button.release()
        
key_1 = BUTTON(6, "H")
key_2 = BUTTON(7, "H")
key_3 = BUTTON(8, "H")
key_big = [key_1,key_2,key_3]
def Get_Key_State() :
    temp_state = 0
    if key_1.is_pressed() :
        temp_state = 1
    elif key_2.is_pressed() :
        temp_state = 2
    elif key_3.is_pressed() :
        temp_state = 3
    return temp_state

#

temp_num = 1

while True:
#     temp_num = Get_Key_State()
    img = image.new(size = (240, 240),color = (255,255,255), mode = "RGB")     #创建一张红色背景图
    if temp_num == 1 :
        img.draw_string(30, 30, "hello world !", scale = 1.4, color = (250,0,0), thickness = 1)
    if temp_num == 2 :
        img.draw_string(30, 30, "hello world !", scale = 1.4, color = (0,250,0), thickness = 1)
    if temp_num == 3 :
        img.draw_string(30, 30, "hello world !", scale = 1.4, color = (0,0,250), thickness = 1)
    
    img.rotate(90)
    display.show(img)   #把这张图显示出来
