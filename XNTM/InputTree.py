HASHES = []
import random 
### 入力の希釈木を生成
class TreeNode: 
    def __init__(self,size,ProvSize,isMixer,name=""): 
        self.children = []
        self.hash = random.randint(1,10010)
        while(self.hash in HASHES): 
            self.hash = random.randint(1,10010)
        HASHES.append(self.hash)
        self.size = size 
        self.isMixer = isMixer
        self.name = name
        self.ProvSize = ProvSize

MixerSize = [6,4]
def genMixerNode(ProvSize,Forced = 0): 
    global MixerSize 
    Msize = -1
    while(ProvSize>=Msize):
        ret = random.choice(MixerSize) 
        Msize = ret 
    if Forced: 
        Msize = Forced
    return TreeNode(Msize,ProvSize,True)

def genReagentNode(Provsize,name): 
    Rsize = Provsize 
    return TreeNode(Rsize,Rsize,False,name=name) 

def genProvidedRatio(Msize): 
    rest = Msize 

    Ratio = []
    First = random.randint(1,rest-1)
    Ratio.append(First)
    rest -= First

    while rest: 
        v = random.randint(1,rest)
        rest -= v
        Ratio.append(v)
    return Ratio

def AllReagentUsed(Dict): 
    global ReagentName 
    for name in ReagentName : 
        if name not in Dict : 
            return False 
    return True 

def MergeDrop(name,Dict,DropSize): 
    global AllModules
    HashAdded = Dict[name] 
    return [HashAdded,DropSize] 

def ProcessMergeQuery(MergeQuery): 
    global AllModules 
    for hash,size in MergeQuery: 
        AllModules[str(hash)].ProvSize += size
        AllModules[str(hash)].size += size

def ConstructList(hash): 
    global AllModules 
    module = AllModules[str(hash)]
    if module.isMixer: 
        ret = []
        ratio = tuple()
        for CHash in module.children: 
            prov = AllModules[str(CHash)].ProvSize
            ratio += tuple([prov])
            content = ConstructList(CHash)
            ret.append(content)
        ret.insert(0,ratio)
        return ret 
    else : 
        return module.name 

def CornerCase(modules,ProvRatio): 
    if modules == [True,True] and ProvRatio == [3,3]:
        return 6
    return 0
        
ReagentName = []
AllModules = {}
def genInputTree(MaxHeight,MixerRatio,ReagentKind): 
    global HASHES,AllModules,ReagentName
    for i in range(1,ReagentKind+1): 
        ReagentName.append("R"+str(i))
    AllModules = {}
    
    max_height = 0
    root = genMixerNode(0)  
    q = []
    MergeQuery = []
    q.append([root,0])
    while(q): 
        e,height = q.pop(0)
        AllModules[str(e.hash)] = e 
        if height > max_height: 
            max_height = height
        if e.isMixer: 
            ProvRatio = genProvidedRatio(e.size)
            IsMixr = [True,False]
            ratio = [MixerRatio,1-MixerRatio]
            ChildModules = random.choices(IsMixr,weights=ratio,k=len(ProvRatio))
            ProvReagent = {}
            for idx,isMixer in enumerate(ChildModules): 
                if isMixer and height < MaxHeight : 
                    Corner = CornerCase(ChildModules,ProvRatio)
                    if not Corner : 
                        mixer = genMixerNode(ProvRatio[idx])
                        e.children.append(mixer.hash)
                        q.append([mixer,height+1])
                    else : 
                        mixer = genMixerNode(ProvRatio[idx],Forced=Corner)
                        e.children.append(mixer.hash)
                        q.append([mixer,height+1])

                else: 
                    name = random.choice(ReagentName)
                    if name in ProvReagent: 
                        if AllReagentUsed(ProvReagent): 
                            query = MergeDrop(name,ProvReagent,ProvRatio[idx])
                            MergeQuery.append(query)
                            continue
                        else : 
                            while name in ProvReagent : 
                                name = random.choice(ReagentName)
                    reagent = genReagentNode(ProvRatio[idx],name)
                    ProvReagent[name] = reagent.hash
                    e.children.append(reagent.hash)
                    q.append([reagent,height+1])
    ProcessMergeQuery(MergeQuery)

    ret = ConstructList(root.hash)
    return [max_height,ret] 


