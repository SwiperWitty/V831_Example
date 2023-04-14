#!/usr/bin/python3
    
from maix import nn, camera, image, display
from maix.nn.app.face import FaceRecognize
import serial,time
from evdev import InputDevice
from select import select

#UART1 + KEY + Face

ser = serial.Serial("/dev/ttyS1",9600,timeout=0.2)    # 连接串口
tmp = ser.readline()

Over_ID = {"a"}
MK_Face = {'A':0,'B':0,'C':0,'D':0,'E':0,'F':0 } 
score_threshold = 70                            #识别分数阈值
input_size = (224, 224, 3)                      #输入图片尺寸
input_size_fe = (128, 128, 3)                   #输入人脸数据
feature_len = 256                               #人脸数据宽度
steps = [8, 16, 32]                             #
channel_num = 0                                 #通道数量
users = []                                      #初始化用户列表
names = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]  #人脸标签定义
model = {                                                                                                                                   
    "param": "/home/model/face_recognize/model_int8.param",
    "bin": "/home/model/face_recognize/model_int8.bin"
}
model_fe = {
    "param": "/home/model/face_recognize/fe_res18_117.param",
    "bin": "/home/model/face_recognize/fe_res18_117.bin"
}


for i in range(len(steps)):
    channel_num += input_size[1] / steps[i] * (input_size[0] / steps[i]) * 2
channel_num = int(channel_num)     #统计通道数量
options = {                             #准备人脸输出参数
    "model_type":  "awnn",
    "inputs": {
        "input0": input_size
    },
    "outputs": {
        "output0": (1, 4, channel_num) ,
        "431": (1, 2, channel_num) ,
        "output2": (1, 10, channel_num) 
    },
    "mean": [127.5, 127.5, 127.5],
    "norm": [0.0078125, 0.0078125, 0.0078125],
}
options_fe = {                             #准备特征提取参数
    "model_type":  "awnn",
    "inputs": {
        "inputs_blob": input_size_fe
    },
    "outputs": {
        "FC_blob": (1, 1, feature_len)
    },
    "mean": [127.5, 127.5, 127.5],
    "norm": [0.0078125, 0.0078125, 0.0078125],
}
keys = InputDevice('/dev/input/event0')

threshold = 0.5                                         #人脸阈值
nms = 0.3                                               
max_face_num = 1                                        #输出的画面中的人脸的最大个数
print("-- load model:", model)
m = nn.load(model, opt=options)
print("-- load ok")
print("-- load model:", model_fe)
m_fe = nn.load(model_fe, opt=options_fe)
print("-- load ok")
face_recognizer = FaceRecognize(m, m_fe, feature_len, input_size, threshold, nms, max_face_num)

MK_ID = 0

def get_key():                                      #按键检测函数
    r,w,x = select([keys], [], [],0)
    if r:
        for event in keys.read(): 
            if event.value == 1 and event.code == 0x02:     # 右键
                return 1
            elif event.value == 1 and event.code == 0x03:   # 左键
                return 2
            elif event.value == 2 and event.code == 0x03:   # 左键连按
                return 3
    return 0

def map_face(box,points):                           #将224*224空间的位置转换到240*240或320*240空间内
    # print(box,points)
    if display.width() == display.height():
        def tran(x):
            return int(x/224*display.width())
        box = list(map(tran, box))
        def tran_p(p):
            return list(map(tran, p))
        points = list(map(tran_p, points))
    else:
        # 168x224(320x240) > 224x224(240x240) > 320x240
        s = (224*display.height()/display.width()) # 168x224
        w, h, c = display.width()/224, display.height()/224, 224/s
        t, d = c*h, (224 - s) // 2 # d = 224 - s // 2 == 28
        box[0], box[1], box[2], box[3] = int(box[0]*w), int((box[1]-28)*t), int(box[2]*w), int((box[3])*t)
        def tran_p(p):
            return [int(p[0]*w), int((p[1]-d)*t)] # 224 - 168 / 2 = 28 so 168 / (old_h - 28) = 240 / new_h
        points = list(map(tran_p, points))
    # print(box,points)
    return box,points

def darw_info(draw, box, points, disp_str, bg_color=(255, 0, 0), font_color=(255, 255, 255)):    #画框函数
    box,points = map_face(box,points)
    font_wh = image.get_string_size(disp_str)
    for p in points:
        draw.draw_rectangle(p[0] - 1, p[1] -1, p[0] + 1, p[1] + 1, color=bg_color)
    draw.draw_rectangle(box[0], box[1], box[0] + box[2], box[1] + box[3], color=bg_color, thickness=2)
    draw.draw_rectangle(box[0], box[1] - font_wh[1], box[0] + font_wh[0], box[1], color=bg_color, thickness = -1)
    draw.draw_string(box[0], box[1] - font_wh[1], disp_str, color=font_color)
