# generated by maixhub, tested on maixpy3 v0.4.8
from maix import nn, camera, display, image
import serial,time

input_size = (224, 224)
model = "model-50807.awnn.mud"
labels = ['wheel']
anchors = [2.47, 2.47, 1.88, 1.78, 2.95, 2.67, 2.16, 2.41, 1.84, 2.47]

ser = serial.Serial("/dev/ttyS1",9600,timeout=0.2)    # 连接串口
ser.write(b"{V831:Ready!}\n")
Time_last = time.time()
Time_now = time.time()

class YOLOv2:
    def __init__(self, model_path, labels, anchors, net_in_size, net_out_size):
        self.labels = labels
        self.anchors = anchors
        self.net_in_size = net_in_size
        self.net_out_size = net_out_size
        print("-- load model:", model)
        self.model = nn.load(model_path)
        print("-- load ok")
        print("-- init yolo2 decoder")
        self._decoder = nn.decoder.Yolo2(len(labels), anchors, net_in_size=net_in_size, net_out_size=net_out_size)
        print("-- init complete")

    def run(self, img, nms=0.3, threshold=0.5):
        out = self.model.forward(img, layout="hwc")
        boxes, probs = self._decoder.run(out, nms=nms, threshold=threshold, img_size=input_size)
        return boxes, probs

    def draw(self, img, boxes, probs):
        global Time_last,Time_now
        for i, box in enumerate(boxes):
            class_id = probs[i][0]
            prob = probs[i][1][class_id]
            msg = "{}:{:.2f}%".format(self.labels[class_id], prob*100)
            img.draw_rectangle(box[0], box[1], box[0] + box[2], box[1] + box[3], color=(0, 0, 255), thickness=2)
            Time_now = time.time()
            if((Time_now - Time_last) > 0.3):
                Time_last = Time_now
                ser.write(b"{V831:wheel }\n")
            

def main():
    camera.config(size=input_size)
    yolov2 = YOLOv2(model, labels, anchors, input_size, (input_size[0] // 32, input_size[1] // 32))
    while True:
        img = camera.capture()
        boxes, probs = yolov2.run(img, nms=0.3, threshold=0.5)
        yolov2.draw(img, boxes, probs)
        display.show(img)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback, time
        msg = traceback.format_exc()
        print(msg)
        img = image.new(size = (240, 240), color = (255, 0, 0), mode = "RGB")
        img.draw_string(0, 0, msg, scale = 0.8, color = (255, 255, 255), thickness = 1)
        display.show(img)
        time.sleep(20)