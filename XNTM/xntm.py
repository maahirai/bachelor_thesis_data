from .tree import * 
import json
from pathlib import Path
import copy

class Module: 
    def __init__(self,node,ParentHash): 
        self.name = node.name
        self.hash = node.hash
        self.state = "NoTreatment"
        self.size = node.size
        self.ParentHash = ParentHash
        self.ChildrenHash = []
        self.ProvNum = node.provide_vol
        self.kind = "Reagent" if self.ProvNum == self.size else "Mixer" 
        for c in node.children:
            self.ChildrenHash.append(c.hash)

        ### 配置先が決定してから決まる情報
        self.RefCell = []
        self.ProvCell = []
        self.FlushCell = []
        self.CoveringCell = []
        self.orientation = ""

#######################################################################################
### general use functions
ModulePrefix = ["6","4","r"]
def getModulePrefixIdx(module): 
    for i in range(len(ModulePrefix)): 
        ### Prefix of Mixer Name is 6 or 4
        if ModulePrefix[i] == module[0]: 
            return i 
    ### Reagent can take other char than "r" as the prefix of the node-name like "R"
    return 2

def getMixerCoveringCell(RefCell,orientation=""): 
    CoveringCell = []
    refy,refx = RefCell
    Range = []
    if orientation == "h": 
        Range = [2,3]
    elif orientation == "v": 
        Range = [3,2]
    else : 
        Range = [2,2]

    range_y,range_x = Range
    for i in range(range_y): 
        for j in range(range_x): 
            y = refy + i 
            x = refx + j 
            cell = [y,x]
            CoveringCell.append(cell)
    return CoveringCell

def getAllAncestorsHash(hash): 
    AncestorHash = []
    Hash = hash
    while(getNode(Hash).ParentHash!=0):
        AncestorHash.append(getNode(Hash).ParentHash)
        Hash = getNode(Hash).ParentHash
    return AncestorHash 

def getNode(hash): 
    global NodeInfo 
    return NodeInfo[str(hash)]

def Mixing(MixerHash):
    global PMDState
    ChangeState(MixerHash,"OnlyProvDrop")   
    for cell in getNode(MixerHash).CoveringCell: 
        y,x = cell
        PMDState[y][x] = -1*MixerHash
    for ProvCell in getNode(MixerHash).ProvCell: 
        CellForProtectFromFlushing.append(ProvCell)
    for FlushCell in getNode(MixerHash).FlushCell:
        CellForFlushing.append(FlushCell)

########################################################################################
def getRatioAndPrefixOfChildren(mixer): 
    global NodeInfo
    PHash = mixer.hash 
    ratio = []
    modules = []
    for CHash in mixer.ChildrenHash:
        Node = getNode(CHash)
        ratio.append(Node.ProvNum)
        if Node.kind == "Reagent":
            modules.append("r")
        else : 
            modules.append(str(Node.size))
    return [ratio,modules]

def mv(lib,ParentMixerHash): 
    global NodeInfo
    ParentMixer = getNode(ParentMixerHash)
    ParentRefcell = ParentMixer.RefCell
    py,px = ParentRefcell
    diffY,diffX = py-2,px-2 
    ### Acording to the diffRefCell, modify the cell
    MovedLib = copy.deepcopy(lib)
    for prefix in ModulePrefix:
        for pattern in MovedLib["Module"][prefix]:
            if "ref_cell" in pattern: 
                y,x = pattern
                MovedRefCell = [y+diffY,x+diffX]
                pattern["ref_cell"] = MovedRefCell
            if "flushing_cell" in pattern: 
                MovedCells = []
                for cell in pattern["flushing_cell"]:
                    y,x = cell
                    MovedCell = [y+diffY,x+diffX]
                    MovedCells.append(MovedCell)
                pattern["flushing_pattern"] = MovedCells 
            if "overlapping_cell" in pattern: 
                MovedCells = []
                for cell in pattern["overlapping_cell"]: 
                    y,x = cell
                    MovedCell = [y+diffY,x+diffX]
                    MovedCells.append(MovedCell)
                pattern["overlapping_cell"] = MovedCells 
    return MovedLib 

