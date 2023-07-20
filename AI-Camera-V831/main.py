#!/usr/bin/python3

from maix import image, display, camera, gpio

camera.config(size=(240, 240))

import serial, time

ser = serial.Serial("/dev/ttyS1", 115200, timeout=0.2)  # 连接串口

tmp = ser.readline()
print('serial test start ...')

ser.write(b" \r\n")
time.sleep(1)
ser.write(b"{V831:Ready!}\n")

set_LAB = [[(0, 46, 22, 61, -45, 74)],  # red
           [(3, 35, 8, 127, -128, -25)]]  # blue
# LAB阈值的初始化格式:[L_MIN,A_MIN,B_MIN,L_MAX,A_MAX,B_MAX]

flag = '1'
now_time = time.time()

ser.write(b"ok\n")

while True:
    img = camera.capture()
    img.flip(flip = 0)
    img.flip(flip = 1)
    
    
    for j in range(2):
        blobs = img.find_blobs(set_LAB[j])  # 在图片中查找lab阈值内的颜色色块
        if blobs:
            for i in blobs:
                size = i["w"] * i["h"]  # 最大是240 *240也就是57600
                if size > 2000:
                    x_start = i["x"]
                    x_end = i["x"] + i["w"]
                    x_center = int((x_start + x_end) / 2)  # 中心坐标
                    y_start = i["y"]
                    y_end = i["y"] + i["h"]
                    y_center = int((y_start + y_end) / 2)
                    m = max((x_center - i["w"] * 0.3), 0)
                    n = max((y_center - i["h"] * 0.3), 0)
                    m = min((x_center - i["w"] * 0.3), 240)
                    n = min((y_center - i["h"] * 0.3), 240)
                    mk = [int(m), int(n), 20, 20]
                    if (mk[0] + 20) < 220 and (mk[1] + 20) < 220:
                        git_color = img.get_blob_color(mk, 0, 0)
                        img.draw_rectangle(9, 9, 21, 21, color=(255, 255, 255), thickness=1)  # 左上角颜色区域画出来
                        color = (int(git_color[0]), int(git_color[1]), int(git_color[2]))
                        img.draw_rectangle(10, 10, 20, 20, color, thickness=-1)  # 将颜色填充到左上角
                        img.draw_circle(x_center, y_center, int(i["h"] / 2 + 8), color,
                                        thickness=3)  # 画一个中心点在（50,50），半径为20的空心 圆
                        if (j == 0):
                            string = 'Red'
                        elif j == 1:
                            string = 'Blue'
                        str_size = image.get_string_size(string)
                        img.draw_string(x_center - int(str_size[0] / 2) - 5, y_start - 35, string, scale=1.5,
                                        color=(int(git_color[0]), int(git_color[1]), int(git_color[2])), thickness=2) 
    img.rotate(90)
    display.show(img)
