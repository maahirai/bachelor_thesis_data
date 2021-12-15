import json
import copy
import itertools
import sys
import datetime
from pathlib import Path

Mixer = ['6h','6v','4']
Module = ['6h','6v','4','r1','r2','r3','r4','r5']
GridSize = 7

def Msize(M):
    Malt = ["6h","6v","4"]
    size = [[2,3],[3,2],[2,2]]
    
    idx = -1
    for i in range(len(Malt)):
        if Malt[i] == M:
            idx = i
    if idx == -1:
        if M[-1:]=="r":
            return int(M[:-1])
        else :
            print("unexpected input!! in Msize()",file=sys.stderr)
    else : return size[idx]

def numCells(M):
    size = Msize(M)
    ret = 1
    for length in size:
        ret *= length
    return ret 

def gengrid(M):
    grid = [[-1 for h in range(GridSize)]for v in range(GridSize)]
    ParentSize = Msize(M)
    hs,vs = ParentSize
    
    ref_x,ref_y = 2,2 
    for i in range(hs):
        for j in range(vs):
            grid[i+ref_y][j+ref_x] = 0
    return grid

def rootAllCell(M):
    ret = []
    grid = gengrid(M)
    for i in range(GridSize):
        for j in range(GridSize):
            if grid[i][j] == 0:
                ret.append([i,j])
    return ret

### for debugging and checking the generated pattern
def showGrid(grid):
    for y in range(GridSize):
        for x in range(GridSize):
            print("%2d"%(grid[y][x]),end=" ")
        print("\n")

   
def getProvRatio():
    prov_ratio = {}
    ### generate ratio of droplets providing to parent mixer
    for pm in range(len(Mixer)):
        PM = Mixer[pm]
        PMsize = int(PM[0])
        prov_ratio[PM] = []
        q = []
        for i in range(1,6):
            q.append([i])
        while q:
            e = q.pop()
            for i in range(1,6):
                Sum = sum(e)
                nSum = i+Sum
                if nSum > PMsize:
                    continue
                elif nSum == PMsize:
                    ne = copy.deepcopy(e)
                    ne.append(i)
                    insert = sorted(ne,reverse=True)
                    if insert not in prov_ratio[PM]:
                        prov_ratio[PM].append(insert)
                else :
                    ne = copy.deepcopy(e)
                    ne.append(i)
                    q.append(ne)
        #print(prov_ratio[PM],end="\n"*2)
    return prov_ratio

def CanLeftDropPlace(placement,condition):
    search_cell = copy.deepcopy(placement["overlapping_cell"])
    if "flushing_cell" in placement :
        search_cell += placement["flushing_cell"] 
    empty_cell = condition[0][0]
    for cell in search_cell:
        if cell not in empty_cell:
            return False
    return True
    
def LeftDropPlace(placement,condition):
    cells = placement["overlapping_cell"]
    new_condition = copy.deepcopy(condition)

    for cell in cells:
        if cell not in new_condition[0][0]:
            print("error : LeftDropPlace()セルが空いてない!!")
            return -1
        else :
            new_condition[0][0].remove(cell)
            new_condition[0][1].append(cell)
    new_condition[1].append(cells)
    return new_condition
 
def genTemplate(pattern):
    #print(pattern)
    template = {}
    for pm in range(len(Mixer)):
        PM = Mixer[pm]
        template[PM] = {}
        prov_ratio = getProvRatio()
        for ratio in prov_ratio[PM]:
            buffer = [[] for i in range(len(ratio)+1)]
            start = [[rootAllCell(PM),[]],[]]
            buffer[0].append(start)
            
            if numCells(PM) in ratio:
                return
            for idx,num in enumerate(ratio):
                for condition in buffer[idx]:
                    drop = "r"+str(num)
                    for placement in pattern[PM][drop][str(num)]:
                        if CanLeftDropPlace(placement,condition):
                            next_condition = LeftDropPlace(placement,condition)
                            #print(condition,placement,next_condition,sep='\n')
                            buffer[idx+1].append(next_condition)
                #print("\n")
            
            for data in buffer[len(ratio)]:
                if str(ratio) not in template[PM]:
                    template[PM][str(ratio)]=[]
                template[PM][str(ratio)].append(data[1])
            for i in buffer[len(ratio)][1]:
                if not i:
                    print("なんでやねん")
                    return -1
    return template