### functions relating library
def GenLibKey(ratio,Modules): 
    # 6Mixer,4Mixer,Reagent Dropletについて，それぞれ含まれる数と親ミキサーに提供する液滴数をソートしたものを返す
    UsedNum = [0 for i in range(len(ModulePrefix))]
    ProvDropNum = ["" for i in range(len(ModulePrefix))]
    for idx,module in enumerate(Modules): 
        UsedNum[getModulePrefixIdx(module)]+=1
        ProvDropNum[getModulePrefixIdx(module)] += (str(ratio[idx]))

    for i in range(len(ModulePrefix)): 
        ProvDropNum[i] = "".join(sorted(ProvDropNum[i]))
    ret = []
    for i in range(len(ModulePrefix)):
        data = []
        data.append(UsedNum[i])
        data.append([ProvDropNum[i]])
        ret.append(data)

    key = str(ret)
    RemovedChars = " '"
    for c in RemovedChars: 
        key = key.replace(c,"")
    return key

### lib.jsonから該当値を抜き出してきて，返す
def _getLib(ParentMixer,ratio,EachModuleName):
    SortedRatio = sorted(ratio)
    key = GenLibKey(ratio,EachModuleName)
    FileName = ("lib"+ParentMixer+str(SortedRatio)+key+".json").replace(" ","")

    LibPath = Path("XNTM/sepdata/",FileName)
    readfile = open(LibPath,'r')
    lib = json.load(readfile)
    return lib
        
def getLib(ParentMixer,ratio,RatioOrderedModuleName):
    ret = _getLib(ParentMixer,ratio,RatioOrderedModuleName)
    return ret

from itertools import permutations
def AssignModuleToLib(lib,PHash): 
    global ModulePrefix
    parent = getNode(PHash) 
    ### 子供の分類
    KeyChildInfo = set()
    ChildInfo = {}
    for CHash in parent.ChildrenHash: 
        child = getNode(CHash) 
        info = ""
        if child.kind == "Mixer": 
             # 62 みたいな感じでミキサーサイズと残すセル数を表す
             info = str(child.size)+str(child.ProvNum)
        else :
             info = "r"+str(child.ProvNum)
        if info not in KeyChildInfo:
            KeyChildInfo.add(info)
            ChildInfo[str(info)] = []
        ChildInfo[str(info)].append(CHash)
    ### lib内のパターンをモジュールのサイズとprov_sizeで分類
    LibClassification = {}
    for prefix in ModulePrefix: 
        for pattern in lib["Module"][prefix]: 
            ProvNum = len(pattern["overlapping_cell"])
            key = prefix + str(ProvNum)
            if key not in LibClassification: 
                LibClassification[key] = []
            LibClassification[key].append(pattern)
    ### 割当
    print(LibClassification)
    ret = [{"Module":{"6":[],"4":[],"r":[]}}]
    for assignment in ret : 
        data = copy.deepcopy(assignment)
        for key in KeyChildInfo:     
            ChildHashes = ChildInfo[info] 
            perm = permutations(ChildHashes)
            for combo in perm: 
                for idx,hash in enumerate(combo):
                    pattern = copy.deepcopy(LibClassification[key][idx])
                    pattern["hash"] = hash 
                    # 6 or 4 or r
                    ModulePrefix = key[0]
                    data["Module"][ModulePrefix].append(pattern)
        ret.append(data)
        ret.remove(assignment)
    return ret

    
MaxLayerNum = 5
def getLayeredLib(lib): 
    global MaxLayerNum
    LayeredLib = [[[] for i in range(len(ModulePrefix))] for j in range(MaxLayerNum)]
    for prefix in ModulePrefix: 
        ModulePatterns = lib["Module"][prefix]
        for pattern in ModulePatterns: 
            ### layer-value starts from 1 so you should modify to use the value as array index
            layer = pattern["layer"]-1
            idx = getModulePrefixIdx(prefix)
            LayeredLib[layer][idx].append(pattern)
    return LayeredLib 


#def hasAncestorAsParent(CheckCellState,Module):
#    global NodeInfo 
#    Ancestor = getAllAncestorsHash(Module)
#    if NodeInfo[str(CheckCellState)].ParentHash in Ancestor:
#        return True 
#    else : 
#        return False

#def getAllCheckCells(CheckCells,ExpandDirection,SubTreeDepth): 
#    global Hsize,Vsize
#    ret = CheckCells
#    YMin,YMax  = 10000,0
#    XMin,XMax = 10000,0
#
#    for cell in CheckCells: 
#        y,x = cell 
#        if y < YMin : 
#            YMin = y 
#        if YMax < y : 
#            YMax = y 
#        if x < XMin : 
#            XMin = x
#        if XMax < x : 
#            XMax = x 
#
#    dy = [0,1,0,-1]
#    dx = [-1,0,1,0]
#    for idx,direction in enumerate(ExpandDirection) : 
#        if direction: 
#            if dx[direction] != 0:
#                if dx[direction] > 0:
#                    XMax += SubTreeDepth 
#                else : 
#                    XMin -= SubTreeDepth
#            else : 
#                if dy[direction] > 0: 
#                    YMax += SubTreeDepth 
#                else : 
#                    YMin -= SubTreeDepth 
#    for y in range(YMin,YMax+1): 
#        for x in range(XMin,XMax+1): 
#            if 0 < y and y < Vsize and 0 < x and x < Hsize :
#                AddCell = [y,x]
#                if AddCell not in ret: 
#                    ret.append(AddCell)
#    return ret