def recognize(feature):                                                                   #进行人脸匹配
    def _compare(user):                                                         #定义映射函数
        return face_recognizer.compare(user, feature)                      #推测匹配分数 score相关分数
    face_score_l = list(map(_compare,users))                               #映射特征数据在记录中的比对分数
    return max(enumerate(face_score_l), key=lambda x: x[-1])                #提取出人脸分数最大值和最大值所在的位置

array_str = "{V831:Ready! }"
ser.write(array_str.encode("utf-8"))

if __name__ == "__main__":
    import signal
    def handle_signal_z(signum,frame):
        print("APP OVER")
        exit(0)
    signal.signal(signal.SIGINT,handle_signal_z)
    Flag_GO = 0
    face_ID_num = 0
    face_ID_NOW = 0
    Temp_A = 0
    Temp_B = 0
    while True:
        # tmp = ser.readline()
        # if "{V831-GO}" in tmp:
        #     Flag_GO = 1
        img = camera.capture()                       #获取224*224*3的图像数据
        if not img:
            time.sleep(0.02)
            exit(0)

        mks = img.find_qrcodes()
        for mk in mks:
            #外框数据
            X = mk['x']
            Y = mk['y']
            W = mk['w']
            H = mk['h']
            #二维码信息
            string = mk['payload']
            if("A" in string) :
                MK_ID = 'a'
            elif("B" in string) :
                MK_ID = 'b'
            else:
                MK_ID = 0
            #内框数据
            x1,y1 = mk['corners'][0]   #访问字典的列表
            x2,y2 = mk['corners'][1]
            x3,y3 = mk['corners'][2]
            x4,y4 = mk['corners'][3]

            #画外框
            img.draw_rectangle(X, Y, X + W, Y + H, color=(0, 0, 255), thickness = 2) 
            #打印信息
            img.draw_string(int(X) , int(Y - 35) , str(string), scale = 2.0, color = (255, 0, 0), thickness = 2)  #内框ID


        AI_img = img.copy().resize(224, 224)
        faces = face_recognizer.get_faces(AI_img.tobytes(),False)           #提取人脸特征信息
        if faces:
            for prob, box, landmarks, feature in faces:
                key_val = get_key()
                if key_val == 1 and Flag_GO == 0:     # 右键添加人脸记录
                    if len(users) < len(names):
                        face_ID_num += 1
                        # print("add user:", len(users))
                        users.append(feature)
                    else:
                        print("user full")

    #########################################################
                if len(users):                             #判断是否记录人脸
                    maxIndex = recognize(feature)
                    if maxIndex[1] > score_threshold:                                      #判断人脸识别阈值,当分数大于阈值时认为是同一张脸,当分数小于阈值时认为是相似脸
                        darw_info(img, box, landmarks, "{}:{:.2f}".format(names[maxIndex[0]], maxIndex[1]), font_color=(0, 0, 255, 255), bg_color=(0, 255, 0, 255))
                        temp = names[maxIndex[0]]
                        if Flag_GO == 0:
                            MK_Face[temp] = MK_ID
                            array = []
                            for a in MK_Face:
                                array.append(MK_Face[a])
                            Temp_A = array.count('a')     #找多少个‘a’
                            Temp_B = face_ID_num - Temp_A

                        if (temp not in Over_ID) and (Flag_GO == 1):
                            if MK_Face[temp] == MK_ID:
                                Over_ID.add(temp)
                                face_ID_NOW += 1
                                array_str = "{V831:B:" + str(temp) + "-new" + str(face_ID_NOW) + "}"
                                ser.write(array_str.encode("utf-8"))
                                time.sleep(0.05)
                                if MK_ID == 'a':
                                    Temp_A -= 1
                                elif MK_ID == 'b':
                                    Temp_B -= 1
                                if(Temp_A == 0):
                                    Temp_A = 1
                                    array_str = "{V831:C-" + str(MK_ID) + " Over}"      #完成
                                    ser.write(array_str.encode("utf-8"))
                                elif(Temp_B == 0):
                                    Temp_B = 1
                                    array_str = "{V831:C-" + str(MK_ID) + " Over}"      #完成
                                    ser.write(array_str.encode("utf-8"))
                        # print("user: {}, score: {:.2f}".format(names[maxIndex[0]], maxIndex[1]))
                    else:
                        darw_info(img, box, landmarks, "{}:{:.2f}".format(names[maxIndex[0]], maxIndex[1]), font_color=(255, 255, 255, 255), bg_color=(255, 0, 0, 255))
                        #print("maybe user: {}, score: {:.2f}".format(names[maxIndex[0]], maxIndex[1]))
                else:                                           #没有记录脸
                    darw_info(img, box, landmarks, "error face", font_color=(255, 255, 255, 255), bg_color=(255, 0, 0, 255))

        if (get_key() == 2):                                    #左键删除人脸记录
            if len(users) > 0:
                array_str = "{V831:A:" + str(Temp_A) + '+' + str(Temp_B) + "}"         #array_str = "{V831:C:Over}"
                ser.write(array_str.encode("utf-8"))
                Flag_GO = 1
                # print("remove user:", names[len(users) - 1])
                # users.pop()
            else:
                print("user empty")

        display.show(img)

