from Polynomial import Polynomial
import copy
import random
import codecs

class ReedSolomon:

    def __init__(self, error_size):
        self.polyObject = Polynomial()
        self.generator_polynomial = Polynomial.generator(error_size=error_size)
        self.GF = self.polyObject.GF

    def encode(self, message: list, error_size: int) -> list:
        """
        用RS校验码 将信息编码
        :message：传入的原始信息:
        :param error_size: 整形错误位数
        :return: 以校验位作为字节的信息
        """

        buffer = message+[0]*error_size

        # 对于每个字符，将字符的字节与生成多项式中的适当项相乘
        # 在缓冲区末尾添加错误位
        for position in range(len(message)):
            char = buffer[position]

            # 不能计算log0
            if char:
                for poly_position in range(len(self.generator_polynomial)):
                    buffer[position + poly_position] ^= self.GF.gfMul(
                        self.generator_polynomial[poly_position], char)

        buffer = message+buffer[len(message):]

        return buffer

    def forneySyndromes(self, syndrome_polynomial: Polynomial, erasures: list, message: list) -> Polynomial:
        """
        与擦除无关的信息中的错误的伴随式
        :param syndrome_polynomial: 伴随多项式
        :param erasures:擦除位置列表
        :param message: 原始信息
        :return: 返回一个表示非零的forney伴随式的多项式-全部为0意味着没有错误
        """

        # 位置系数（coefficient positions）
        erasures = [len(message) - 1 - p for p in erasures]
        forney_syndromes = copy.deepcopy(syndrome_polynomial)

        for i in range(len(erasures)):
            x = self.GF.gfPow(2, erasures[i])

            for j in range(len(forney_syndromes) - 1):
                y = self.GF.gfMul(
                    forney_syndromes[j], x) ^ forney_syndromes[j + 1]
                forney_syndromes[j] = y
            forney_syndromes.pop()

        return forney_syndromes

    def findErrors(self, forney_syndromes: Polynomial, length_message: int) -> list:
        """
        BM算法和Chien钱搜索找到0的错误定位多项式
        :param forney_syndromes: 表示forney伴随式的多项式
        :param length_message: 信息长度和校验位长度之和
        :return: 错误定位多项式
        """

        error_loc_polynomial = Polynomial([1])
        last_known = Polynomial([1])

        # 生成错误定位多项式
        # BM算法
        for i in range(0, len(forney_syndromes)):

            # d = S[k] + C[1]*S[k-1] + C[2]*S[k-2] + ... + C[l]*S[k-L]
            # 偏差delta
            delta = forney_syndromes[i]
            for j in range(1, len(error_loc_polynomial)):
                delta ^= self.GF.gfMul(
                    error_loc_polynomial[-(j+1)], forney_syndromes[i - j])

            # 计算多项式次幂
            last_known.append(0)

            # 如果偏差delta不为0 改正
            if delta != 0:
                if len(last_known) > len(error_loc_polynomial):
                    new_polynomial = last_known.scale(delta)
                    last_known = error_loc_polynomial.scale(
                        self.GF.gfInv(delta))
                    error_loc_polynomial = new_polynomial

                error_loc_polynomial += last_known.scale(delta)

        error_loc_polynomial = error_loc_polynomial[::-1]

        # 如果错误太多 停止
        error_count = len(error_loc_polynomial) - 1
        if error_count * 2 > len(forney_syndromes):
            raise ReedSolomonError("Too many errors to correct1")

        # 用钱（Chien）搜索找到多项式的零点
        error_list = []
        for i in range(self.GF.lowSize):
            error_z = error_loc_polynomial.eval(self.GF.gfPow(2, i))
            if error_z == 0:
                error_list.append(length_message - i - 1)

        # 完整性检查
        if len(error_list) != error_count:
            raise ReedSolomonError("Too many errors to correct2")
        else:
            return error_list

    def correct(self, message, syndrome_polynomial: Polynomial, errors: list) -> Polynomial:
        """
        使用计算过的擦除和错误，恢复原始信息
        :param message: 传输的信息+校验位
        :param syndrome_polynomial: 伴随多项式
        :param errors: 一个擦除+错误的列表
        :return:解码并改正的信息
        """

        # 为擦除和错误计算错误定位多项式
        coefficient_pos = [len(message) - 1 - p for p in errors]
        error_locator = Polynomial.errorLocatorPolynomial(coefficient_pos)

        # 计算误差评估多项式
        error_eval = Polynomial.errorEvaluatorPolynomial(
            syndrome_polynomial[::-1], error_locator, len(error_locator))

        # 计算误差位置多项式
        error_positions = []
        for i in range(len(coefficient_pos)):
            x = self.GF.lowSize - coefficient_pos[i]
            error_positions.append(self.GF.gfPow(2, -x))

        # 这是福尼算法
        error_magnitudes = Polynomial([0] * len(message))
        for i, error in enumerate(error_positions):

            error_inv = self.GF.gfInv(error)

            # 错误定位多项式的形式导数（Formal derivative of the error locator polynomial）
            error_loc_derivative_tmp = Polynomial([])
            for j in range(len(error_positions)):
                if j != i:
                    error_loc_derivative_tmp.append(
                        1 ^ self.GF.gfMul(error_inv, error_positions[j]))

            # 错误定位导数 Error locator derivative
            error_loc_derivative = 1
            for coef in error_loc_derivative_tmp:
                error_loc_derivative = self.GF.gfMul(
                    error_loc_derivative, coef)

            # 根据误差的倒数求出误差评价多项式
            y = error_eval.eval(error_inv)

            # 计算误差的大小
            magnitude = self.GF.gfDiv(y, error_loc_derivative)
            error_magnitudes[errors[i]] = magnitude

        # 使用错误大小纠正消息
        message_polynomial = Polynomial(message)
        message_polynomial += error_magnitudes
        return message_polynomial

    def decode(self, message: list, error_size: int) -> str:
        """
        :param message: 具有奇偶校验位的消息，它可能包含错误，也可能不包含错误
        :param error_size: 错误符号的数目
        :return:一个解码的消息，如果可能的话
        """
        buffer = copy.deepcopy(message)
        # 首先检查是否有擦除
        erasures = []
        for position in range(len(buffer)):
            if buffer[position] < 0:
                buffer[position] = 0
                erasures.append(position)

        # 错误太多 退出
        if len(erasures) > error_size:
            raise ReedSolomonError("Too many erasures3")
        # 计算伴随多项式
        syndrome_polynomial = Polynomial.syndromePolynomial(buffer, error_size)
        if max(syndrome_polynomial) == 0:
            return bytearray(buffer[:-error_size])#.decode('ascii',"ignore")
        forney_syndromes = self.forneySyndromes(
            syndrome_polynomial, erasures, buffer)
        
        error_list = self.findErrors(forney_syndromes, len(message))
        if error_list is None:
           
            raise ReedSolomonError("Could not find errors")
        

        decoded_symbols = self.correct(
            buffer, syndrome_polynomial, (erasures + error_list))
        return bytearray(decoded_symbols[:-error_size])#.decode('ascii',"ignore")


