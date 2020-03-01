import random
import math
import numpy as np
import cv2
import matplotlib.pyplot as plt


def show_matrix(array):  # 显示矩阵（DEBUG用）
    print(array)
    plt.imshow(array)
    plt.show()


def summon_video():  # 生成视频
    pass


class MyCode:
    MyCodeSize = 64  # 二维码边长(单位：单元)
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
        self.canWirteSum = math.floor(self.canWirteSum/6)*4
        print(self.canWirteSum)

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
    # 0001 0010 0011 0100 0101 0110 0111 1000 1001 1010 1011 1100
    #    1    2    3    4    5    6    7    8    9   10   11   12
    #    C    C         C                   C
    #    1         1         1         1         1         1
    #         2    2              2    2              2    2
    #                   4    4    4    4                        4
    #                                       8    8    8    8    8

    def Hamming_encode(self, data):
        result = []
        for i in range(int(len(data)/2)):
            tempresult = 0
            for j in range(2):
                num = data[2*i+j]
                for k in range(12):
                    if k == 0 or k == 1 or k == 3 or k == 7:
                        tempresult <<= 1
                    else:
                        tempresult <<= 1
                        tempresult += ((num & 0b10000000) >> 7)
                        num <<= 1
                for k in range(12):
                    if k != 0 and k != 1 and k != 3 and k != 7:
                        #print((k+1) & 0b1)
                        if (k+1) & 0b1 == 0b1:
                           # print((tempresult << k) & 0b100000000000)
                            tempresult ^= ((tempresult << k) & 0b100000000000)
                            
                        if (k+1) & 0b10 == 0b10:
                            tempresult ^= ((tempresult << (k-1))
                                           & 0b010000000000)
                        if (k+1) & 0b100 == 0b100:
                            tempresult ^= ((tempresult << (k-3))
                                           & 0b000100000000)
                        if (k+1) & 0b1000 == 0b1000:
                            tempresult ^= ((tempresult << (k-7))
                                           & 0b000000010000)
            #print(tempresult)
            result.append(tempresult>>16)
            result.append((tempresult>>8)&0b11111111)
            result.append(tempresult&0b11111111)
        return result

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

    def summon_pic(self, MyCodeMatrix):
        img = np.zeros((self.FrameSize*self.CellSize,
                        self.FrameSize*self.CellSize, 3), dtype=np.uint8)
        color = [(255, 255, 255), (0, 0, 0),  # 白 黑
                 (255, 0, 0), (0, 255, 0), (0, 0, 255)]  # 蓝 绿 红
        for i in range(self.FrameSize):
            for j in range(self.FrameSize):
                cv2.rectangle(img, (i*self.CellSize, j*self.CellSize),
                              ((i+1)*self.CellSize, (j+1)*self.CellSize),
                              color[MyCodeMatrix[j][i]], thickness=-1)
        cv2.imwrite('input.png', img)


# 初始化
NewCode = MyCode()
data = []
for i in range(math.floor(NewCode.canWirteSum/4)):
    data.append(i%256)
NewCode.summon_pic(NewCode.summon_MyCode(NewCode.Hamming_encode(data)))
print()