def EvalLib(lib,PHash):
    global PMDState,NodeInfo,MaxLayerNum
    CopyPMD = copy.deepcopy(PMDState)  
    ParentMixer = getNode(PHash)
    ParentCoveringCell = ParentMixer.CoveringCell
    ParentRefcell = ParentMixer.RefCell
    py,px = ParentRefcell
    diffRefCell = [py-2,px-2]
    ### Acording to the diffRefCell, modify the cell
    MovedPattern = mv(lib,diffRefCell)
    AssignedLib = AssigneModuleToLib(lib,PHash)

    
    ### sort lib by layer value 
    LayeredMovedPattern = getLayeredLib(Movedlib)
    evalv = 0 
    for layer in range(MaxLayerNum): 
        for prefix in ModulePrefix: 
            PatternLayerModule = LayeredLib[layer][getModulePrefixIdx(prefix)]
            for pattern in PatternLayerModule: 
                ### At First, get Module Covering Cells 
                CheckCells = []
                ### 6Mixer or 4Mixer
                if "ref_cell" in pattern: 
                    RefY,RefX = pattern["ref_cell"]
                    DiffY,DiffX = diffRefCell
                    RefCellMoved = [RefY+DiffY,RefX+DiffX]
                    ### 6Mixer
                    if "orientation" in pattern: 
                        CheckCells = getMixerCoveringCell(RefCellMoved,orientation=pattern[orientation])
                    else :
                        CheckCells = getMixerCoveringCell(RefCellMoved)
                else :
                    CoveringCell = pattern["overlapping_cell"]
                ExpandDirection = [False for i in range(4)]
                dy = [0,1,0,-1]
                dx = [-1,0,1,0]
                for cell in pattern["overlapping_cell"]: 
                    for direction in range(4): 
                        y,x = cell 
                        ty,tx = y+dy[direction],x+dx[direction] 
                        tCell = [ty,tx]
                        if tCell not in ParentCoveringCell:
                            ExpandDirection[direction] = True
                SubTreeDepth = getSubTreeDepth(mixer)
                ### 評価する範囲を決定
                CheckCells = getAllCheckCells(CheckCells,ExpandDirection,SubTreeDepth)
                for CheckCell in CheckCells: 
                    CheckY,CheckX = CheckCell
                    CheckCellState = PMDState[CheckY][CheckX] 
                    if CheckCellState > 0:
                        evalv += 1
                        if hasAncestorAsParent(CheckCellState,ModuleHash):
                            ### 失格 
                            evalv += 10000
    return evalv

def getOptLib(mixer): 
    PHash = mixer.hash 
    ratio = []
    modules = []
    for CHash in mixer.ChildrenHash:
        Node = NodeInfo[str(CHash)]
        ratio.append(Node.ProvNum)
        if Node.size == Node.ProvNum:
            modules.append(Node.name)
        else : 
            modules.append(str(Node.size))
    ParentMixer = str(mixer.size) + mixer.orientation
    lib = getLib(ParentMixer,ratio,modules)
    ValueAndLib = []
    for l in lib: 
        data =  EvalLib(l,PHash)
        ValueAndLib.append(data)
    SortedLib = sorted(ValueAndLib,reverse=True)
    OptLib = SortedLib[0][1]
    return OptLib

##################################### xntm #####################################

PMDState = []
NodeInfo = {}
MixerNodeHash = []

def NodeInfoInit(root): 
    global NodeInfo,MixerNodeHash
    q = []
    q.append(root)
    while(q): 
        e = q.pop(0)
        for child in e.children:
            module = Module(child,e.hash)
            NodeInfo[str(module.hash)] = module 
            if child.size != child.provide_vol:
                MixerNodeHash.append(module.hash)
            q.append(child)
    return 
          
CellForFlushing = []
CellForProtectFromFlushing = []
PlacementSkipped = []
WaitingProvDrops = []
OnlyProvDrop = []
AtTopOfPlacedMixer = []
Done = []

