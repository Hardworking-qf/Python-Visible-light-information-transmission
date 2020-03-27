import struct
if __name__ == '__main__':
    l=[62, 91, 89, 14, 212, 252, 137, 133, 149, 139, 168, 7, 182, 120, 52, 166, 80, 132, 188, 70, 8, 213, 162, 81, 239, 69, 31, 172, 167, 0, 135, 234]
    '''
    一个问题，判断啥时候是失帧，而不是非二维码帧。
    失帧用失帧的vout.bin 写入方法（在后面）
    有效帧用有效帧的vout.bin写入（在后面）
    '''
    #注意改变文件路径和文件名
    
    #写入out.bin  将decode出来的list 写入二进制 测试无问题
    with open("D:\\2.bin","ab+")as f1:
        for i in range(len(l)):
            f1.write(struct.pack("B",l[i]))
    f1.close()

    #失帧写入vout 0000 0000     个数需要改
    with open("D:\\2.bin","ab+")as f2: #ab+  读写模式 追加读写 不覆盖
        f2.write(struct.pack("B",0))#依次输入1个八位为0的字节  格式B 表示无符号整型一个字节 0 二进制 00000000 已测试
    f2.close()
    #有效帧 对比 写入 vout.bin
    with open("D:\\1.bin") as f1:#打开 信息文件 注意 信息文件不借助原文件，需在encode之时，将信息重新读入另一二进制文件
        with open("D:\\2.bin")as f2:#打开 out.bin文件
            with open("D:\\3.bin","ab+")as f3:#打开 vout.bin 文件
                str1 = f1.read(1)
                str2 = f2.read(1)
                str3 = ord(str1)^ord(str2)
                f3.write(struct.pack("B",~str3+256))
    f1.close()
    f2.close()
    f3.close()
    #在encode读入信息的时候， 顺便写入新文件。
    with open("in.bin","rb")as f1:
        with open("new_in.bin","rb")as f2:
            data = f1.read(1)
            f2.write(data)
    f1.close()
    f2.close()


    