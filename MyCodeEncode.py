import shutil
import os
import random
import math
import numpy as np
import cv2
import matplotlib.pyplot as plt
from ReedSolomon import ReedSolomon
import Video_Frame


def show_matrix(array):  # 显示矩阵（DEBUG用）
    print(array)
    plt.imshow(array)
    plt.show()


def summon_video():  # 生成视频
    pass


class MyCode:
    MyCodeSize = 48  # 二维码边长(单位：单元)
    EdgeWidth = 4  # 最小为4（单位：单元）
    CellSize = 12  # 每一个单元大小（单位：像素）

    def __init__(self):
        self.FrameSize = self.MyCodeSize + 2 * self.EdgeWidth
        PointPos = np.array([[1, 1, 1, 1, 1, 1, 1],
                             [1, 0, 0, 0, 0, 0, 1],
                             [1, 0, 1, 1, 1, 0, 1],
                             [1, 0, 1, 1, 1, 0, 1],
                             [1, 0, 1, 1, 1, 0, 1],
                             [1, 0, 0, 0, 0, 0, 1],
                             [1, 1, 1, 1, 1, 1, 1]], dtype=np.uint8)  # 定位点
        self.BaseCodeMatrix = np.zeros(
            (self.FrameSize, self.FrameSize), dtype=np.uint8)  # 初始矩阵
        BigPointPos = np.zeros((14, 14), dtype=np.uint8)
        for i in range(7):
            for j in range(7):
                BigPointPos[i * 2][j * 2] =\
                    BigPointPos[i * 2 + 1][j * 2] =\
                    BigPointPos[i * 2][j * 2 + 1] =\
                    BigPointPos[i * 2 + 1][j * 2 + 1] = PointPos[i][j]
        self.put_pointpos(self.BaseCodeMatrix, BigPointPos, posX=0, posY=0)
        self.put_pointpos(self.BaseCodeMatrix, BigPointPos,
                          posX=self.MyCodeSize - 14, posY=0)
        self.put_pointpos(self.BaseCodeMatrix, BigPointPos,
                          posX=0, posY=self.MyCodeSize - 14)
        # self.put_pointpos(self.BaseCodeMatrix, PointPos,
        #                  posX=self.MyCodeSize - 14, posY=self.MyCodeSize - 14)
        # show_matrix(self.BaseCodeMatrix)
        # 计算可填充数据区域
        self.canWrite = np.zeros((self.FrameSize, self.FrameSize))
        #self.canWirteSum = 0
        for i in range(self.EdgeWidth, self.EdgeWidth+16):
            self.canWrite[i] = np.insert(
                np.zeros(self.EdgeWidth*2+32), self.EdgeWidth+16, np.ones(self.MyCodeSize-32))
            #self.canWirteSum += self.MyCodeSize-32
        for i in range(self.EdgeWidth+16, self.FrameSize-self.EdgeWidth-16):
            self.canWrite[i] = np.insert(
                np.zeros(self.EdgeWidth*2), self.EdgeWidth, np.ones(self.MyCodeSize))
            #self.canWirteSum += self.MyCodeSize
        for i in range(self.FrameSize-self.EdgeWidth-16, self.FrameSize-self.EdgeWidth):
            self.canWrite[i] = np.insert(
                np.zeros(self.EdgeWidth*2+16), self.EdgeWidth+16, np.ones(self.MyCodeSize-16))
            #self.canWirteSum += self.MyCodeSize-16
        # show_matrix(self.canWrite)
        # print(self.canWirteSum)
        # show_matrix(self.BaseCodeMatrix+0.5*self.canWrite)
        self.canWirteSum = self.MyCodeSize**2-3*16*16  # 单位：B
        # print(self.canWirteSum)

    def put_pointpos(self, CodeMatrix, PointPos, posX, posY):
        # print(PointPos)
        dx, dy = posX + self.EdgeWidth, posY + self.EdgeWidth
        PointPosSize = int(PointPos.size ** 0.5)
        temp = np.hstack(
            (np.zeros((PointPosSize, dx), dtype=np.uint8), PointPos))
        temp = np.hstack(
            (temp, np.zeros((PointPosSize, self.FrameSize-dx-PointPosSize), dtype=np.uint8)))
        temp = np.vstack(
            (np.zeros((dy, self.FrameSize), dtype=np.uint8), temp))
        temp = np.vstack(
            (temp, np.zeros((self.FrameSize-dy-PointPosSize, self.FrameSize), dtype=np.uint8)))
        CodeMatrix += temp

    def summon_MyCode(self, data: list):
        result = self.BaseCodeMatrix.copy()
        index = 0
        SHR_MODE = 0
        for i in range(self.EdgeWidth, self.FrameSize-self.EdgeWidth):
            for j in range(self.EdgeWidth, self.FrameSize-self.EdgeWidth):
                if self.canWrite[i][j] == 1 and index < len(data):
                    result[i][j] = ((data[index] >> (6-SHR_MODE*2)) & 0b11)+1
                    if SHR_MODE == 3:
                        SHR_MODE, index = 0, index+1
                    else:
                        SHR_MODE += 1
        return result

    def summon_pic(self, MyCodeMatrix, index=0):
        img = np.zeros((self.FrameSize*self.CellSize,
                        self.FrameSize*self.CellSize, 3), dtype=np.uint8)
        color = [(255, 255, 255), (0, 0, 0),  # 白 黑
                 (255, 0, 0), (0, 255, 0), (0, 0, 255)]  # 蓝 绿 红
        for i in range(self.FrameSize):
            for j in range(self.FrameSize):
                cv2.rectangle(img, (i*self.CellSize, j*self.CellSize),
                              ((i+1)*self.CellSize, (j+1)*self.CellSize),
                              color[MyCodeMatrix[j][i]], thickness=-1)
        cv2.imwrite("encode_frames_output\\"+str(index)+".jpg", img)


if __name__ == "__main__":
    shutil.rmtree("encode_frames_output", True)
    os.mkdir("encode_frames_output")

    # 初始化
    NewCode = MyCode()
    # 总共可写canWriteSum个像素，即2*canWriteSum个位，canWriteSum/4个字节
    canWirteSum = NewCode.canWirteSum
    # 纠错码规定为每张192个
    ErrorSizeEachFrame = 128
    MessageEachFrame = int(canWirteSum/4)-ErrorSizeEachFrame

    data = []
    binfile = open("e1.bin", 'rb')
    #size = os.path.getsize("e1.bin")

    import binascii
    sec=input()
    for i in range(sec*5*MessageEachFrame):
        data.append(int(binascii.b2a_hex(binfile.read(1)),16))
    print(data)

    index = 0
    reed_solomon = ReedSolomon(error_size=ErrorSizeEachFrame)
    while len(data) > MessageEachFrame:
        batch_data = data[:MessageEachFrame]  # 截取前MessageEachFram个字节
        data = data[MessageEachFrame:]  # 剩余字节
        NewCode.summon_pic(NewCode.summon_MyCode(reed_solomon.encode(
            message=batch_data, error_size=ErrorSizeEachFrame)), index)
        index += 1
    NewCode.summon_pic(NewCode.summon_MyCode(reed_solomon.encode(
        message=data+[0]*(MessageEachFrame-len(data)), error_size=ErrorSizeEachFrame)), index)

    Video_Frame.frame_to_video()
