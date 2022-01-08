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
        self.SubTreeDepth = 0
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
def Flush(): 
    pass 

def WritePMD(PlaceCells,v): 
    global PMDState
    for cell in PlaceCells: 
        y,x = cell 
        PMDState[y][x] = v

########################################################################################
def getRatioAndPrefixOfChildren(MHash): 
    global NodeInfo 
    mixer = getNode(MHash)
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
    Movedlib = copy.deepcopy(lib)
    for prefix in ModulePrefix:
        for pattern in Movedlib["Module"][prefix]:
            if "ref_cell" in pattern: 
                y,x = pattern["ref_cell"]
                MovedRefCell = [y+diffY,x+diffX]
                pattern["ref_cell"] = MovedRefCell
            if "flushing_cell" in pattern: 
                MovedCells = []
                for cell in pattern["flushing_cell"]:
                    y,x = cell
                    MovedCell = [y+diffY,x+diffX]
                    MovedCells.append(MovedCell)
                pattern["flushing_cell"] = MovedCells 
            if "overlapping_cell" in pattern: 
                MovedCells = []
                for cell in pattern["overlapping_cell"]: 
                    y,x = cell
                    MovedCell = [y+diffY,x+diffX]
                    MovedCells.append(MovedCell)
                pattern["overlapping_cell"] = MovedCells 
    return Movedlib 

### functions relating library
def GenLibKey(ratio,Modules): 
    # 6Mixer,4Mixer,Reagent Dropletについて，それぞれ含まれる数と親ミキサーに提供する液滴数をソートしたものを返す
    global ModulePrefix
    UsedNum = [0 for i in range(len(ModulePrefix))]
    ProvDropNum = ["" for i in range(len(ModulePrefix))]
    for idx,module in enumerate(Modules): 
        UsedNum[getModulePrefixIdx(module)]+=1
        ProvDropNum[getModulePrefixIdx(module)] += (str(ratio[idx]))

    for i in range(len(ModulePrefix)): 
        ProvDropNum[i] = "".join(sorted(ProvDropNum[i],reverse=True))
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
def _getLib(ParentMixerHash):
    ParentMixer = getNode(ParentMixerHash)
    PMixerAttribute = str(ParentMixer.size) + ParentMixer.orientation
    RatioAndPrefix = getRatioAndPrefixOfChildren(ParentMixerHash)
    Ratio,Prefix = RatioAndPrefix 
    key = GenLibKey(Ratio,Prefix)
    SortedRatio = sorted(Ratio,reverse=True)
    FileName = ("lib"+PMixerAttribute+str(SortedRatio)+key+".json").replace(" ","")

    LibPath = Path("XNTM/sepdata/",FileName)
    readfile = open(LibPath,'r')
    lib = json.load(readfile)
    return lib
        
def getLib(ParentMixerHash):
    ret = _getLib(ParentMixerHash)
    return ret

from itertools import permutations
def AssignModuleTolib(lib,PHash): 
    global ModulePrefix
    parent = getNode(PHash) 
    ### 子供の分類
    KeyChildInfo = []
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
            KeyChildInfo.append(info)
            ChildInfo[str(info)] = []
        ChildInfo[str(info)].append(CHash)
    ### lib内のパターンをモジュールのサイズとprov_sizeで分類
    PatternClassification = {}
    for prefix in ModulePrefix: 
        for pattern in lib["Module"][prefix]: 
            ProvNum = len(pattern["overlapping_cell"])
            key = prefix + str(ProvNum)
            if key not in PatternClassification: 
                PatternClassification[key] = []
            PatternClassification[key].append(pattern)
    ### 割当
    ret = [{"Module":{"6":[],"4":[],"r":[]}}]
    for key in KeyChildInfo:     
        ChildHashes = ChildInfo[key] 
        nret = []
        for assignment in ret : 
            perm = permutations(ChildHashes)
            for combo in perm: 
                data = copy.deepcopy(assignment)
                for idx,hash in enumerate(combo):
                    pattern = copy.deepcopy(PatternClassification[key][idx])
                    pattern["hash"] = hash 
                    # 6 or 4 or r
                    prefix = key[0]
                    data["Module"][prefix].append(pattern)
                nret.append(data)
        ret = nret 
    return ret

    
MaxLayerNum = 6 
def getLayeredlib(lib): 
    global MaxLayerNum 
    if lib == {}: 
        return {}
    Layeredlib = [[[] for i in range(len(ModulePrefix))] for j in range(MaxLayerNum)]
    for prefix in ModulePrefix: 
        ModulePatterns = lib["Module"][prefix]
        for pattern in ModulePatterns: 
            ### layer-value starts from 1 so you should modify to use the value as array index
            layer = pattern["layer"]-1
            idx = getModulePrefixIdx(prefix)
            Layeredlib[layer][idx].append(pattern)
    return Layeredlib 