def showColoredTemplate(prov_ratio,template):
    for pm in range(len(Mixer)):
            PM = Mixer[pm]
            for ratio in prov_ratio[PM]:
                cnt = 0
                for temp in template[PM][str(ratio)]:
                    cnt +=1
                    grid = gengrid(PM)
                    for idx,group in enumerate(temp):
                        for cell in group :
                            color = idx+1
                            y,x = cell
                            grid[y][x] = color
                    print(PM,ratio,sep='\t')
                    showGrid(grid)
                print(PM,ratio,cnt,sep='\t')

def search_placement(pattern,PM,module,drop):
    cnt_drop = len(drop)
    return pattern[PM][module][str(cnt_drop)]
    
def getModule(module):
    FirstLetter = ['6','4','r']
    for i in range(len(FirstLetter)):
        if FirstLetter[i] == module[0]:
            return FirstLetter[i]
    return -1

def main():
    start = datetime.datetime.now()
    readfile = open('XNTM/data/placement.json','r')
    pattern = json.load(readfile)
    prov_ratio = getProvRatio()
    ### generate the combination of placements of dropret left by children-mixers
    template = genTemplate(pattern)
    ### generate library of placement of children-mixers
    lib = {}
    for pm in range(len(Mixer)):
        PM = Mixer[pm]
        lib[PM] = {}
        for ratio in prov_ratio[PM]:
            lib[PM][str(ratio)] = {}
            RatioOrderedCombos = template[PM][str(ratio)]
            for RatioOrderedCombo in RatioOrderedCombos:
                PermuCombo = list(itertools.permutations(RatioOrderedCombo,len(RatioOrderedCombo)))
                for combo in PermuCombo:
                #for combo in RatioOrderedCombo:
                    buffer = [[] for i in range(len(ratio)+1)]
                    ### [[[配置した6ミキサー],[配置した4ミキサー],[配置した試薬液滴]],[試薬液滴を残せるセル],[レイヤーの確認の為のgrid]]
                    buffer[0].append({"Module":{"6":[],"4":[],"r":[]},"CannotPlace":[],"Layer":gengrid(PM)})
                    for idx,DropsLeftByAModule in enumerate(combo):
                        for buff in buffer[idx]:
                        ### DropsLeftByAModuleをFlush後に残すモジュールをbuffer[idx]に追加し，buffer[idx+1]に書き込み
                            for module in range(len(Module)) :
                                MODULE = Module[module]
                                if str(len(DropsLeftByAModule)) in pattern[PM][MODULE]:
                                    for candidate in pattern[PM][MODULE][str(len(DropsLeftByAModule))]:
                                        if candidate["overlapping_cell"] == DropsLeftByAModule:
                                            ### check whether the module overlapps droplets left by mixers that placed formerly
                                            passing = True
                                            check_cells = candidate["flushing_cell"]
                                            for check_cell in check_cells:
                                                if check_cell in buff["CannotPlace"]:
                                                    passing = False
                                            if passing :
                                                new_buff = copy.deepcopy(buff)
                                                layer = 1
                                                layer_search_cells = candidate["flushing_cell"]+candidate["overlapping_cell"]
                                                for layer_search_cell in layer_search_cells:
                                                    y,x = layer_search_cell
                                                    layer = max(layer,buff["Layer"][y][x]+1)
                                                for y,x in layer_search_cells:
                                                    new_buff["Layer"][y][x] = layer
                                                for y,x in candidate["overlapping_cell"]:
                                                    new_buff["CannotPlace"].append([y,x])
                                                AddedModule = copy.deepcopy(candidate)
                                                AddedModule["layer"] = layer
                                                if getModule(MODULE) == '6':
                                                    AddedModule["orientation"] = MODULE[-1:]
                                                new_buff["Module"][getModule(MODULE)].append(AddedModule)
                                                buffer[idx+1].append(new_buff)
                    if buffer[len(ratio)]:
                        for data in buffer[len(ratio)]:
                            modulecnt = [0,0,0]
                            ModuleFirstC = ["6","4","r"]
                            for idx,fc in enumerate(ModuleFirstC):
                                modulecnt[idx] += len(data["Module"][ModuleFirstC[idx]])
                            del data["Layer"]
                            del data["CannotPlace"]
                            if str(modulecnt) not in lib[PM][str(ratio)]:
                                lib[PM][str(ratio)][str(modulecnt)] = []
                            lib[PM][str(ratio)][str(modulecnt)].append(data)
                    else :
                        print("ホンマ，ありえへんてぇ~!! in genlib.py",file=sys.stderr)
                    

    ### output lib to json file
    with open("XNTM/data/data/lib.json","w") as f:
        json.dump(lib,f,indent=4)  

    end = datetime.datetime.now()
    diff = end-start
    print("実行時間 = end - start = {} - {} = {}".format(end,start,diff))

if __name__ == '__main__':
    main()
