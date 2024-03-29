# -*- coding: utf-8 -*-
from XNTM import *
from XNTM import tree
from XNTM import xntm
from importlib import reload 
from pathlib import Path
import sys 
import csv
import os 
def create_directory(dir_name):
    if not os.path.exists(dir_name):
        print ('Creating directory: ', dir_name)
        os.makedirs(dir_name)

R1,R2,R3,R4,R5 = "R1","R2","R3","R4","R5"
import pathlib 

# デフォルトの木の高さ 3,デフォルトのPMDサイズ 20x20
height, size = 3,20
height,num22,num23,TREE = genInputTree(int(height),0.8,4,fair=True)

#*************************tmp.pyの動かし方*********************************#
# python3 tmp.py #1 
# 入力パターン1: #1_混合木を表すリストの文字列
# 入力パターン2: #1_混合木の高さ

# python3 tmp.py #1 #2 
# 入力パターン1: #1_混合木を表すリスト文字列，#2_PMDのサイズ
# 入力パターン2: #1_混合木の高さ，#2_PMDのサイズ

# python3 tmp.py #1 #2 #3 
# 入力パターン1: #1_混合木を表すリスト，#2_ノードカラーの配列，#3_PMDのサイズ
#******************************************************************************#


# tmp.py　が一つ目の引数
# python3 tmp.py #1 
# 入力パターン1: #1_混合木を表すリストの文字列
# 入力パターン2: #1_混合木の高さ
if len(sys.argv) == 2: 
    input = eval(sys.argv[1])
    # 入力で混合木（リストのインスタンス）が与えられている場合は，そのデータで試薬合成を行う
    if isinstance(input,list):
        TREE = input 
    else: 
        while(height!=input): 
            height,num22,num23,TREE = genInputTree(input,0.8,4,fair=True)
# python3 tmp.py #1 #2 
# 入力パターン1: #1_混合木を表すリスト文字列，#2_PMDのサイズ
# 入力パターン2: #1_混合木の高さ，#2_PMDのサイズ
if len(sys.argv) == 3: 
    input = eval(sys.argv[1])
    if isinstance(input,list):
        TREE = input 
    else: 
        while(height!=input): 
            height,num22,num23,TREE = genInputTree(input,0.8,4,fair=True)
    size = eval(sys.argv[2])
color = []
# python3 tmp.py #1 #2 #3 
# 入力パターン1: #1_混合木を表すリスト，#2_ノードカラーの配列，#3_PMDのサイズ
if len(sys.argv) == 4: 
    num22 = -1
    num23 = -1
    input = eval(sys.argv[1])
    TREE = input 
    color = eval(sys.argv[2])
    size = eval(sys.argv[3])

print(TREE)

Tree = tree.InputToTree(TREE)
if color : 
    tree.ColorList = color
create_directory("image")
tree.saveTree(Tree,"image/Tree"+"slide.png")
TransformedTree = tree.TransformTree(Tree)
#TransformedTree = tree.OctTransformTree(Tree)
tree.saveTree(TransformedTree,"image/TransformedTree"+"slide.png")
ColorList = tree.ColorList 
print(ColorList)
if color : 
    ColorList = color 
print(ColorList)
#ColorList = ['#4ccdd1', '#ec8f8a', '#41ee85', '#957470', '#89a772', '#f3bad0', '#d5b38b', '#e3c283', '#5a58e3', '#e59545']

#WithoutTransform,cmpOverlappNum,cmpFootPrint,cmpFreq = xntm(Tree,[size,size],ColorList=ColorList,ImageName="slide",ImageOut=True,ProcessOut=False) 
#Transformed,OverlappNum,FootPrint,Freq = xntm(TransformedTree,[size,size],ColorList=ColorList,ImageName="slide"+"_transformed",ImageOut=True,ProcessOut=False)

WithoutTransform,cmpOverlappNum,cmpFootPrint,cmpFreq = xntm(Tree,[size,size],ColorList=ColorList,ImageName="slide",ImageOut=True,ProcessOut=True) 
Transformed,OverlappNum,FootPrint,Freq = xntm(TransformedTree,[size,size],ColorList=ColorList,ImageName="slide"+"_transformed",ImageOut=True,ProcessOut=True)
#WithoutTransform = xntm(Tree,[20,20],ColorList=ColorList,ImageName="slide",ImageOut=True,ProcessOut=True) 
#Transformed = xntm(TransformedTree,[20,20],ColorList=ColorList,ImageName="slide"+"_transformed",ImageOut=True,ProcessOut=True)
result = [height,cmpOverlappNum,OverlappNum,WithoutTransform,Transformed]
print(result)
print("変形なしFlushing:{},変形ありFlushing:{}".format(WithoutTransform,Transformed))
print("変形なしFootPrint:{},変形ありFootPrint:{}".format(cmpFootPrint,FootPrint))
print("変形なしFreq:{:.3f},変形ありFreq:{:.3f}".format(cmpFreq,Freq))

print(num22,num23)
reload(tree)
