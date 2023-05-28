from maix import camera, dispaly
import serial,time

add = 0
while 1:
    img = camera.capture()
    add = add + 1
    str_temp = "/root/" + 'photo' + str(add) + '.jpg'
    img.save(str_temp)
    
    display(img)
    time.sleep(20)