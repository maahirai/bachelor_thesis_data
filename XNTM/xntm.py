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
        self.MixedTimeStep = -1 
        self.PlaceTimeStep = -1

#######################################################################################
### general use functions
ModulePrefix = ["6","4","r"]

def globalInit(): 
    global PMDState,NodeInfo,PlacementSkipped,OnlyProvDrop,WaitingProvDrops,AtTopOfPlacedMixer,CellForFlushing,CellForProtectFromFlushing,Done,Vsize,Hsize,PlacementSkippedLib,CntRollBack,SubTreeDepthMean,MixerNodeHash,RollBackHash
    PMDState = [[0 for j in range(Hsize)] for i in range(Vsize)]
    NodeInfo = {}
    CntRollBack = 0
    PlacementSkipped,OnlyProvDrop,WaitingProvDrops,AtTopOfPlacedMixer,Done = [],[],[],[],[]
    CellForFlushing,CellForProtectFromFlushing = [],[]
    PlacementSkippedLib = []
    MixerNodeHash = []
    SubTreeDepthMean = 0
    RollBackHash=[]

def viewAllModule(RootHash): 
    q = [] 
    q.append(RootHash)
    while(q): 
        e = q.pop(0) 
        print([e,getNode(e).name,getNode(e).kind],end="")
        for c in getNode(e).ChildrenHash: 
            q.append(c)
    print("")

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
    global NodeInfo,PMDState,CellForFlushing,CellForProtectFromFlushing,TimeStep
    NodeInfo[str(MixerHash)].MixedTimeStep = TimeStep
    Mixer = getNode(MixerHash)
    
    for cell in getMixerCoveringCell(Mixer.RefCell,Mixer.orientation): 
        if cell in CellForProtectFromFlushing: 
            CellForProtectFromFlushing.remove(cell)
        y,x = cell
        PMDState[y][x] = -1*MixerHash
    for provCell in Mixer.ProvCell: 
        CellForProtectFromFlushing.append(provCell)
    for FlushCell in Mixer.FlushCell:
        CellForFlushing.append(FlushCell)
    ### Mixingによって発生する状態遷移
    StateChanges = [ChangeState(MixerHash,"OnlyProvDrop")]   
    for CHash in getNode(MixerHash).ChildrenHash: 
        stateChange = ChangeState(CHash,"Done")
        StateChanges.append(stateChange)
    return StateChanges

def InsidePMD(Y,X): 
    global Vsize,Hsize 
    if 0 <= Y and Y < Hsize and  0 <= X and X < Vsize : 
        return True 
    else : 
        return False 

def CanReachCell(cell): 
    global CellForProtectFromFlushing,Vsize,Hsize
    dx = [-1,0,1,0]
    dy = [0,-1,0,1]
    Cells = []
    if cell in CellForProtectFromFlushing: 
        return []

    q = [cell]
    IsVisited = [[False for i in range(Hsize)]for j in range(Vsize)]
    while(q): 
        cell = q.pop(0)
        y,x = cell
        if cell not in Cells : 
            Cells.append(cell)
        for way in range(4): 
           ny,nx = y+dy[way],x+dx[way] 
           if InsidePMD(ny,nx): 
               ncell = [ny,nx]
               if ncell not in CellForProtectFromFlushing and not IsVisited[ny][nx]: 
                    IsVisited[ny][nx] = True
                    q.append(ncell) 
    return Cells 

def Flush(): 
    global PMDState,Vsize,Hsize,CellForFlushing,CellForProtectFromFlushing 
    dx = [-1,0,1,0]
    dy = [0,-1,0,1]
    CornerCell = [[0,0],[0,Hsize-1],[Vsize-1,0],[Vsize-1,Hsize-1]]
    for CheckY,CheckX in CellForFlushing: 
        CanPassThrough = 0
        for way in range(4): 
            NeighborY = CheckY + dy[way]
            NeighborX = CheckX + dx[way]
            if InsidePMD(NeighborY,NeighborX): 
                if [CheckY,CheckX] not in CellForProtectFromFlushing: 
                    CanPassThrough += 1
        if [CheckY,CheckX] not in CornerCell: 
            if CanPassThrough < 2:
                return False 
        else : 
            if CanPassThrough == 0:
                return False

    inCell = [[0,0],[0,Vsize-1]]
    outCell = [[Hsize-1,0],[Hsize-1,Vsize-1]]
    for inport in inCell: 
        for outport in outCell: 
            FromIN = CanReachCell(inport)
            FromOUT = CanReachCell(outport)
            ok = True
            for cell in CellForFlushing: 
                if cell not in FromIN or cell not in FromOUT: 
                    ok = False 
            if ok : 
                ### フラッシュ可能
                for i in range(Vsize): 
                    for j in range(Hsize): 
                        if [i,j] not in CellForProtectFromFlushing and PMDState[i][j] < 0: 
                            PMDState[i][j] = 0
                CellForFlushing = []
                return True
    return False

