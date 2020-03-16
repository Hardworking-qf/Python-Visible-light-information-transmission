from GaloisField import GaloisField
import copy
import numpy as np


class Polynomial:
    GF = GaloisField()

    def __init__(self, init: list = None):
        if init is None:
            init = [0]

        self.polynomial = init

    def __len__(self):
        return len(self.polynomial)

    def append(self, object):
        self.polynomial.append(object)
        return self

    def __reversed__(self):
        self.polynomial.reverse()
        return self

    def __getitem__(self, key):
        """
       重载 []
        :param key: index to get
        :return: item at position self.polynomial[key] or slice
        """
        if isinstance(key, slice):
            return Polynomial(self.polynomial[key.start:key.stop:key.step])

        return self.polynomial[key]

    def __setitem__(self, key, value):
        """
        重载x[key] = value
        :param key: index
        :param value: value to set
        :return: item at position self.polynomial = value
        """
        self.polynomial[key] = value
        return self

    def __add__(self, other):
        """
       重载+运算符来执行多项式加法
        """
        sum = [0] * max(len(self), len(other))

        sum[len(sum) - len(self):len(sum)] = copy.deepcopy(self.polynomial)

        for n in range(len(other)):
            sum[n + len(sum) - len(other)] ^= other[n]

        return Polynomial(sum)

    def __iadd__(self, other):
        """
        重载+=运算符来执行多项式加法
        """
        self.polynomial = self.__add__(other).polynomial
        return self

    def pop(self, key=-1):
        """
       删除索引处的元素
        :param key: 要删除的元素的索引
        :return: 删除的元素
        """
        item = self.polynomial.pop(key)
        return item

    def scale(self, x):
        """
       将多项式的所有元素乘以一个值x
        :param x: 标量值
        :return: a new scaled Polynomial
        """

        new_polynomial = [self.GF.gfMul(self.polynomial[i], x) for i in range(len(self.polynomial))]
        return Polynomial(new_polynomial)

    def iscale(self, x):
        """
       自身乘以一个值x
        :param x: 标量值
        :return: itself
        """
        self.polynomial = self.scale(x).polynomial
        return self

    def eval(self, x):
        """
        求自变量x的值
        :param x:要评估的值
        :return: 评估结果
        """

        val = self.polynomial[0]
        for position in range(1, len(self.polynomial)):
            val = Polynomial.GF.gfMul(val, x) ^ self.polynomial[position]

        return val

    def __mul__(self, other):
        """
        重载*运算符来执行多项式乘法
        """
        num = len(self) + len(other) - 1
        mul = [0] * num

        for posY in range(len(other)):
            for posX in range(len(self)):
                mul[posY + posX] ^= Polynomial.GF.gfMul(self[posX], other[posY])

        return Polynomial(mul)

    def __imul__(self, other):
        """
        重载*=运算符来执行多项式乘法
        """
        self.polynomial = self.__mul__(other).polynomial
        return self

    def __truediv__(self, other):
        """
       重载/运算符来执行多项式除法
        :return: the quotient, the remainder
        """
        num = copy.deepcopy(self)

        for posX in range(len(self) - len(other) - 1):
            for posY in range(1, len(other)):
                num[posX + posY] ^= Polynomial.GF.gfMul(other[posY], num[posX])

        div = -(len(other) - 1)
        return num[:div], num[div:]

    @staticmethod
    def generator(error_size):
        """
        为给定的错误大小创建生成器多项式
        :param error_size: 给定的错误大小
        :return: 给定误差大小的特定伽罗瓦域的生成多项式
        """

        # 初始化发生器多项式为1
        polynomial_value = Polynomial([1])

        # 在GF中相乘“error_size”的连续值
        for position in range(error_size):
            polynomial_value *= Polynomial([1, Polynomial.GF[position]])

        return polynomial_value

    @staticmethod
    def syndromePolynomial(block, error_size):
        """
        创建伴随多项式
        :param block: 我们用来创建伴随多项式的块
        :param error_size: 奇偶校验符号的数目
        :return: 综合症的多项式
        """
        block_polynomial = Polynomial(block)
        generator_polynomial = Polynomial([0] * error_size)

        for i in range(error_size):
            val = Polynomial.GF[i]
            generator_polynomial[i] = block_polynomial.eval(val)

        return generator_polynomial

    @staticmethod
    def errorLocatorPolynomial(error_positions):
        """
        计算错误定位多项式
        :param error_positions:错误符号的数目
        :return: 错误定位多项式
        """
        error_locator = Polynomial([1])

        for i in error_positions:
            error_locator *= (Polynomial([1]) + Polynomial([Polynomial.GF.gfPow(2, i), 0]))

        return error_locator

    @staticmethod
    def errorEvaluatorPolynomial(syndrome_polynomial, error_locator, error_size):
        """
        误差评估多项式
        :param syndrome_polynomial: 伴随多项式
        :param error_locator: the error locator polynomial
        :param error_size:：错误定位多项式
        :return: 误差评估多项式
        """
        _, remainder = (syndrome_polynomial * error_locator) / Polynomial([1] + [0]*error_size)

        return remainder
