import json
import copy
import itertools
import sys
import datetime
from pathlib import Path

Mixer = ['6h','6v','4']
Module = ['6h','6v','4','r1','r2','r3','r4','r5']
GridSize = 7

def keystr(s):
    S = str(s)
    return S.replace(" ","")

def Msize(M):
    Malt = ["6h","6v","4"]
    size = [[2,3],[3,2],[2,2]]
    
    idx = -1
    for i in range(len(Malt)):
        if Malt[i] == M:
            idx = i
    if idx == -1:
        if M[0]=="r":
            return int(M[1:])
        else :
            print("unexpected input!! in Msize()",file=sys.stderr)
    else : 
        return size[idx]

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
    prov_ratio = getProvRatio()
    for pm in range(len(Mixer)):
        PM = Mixer[pm]
        template[PM] = {}
        for ratio in prov_ratio[PM]:
            buffer = [[] for i in range(len(ratio)+1)]
            # [[[残っているセル]，[占拠されたセル]],[一回の配置で占拠されるセルの組]]
            start = [[rootAllCell(PM),[]],[]]
            buffer[0].append(start)
            
            # すべての提供液滴が1つのモジュールから提供されてる場合()
            if numCells(PM) in ratio:
                print("バグってるやん，ソレイ")
                return
            for idx,num in enumerate(ratio):
                for condition in buffer[idx]:
                    drop = "r"+keystr(num)
                    for placement in pattern[PM][drop][keystr(num)]:
                        if CanLeftDropPlace(placement,condition):
                            next_condition = LeftDropPlace(placement,condition)
                            #print(condition,placement,next_condition,sep='\n')
                            buffer[idx+1].append(next_condition)
                #print("\n")
            
            for data in buffer[len(ratio)]:
                if keystr(ratio) not in template[PM]:
                    template[PM][keystr(ratio)]=[]
                data[1] = sorted(data[1])
                if data[1] not in template[PM][keystr(ratio)]:
                    template[PM][keystr(ratio)].append(data[1])
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
                for temp in template[PM][keystr(ratio)]:
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

def getModule(module):
    FirstLetter = ['6','4','r']
    for i in range(len(FirstLetter)):
        if FirstLetter[i] == module[0]:
            return FirstLetter[i]
    return -1

def main():
    start = datetime.datetime.now()
    readfile = open('XNTM/data/PlacementChild.json','r',encoding='utf-8')
    pattern = json.load(readfile)
    readfile.close()

    WriteFile = open('XNTM/data/prov_ratio.json','w',encoding='utf-8')
    prov_ratio = getProvRatio()
    json.dump(prov_ratio,WriteFile,separators=(',', ':'))  
    WriteFile.close()

    ### generate the combination of placements of dropret left by children-mixers
    readfile = open('XNTM/data/prov_ratio.json','r',encoding='utf-8')
    prov_ratio = json.load(readfile)
    readfile.close()
    WriteFile = open('XNTM/data/PlacementProvDrops.json','w',encoding='utf-8')
    template = genTemplate(pattern)
    json.dump(template,WriteFile,separators=(',', ':'))  
    WriteFile.close()
    

if __name__ == '__main__':
    main()