def RollBack(PMixerHash): 
    global PMDState,CellForProtectFromFlushing,CellForFlushing,Vsize,Hsize
    PMixer = getNode(PMixerHash)
    StateChanges = []
    q = []
    des = []
    for CHash in getNode(PMixerHash).ChildrenHash: 
        q.append(CHash)
    while(q): 
        ModuleHash = q.pop(0)
        des.append(ModuleHash)
        if getNode(ModuleHash).state != "NoTreatment": 
            stateChange = ChangeState(ModuleHash,"NoTreatment")
            StateChanges.append(stateChange)

        Module = getNode(ModuleHash)
        for CHash in Module.ChildrenHash: 
            q.append(CHash)

    RollBackCell = []
    for y in range(Vsize): 
        for x in range(Hsize): 
            cell = [y,x]
            if abs(PMDState[y][x]) in des: 
                RollBackCell.append(cell)
                if cell in CellForFlushing : 
                    CellForFlushing.remove(cell)
                elif cell in CellForProtectFromFlushing: 
                    CellForProtectFromFlushing.remove(cell)   
    WritePMD(RollBackCell,0)
    stateChange = ChangeState(PMixerHash,"AtTopOfPlacedMixer")
    StateChanges.append(stateChange)
    WritePMD(getNode(PMixerHash).CoveringCell,PMixerHash)
    return StateChanges

def WritePMD(PlaceCells,v): 
    global PMDState,CellForProtectFromFlushing 
    for cell in PlaceCells: 
        y,x = cell 
        PMDState[y][x] = v 
    
def viewPMD(): 
    global PMDState
    for row in PMDState : 
        for CellState in row: 
            print("{:6d}".format(CellState),end=" ")
        print("")

def countMixerTimeStep(RootHash):
    TimeSteps = []
    q = []
    q.append(RootHash)
    while(q): 
        hash = q.pop()
        Node = getNode(hash)
        print(Node.name,Node.MixedTimeStep)
        TimeSteps.append(Node.MixedTimeStep)
        for chash in Node.ChildrenHash: 
            if getNode(chash).kind == "Mixer": 
                q.append(chash)
    return len(set(TimeSteps))

from .utility import ProcessImage
def CountFlushing(RootHash,savefile,ColorList,ImageOut=False): 
    global Vsize,Hsize,TimeStep
    PMD = [[0 for j in range(Hsize)]for i in range(Vsize)]
    Drop = {}
    Mixer = {}
    q = []
    q.append(RootHash)
    while(q): 
        hash = q.pop()
        Node = getNode(hash)
        #print(Node.name,Node.MixedTimeStep)
        ts = 0
        if Node.kind=="Mixer":
            ts = Node.MixedTimeStep
            if str(ts) not in Mixer:
                Mixer[str(ts)] = []
            Mixer[str(ts)].append(hash)
        else : 
            ts = Node.PlaceTimeStep 
            if str(ts) not in Drop:
                Drop[str(ts)] = []
            Drop[str(ts)].append(hash)
        for chash in Node.ChildrenHash: 
            q.append(chash) 
    ret = 0
    skipped = 0
    for ts in range(1,TimeStep+1):
        if str(ts) in Drop:
            for dhash in Drop[str(ts)]:
                for y,x in getNode(dhash).ProvCell: 
                    if PMD[y][x]!= 0: 
                        ret += 1
                        flushed = []
                        for i in range(Vsize): 
                            for j in range(Hsize): 
                                hash = -1*PMD[i][j]
                                if PMD[i][j]!= 0 and hash not in flushed:
                                    Node = getNode(hash)
                                    if Node.kind=="Mixer":
                                        provcell = Node.ProvCell 
                                        covering_cell = Node.CoveringCell 
                                        for cell in covering_cell: 
                                            ty,tx = cell
                                            if cell in provcell : 
                                                continue 
                                            else : 
                                                if PMD[ty][tx]==-1*hash:
                                                    PMD[ty][tx] = 0 
                                        flushed.append(hash)
                    if PMD[y][x]!= 0:
                        return -2
                    else: 
                        PMD[y][x] = -1*dhash 
        if str(ts) in Mixer:
            if ImageOut: 
                ProcessImage(savefile+"_"+str(ts),Vsize,Hsize,ColorList,ts-skipped,ret,PMD,Mixer[str(ts)],NodeInfo) 
            for mhash in Mixer[str(ts)]: 
                for wy,wx in getNode(mhash).CoveringCell: 
                    PMD[wy][wx] = -1*mhash 
        else : 
            skipped += 1 
    return ret

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
    is_ok = True
    for prefix in ModulePrefix:
        for pattern in Movedlib["Module"][prefix]:
            if "ref_cell" in pattern: 
                y,x = pattern["ref_cell"]
                mvy,mvx = y+diffY,x+diffX 
                
                if InsidePMD(mvy,mvx):
                    MovedRefCell = [mvy,mvx]
                    pattern["ref_cell"] = MovedRefCell 
                    orientation = ""
                    if "orientation" in pattern: 
                        orientation = pattern["orientation"]
                    for y,x in getMixerCoveringCell(pattern["ref_cell"],orientation): 
                        if not InsidePMD(y,x): 
                            is_ok = False
                else : 
                    is_ok = False
            if "flushing_cell" in pattern: 
                MovedCells = []
                for cell in pattern["flushing_cell"]:
                    y,x = cell
                    mvy,mvx = y+diffY,x+diffX 
                    if InsidePMD(mvy,mvx):
                        MovedCell = [mvy,mvx]
                        MovedCells.append(MovedCell)
                    else : 
                        is_ok = False
                pattern["flushing_cell"] = MovedCells 
            if "overlapping_cell" in pattern: 
                MovedCells = []
                for cell in pattern["overlapping_cell"]: 
                    y,x = cell
                    mvy,mvx = y+diffY,x+diffX 
                    if InsidePMD(mvy,mvx):
                        MovedCell = [mvy,mvx]
                        MovedCells.append(MovedCell)
                    else : 
                        is_ok = False
                pattern["overlapping_cell"] = MovedCells 
    if is_ok :
        return Movedlib 
    else : 
        return {}

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
    Lib = json.load(readfile)
    return Lib
        
