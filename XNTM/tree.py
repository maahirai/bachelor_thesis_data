import random
import sys

Registered_Hash = []

class node(object):
    def __init__(self, name, size=6, provide_vol=0, children = None ):
        self.name = name 
        self.size = size
        self.provide_vol = provide_vol
        self.children = children if children else []
        hash_v = 1
        while(hash_v in Registered_Hash):
            hash_v = random.randint(1,100001)
        Registered_Hash.append(hash_v)
        self.hash = hash_v 

def IsMixerNode(Node):
    if IsMixerName(Node.name):
        return True
    else :
        return False

def IsMixerName(name):
    if name[0]=='M':
        return True
    else :
        return False

######################################################################################
MIX_COUNTER = 0

def InputToTree(Input):
    root = _InputToTree(Input,0)
    tree = LabelingMixers(root)
    return tree

def _InputToTree(Input,provide_vol):
    global MIX_COUNTER
    RootNodeSize = sum(Input[0])
    if RootNodeSize == 6 or RootNodeSize == 4:
        root = node('M',size=sum(Input[0]),provide_vol=provide_vol)
        MIX_COUNTER += 1 
        for idx,item in enumerate(Input[1:]):
            ### mixer
            if type(item) == list:
                root.children.append(_InputToTree(item,Input[0][idx]))
            ### droplet of reagent
            elif type(item) == str:
                root.children.append(node(item,size=Input[0][idx],provide_vol=Input[0][idx]))
            else :
                pass
        return root
    else :
        print("入力された希釈木データに異常あり．希釈木に含まれるミキサーサイズは4，もしくは，6のみです．",file=sys.stderr)
    
def LabelingMixers(root):
    q = []
    q.append(root)
    idx = 0
    while not len(q)==0:
        n = q.pop(0)
        n.name = n.name + str(idx)
        idx += 1
        for item in n.children :
            if item.name[0] == "M":
                q.append(item)
    return root

######################################################################################
# transform the input tree
from copy import deepcopy
import itertools

# Sum of Number of children-mixer in the subtree
lNumChildMixer = []

def TransformTree(root):
    global lNumChildMixer,MIX_COUNTER
    lNumChildMixer = list(itertools.repeat(-1,MIX_COUNTER))
    transformed_tree = _TransformTree(root)
    return transformed_tree

def _TransformTree(root):
    Children = []
    for item in root.children:
        ppv = 0
        if IsMixerNode(item):
            # Sum of Number of children-mixer in the subtree
            ppv += NumChildMixer(item)
            # providing volume 
            ppv += item.provide_vol
            # we must place tht item firstly if (item.provide_vol == (ParentMixer.size - 1))
            if item.provide_vol == root.size - 1:
                # so large value
                INF = 10000000
                ppv += INF
        Children.append((item,ppv))
    SortedByPPV = sorted( Children, key = lambda x: x[1], reverse = True)
    res = []
    for item in SortedByPPV:
        Subtree = _TransformTree(item[0])
        res.append(Subtree)
    root.children = res
    return root

        
def NumChildMixer(root):
    global lNumChildMixer
    if not IsMixerNode(root):
        return 0
    else :
        mixeridx = int(root.name[1:])
        if not lNumChildMixer[mixeridx] == -1:
            return lNumChildMixer[mixeridx]
        else :
            v = 0
            for item in root.children:
                if IsMixerNode(item):
                    v += 1
                    v += NumChildMixer(item)
            lNumChildMixer[mixeridx] = v
            return lNumChildMixer[mixeridx]

######################################################################################

def _getNodesEdges(node):
    '''
    returns list of nodes and edges of a tree from NODE data structure
    '''
    nodelist = [(node.hash, node.name)]
    edgelist = []
    for child in node.children:
        edgelist.append(((node.hash, node.name, node.provide_vol), (child.hash, child.name, child.provide_vol)))
        temp_nodelist, temp_edgelist = _getNodesEdges(child)
        nodelist += temp_nodelist
        edgelist += temp_edgelist
    
    return nodelist, edgelist

import pydot

ColorList = []
def _createTree(root, label=None):
    '''
    convert a tree from NODE data structure to Pydot Graph for visualisation
    '''
    global MIX_COUNTER,ColorList
    if not ColorList:
        ColorList = list(itertools.repeat("#000000",MIX_COUNTER))
    P = pydot.Dot(graph_type='digraph', label=label, labelloc='top', labeljust='left')#, nodesep="1", ranksep="1")
    P.set_node_defaults(style='filled',fixedsize='true')
    P.set_graph_defaults(bgcolor="#00000000")
    P.set_edge_defaults(fontsize = '20',arrowsize = '0.5')

    nodelist, edgelist = _getNodesEdges(root)
    
    for i,node in enumerate(nodelist):
        RGB = 0
        for d in range(3):
            RGB = RGB * 256 + random.randint(64,255)

        ### 試薬液滴ノードの出力設定
        shape,color,width='plaintext',"#FFFFFF","0.3" 
        ### ミキサーノードの出力設定
        if node[1][0]=="M" :
            mixeridx = int(node[1][1:])
            if ColorList[mixeridx] == "#000000":
                ColorList[mixeridx] = "#"+hex(RGB)[2:]
            shape,color,width = 'circle',ColorList[mixeridx],"0.75"
        n = pydot.Node(node[0], shape = shape,label=node[1],fillcolor=color ,width= width)
        P.add_node(n)
    
    # Edges
    for edge in edgelist:
        e = pydot.Edge(*(edge[0][0], edge[1][0]), label=edge[1][2], dir='back')
        P.add_edge(e)
    return P


from IPython.display import Image, display
def _viewPydot(pydot):
    '''
    generates a visual plot of Pydot Graph
    '''
    plt = Image(pydot.create_png(prog='dot'))
    display(plt)
    
    
def viewTree(root):
    _viewPydot(_createTree(root))

import os
from .utility import create_directory
def saveTree(root, save):
    save = save.split('/')
    dir_name = '/'.join(save[:-1])
    if not save[-1].endswith('.png'):
        file_name = save[-1] + '.png'
    else:
        file_name = save[-1]
    create_directory(dir_name)
        
    # plt.savefig(os.path.join(dir_name, file_name), #dpi = 128,
    #             bbox_inches = 'tight', pad_inches = 0)

    _createTree(root).write_png(os.path.join(dir_name, file_name))

######################################################################################    
