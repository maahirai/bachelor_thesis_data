import json 
import random
from enum import Enum 
import sys

input1 = open('Graph444.json','r')
f1 = json.load(input1)

input2 = open('Graph446.json','r')
f2 = json.load(input2)

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

def convert(tree): 
    ntm_styled = dfs(tree,tree.root,parentnode=None,format=OutputFormat.ntm)
    xntm_styled = dfs(tree,tree.root,parentnode=None,format=OutputFormat.xntm)
    l = [ntm_styled,xntm_styled]
    return l

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

def JsonToList(json):
    mid = tree(json)
    l = convert(mid)
    return l 

def main(): 
    trees = []
    #for i in range(len(data)): 
    #    JsonToList(f[str(i)])
    data = '''{
          "name": "%3",
          "directed": true,
          "strict": false,
          "_subgraph_cnt": 0,
          "objects": [
            {
              "_gvid": 0,
              "name": "(30, 15, 11, 8)",
              "label": "(30, 15, 11, 8)"
            },
            {
              "_gvid": 1,
              "name": "(0, 12, 2, 2)",
              "label": "(0, 12, 2, 2)"
            },
            {
              "_gvid": 2,
              "name": "(10, 1, 3, 2)",
              "label": "(10, 1, 3, 2)"
            },
            {
              "_gvid": 3,
              "name": "(0, 0, 1, 1)",
              "label": "(0, 0, 1, 1)"
            },
            {
              "_gvid": 4,
              "name": "(0, 2, 0, 0)",
              "label": "(0, 2, 0, 0)"
            },
            {
              "_gvid": 5,
              "name": "(0, 0, 1, 0)",
              "label": "(0, 0, 1, 0)"
            },
            {
              "_gvid": 6,
              "name": "(0, 0, 0, 1)",
              "label": "(0, 0, 0, 1)"
            },
            {
              "_gvid": 7,
              "name": "(0, 0, 3, 1)",
              "label": "(0, 0, 3, 1)"
            },
            {
              "_gvid": 8,
              "name": "(2, 1, 0, 1)",
              "label": "(2, 1, 0, 1)"
            },
            {
              "_gvid": 9,
              "name": "(4, 0, 0, 0)",
              "label": "(4, 0, 0, 0)"
            },
            {
              "_gvid": 10,
              "name": "(0, 1, 0, 0)",
              "label": "(0, 1, 0, 0)"
            },
            {
              "_gvid": 11,
              "name": "(1, 0, 0, 0)",
              "label": "(1, 0, 0, 0)"
            },
            {
              "_gvid": 12,
              "name": "(0, 6, 1, 1)",
              "label": "no"
            },
            {
              "_gvid": 13,
              "name": "(0, 0, 2, 2)",
              "label": "no"
            }
          ],
          "edges": [
            {
              "_gvid": 0,
              "tail": 1,
              "head": 0,
              "constraint": "true",
              "label": "1"
            },
            {
              "_gvid": 1,
              "tail": 2,
              "head": 0,
              "constraint": "true",
              "label": "3"
            },
            {
              "_gvid": 2,
              "tail": 3,
              "head": 12,
              "constraint": "true",
              "label": "1"
            },
            {
              "_gvid": 3,
              "tail": 4,
              "head": 12,
              "constraint": "true",
              "label": "1"
            },
            {
              "_gvid": 4,
              "tail": 4,
              "head": 12,
              "constraint": "true",
              "label": "2"
            },
            {
              "_gvid": 6,
              "tail": 5,
              "head": 13,
              "constraint": "true",
              "label": "1"
            },
            {
              "_gvid": 7,
              "tail": 5,
              "head": 13,
              "constraint": "true",
              "label": "1"
            },
            {
              "_gvid": 10,
              "tail": 6,
              "head": 13,
              "constraint": "true",
              "label": "1"
            },
            {
              "_gvid": 11,
              "tail": 6,
              "head": 13,
              "constraint": "true",
              "label": "1"
            },
            {
              "_gvid": 12,
              "tail": 7,
              "head": 2,
              "constraint": "true",
              "label": "1"
            },
            {
              "_gvid": 13,
              "tail": 8,
              "head": 2,
              "constraint": "true",
              "label": "1"
            },
            {
              "_gvid": 14,
              "tail": 9,
              "head": 2,
              "constraint": "true",
              "label": "1"
            },
            {
              "_gvid": 15,
              "tail": 9,
              "head": 2,
              "constraint": "true",
              "label": "1"
            },
            {
              "_gvid": 8,
              "tail": 6,
              "head": 7,
              "constraint": "true",
              "label": "1"
            },
            {
              "_gvid": 5,
              "tail": 5,
              "head": 7,
              "constraint": "true",
              "label": "3"
            },
            {
              "_gvid": 9,
              "tail": 6,
              "head": 8,
              "constraint": "true",
              "label": "1"
            },
            {
              "_gvid": 16,
              "tail": 10,
              "head": 8,
              "constraint": "true",
              "label": "1"
            },
            {
              "_gvid": 17,
              "tail": 11,
              "head": 8,
              "constraint": "true",
              "label": "1"
            },
            {
              "_gvid": 18,
              "tail": 11,
              "head": 8,
              "constraint": "true",
              "label": "1"
            }
          ]
        }'''
    json_data = json.loads(data)
    t = tree(json_data)
    t.dump()
    ntm,xntm = JsonToList(json_data)
    print(ntm)
    print(xntm)

main()