def getLib(ParentMixerHash):
    Lib = _getLib(ParentMixerHash)
    return Lib

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
    global MaxLayerNum,ModulePrefix
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

def getHashlib(lib): 
    Hashlib = {}
    for prefix in ModulePrefix:
        ModulePatterns = lib["Module"][prefix]
        for pattern in ModulePatterns: 
            if "hash" in pattern: 
                hash = pattern["hash"]
                Hashlib[str(hash)] = pattern
            else : 
                print("getHashlib():ハッシュ値がアサインされていないlibを受け取りました．",file=sys.stderr)
    return Hashlib 

def CanPlace(ModuleHash,PatternCoveringCells,layer): 
    global NodeInfo,PMDState,CellForProtectFromFlushing
    Module = getNode(ModuleHash)
    eval = 0 

    NGNode = getAllAncestorsHash(ModuleHash)
    NGtoo = []
    for Hash in NGNode:
        for ng in getNode(Hash).ChildrenHash:  
            NGtoo.append(ng)
    CoveringCell = PatternCoveringCells
    for cell in CoveringCell: 
        y,x = cell
        if PMDState[y][x]<0 :
            cmphash = -1*PMDState[y][x] 
            if (cmphash in NGNode or cmphash in NGtoo )and cell in CellForProtectFromFlushing:
                return -1000
        else: 
            cmphash = PMDState[y][x] 
            if cmphash in NGNode or cmphash in NGtoo :  
                ### 極力辞めたほうがいい
                return 100000000000.0 * (layer+1)
    return 0


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
    global PMDState,MaxLayerNum,CellForProtectFromFlushing,SubTreeDepthMean
    PMixer = getNode(PHash)
    Layeredlib = getLayeredlib(lib)

    ### 希釈木に対応したミキサーの順番で配置しているかチェック
    ChildrenHashes = copy.deepcopy(PMixer.ChildrenHash)
    for layer in range(MaxLayerNum):
        MixerPatterns = Layeredlib[layer][getModulePrefixIdx("6")]+Layeredlib[layer][getModulePrefixIdx("4")]
        Hashes = []
        for pattern in MixerPatterns:
            Hashes.append(pattern["hash"])    
        CmpHashes = []
        while (len(CmpHashes) < len(Hashes)):
            hash = ChildrenHashes.pop(0)
            if getNode(hash).kind == "Mixer": 
                CmpHashes.append(hash)
        for ChildHash in Hashes: 
            if ChildHash not in CmpHashes: 
                ### 失格
                return 100000000000000001.0
    ### 以上のパートをくぐり抜けたなら: 配置順がok
    
    ### 評価開始
    evalv = 0
    ### 配置予定地がまずくないかチェック
    for layer in range(MaxLayerNum):
         for idx,prefix in enumerate(ModulePrefix): 
            for pattern in Layeredlib[layer][idx]: 
                PatternCoveringCells = []
                Module = getNode(pattern["hash"])
                if Module.kind == "Mixer":
                    RefCell = pattern["ref_cell"]
                    orientation = pattern["orientation"] if Module.size == 6 else ""
                    PatternCoveringCells = getMixerCoveringCell(RefCell,orientation)
                else : 
                    PatternCoveringCells = copy.deepcopy(pattern["overlapping_cell"])
                v =  CanPlace(Module.hash,PatternCoveringCells,layer)
                if v<0: 
                    ### 失格
                    return 100000000000000001.0 
                else : 
                    evalv += v
     
    #　ミキサー同士が離れて配置されているか評価
    for layer in range(MaxLayerNum):
        MixerPatterns = copy.deepcopy(Layeredlib[layer][getModulePrefixIdx("6")]+Layeredlib[layer][getModulePrefixIdx("4")] )
        Len = len(MixerPatterns)
        for first in range(Len): 
            for second in range(Len): 
                if  first >= second: 
                    continue
                FirstPattern = MixerPatterns[first]
                SecondPattern = MixerPatterns[second]
                FHash = FirstPattern["hash"]
                SHash = SecondPattern["hash"]
                FEvalCell = copy.deepcopy(FirstPattern["overlapping_cell"]+FirstPattern["flushing_cell"])
                SEvalCell = copy.deepcopy(SecondPattern["overlapping_cell"]+SecondPattern["flushing_cell"])  
                MinDist = 100
                for FCell in FEvalCell: 
                    for SCell in SEvalCell: 
                        fy,fx = FCell
                        sy,sx = SCell
                        tdist = abs((fy-sy)+(fx-sx))
                        if MinDist > tdist : 
                            MinDist = tdist 
                ### 各ミキサーノードを根とする部分木が子孫ノードを持つほど，ミキサー間の距離が重要になってくる
                expo = (((getNode(FHash).SubTreeDepth+getNode(SHash).SubTreeDepth+layer))-(2**(MinDist)*SubTreeDepthMean))
                if expo < 0: 
                    expo = 0
                v = 1000*(expo)
                evalv += v

    PMixerCoveringCell = getMixerCoveringCell(PMixer.RefCell,PMixer.orientation)
    dy = [0,1,0,-1]
    dx = [-1,0,1,0]
    # lib内の各パターンを評価する
    for layer in range(MaxLayerNum): 
        for idx,prefix in enumerate(ModulePrefix): 
            for pattern in Layeredlib[layer][idx]: 
                ### libのlayerが大きいほどflushingの回数増える
                evalv += 1000.0*(layer+1)

                ### 各prov_cellの4方に同lib内patternのprov_cellが無いかチェックする
                OkDirection = [False for i in range(4)]
                OnParentCell = copy.deepcopy(pattern["overlapping_cell"]+pattern["flushing_cell"])
                for y,x in OnParentCell: 
                    for direction in range(4): 
                        CheckCell = [y+dy[direction],x+dx[direction]]
                        if CheckCell not in PMixerCoveringCell: 
                            OkDirection[direction] = True 
                AllCheckCells = getAllCheckCells(PMixerCoveringCell,OkDirection,getNode(pattern["hash"]).SubTreeDepth)
                for CheckCell in AllCheckCells: 
                    checkY,checkX = CheckCell
                    CheckCellState = PMDState[checkY][checkX]
                    if CheckCellState != 0 and CheckCellState != PHash:
                        ### オーバーラップが起こるかも
                        evalv += 1000.0/(layer+1)
    return evalv

