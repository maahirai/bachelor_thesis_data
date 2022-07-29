# -*- coding: utf-8 -*-
import json 
import random
import sys
import copy
from enum import Enum 
from importlib import reload 
from pathlib import Path 
#import NTM 
#from XNTM import *
#from XNTM import tree
#from XNTM import xntm
import csv

class tree:
    def __init__(self,json_data):
        self.allnode = {}
        self.VtoID = {}
        self.IDtoV = {}
        self.VtoOriginal = {}
        #self.name = json["name"]
        #self.directed = json["directed"]
        self.nodecnt = 0
        self.root = None

        #js = json[0]
        tmp = {}
        js = json_data
        for obj in js["objects"]:
            n = node(obj)
            self.nodecnt += 1
            self.allnode[str(n.id)] = n 
            if str(n.v) not in self.VtoID: 
                self.VtoID[str(n.v)] = []
            self.VtoID[str(n.v)].append(n.id)
            self.IDtoV[str(n.id)]=n.v 
             

        for edge in js["edges"]: 
            tail = edge["tail"]
            head = edge["head"]
            amount = int(edge["label"])
            tailnv = self.IDtoV[str(tail)]
            headnv = self.IDtoV[str(head)]
            ### ✨✨✨tail側に同じvを持つ複数のノードが存在する可能性あり
            ### ✨✨✨→child側は，tailnvをキー値に取る
            if str(tail) not in self.allnode[str(head)].child: 
                self.allnode[str(head)].child[str(tail)] = amount 
            else : 
                self.allnode[str(head)].child[str(tail)] += amount 
            if str(head) not in self.allnode[str(tail)].parent: 
                self.allnode[str(tail)].parent[str(head)] = amount 
            else : 
                self.allnode[str(tail)].parent[str(head)] += amount 
        ### 子供を持つ方がオリジナル(オリジナルノードが複数あるケース確認済み,5個提供の時.4mixerの方では足りない)
        ### 6ミキサー単体では，作れない比率[3, 0, 0, 0, 1]は一旦4mixerをかます必要がある.
        ### [3, 0, 0, 0, 1] {'[0, 0, 0, 0, 1]': 1, '[1, 0, 0, 0, 0]': 3, '[3, 0, 0, 0, 1]': 2} {'[0, 0, 0, 0, 1]': 1, '[1, 0, 0, 0, 0]': 3}
        for n in self.allnode.values(): 
            if n.ismixing:
                ### ミキサーノードにはエイリアスの場合がある
                if n.child:
                    if str(n.v) not in self.VtoOriginal:
                        self.VtoOriginal[str(n.v)] = []
                    self.VtoOriginal[str(n.v)].append(n.id)
                    self.allnode[str(n.id)].setMixersize(n.id,tree)
            else: 
                if str(n.v) not in self.VtoOriginal:
                    self.VtoOriginal[str(n.v)] = []
                    ### 試薬液滴は，一個だけ登録しとけばいいと思う 
                    self.VtoOriginal[str(n.v)].append(n.id)

        #print(self.VtoOriginal)
        self.DefineRoot()

    def DefineRoot(self): 
        for node in self.allnode.values(): 
            # A Node that has no out edge and same concentration node is the root node. 
            if not node.parent and len(self.VtoID[str(node.v)]) == 1: 
                self.root = node 

    

    def dump(self): 
        print("root:{},v:{}".format(self.root.id,self.root.v))
        for i in range(0,self.nodecnt): 
            self.allnode[str(i)].ndump()
        print(self.VtoID)

class node:
    def __init__(self,json):
        self.id = json["_gvid"]
        self.parent = {}
        self.child = {}
        self.ismixing = True 
        ### エイリアスと試薬液滴ノードは-1
        ### 実体なら，ミキサーサイズ
        self.mixersize = -1
        tv = interpret(json["name"])
        l = []
        div = gcd(tv)
        for i in range(len(tv)): 
            l.append(int(tv[i]/div))
        self.v = str(l)
        if div == max(tv) and sum(eval(self.v)) == 1: 
            self.ismixing = False    

    def setMixersize(self,id,tree): 
        res = 0
        for provided in self.child.values(): 
            res += provided 
        self.mixersize = res
        ### MRCM側のバグ?に対応するため，ハードコーディング
        #if self.mixersize != 4 and self.mixersize != 6: 
        #    candiv4 ,candiv6= True,True 
        #    div = -1
        #    if self.mixersize%6==0: 
        #        modif6 = int(self.mixersize//6)
        #        for provided in self.child.values(): 
        #            if provided%modif6 :
        #                candiv6 = False 
        #        if candiv6: 
        #            div = modif6
        #    if self.mixersize%4==0: 
        #        modif4 = int(self.mixersize//4)
        #        for provided in self.child.values(): 
        #            if provided%modif4 :
        #                candiv4 = False 
        #        if candiv4: 
        #            div = modif4 
        #    if div != -1: 
        #        for cidx,provided in self.child.items():
        #            tree.allnode[str(idx)].child[str(cidx)] = int(provided//div)
        #            tree.allnode[str(cidx)].parent[str(idx)] = int(provided//div)
        #        self.mixersize = int(self.mixersize//div)

    def ndump(self):
        print("id:{},v:{}".format(self.id,self.v))
        print("ismixing:{}".format(self.ismixing))
        print("parent:{}".format(self.parent))
        print("child:{}\n".format(self.child))

