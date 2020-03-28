import shutil
import os
import cv2
import numpy as np
import math
from ReedSolomon import ReedSolomon
import Video_Frame
import struct

CodeSize = 48
FrameSize = CodeSize+8
canWirteBit = CodeSize**2-16*16*3
error_size = 128
BytePerFrame = int(canWirteBit/4-error_size)

isStartReading = False

canWrite = np.zeros((FrameSize, FrameSize))
for i in range(4, 20):
    canWrite[i] = np.insert(
        np.zeros(40), 20, np.ones(CodeSize-32))
for i in range(20, FrameSize-20):
    canWrite[i] = np.insert(
        np.zeros(8), 4, np.ones(CodeSize))
    #self.canWirteSum += self.MyCodeSize
for i in range(FrameSize-20, FrameSize-4):
    canWrite[i] = np.insert(
        np.zeros(24), 20, np.ones(CodeSize-16))


def show_img(img, winname='OpenCV'):  # debug用
    cv2.namedWindow(winname)
    cv2.imshow(winname, img)
    cv2.waitKey(0)


def show_Analyze_Result(img, AffineCellSize, FrameSize):
    cv2.circle(img, (AffineCellSize*11, AffineCellSize*11),
               AffineCellSize, (0, 255, 0), -1)
    cv2.circle(img, (AffineCellSize*(FrameSize-11), AffineCellSize*11),
               AffineCellSize, (0, 255, 0), -1)
    cv2.circle(img, (AffineCellSize*11, AffineCellSize*(FrameSize-11)),
               AffineCellSize, (0, 255, 0), -1)
    cv2.rectangle(img, (AffineCellSize*4, AffineCellSize*4),
                  (AffineCellSize*(FrameSize-4), AffineCellSize*(FrameSize-4)), (0, 255, 0), 1)
    #show_img(img, 'Result')
    cv2.imwrite('AnalyzeResult.png', img)


def crop_rect(img, rect):  # 仿射变换 CSDN抄的
    center, size, angle = rect[0], rect[1], rect[2]
    center, size = tuple(map(int, center)), tuple(map(int, size))
    height, width = img.shape[0], img.shape[1]
    M = cv2.getRotationMatrix2D(center, angle, 1)
    img_rot = cv2.warpAffine(img, M, (width, height))
    img_crop = cv2.getRectSubPix(img_rot, size, center)
    return img_crop  # , img_rot


def isRate1(rate):
    return 0.5 < rate < 2


def isRate3(rate):
    return 1.5 < rate < 6


def isQrPointRateX(img):  # x方向上是否1:1:3:1:1
    # print(img)
    mid = int(len(img[0])/2)
    lastColor = 255 if img[0][mid] > 0 else 0
    changepoint = []

    for i in range(len(img)):  # 计算变化点
        color = 255 if img[i][mid] > 0 else 0
        if color != lastColor:
            lastColor = color
            changepoint.append(i)
    # print(changepoint)
    # 将数组长度整理为6，方便计算
    if len(changepoint) < 4 or len(changepoint) > 6:
        return False
    elif len(changepoint) == 4:
        changepoint = [0]+changepoint+[len(img[0])]
    elif len(changepoint) == 5:
        lside, rside = changepoint[0], len(img[0])-changepoint[4]
        changepoint = [0]+changepoint\
            if lside > rside else changepoint+[len(img[0])]
    arealength = []
    for i in range(5):
        arealength.append(changepoint[i+1]-changepoint[i])
    # print(changepoint)
    # print(arealength)
    # print(arealength[1]/arealength[0], arealength[2]/arealength[1],
    #      arealength[2]/arealength[3], arealength[3]/arealength[4])
    return (isRate1(arealength[1]/arealength[0])
            and isRate3(arealength[2]/arealength[1])
            and isRate3(arealength[2]/arealength[3])
            and isRate1(arealength[3]/arealength[4]))