def getOptlib(PHash): 
    Optlib = {}
    Lib = getLib(PHash)
    min_v = 100000000000000.0
    for lib in Lib: 
        Assignedlib = AssignModuleTolib(lib,PHash)
        for alib in Assignedlib: 
            alib = mv(alib,PHash)
            if not alib : 
                continue
            v =  Evallib(alib,PHash)
            if v < min_v: 
                min_v = v 
                Optlib = alib 
    return Optlib

##################################### xntm #####################################

PMDState = []
NodeInfo = {}
MixerNodeHash = []
SubTreeDepthMean = 0
def NodeInfoInit(root): 
    global NodeInfo,MixerNodeHash,SubTreeDepthMean
    q = []
    q.append(root)
    leaves = []
    d = []
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
    for mhash in MixerNodeHash: 
        d.append(NodeInfo[str(mhash)].SubTreeDepth)
    Sum = 0
    for depth in set(d): 
        Sum += depth 
    SubTreeDepthMean = Sum/len(set(d))
    return 
          
CellForFlushing = []
CellForProtectFromFlushing = []
PlacementSkipped = []
PlacementSkippedLib = []
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
    stateChange = ChangeState(root.hash,"AtTopOfPlacedMixer")
    StateChanges = [stateChange]
    ReflectStateChanges(StateChanges)
    return root.hash