def interpret(tuplestring): 
    t = eval(tuplestring)
    l = []
    for v in t : 
        l.append(v)
    return l

def gcd(obj): 
    res = 1
    Mv = max(obj)
    for i in range(1,Mv+1): 
        flag = True
        for j in range(len(obj)): 
            if obj[j]%i != 0: 
                flag = False 
        if flag: 
            res = i 
    return res

class OutputFormat(Enum): 
    ntm = 1
    xntm = 2

def convert(tree,format=OutputFormat.xntm): 
    ret = dfs(tree,tree.root,parentnode=None,format=format)
    return ret 

def dfs(tree,node,parentnode=None,format=OutputFormat.xntm): 
    l = []
    if format == OutputFormat.ntm:
        if node == tree.root: 
            prov_v = 0 
            for cv in node.child.values():
                prov_v += cv
            l.append(prov_v)
        else : 
            prov_v = node.parent[str(parentnode.id)]
            if node.ismixing : 
                l.append(prov_v)
        ### 根から辿ったら(12,2,2,0)はMRCMが作った木では，子を持たないノードだが(6,1,1,0)の濃度を持つノードが他にある
        for id,VtoP in node.child.items(): 
            ### if the child-node is mixing-node,
            child = tree.allnode[str(id)]
            if child.ismixing:
                ### エイリアスでない，正しい子ノードに切り替え
                childnode = switching(child.id,node.id,tree)
                cl = dfs(tree,childnode,node,format)
                l.append(cl)
            else : 
                ### 親に渡す液滴個数分に分割する．(NTMの入力形式に合わすため)
                for cnt in range(VtoP):
                    l.append(rename(child.v))
    ### format of the proposed method
    else: 
        prov_v = []
        for ProvAmount in node.child.values():
            prov_v.append(ProvAmount)
        l.append(tuple(prov_v))
        for id in node.child.keys(): 
            ### if the child-node is mixing-node,
            child = tree.allnode[str(id)]
            if child.ismixing:
                ### エイリアスでない，正しい子ノードに切り替え
                childnode = switching(child.id,node.id,tree)
                cl = dfs(tree,childnode,node,format)
                l.append(cl)
            else: 
                l.append(rename(child.v))
    return l
         
                
def rename(v):
    l = eval(v)
    for i in range(len(l)): 
        if l[i] == 1: 
            return "R"+str(i+1)
    else : 
        print("以上な入力:{} for rename()".format(v),file=sys.stderr)

### 同じ濃度の混合液滴が複数回異なるミキサーによって作られないという前提
def switching(id,parentid,tree): 
    ### idの指すノード自体が実態を持つ(実態のあるミキサーノードか，試薬液滴ノード)MRCMのバグでこれでは動かない
    ### if tree.allnode[str(id)].child or not tree.allnode[str(id)].ismixing: 
    if not tree.allnode[str(id)].ismixing: 
        return tree.allnode[str(id)]
    ### 以下，idの指すノードがエイリアスの場合
    v = tree.IDtoV[str(id)]
    OriginalsID = copy.deepcopy(tree.VtoOriginal[v])
    if len(OriginalsID) > 1: 
        #print(tree.allnode[str(id)].v)
        prov_amount = tree.allnode[str(id)].parent[str(parentid)]
        alts = []
        for origid in OriginalsID: 
            alt = copy.deepcopy(tree.allnode[str(origid)])
            e = [alt.mixersize,alt]
            alts.append(e)
        sorted_alts = sorted(alts)
        for size,alt in sorted_alts: 
            #print(size,prov_amount)
            if size > prov_amount: 
                #print(alt.id)
                return alt 
        print("バグっています.switching関連")
    else: 
        OriginalID = OriginalsID.pop()
        ret = copy.deepcopy(tree.allnode[str(OriginalID)])
        return ret


def isMixingNode(v): 
    l = eval(v)
    if sum(l) != 1: 
        return True
    else: 
        return False

def JsonToList(json,format):
    mid = tree(json)
    l = convert(mid,format)
    return l 

# 自由記述処理モード
if len(sys.argv) == 1: 
    input1 = open('Graph444.json','r')
    f1 = json.load(input1)

    input2 = open('Graph446.json','r')
    f2 = json.load(input2)

    ntmstyle = open("ntmInput.txt","wt")
    xntmstyle = open("xntmInput.txt","wt")

    for i in range(1,len(f1)+1): 
        List = JsonToList(f1[str(i)],format=OutputFormat.ntm)
        ntmstyle.write(str(List)+"\n")

        xntmlist = JsonToList(f2[str(i)],format=OutputFormat.xntm)
        xntmstyle.write(str(xntmlist)+"\n")
elif len(sys.argv) == 4: 
    input = sys.argv[1]
    output = sys.argv[2]
    format = -1
    if sys.argv[3]=="n" or sys.argv[3]=="ntm": 
       format = OutputFormat.ntm 
    else: 
       format = OutputFormat.xntm 
    t = open(input,'r')
    fi = json.load(t)
    fo = open(output,'w')
    for i in range(1,len(fi)+1):
        list = JsonToList(fi[str(i)],format)
        fo.write(str(list)+"\n")
    fo.close()
else: 
    print("invalid num of input!!")