def isQrPointRateY(img):  # 同isQrPointRateX(img)
    mid = int(len(img)/2)
    lastColor = 255 if img[mid][0] > 0 else 0
    changepoint = []

    for i in range(len(img[0])):
        color = 255 if img[mid][i] > 0 else 0
        if color != lastColor:
            lastColor = color
            changepoint.append(i)
    if len(changepoint) < 4 or len(changepoint) > 6:
        return False
    elif len(changepoint) == 4:
        changepoint = [0]+changepoint+[len(img)]
    elif len(changepoint) == 5:
        lside, rside = changepoint[0], len(img)-changepoint[4]
        changepoint = [0] + changepoint\
            if lside > rside else changepoint+[len(img)]
    arealength = []
    for i in range(5):
        arealength.append(changepoint[i+1]-changepoint[i])
    # print(changepoint)
    # print(arealength)
    # print(arealength[1]/arealength[0], arealength[2]/arealength[1],
    #      arealength[2]/arealength[3], arealength[3]/arealength[4])
    return (isRate1(arealength[1]/arealength[0])
            and isRate3(arealength[2]/arealength[1])
            and isRate3(arealength[2]/arealength[3])
            and isRate1(arealength[3]/arealength[4]))


def isQrPointRate(img):  # 是否1:1:3:1:1
    return (isQrPointRateX(img) and isQrPointRateY(img))


def isQrPointPos(rotatedRect, img):
    if rotatedRect[1][0] < 100 or rotatedRect[1][1] < 100:  # 小于200的直接忽视
        return False
    # print(rotatedRect)
    img_crop = crop_rect(img, rotatedRect)
    # show_img(img_crop)
    # print(isQrPointRate(img_crop))
    return isQrPointRate(img_crop)


def three_point_angle(A, B, C):  # 求角BAC
    AB = np.array([B[0]-A[0], B[1]-A[1]])
    AC = np.array([C[0]-A[0], C[1]-A[1]])
    LB, LC = np.sqrt(AB.dot(AB)), np.sqrt(AC.dot(AC))
    # print(AB.dot(AC))
    return math.degrees(np.arccos(AB.dot(AC)/(LB*LC)))


def Analyze_Color(color):
    if color[0] < 100 and color[1] < 100 and color[2] < 100:  # 黑色
        return 1
    elif color[0] > 205 and color[1] > 205 and color[2] > 205:  # 白色
        return 0
    else:
        color_list = color.tolist()
        return (list.index(color_list, max(color_list))+2)


def isPosPointArea(i, j, FrameSize):
    if 4 <= i < 20 and 4 <= j < 20:
        return False
    elif 4 <= i < 20 and FrameSize-20 <= j < FrameSize-4:
        return False
    elif FrameSize-20 <= i < FrameSize-4 and 4 <= j < 20:
        return False
    return True


def Decode(img, AffineCellSize, FrameSize):
    result = np.zeros((FrameSize, FrameSize), dtype=np.uint8)
    for i in range(4, FrameSize-4):
        for j in range(4, FrameSize-4):
            if isPosPointArea(i, j, FrameSize):
                # print(i,j,result[i][j])
                result[i][j] = Analyze_Color(img[int((i+0.5)*AffineCellSize)]
                                             [int((j+0.5)*AffineCellSize)])
    return result


def summon_pic(CodeMatrix, CellSize, FrameSize):
    img = np.zeros((FrameSize*CellSize,
                    FrameSize*CellSize, 3), dtype=np.uint8)
    color = [(255, 255, 255), (0, 0, 0),  # 白 黑
             (255, 0, 0), (0, 255, 0), (0, 0, 255)]  # 蓝 绿 红
    for i in range(FrameSize):
        for j in range(FrameSize):
            cv2.rectangle(img, (i*CellSize, j*CellSize),
                          ((i+1)*CellSize, (j+1)*CellSize),
                          color[CodeMatrix[j][i]], thickness=-1)
    cv2.imwrite('result.png', img)


def ResultMatrixToList(ResultMatrix, canWrite, FrameSize):
    result = []
    count = 0
    tempresult = 0
    for i in range(FrameSize):
        for j in range(FrameSize):
            if canWrite[i][j] == 1:
                tempresult <<= 2
                if ResultMatrix[i][j] != 0:
                    tempresult += (ResultMatrix[i][j]-1)
                else:
                    tempresult += 2  # 白色当绿色算
                count += 1
                if count == 4:
                    count = 0
                    result.append(tempresult)
                    tempresult = 0
    return result
    pass


