import cv2
import os
MyCodeSize = 64  # 二维码边长(单位：单元)
EdgeWidth = 4  # 最小为4（单位：单元）
CellSize = 12  # 每一个单元大小（单位：像素）
FPS = 5  # 每秒图片数

FrameSize = CellSize*(MyCodeSize+EdgeWidth*2)


def frame_to_video():
    print(FrameSize)
    video = cv2.VideoWriter("encode_output.mp4",
                            cv2.VideoWriter_fourcc(*'DIVX'),
                            30,  # FPS
                            (FrameSize, FrameSize))  # 视频格式
    frame = cv2.imread("blank.jpg")
    for i in range(60):
        video.write(frame)
    for i in range(len(os.listdir("encode_frames_output\\"))):
        frame = cv2.imread("encode_frames_output\\"+str(i)+'.jpg')
        print(i)
        for j in range(int(30/FPS)):
            # print("write"+str(j))
            video.write(frame)
    video.release()


def video_to_frame():
    import cv2
    from pyzbar import pyzbar
    pic_per_frame = 5  # 每秒图片数
    video = cv2.VideoCapture('decode_input.mp4')  # 需要Decode的视频文件名
    framerate = int(video.get(5))  # FPS
    framenum = int(video.get(7))  # 总帧数
    total_pic_count = int(framenum / framerate * pic_per_frame) + 1  # 向上取整
    for i in range(total_pic_count):
        video.set(cv2.CAP_PROP_POS_FRAMES, 1 * framerate * i / pic_per_frame)
        ret, frame = video.read()
        cv2.imwrite("decode_frames_input\\"+str(i)+'.jpg', frame)