def isEmptyLayeredlib(lib): 
    global MaxLayerNum 
    for i in range(MaxLayerNum): 
        for j in range(len(ModulePrefix)): 
            if lib[i][j]: 
                return False 
    return True

def OK(CheckCell,CheckCellState,ModuleHash):
    global NodeInfo 
    checkHash = abs(CheckCellState)
    if CheckCell in NodeInfo[str(checkHash)].ProvCell: 
        Ancestor = getAllAncestorsHash(ModuleHash)
        if NodeInfo[str(checkHash)].ParentHash in Ancestor:
            return False
    else : 
        return True

def getAllCheckCells(CheckCells,ExpandDirection,SubTreeDepth): 
    global Hsize,Vsize
    ret = CheckCells
    YMin,YMax  = 10000,0
    XMin,XMax = 10000,0

    for cell in CheckCells: 
        y,x = cell 
        if y < YMin : 
            YMin = y 
        if YMax < y : 
            YMax = y 
        if x < XMin : 
            XMin = x
        if XMax < x : 
            XMax = x 
    dy = [0,1,0,-1]
    dx = [-1,0,1,0]
    for idx,direction in enumerate(ExpandDirection) : 
        if direction: 
            if dx[idx] != 0:
                if dx[idx] > 0:
                    XMax += SubTreeDepth 
                else : 
                    XMin -= SubTreeDepth
            else :
                if dy[idx] > 0: 
                    YMax += SubTreeDepth 
                else : 
                    YMin -= SubTreeDepth 
    for y in range(YMin,YMax+1): 
        for x in range(XMin,XMax+1): 
            if 0 <= y and y < Vsize and 0 <= x and x < Hsize :
                AddCell = [y,x]
                if AddCell not in ret: 
                    ret.append(AddCell)
    return ret

def Evallib(lib,PHash):
    global PMDState,MaxLayerNum
    PMixer = getNode(PHash)
    
    PMixerCoveringCell = PMixer.CoveringCell
    dy = [0,1,0,-1]
    dx = [-1,0,1,0]
    Layeredlib = getLayeredlib(lib)
    # lib内の各パターンを評価する
    evalv = 0 
    ChildrenHashes = copy.deepcopy(PMixer.ChildrenHash)
    for layer in range(MaxLayerNum): 
        for prefix in ModulePrefix: 
            Patterns = Layeredlib[layer][getModulePrefixIdx(prefix)]
            for pattern in Patterns:
                ### 変形した希釈木に対応したミキサーの順番で配置しているかチェック
                Chash = pattern["hash"]
                if getNode(Chash).kind == "Mixer": 
                    while(ChildrenHashes):
                        CmpHash = ChildrenHashes.pop(0)
                        if getNode(CmpHash).kind == "Mixer": 
                            if CmpHash != Chash: 
                                evalv+= 10000001.0
                            else : 
                                break
                        else : 
                            continue

                evalv += 10.0**(layer+1)
                ProvCell = pattern["overlapping_cell"]
                PatternCoveringCells = pattern["overlapping_cell"]
                if "flushing_cell" in pattern: 
                    PatternCoveringCells += pattern["flushing_cell"]
                for cell in PatternCoveringCells:
                    y,x = cell
                    CheckCellState = PMDState[y][x]
                    if CheckCellState != 0 and not OK(cell,CheckCellState,pattern["hash"]): 
                        evalv+= 10000001.0
                ### 各prov_cellの4方に同lib内patternのprov_cellが無いかチェックする
                OkDirection = [False for i in range(4)]
                for y,x in ProvCell: 
                    for direction in range(4): 
                        CheckCell = [y+dy[direction],x+dx[direction]]
                        if CheckCell not in PMixerCoveringCell: 
                            OkDirection[direction] = True 
                AllCheckCells = getAllCheckCells(PMixerCoveringCell,OkDirection,getNode(pattern["hash"]).SubTreeDepth)
                for CheckCell in AllCheckCells: 
                    checkY,checkX = CheckCell
                    CheckCellState = PMDState[checkY][checkX]
                    if CheckCellState != 0 and CheckCellState != PHash:
                        evalv += 10.0**layer
    return evalv

def getOptlib(PHash): 
    Optlib = {}
    Lib = getLib(PHash)
    min_v = 100000000000000.0
    for lib in Lib: 
        Assignedlib = AssignModuleTolib(lib,PHash)
        for alib in Assignedlib: 
            #if alib == {"Module":{"6":[],"4":[],"r":[]}} or alib == {}: 
            #    continue 
            alib = mv(alib,PHash)
            v =  Evallib(alib,PHash)
            if v < min_v: 
                min_v = v 
                Optlib = alib 
    print(Optlib)
    return Optlib

