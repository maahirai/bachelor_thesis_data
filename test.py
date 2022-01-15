from XNTM import  *
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

gomi,MaxDepth,datanum,filename = "","","",""
if len(sys.argv ) == 4:
    gomi,MaxDepth,datanum,filename = sys.argv 
else : 
    gomi,MaxDepth = sys.argv 

import datetime
if not filename : 
    filename = MaxDepth+"_"+str(datetime.datetime.now())
if not datanum : 
    ### 生成する入力希釈木数
    datanum = "1"

import pathlib 
path = Path('result/',filename+'.csv')
with open(path,'w',newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["木の高さ","変形なし","変形あり"])
    for i in range(int(datanum)):
        height,TREE = genInputTree(int(MaxDepth),0.8,4)
        while(height!=int(MaxDepth)): 
            height,TREE = genInputTree(int(MaxDepth),0.8,4)
        Tree = tree.InputToTree(TREE)

        create_directory("image")
        tree.saveTree(Tree,"image/Tree"+str(i+1)+".png")
        TransformedTree = tree.TransformTree(Tree)
        tree.saveTree(TransformedTree,"image/TransformedTree"+str(i+1)+".png")
        ColorList = tree.ColorList
        WithoutTransform = xntm(Tree,[10,10],ColorList=ColorList,ImageName=str(i+1),ImageOut=True) 
        Transformed = xntm(TransformedTree,[10,10],ColorList=ColorList,ImageName=str(i+1)+"_transformed",ImageOut=True)
        result = [height,WithoutTransform,Transformed]
        writer.writerow(result)

        ### ノードの色などグローバル変数の初期化
        reload(tree)