def WritePlacementInfo(pattern,Hash): 
    global NodeInfo,TimeStep 
    if "ref_cell" in pattern: 
        NodeInfo[str(Hash)].RefCell = pattern["ref_cell"]
    if "orientation" in pattern: 
        NodeInfo[str(Hash)].orientation = pattern["orientation"]
    NodeInfo[str(Hash)].ProvCell = pattern["overlapping_cell"]
    NodeInfo[str(Hash)].FlushCell = pattern["flushing_cell"]
    if NodeInfo[str(Hash)].kind == "Reagent": 
        NodeInfo[str(Hash)].CoveringCell = pattern["overlapping_cell"] 
    else : 
        NodeInfo[str(Hash)].CoveringCell = getMixerCoveringCell(NodeInfo[str(Hash)].RefCell,NodeInfo[str(Hash)].orientation)
    
    return 

def ChangeState(Hash,NextState): 
    global AtTopOfPlacedMixer,WaitingProvDrops,OnlyProvDrop,PlacementSkipped,Done,PlacementSkippedLib
    ModuleKind = getNode(Hash).kind 
    Now = getNode(Hash).state

    if Now == "NoTreatment": 
        if NextState == "AtTopOfPlacedMixer": 
            if ModuleKind == "Mixer": 
                NodeInfo[str(Hash)].state = NextState 
                return [Hash,[Now,NextState]]
            else:
                print("異常な遷移{}:{}→{}".format(NodeInfo[str(Hash)].kind,Now,NextState),file=sys.stderr)
        elif NextState == "OnlyProvDrop": 
            if ModuleKind == "Reagent": 
                NodeInfo[str(Hash)].state = NextState 
                return [Hash,[Now,NextState]]
            else :
                print("異常な遷移{}:{}→{}".format(NodeInfo[str(Hash)].kind,Now,NextState),file=sys.stderr)
        elif NextState == "PlacementSkipped": 
            ### チェックは呼び出し側に任す
            NodeInfo[str(Hash)].state = NextState 
            return [Hash,[Now,NextState]]
        else : 
            print("異常な遷移{}:{}→{}".format(NodeInfo[str(Hash)].kind,Now,NextState),file=sys.stderr)
    elif Now == "AtTopOfPlacedMixer": 
        if NextState == "WaitingProvDrops": 
            if ModuleKind == "Mixer" and Hash in AtTopOfPlacedMixer: 
                NodeInfo[str(Hash)].state = NextState 
                return [Hash,[Now,NextState]]
            else :
                print("異常な遷移{}:{}→{}".format(NodeInfo[str(Hash)].kind,Now,NextState),file=sys.stderr)
        elif NextState == "OnlyProvDrop": 
            if ModuleKind == "Mixer" and Hash in AtTopOfPlacedMixer: 
                NodeInfo[str(Hash)].state = NextState 
                return [Hash,[Now,NextState]]
            else :
                print("異常な遷移{}:{}→{}".format(NodeInfo[str(Hash)].kind,Now,NextState),file=sys.stderr)
        elif NextState == "NoTreatment":
            if Hash in AtTopOfPlacedMixer:
                NodeInfo[str(Hash)].state = NextState 
                return [Hash,[Now,NextState]]
            else :
                print("異常な遷移{}:{}→{}".format(NodeInfo[str(Hash)].kind,Now,NextState),file=sys.stderr)
        else : 
            print("異常な遷移{}:{}→{}".format(NodeInfo[str(Hash)].kind,Now,NextState),file=sys.stderr)
    elif Now == "WaitingProvDrops": 
        if NextState == "AtTopOfPlacedMixer":
            if ModuleKind == "Mixer" and (Hash in WaitingProvDrops): 
                NodeInfo[str(Hash)].state = NextState 
                return [Hash,[Now,NextState]]
            else :
                print("異常な遷移{}:{}→{}".format(NodeInfo[str(Hash)].kind,Now,NextState),file=sys.stderr)
        elif NextState == "NoTreatment":
            if Hash in WaitingProvDrops:
                NodeInfo[str(Hash)].state = NextState 
                return [Hash,[Now,NextState]]
            else :
                print("異常な遷移{}:{}→{}".format(NodeInfo[str(Hash)].kind,Now,NextState),file=sys.stderr)
        else : 
            print("異常な遷移{}:{}→{}".format(NodeInfo[str(Hash)].kind,Now,NextState),file=sys.stderr)
    elif Now == "OnlyProvDrop": 
        if NextState == "Done":
            if Hash in OnlyProvDrop: 
                NodeInfo[str(Hash)].state = NextState 
                return [Hash,[Now,NextState]]
            else : 
                print("{}の異常な遷移{}:{}→{}".format(Hash,NodeInfo[str(Hash)].kind,Now,NextState),file=sys.stderr)
        elif NextState == "NoTreatment":
            if Hash in OnlyProvDrop: 
                NodeInfo[str(Hash)].state = NextState 
                return [Hash,[Now,NextState]]
            else : 
                print("{}の異常な遷移{}:{}→{}".format(Hash,NodeInfo[str(Hash)].kind,Now,NextState),file=sys.stderr)
    elif Now == "PlacementSkipped": 
        if NextState == "AtTopOfPlacedMixer": 
            if ModuleKind == "Mixer": 
                NodeInfo[str(Hash)].state = NextState 
                return [Hash,[Now,NextState]]
            else : 
                print("異常な遷移{}:{}→{}".format(NodeInfo[str(Hash)].kind,Now,NextState),file=sys.stderr)
        elif NextState == "OnlyProvDrop":
            if ModuleKind == "Reagent":
                NodeInfo[str(Hash)].state = NextState 
                return [Hash,[Now,NextState]]
            else : 
                print("異常な遷移{}:{}→{}".format(NodeInfo[str(Hash)].kind,Now,NextState),file=sys.stderr) 
        elif NextState == "NoTreatment": 
            NodeInfo[str(Hash)].state = NextState 
            return [Hash,[Now,NextState]]
        elif NextState ==  "PlacementSkipped": 
            return [Hash,[Now,NextState]]
        else : 
            print("異常な遷移{}:{}→{}".format(NodeInfo[str(Hash)].kind,Now,NextState),file=sys.stderr)
    elif Now == "Done": 
        if NextState == "NoTreatment":
            NodeInfo[str(Hash)].state = NextState 
            return [Hash,[Now,NextState]]
        else : 
            print("異常な遷移{}:{}→{}".format(NodeInfo[str(Hash)].kind,Now,NextState),file=sys.stderr)
    else : 
        print("異常な遷移{}:{}→{}".format(NodeInfo[str(Hash)].kind,Now,NextState),file=sys.stderr)

