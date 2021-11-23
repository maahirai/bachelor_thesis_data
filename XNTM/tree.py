import random

class node(object):
    def __init__(self, name, size=6, provide_vol=0, children = []):
        self.name = name 
        self.size = size
        self.provide_vol = provide_vol
        self.children = children or []
        self.hash = random.randint(1,100000001)

######################################################################################
MIX_COUNTER = 0
def _InputToTree(Input,provide_vol):
    global MIX_COUNTER
    root = node('M{}'.format(MIX_COUNTER),size=sum(Input[0]),provide_vol=provide_vol)
    MIX_COUNTER += 1
    idx = 0 
    for item in Input[1:]:
        ### ミキサー
        if type(item) == list:
            root.children.append(_InputToTree(item,Input[0][idx]))
        ### 試薬液滴
        elif type(item) == str:
            root.children.append(node(item,size=Input[0][idx],provide_vol=Input[0][idx]))
        else :
            return
        idx += 1
    return root
    
def InputToTree(Input):
    global MIX_COUNTER
    MIX_COUNTER = 0
    return _InputToTree(Input,0)

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
def _createTree(root, label=None):
    '''
    convert a tree from NODE data structure to Pydot Graph for visualisation
    '''
    P = pydot.Dot(graph_type='digraph', label=label, labelloc='top', labeljust='left')#, nodesep="1", ranksep="1")
    
    nodelist, edgelist = _getNodesEdges(root)
    
    for node in nodelist:
        n = pydot.Node(node[0], shape = 'circle' if node[1][0]=="M" else 'plaintext',label=node[1])
        ### ミキサーは円で囲む，試薬液滴はテキストのみ.
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
### 希釈木の写真の保存
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
