from XNTM import  *

R1,R2,R3,R4,R5,R6 = "R1","R2","R3","R4","R5","R6"

root = [(1,1,1,1,1,1),[(3,2,1),R1,R2,R3],[(2,2),R2,R4],R1,R2,R3,R4]
aroot =[(3,2,1),[(1,5),[(1,2,1),R1,R2,R3],[(2,2),R1,R3]],[(2,3,1),[(1,2,1),R1,R2,R3],[(2,2),R1,R3],R3],[(3,1),[(1,2,1),R2,R3,R4],R4]]
broot =[(3,2,1),[(1,5),[(1,2,1),R1,R2,[(1,2,1),R1,R2,R3]],[(2,2),R1,R3]],[(2,3,1),[(1,2,1),R1,R2,R3],[(2,2),R1,R3],R3],[(3,1),[(1,2,1),R2,R3,R4],R4]]
easy4 = [(1,1,1,1),R1,R2,R3,R4]
easy6 = [(1,1,1,1,1,1),R1,R2,R3,R4,R5,R6]

Tree = tree.InputToTree(easy6)
tree.viewTree(Tree)
PPVconsideredTree = tree.TransformTree(Tree)
tree.viewTree(PPVconsideredTree)

CPxntm.xntm(Tree,[10,10])
