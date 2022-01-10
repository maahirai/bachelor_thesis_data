from XNTM import  *
from XNTM import xntm
from importlib import reload 

R1,R2,R3,R4,R5,R6 = "R1","R2","R3","R4","R5","R6"

### passed
easy4 = [(1,1,1,1),R1,R2,R3,R4]
easy6 = [(1,1,1,1,1,1),R1,R2,R3,R4,R5,R6]

### notpassed
root = [(1,1,1,1,1,1),[(3,2,1),R1,R2,R3],[(2,2),R2,R4],R1,R2,R3,R4]
aroot =[(3,2,1),[(1,5),[(1,2,1),R1,R2,R3],[(4,2),R1,R3]],[(2,3,1),[(1,2,1),R1,R2,R3],[(2,2),R1,R3],R3],[(3,1),[(1,2,1),R2,R3,R4],R4]]
broot =[(3,2,1),[(1,5),[(1,2,1),R1,R2,[(4,2),R1,R2]],[(2,4),R1,R3]],[(2,3,1),[(1,2,1),R1,R2,R3],[(2,2),R1,R3],R3],[(3,1),[(1,2,1),R2,R3,R4],R4]]

#tree.viewTree(Tree)
Tree = tree.InputToTree(broot)
PPVconsideredTree = tree.TransformTree(Tree)
tree.viewTree(PPVconsideredTree)

a = xntm.xntm(Tree,[10,10]) 

### グローバル変数の初期化
reload(xntm)
b = xntm.xntm(PPVconsideredTree,[10,10])

print("変形なし/変形あり = {}/{} = {}".format(a,b,a/b))