##################################### xntm #####################################

PMDState = []
NodeInfo = {}
MixerNodeHash = []

def NodeInfoInit(root): 
    global NodeInfo,MixerNodeHash
    q = []
    q.append(root)
    leaves = []
    while(q): 
        e = q.pop(0)
        if not e.children: 
            leaves.append(e.hash)
        for child in e.children:
            module = Module(child,e.hash)
            NodeInfo[str(module.hash)] = module 
            if child.size != child.provide_vol:
                MixerNodeHash.append(module.hash)
            q.append(child)
    q = []
    for leaf in leaves: 
        e = [leaf,0]
        q.append(e)
    while(q): 
        e = q.pop(0)
        hash,height = e 
        Node = getNode(hash)
        if  Node.SubTreeDepth < height: 
            NodeInfo[str(hash)].SubTreeDepth = height
        PHash = Node.ParentHash
        if PHash != 0 : 
            q.append([PHash,height+1])
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

def WritePlacementInfo(pattern,Hash): 
    global NodeInfo 
    if "ref_cell" in pattern: 
        NodeInfo[str(Hash)].RefCell = pattern["ref_cell"]
    if "orientation" in pattern: 
        NodeInfo[str(Hash)].orientation = pattern["orientation"]
    NodeInfo[str(Hash)].ProvCell = pattern["overlapping_cell"]
    NodeInfo[str(Hash)].FlushCell = pattern["flushing_cell"]
    NodeInfo[str(Hash)].CoveringCell = pattern["overlapping_cell"]+pattern["flushing_cell"]
    return 

def ChangeState(Hash,NextState): 
    global AtTopOfPlacedMixer,WaitingProvDrops,OnlyProvDrop,PlacementSkipped,Done 
    ModuleKind = getNode(Hash).kind 
    Now = getNode(Hash).state

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
    
    ### getOptなど使う pass
    lib = getOptlib(ParentMixerHash)
    Layeredlib = getLayeredlib(lib)
    RestOflib = placelib(Layeredlib,ParentMixerHash)
    ### 配置しきったなら
    if not RestOflib: 
        return 
    else : 
        PlacementSkipped.append(RestOflib)

def NoOverlapping(pattern): 
    global PMDState 
    ParentMixerHash = getNode(pattern["hash"]).ParentHash
    Cells = pattern["overlapping_cell"]
    if "flushing_cell" in pattern: 
        Cells = Cells+pattern["flushing_cell"]
    for y,x in Cells: 
        if PMDState[y][x]!=0 and PMDState[y][x]!=ParentMixerHash: 
            return False 
    return True

def placelib(Layeredlib,ParentMixerHash): 
    ### pass 消す
#    p= lib.pop()
#    pa = AssignModuleTolib(p,ParentMixerHash)
#    pattern = pa.pop()
#    Movedlib = mv(lib,ParentMixerHash)
    #Layeredlib = getLayeredlib(MovedPattern)
    global MaxLayerNum
    retLayeredlib = [[[] for i in range(len(ModulePrefix))] for j in range(MaxLayerNum)]

    PlacementSkipped = False
    for layer in range(MaxLayerNum): 
        for prefix in ModulePrefix: 
            PrefixIdx = getModulePrefixIdx(prefix)
            for pattern in Layeredlib[layer][PrefixIdx]:
                ModuleHash = pattern["hash"]
                if not PlacementSkipped and NoOverlapping(pattern):
                    # 試薬液滴
                    if getNode(ModuleHash).kind == "Reagent": 
                        WritePMD(pattern["overlapping_cell"],ModuleHash*-1)
                        ChangeState(ModuleHash,"OnlyProvDrop")
                        WritePlacementInfo(pattern,ModuleHash)
                    else : 
                        WritePMD(pattern["overlapping_cell"]+pattern["flushing_cell"],ModuleHash)
                        ChangeState(ModuleHash,"AtTopOfPlacedMixer")
                        WritePlacementInfo(pattern,ModuleHash)
                else: 
                    PlacementSkipped = True 
                    ChangeState(ModuleHash,"PlacementSkipped")
                    WritePlacementInfo(pattern,ModuleHash)
                    retLayeredlib[layer][PrefixIdx].append(pattern)
    if isEmptyLayeredlib(retLayeredlib):
        return []
    return retLayeredlib
    
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
                print(AtTopOfPlacedMixer)
                print(WaitingProvDrops)
                print(OnlyProvDrop)
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