class ReedSolomonError(Exception):
    def __init__(self, message):
        self.message = message


if __name__ == "__main__":
    # 使用相同的ReedSolomon()对象进行编码和解码!误差大小和生成多项式必须匹配
    reed_solomon = ReedSolomon(error_size=32)
    transmission = "qwertyuioplkjhgfdsamnzxbv./p;.lldsdwasdfgghjkjlikujyhtgrewqfewghduifvejofwejoepw[VEPBNVAEPUBNRAPVMADBVNPo pam OIHFUEFNWEFHEWPOFJIAEOPWGNWPORBNUPORGPAWMEFMAJIWOGNMARIGHNRIUAEGAP'EKFK[Oqffk[FKOPfe'fwkap[ghareolgnroesnaponvpwuoefh329t745pgijwovkmdhfusaihfasdjsdvnadjvnduivnueifhegfbvhdjnvsjncjxkcvnjskvbeuidvbnjsdnvxmcmkocsdnvfuefhweufnjdx vccxmvsebffisfnjxvcjsdv sjfbneujfnsdvndsv sdovehfuebgvsidjvgnsdjkvnaofhweiofndsjvksnfbkjsndvnoesvnk"
    print("transmission len:", len(transmission))
    encoded_block = reed_solomon.encode(message=transmission, error_size=32)
    print("Encoded message:", encoded_block)
    print("Encoded len:", len(encoded_block))

    numbers_pos = list(range(0, len(encoded_block) - 16))
    positions = random.sample(numbers_pos, 8)
    for pos in positions:
        mod = random.randrange(1, 255)
        encoded_block[pos] = mod

    print("Modified message:", encoded_block)
    decoded_block = reed_solomon.decode(encoded_block, error_size=32)
    print("Decoded message:", decoded_block)