def ReflectStateChanges(StateChanges): 
    global AtTopOfPlacedMixer,WaitingProvDrops,OnlyProvDrop,PlacementSkipped,Done 
    for Hash,stateChange in StateChanges: 
        if Hash == -1 and not stateChange: 
            return -1
        Now,NextState = stateChange
        if Now == "NoTreatment": 
            if NextState == "AtTopOfPlacedMixer": 
                AtTopOfPlacedMixer.append(Hash)
            elif NextState == "OnlyProvDrop": 
                OnlyProvDrop.append(Hash)
            elif NextState == "PlacementSkipped": 
                PlacementSkipped.append(Hash)
        elif Now == "WaitingProvDrops": 
            if NextState == "AtTopOfPlacedMixer":
                WaitingProvDrops.remove(Hash) 
                AtTopOfPlacedMixer.append(Hash)
            elif NextState == "NoTreatment": 
                WaitingProvDrops.remove(Hash) 
        elif Now == "AtTopOfPlacedMixer": 
            if NextState == "WaitingProvDrops": 
                AtTopOfPlacedMixer.remove(Hash)
                WaitingProvDrops.append(Hash)
            elif NextState == "OnlyProvDrop": 
                AtTopOfPlacedMixer.remove(Hash)
                OnlyProvDrop.append(Hash)
            elif NextState == "NoTreatment": 
                AtTopOfPlacedMixer.remove(Hash)
        elif Now == "PlacementSkipped": 
            if NextState == "AtTopOfPlacedMixer": 
                PlacementSkipped.remove(Hash)
                AtTopOfPlacedMixer.append(Hash)
            elif NextState == "OnlyProvDrop": 
                PlacementSkipped.remove(Hash)
                OnlyProvDrop.append(Hash)
            elif NextState =="NoTreatment": 
                PlacementSkipped.remove(Hash)
        elif Now == "OnlyProvDrop": 
            if NextState == "Done":
                OnlyProvDrop.remove(Hash) 
                Done.append(Hash)
            elif NextState == "NoTreatment": 
                OnlyProvDrop.remove(Hash) 
        elif Now == "Done":
            if NextState =="NoTreatment": 
                Done.remove(Hash)
    return 0