def PMDRootPlace(root,RefCell):
    global NodeInfo,MixerNodeHash,PMDState
    RootMixer = Module(root,0)
    ### ルートミキサーが6の場合のみ，配置の向きを考える必要あり
    if RootMixer.size == 6:
        RootMixer.orientation = "h"
    RootMixer.RefCell = RefCell
    RootMixer.CoveringCell = getMixerCoveringCell(RefCell,RootMixer.orientation)
    for y,x in RootMixer.CoveringCell: 
        PMDState[y][x] = RootMixer.hash
    RootMixer.ProvCell = RootMixer.CoveringCell
    ### Registering the root mixer
    NodeInfo[str(root.hash)] = RootMixer
    MixerNodeHash.append(root.hash)
    ChangeState(root.hash,"AtTopOfPlacedMixer")
    return root.hash

def ChangeState(Hash,NextState): 
    global AtTopOfPlacedMixer,WaitingProvDrops,OnlyProvDrop,PlacementSkipped,Done
    ModuleKind = getNode(Hash).kind 
    Now = getNode(Hash).state

    print(ModuleKind,Hash,WaitingProvDrops)
    if Now == "NoTreatment": 
        if NextState == "AtTopOfPlacedMixer": 
            if ModuleKind == "Mixer": 
                AtTopOfPlacedMixer.append(Hash)
                NodeInfo[str(Hash)].state = NextState 
            else:
                print("異常な遷移{}:{}→{}".format(NodeInfo[str(Hash)].kind,Now,NextState),file=sys.stderr)
        elif NextState == "OnlyProvDrop": 
            if ModuleKind == "Reagent": 
                OnlyProvDrop.append(Hash)
                NodeInfo[str(Hash)].state = NextState 
            else :
                print("異常な遷移{}:{}→{}".format(NodeInfo[str(Hash)].kind,Now,NextState),file=sys.stderr)
        elif NextState == "PlacementSkipped": 
            if ModuleKind == "Mixer": 
                ### スキップ
                print("異常な遷移{}:{}→{}".format(NodeInfo[str(Hash)].kind,Now,NextState),file=sys.stderr)
                pass 
        else : 
            print("異常な遷移{}:{}→{}".format(NodeInfo[str(Hash)].kind,Now,NextState),file=sys.stderr)
    elif Now == "AtTopOfPlacedMixer": 
        if NextState == "WaitingProvDrops": 
            if ModuleKind == "Mixer" and Hash in AtTopOfPlacedMixer: 
                AtTopOfPlacedMixer.remove(Hash)
                WaitingProvDrops.append(Hash)
                NodeInfo[str(Hash)].state = NextState 
            else :
                print("異常な遷移{}:{}→{}".format(NodeInfo[str(Hash)].kind,Now,NextState),file=sys.stderr)
        elif NextState == "OnlyProvDrop": 
            if ModuleKind == "Mixer" and Hash in AtTopOfPlacedMixer: 
                AtTopOfPlacedMixer.remove(Hash)
                OnlyProvDrop.append(Hash)
                NodeInfo[str(Hash)].state = NextState 
            else :
                print("異常な遷移{}:{}→{}".format(NodeInfo[str(Hash)].kind,Now,NextState),file=sys.stderr)
        else : 
            print("異常な遷移{}:{}→{}".format(NodeInfo[str(Hash)].kind,Now,NextState),file=sys.stderr)
    elif Now == "WaitingProvDrops": 
        if NextState == "AtTopOfPlacedMixer":
            if ModuleKind == "Mixer" and (Hash in WaitingProvDrops): 
                WaitingProvDrops.remove(Hash) 
                AtTopOfPlacedMixer.append(Hash)
                NodeInfo[str(Hash)].state = NextState 
            else :
                print("異常な遷移{}:{}→{}".format(NodeInfo[str(Hash)].kind,Now,NextState),file=sys.stderr)
        else : 
            print("異常な遷移{}:{}→{}".format(NodeInfo[str(Hash)].kind,Now,NextState),file=sys.stderr)
    elif Now == "OnlyProvDrop": 
        if NextState == "Done":
            if Hash in WaitingProvDrops : 
                OnlyProvDrop.remove(Hash) 
                Done.append(Hash)
                NodeInfo[str(Hash)].state = NextState 
            else : 
                print("異常な遷移{}:{}→{}".format(NodeInfo[str(Hash)].kind,Now,NextState),file=sys.stderr)
    elif Now == "PlacementSkipped": 
        if NextState == "AtTopOfPlacedMixer": 
            ### ライブラリから抜き出す
            pass 
        else : 
            print("異常な遷移{}:{}→{}".format(NodeInfo[str(Hash)].kind,Now,NextState),file=sys.stderr)
    else : 
        print("異常な遷移{}:{}→{}".format(NodeInfo[str(Hash)].kind,Now,NextState),file=sys.stderr)

