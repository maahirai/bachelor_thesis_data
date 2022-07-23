# -*- coding: utf-8 -*-
import json 
import random
import sys
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
        #self.name = json["name"]
        #self.directed = json["directed"]
        self.nodecnt = 0
        self.root = None

        #js = json[0]
        js = json_data
        for obj in js["objects"]:
            n = node(obj)
            self.nodecnt += 1
            self.allnode[str(n.v)] = n 
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
            if str(tailnv) not in self.allnode[str(headnv)].child: 
                self.allnode[str(headnv)].child[str(tailnv)] = amount 
            else : 
                self.allnode[str(headnv)].child[str(tailnv)] += amount 
            if str(headnv) not in self.allnode[str(tailnv)].parent: 
                self.allnode[str(tailnv)].parent[str(headnv)] = amount 
            else : 
                self.allnode[str(tailnv)].parent[str(headnv)] += amount 
        self.DefineRoot()

    def DefineRoot(self): 
        for node in self.allnode.values(): 
            # A Node that has no out edge and same concentration node is the root node. 
            if not node.parent and len(self.VtoID[str(node.v)]) == 1: 
                self.root = node
    def dump(self): 
        print("root:{},v:{}".format(self.root.id,self.root.v))
        for i in range(0,self.nodecnt): 
            self.allnode[str(self.IDtoV[str(i)])].dump()
        print(self.VtoID)

class node:
    def __init__(self,json):
        self.id = json["_gvid"]
        self.parent = {}
        self.child = {}
        self.ismixing = True
        tv = self.interpret(json["name"])
        self.v = []
        div = gcd(tv)
        for i in range(len(tv)): 
            self.v.append(tv[i]/div)
        if div == max(tv) and sum(self.v) == 1.0: 
            self.ismixing = False    

    def interpret(self,tuplestring): 
        t = eval(tuplestring)
        return list(t)

    def dump(self):
        print("id:{},v:{}".format(self.id,self.v))
        print("ismixing:{}".format(self.ismixing))
        print("parent:{}".format(self.parent))
        print("child:{}\n".format(self.child))

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
            prov_v = node.parent[str(parentnode.v)]
            if node.ismixing : 
                l.append(prov_v)
        ### 根から辿ったら(6,1,1,)は子を持たない， 
        for ckey in node.child.keys(): 
            ### if the child-node is mixing-node,
            if tree.allnode[ckey].ismixing: 
                cl = dfs(tree,tree.allnode[ckey],node,format)
                l.append(cl)
            else : 
                for cnt in range(tree.allnode[str(ckey)].parent[str(node.v)]):
                    l.append(rename(tree.allnode[str(ckey)].v))
    else: 
        prov_v = []
        for cv in node.child.values():
            prov_v.append(cv)
        l.append(tuple(prov_v))
        for ckey in node.child.keys(): 
            # if the child node is mixing-node,
            if tree.allnode[ckey].ismixing: 
                cl = dfs(tree,tree.allnode[ckey],node,format)
                l.append(cl)
            else: 
                l.append(rename(tree.allnode[str(ckey)].v))
    return l
         
                
def rename(v):
    for i in range(4): 
        if v[i] == 1.0: 
            return "R"+str(i+1)
    else : 
        print("以上な入力:{} for rename()".format(v),file=sys.stderr)

def JsonToList(json,format):
    mid = tree(json)
    l = convert(mid,format)
    return l 

def main(): 
    input1 = open('Graph444.json','r')
    f1 = json.load(input1)

    input2 = open('Graph446.json','r')
    f2 = json.load(input2)
    
    lxntm = []
    c = []
    for i in range(1,len(f1)+1): 
        list = JsonToList(f1[str(i)],format=OutputFormat.ntm)
        #Tree = NTM.listToTree(list)
        #output = NTM.ntm(Tree,[0,0],[1])
        #dir  = "./"+str(i)+"ntm"
        #NTM.visualize_placement(output, axis=[[-3,2], [-3,2]], save_dir=dir)
        

        #reload(tree)
        xntmlist = JsonToList(f2[str(i)],format=OutputFormat.xntm)
        #Tree = tree.InputToTree(xntmlist)
        #TransformedTree = tree.TransformTree(Tree)
        #c.append(tree.ColorList)
        #print(c)
        #print(xntmlist)
        #output = XNTM.xntm(Tree,[10,10],ColorList=tree.ColorList,ImageOut=True)
        #lxntm.append(output[0])
    #file = open('Xresult.csv','w', encoding='utf-8')
    #csv.writer(file).writerow(lxntm)
    
main()