def PlaceChildren(ParentMixerHash): 
    global NodeInfo,PMDState,PlacementSkippedLib
    StateChanges = [ChangeState(ParentMixerHash,"WaitingProvDrops")]
    ParentMixer = getNode(ParentMixerHash)
    PMAllCell = getMixerCoveringCell(ParentMixer.RefCell,ParentMixer.orientation)
    WritePMD(PMAllCell,0)
    
    lib = getOptlib(ParentMixerHash)
    if not lib : 
        StateChanges.append([-1,[]])
        return StateChanges
    Hashlib = getHashlib(lib)
    MoreStateChanges,RestOflib = placelib(Hashlib,ParentMixerHash)
    ### 配置しきれなかったなら,
    if RestOflib: 
        PlacementSkippedLib.append([ParentMixerHash,RestOflib])
    for Change in MoreStateChanges: 
        StateChanges.append(Change)
    return StateChanges

def NoOverlapping(pattern): 
    global PMDState,CellForProtectFromFlushing 
    Module = getNode(pattern["hash"])
    ParentMixerHash = Module.ParentHash 
    Cells = []
    if Module.kind == "Mixer": 
        orientation = ""
        if "orientation" in pattern :
            orientation = pattern["orientation"]
        Cells = getMixerCoveringCell(pattern["ref_cell"],orientation)
    else : 
        Cells = pattern["overlapping_cell"]
    for y,x in Cells: 
        if PMDState[y][x]!=0 and PMDState[y][x]!=ParentMixerHash: 
            return False 
    return True

def placelib(Hashlib,ParentMixerHash): 
    global MaxLayerNum,CellForProtectFromFlushing,TimeStep
    retHashlib = {}
    StateChanges = []
    skip = False 
    PlacementOrder = copy.deepcopy(getNode(ParentMixerHash).ChildrenHash)
    for ModuleHash in PlacementOrder: 
        if str(ModuleHash) in Hashlib:
            pattern = Hashlib[str(ModuleHash)]
            if not skip and NoOverlapping(pattern):
                # 試薬液滴
                if getNode(ModuleHash).kind == "Reagent": 
                    NodeInfo[str(ModuleHash)].PlaceTimeStep = TimeStep+1
                    WritePMD(pattern["overlapping_cell"],ModuleHash*-1)
                    ### 試薬はフラッシュから守る必要あり
                    for cell in pattern["overlapping_cell"]:
                        CellForProtectFromFlushing.append(cell)
                    WritePlacementInfo(pattern,ModuleHash)
                    stateChange = ChangeState(ModuleHash,"OnlyProvDrop")
                    StateChanges.append(stateChange) 
                else : 
                    orientation = ""
                    if "orientation" in pattern :
                        orientation = pattern["orientation"]
                    WritePMD(getMixerCoveringCell(pattern["ref_cell"],orientation),ModuleHash)
                    stateChange = ChangeState(ModuleHash,"AtTopOfPlacedMixer")
                    WritePlacementInfo(pattern,ModuleHash)
                    StateChanges.append(stateChange) 
            else: 
                skip = True 
                WritePlacementInfo(pattern,ModuleHash)
                retHashlib[str(ModuleHash)] = pattern
                stateChange = ChangeState(ModuleHash,"PlacementSkipped")
                StateChanges.append(stateChange) 
    if not retHashlib:
        return StateChanges,{}
    return StateChanges,retHashlib
 
