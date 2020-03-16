import numpy as np


class GaloisField:

    def __init__(self):

        self.size = 512
        self.lowSize = 256
        self.GF = np.zeros(shape=(self.size, 1), dtype=np.int32)
        self.__logTable = np.zeros(shape=(self.lowSize, 1), dtype=np.int32)

        self.GF[0] = 1

        val = 1

        # 动初始化GF[0]，并从1开始，因为日志[0]是未定义的，因此未被使用
        for position in range(1, self.lowSize - 1):
            val <<= 1

            if val & 0x100:
                val ^= 0x11d

            self.GF[position] = val
            self.__logTable[val] = position

        for position in range((self.lowSize - 1), self.size):
            self.GF[position] = self.GF[position - (self.lowSize - 1)]

    def gfMul(self, x: int, y: int) -> int:
        """
        Galois字段乘法优化与日志表查找
        :param x: element x
        :param y: element y
        :return: x * y in Galois Field
        """
        if x>256:x%=255
        if y>256:y%=255
        if x == 0 or y == 0:
            return 0

        else:
            value = self.__logTable[x][0]
            value += self.__logTable[y][0]

            value = self.GF[value][0]

            return value

    def gfDiv(self, x: int, y: int) -> int:
        """
       Galois字段划分优化与日志表查找
        :param x: element x
        :param y: element y
        :return: x / y in Galois Field
        """
        if y == 0:
            raise ZeroDivisionError()

        if x == 0:
            return 0
        else:
            value = self.__logTable[x][0] - self.__logTable[y][0]
            value += (self.lowSize - 1)
            value = self.GF[value][0]

            return value

    def gfPow(self, x: int, power: int = 2) -> int:
        """
        使用Galois字段运算中的日志表查找来执行x**幂的计算
        :param x: element x
        :param power: power
        :return: x**power
        """
        element = self.__logTable[x][0] * power % self.lowSize
        return self.GF[element][0]

    def gfInv(self, x):
        """
        计算倒数
        :param x: element
        :return: 1/x
        """
        return self.GF[(self.lowSize - 1) - self.__logTable[x][0]][0]

    def __getitem__(self, item):
        """
        从类外部覆盖对GF[]的访问
        :param item: index of item
        :return: self.GF[item]
        """
        return self.GF[item][0]
