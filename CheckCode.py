import cv2
source=cv2.imread('demo.png')
result=cv2.imread('result.png')
cv2.namedWindow('XOR')
compare=cv2.bitwise_xor(source,result)
cv2.imwrite('compare.png',compare)