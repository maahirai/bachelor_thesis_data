from XNTM import  *
from XNTM import tree
from importlib import reload 
import sys 
import csv

gomi,MaxDepth,datanum,filename = "","","",""
if len(sys.argv ) == 4:
    gomi,MaxDepth,datanum,filename = sys.argv 
else : 
    gomi,MaxDepth = sys.argv 

import datetime
if not filename : 
    filename = MaxDepth+"_"+str(datetime.datetime.now())
if not datanum : 
    datanum = "150"

import pathlib 
path = Path('result/',filename+'.csv')
with open(path,'w',newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["木の高さ,変形なし,変形あり"])
    for i in range(int(datanum)):
        height,TREE = genInputTree(int(MaxDepth),0.7,4)
        Tree = tree.InputToTree(TREE)
        #tree.viewTree(Tree)
        PPVconsideredTree = tree.TransformTree(Tree)
        #tree.viewTree(PPVconsideredTree)
        WithoutTransform = xntm(Tree,[30,30]) 
        Transformed = xntm(PPVconsideredTree,[30,30])
        result = [height,WithoutTransform,Transformed]
        writer.writerow(result)

        ### ノードの色などグローバル変数の初期化
        reload(tree)