from .utility import PMDImage
### lib内のパターンは評価の際に対応するハッシュ値をパッキングする．
### 使用するlibが決定した際に，refCellなどをNodeInfo に書き込む
### ParentMixer = str(mixer.size) + mixer.orientation
CntRollBack = 0
Vsize,Hsize=0,0
RollBackHash=[]
TimeStep = 0 
def xntm(root,PMDsize,ColorList,ProcessOut=0,ImageName="",ImageOut=False):
    global PMDState,NodeInfo,PlacementSkipped,OnlyProvDrop,WaitingProvDrops,AtTopOfPlacedMixer,CellForFlushing,CellForProtectFromFlushing,Done,Vsize,Hsize,PlacementSkippedLib,CntRollBack,RollBackHash,TimeStep
    Vsize,Hsize = PMDsize 
    FlushCount,ImageCount,TimeStep = 0,0,0
    globalInit()
    
    ### placement of root mixer
    RefCell = [(Vsize-1)//2,(Hsize-1)//2]
    RootHash = PMDRootPlace(root,RefCell)
    NodeInfoInit(root) 

    while PlacementSkipped or WaitingProvDrops or AtTopOfPlacedMixer or OnlyProvDrop:
        StateChanges = []
        if ImageName and ColorList:
            ImageCount += 1
            imageName = ImageName+"_"+str(ImageCount)
            PMDImage(imageName,ColorList,TimeStep,Vsize,Hsize,PMDState,NodeInfo,AtTopOfPlacedMixer=AtTopOfPlacedMixer,WaitingProvDrops=WaitingProvDrops,ImageOut=ImageOut)
        
        if getNode(RootHash).state == "OnlyProvDrop": 
            if ProcessOut :
                print("混合手順生成完了")
            result = CountFlushing(RootHash,ImageName,ColorList,ImageOut=ImageOut)
            return result

        CannotDoAnything = True 

        for MixerHash in AtTopOfPlacedMixer: 
            mixer = getNode(MixerHash) 
            shouldPlaceChildren = True
            for ChildHash in mixer.ChildrenHash:
                if getNode(ChildHash).state != "NoTreatment": 
                   shouldPlaceChildren = False
            if shouldPlaceChildren: 
                CannotDoAnything = False
                MoreStateChanges = PlaceChildren(MixerHash)
                for Change in MoreStateChanges: 
                    StateChanges.append(Change)
            else : 
                continue 

        for MixerHash in WaitingProvDrops:
            isDropsProvidedByChildrenReady = True 
            for ChildHash in getNode(MixerHash).ChildrenHash: 
                if getNode(ChildHash).state != "OnlyProvDrop": 
                    isDropsProvidedByChildrenReady = False
            if isDropsProvidedByChildrenReady : 
                CannotDoAnything = False
                stateChange = ChangeState(MixerHash,"AtTopOfPlacedMixer")
                StateChanges.append(stateChange)

        ChangedTimeStep = False 
        if CannotDoAnything: 
            for MixerHash in AtTopOfPlacedMixer: 
                mixer = getNode(MixerHash) 
                isReadyForMixing = True
                for ChildHash in mixer.ChildrenHash:
                    if getNode(ChildHash).state != "OnlyProvDrop": 
                       isReadyForMixing = False 
                if isReadyForMixing : 
                    CannotDoAnything = False 
                    if not ChangedTimeStep: 
                        ChangedTimeStep = True 
                        TimeStep += 1
                    MoreStateChanges = Mixing(MixerHash)
                    for Change in MoreStateChanges: 
                        StateChanges.append(Change)
                else : 
                    continue 

        if CannotDoAnything: 
            ### Flushing
            Succeed = Flush()
            if not Succeed: 
                if ProcessOut:
                    print("十分な大きさのPMDを用意してください.",file=sys.stderr)
                return -1
            else : 
                FlushCount += 1
            ### 配置をスキップされていたミキサーや試薬の配置 
            PlacedSkipped = 0
            Rest = []
            Remove = []
            for LibInfo in reversed(PlacementSkippedLib): 
                Remove.append(LibInfo)
                ParentMixerHash,Lib = LibInfo
                PMixer = getNode(ParentMixerHash)
                TimeToPlace = True
                for CHash in PMixer.ChildrenHash: 
                    CMixer = getNode(CHash)
                    if CMixer.state != "OnlyProvDrop" and CMixer.state != "PlacementSkipped":
                        TimeToPlace = False
                if not TimeToPlace: 
                    Rest.append(LibInfo)
                    continue 
                else : 
                    MoreStateChanges,RestOfLib =  placelib(Lib,ParentMixerHash)
                    if Lib == RestOfLib and not PlacedSkipped : 
                        if ParentMixerHash not in RollBackHash  : 
                            MoreStateChanges = RollBack(ParentMixerHash)
                            for Change in MoreStateChanges: 
                                StateChanges.append(Change)
                            if len(RollBackHash)==2:
                                RollBackHash.pop(0)
                            RollBackHash.append(ParentMixerHash)
                            CntRollBack += 1
                        else : 
                            return -1
                    else : 
                        for change in MoreStateChanges: 
                            StateChanges.append(change)
                        PlacedSkipped = ParentMixerHash
                        if RestOfLib: 
                            Rest.append([ParentMixerHash,RestOfLib])
            for garbage in Remove: 
                PlacementSkippedLib.remove(garbage)
            for rest in Rest: 
                PlacementSkippedLib.append(rest)

        code = ReflectStateChanges(StateChanges)
        if code == -1 or CntRollBack > 100 or FlushCount>1000:
            if ProcessOut:
                print("扱えない希釈木です．十分な大きさのPMDを用意しているか確認してください．",file=sys.stderr)
            return -1
        
        if ProcessOut:
            viewAllModule(RootHash)
            print(StateChanges)
            print("AtTopOfPlacedMixer",AtTopOfPlacedMixer)
            print("WaitingProvDrops",WaitingProvDrops)
            print("OnlyProvDrop",OnlyProvDrop)
            print("PlacementSkipped",PlacementSkipped)
            print("Done",Done)
            viewPMD()