def PlaceChildren(ParentMixerHash): 
    global NodeInfo
    ChangeState(ParentMixerHash,"WaitingProvDrops")
    ParentMixer = getNode(ParentMixerHash)
    MixerAttribute = str(ParentMixer.size) + ParentMixer.orientation
    RatioAndPrefix = getRatioAndPrefixOfChildren(ParentMixer)
    Ratio,Prefix = RatioAndPrefix 
    ### getOptなど使う pass
    lib = getLib(MixerAttribute,Ratio,Prefix)
    placelib(lib,ParentMixerHash)

def place(PlaceCells,v): 
    global PMDState
    for cell in PlaceCells: 
        y,x = cell 
        PMDState[y][x] = -1*v 

### テスト用の仮設．オーバーラップに対応できないなど，欠陥品 optlibとplaceを使う構成が本来．
def placelib(lib,ParentMixerHash): 
    ### pass 消す
    p= lib.pop()
    pa = AssignModuleToLib(p,ParentMixerHash)
    pattern = pa.pop()
    MovedPattern = mv(pattern,ParentMixerHash)
    LayeredLib = getLayeredLib(MovedPattern)
    global MaxLayerNum
    
    for layer in range(MaxLayerNum): 
        for prefix in ModulePrefix: 
            PrefixIdx = getModulePrefixIdx(prefix)
            for idx,pattern in enumerate(LayeredLib[layer][PrefixIdx]):
                if not pattern : 
                    continue 
                else : 
                    if "ref_cell" not in pattern : 
                        place(pattern["overlapping_cell"],pattern["hash"])
                    else : 
                        place(pattern["overlapping_cell"]+pattern["flushing_cell"],pattern["hash"])
    for CHash in getNode(ParentMixerHash).ChildrenHash: 
        if getNode(CHash).kind == "Reagent": 
            ChangeState(CHash,"OnlyProvDrop")
        else : 
            ChangeState(CHash,"AtTopOfPlacedMixer")

    
### lib内のパターンは評価の際に対応するハッシュ値をパッキングする．
### 使用するlibが決定した際に，refCellなどをNodeInfo に書き込む
### ParentMixer = str(mixer.size) + mixer.orientation
Vsize,Hsize=0,0
def xntm(root,PMDsize):
    global PMDState,NodeInfo,PlacementSkipped,WaitingProvDrops,AtTopOfPlacedMixer,CellForFlushing,CellForProtectFromFlushing,Vsize,Hsize
    Vsize,Hsize = PMDsize
    PMDState = [[0 for j in range(Hsize)] for i in range(Vsize)]
    ### -1はどっちでもいい，0はFlushするセル，1はProvDropなので守る必要あり．
    ForFlushRooting = [[-1 for j in range(Hsize)] for i in range(Vsize)]
    
    ### placement of root mixer
    RefCell = [(Vsize-1)//2,(Hsize-1)//2]
    RootHash = PMDRootPlace(root,RefCell)
    NodeInfoInit(root)
    print(AtTopOfPlacedMixer)
    
    while PlacementSkipped or WaitingProvDrops or AtTopOfPlacedMixer or OnlyProvDrop:
        print(AtTopOfPlacedMixer)
        print(WaitingProvDrops)
        print(OnlyProvDrop)
        if getNode(RootHash).state == "OnlyProvDrop": 
            print("混合手順生成完了")
            break
        for MixerHash in AtTopOfPlacedMixer: 
            mixer = getNode(MixerHash) 
            isReadyForMixing = True
            shouldPlaceChildren = False
            for ChildHash in mixer.ChildrenHash:
                if getNode(ChildHash).state != "OnlyProvDrop": 
                   isReadyForMixing = False 
                if getNode(ChildHash).state == "NoTreatment": 
                   shouldPlaceChildren = True 
            if shouldPlaceChildren: 
                PlaceChildren(MixerHash)
            elif isReadyForMixing : 
                Mixing(MixerHash)
            else : 
                continue
            print(PMDState)
        for MixerHash in WaitingProvDrops:
            isDropsProvidedByChildrenReady = True
            for ChildHash in getNode(MixerHash).ChildrenHash: 
                if getNode(ChildHash).state != "OnlyProvDrop": 
                    isDropsProvidedByChildrenReadyReady = False 
            if isDropsProvidedByChildrenReady : 
                ChangeState(MixerHash,"AtTopOfPlacedMixer")

         