def FrameToMessage(index, canWrite):
    global isStartReading
    img = cv2.imread('decode_frames_input/'+str(index)+'.jpg')
    #img = cv2.GaussianBlur(img, (11,11), 1)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)  # 把输入图像灰度化
    #gray=cv2.GaussianBlur(gray, (7,7),7)
    ret, thresh = cv2.threshold(gray, 110, 255, cv2.THRESH_BINARY)  # 二值化
    thresh_copy = thresh.copy()
    #print("阈值：", ret)
    cv2.imwrite('b.png', thresh)
    contours, hierarchy = cv2.findContours(
        thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)  # 轮廓查找
    #print("边缘数量：", len(contours))
    parentIdx, ic = -1, 0
    minRect = []
    for i in range(len(contours)):  # 识别定位点
        if hierarchy[0][i][2] != -1 and ic == 0:
            parentIdx, ic = i, ic+1
        elif hierarchy[0][i][2] != -1:
            ic += 1
        elif hierarchy[0][i][2] == -1:
            ic, parentIdx = 0, -1
            parentIdx = -1
        Rect = cv2.minAreaRect(contours[parentIdx])
        if isQrPointPos(Rect, thresh_copy):
            # PointPos.append(contours[parentIdx])
            minRect.append(Rect)
        parentIdx, ic = -1, 0
    #print("矩形：", minRect)
    # print(angle(minRect[0][0], minRect[1][0], minRect[2][0]))
    # print(PointPos)
    # 0           1
    #
    #
    #
    # 2
    decoded_block = ''
    try:
        angles = [three_point_angle(minRect[0][0], minRect[1][0], minRect[2][0]),
                  three_point_angle(
                      minRect[1][0], minRect[2][0], minRect[0][0]),
                  three_point_angle(minRect[2][0], minRect[0][0], minRect[1][0])]
        # print(angles)
        PosPoint0 = None
        PosPoint1and2 = []
        for i in range(3):
            if 80 < angles[i] < 100:
                PosPoint0 = [minRect[i][0][0], minRect[i][0][1]]
            else:
                PosPoint1and2.append([minRect[i][0][0], minRect[i][0][1]])
        PosPoint1, PosPoint2 = None, None
        for point in PosPoint1and2:
            deltaX, deltaY = point[0]-PosPoint0[0], point[1]-PosPoint0[1]
            if deltaX > deltaY:
                PosPoint1 = point
            else:
                PosPoint2 = point
        # print(PosPoint0, PosPoint1, PosPoint2)
        PosPoint = np.array(
            [PosPoint0, PosPoint1, PosPoint2], dtype=np.float32)
        # CodeSize = int(math.sqrt((PosPoint1[0]-PosPoint0[0]) ** 2 +
        #                         (PosPoint1[1]-PosPoint0[1]) ** 2)/CellSize)+14
        # print(CodeSize)

        AffineCellSize = 12  # 仿射变换后的格子大小（单位：像素）
        AffinePosPoint = np.array([[AffineCellSize*11, AffineCellSize*11],
                                   [AffineCellSize*(FrameSize-11),
                                    AffineCellSize*11],
                                   [AffineCellSize*11, AffineCellSize*(FrameSize-11)]], dtype=np.float32)  # 仿射变换后的坐标
        # print(AffinePosPoint)
        AffineM = cv2.getAffineTransform(PosPoint, AffinePosPoint)
        AffineResult = cv2.warpAffine(img, AffineM, (0, 0))[
            :AffineCellSize*FrameSize, :AffineCellSize*FrameSize]

        show_Analyze_Result(AffineResult.copy(), AffineCellSize, FrameSize)

        DecodeResult = Decode(
            AffineResult.copy(), AffineCellSize, FrameSize)
        reed_solomon = ReedSolomon(error_size)
        encoded_block = ResultMatrixToList(DecodeResult, canWrite, FrameSize)
        decoded_block = reed_solomon.decode(encoded_block, error_size)
        print(index)
        isStartReading = True
        with open('v1.bin', 'ab+')as fp:
            for i in range(BytePerFrame):
                fp.write(struct.pack('B', 0xFF))
        with open('1.bin','ab+')as fp:
            for result in decoded_block:
                fp.write(struct.pack('B',result))
    except:
        if isStartReading:
            with open('v1.bin', 'ab+')as fp:
                for i in range(BytePerFrame):
                    fp.write(struct.pack('B', 0x00))
            with open('1.bin','ab+')as fp:
                for i in range(BytePerFrame):
                    fp.write(struct.pack('B', 0x00))
    return decoded_block


if __name__ == "__main__":
    shutil.rmtree("decode_frames_input", True)
    os.mkdir("decode_frames_input")
    Video_Frame.video_to_frame()
    DecodeResult = []
    for i in range(len(os.listdir("decode_frames_input\\"))):
        DecodeResult += FrameToMessage(i, canWrite=canWrite)
    #print(DecodeResult)
