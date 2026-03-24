import cv2
import numpy as np

def is_blurry(image, threshold=150.0):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    lap = cv2.Laplacian(gray, cv2.CV_64F)
    score = lap.var()
    return score < threshold, score


img = cv2.imread(r"D:\yyb\project\python_test\images\360-03.jpg")
blurry, score = is_blurry(img)

print("清晰度得分:", score)
print("是否模糊:", blurry)
