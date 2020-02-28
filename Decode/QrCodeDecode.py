import cv2
from pyzbar import pyzbar
pic_per_frame = 5#每秒图片数
video = cv2.VideoCapture('input.mp4')#需要Decode的视频文件名
framerate = int(video.get(5))#FPS
framenum = int(video.get(7))#总帧数
total_pic_count = int(framenum / framerate * pic_per_frame) + 1#向上取整
result = ""
for i in range(total_pic_count):
    video.set(cv2.CAP_PROP_POS_FRAMES,1* framerate * i/ pic_per_frame )
    ret,frame = video.read()
    if ret:
        test = pyzbar.decode(frame)
        #print(test)
        if test:
            print(test[0].data.decode())#他刚刚好给我多出个句首回车