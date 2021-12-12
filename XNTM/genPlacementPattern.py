import json
import sys
import copy

GridSize = 7
def gengrid(M):
    grid = [[-1 for h in range(GridSize)]for v in range(GridSize)]
    ParentSize = Msize(M)
    hs,vs = ParentSize
    
    ref_x,ref_y = 2,2 
    for i in range(hs):
        for j in range(vs):
            grid[i+ref_y][j+ref_x] = 0
    return grid

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

def IntermediateCells(cells):
    l = copy.deepcopy(cells) 
    ret = []
    for i in range(len(l)):
        y,x = l[i]
        if [y-1,x] in l and [y+1,x] in l:
            ret.append(l[i])
        elif [y,x-1] in l and [y,x+1] in l:
            ret.append(l[i])
        else :
            continue
    return ret

### for debugging and checking the generated pattern
def showGrid(grid):
    for y in range(GridSize):
        for x in range(GridSize):
            print("%2d"%(grid[y][x]),end=" ")
        print("\n")

def numCells(M):
    size = Msize(M)
    ret = 1
    for length in size:
        ret *= length
    return ret 

def main():
    Mixer = ["6h","6v","4"]
    Reagent = ["1r","2r","3r","4r","5r"]
    res = {}
    cnt_pattern = 0
    ### generating patterns that contains no flushing
    for p in range(len(Mixer)):
        pM = Mixer[p]
        psize = Msize(pM)
        res[pM] = {}
        for c in range(len(Mixer)):
            cM = Mixer[c]
            csize = Msize(cM)
            cheight,cwidth = csize
            res[pM][cM]={}
            for ref_y in range(GridSize):
                for ref_x in range(GridSize):
                    ref_cell = [ref_y,ref_x]
                    right_end = ref_x + cwidth -1
                    lower_end = ref_y + cheight -1
                    if right_end < GridSize and lower_end < GridSize :
                        grid = gengrid(pM)
                        leftdrop = []
                        cnt = 0
                        for y in range(ref_y,lower_end+1):
                            for x in range(ref_x,right_end+1):
                                ### cells that overlapps the parentmixer
                                if grid[y][x] == 0:
                                    cnt += 1
                                    leftdrop.append([y,x])
                                grid[y][x]= 1
                        if cnt >0 :
                            if str(cnt) not in res[pM][cM]:
                                res[pM][cM][str(cnt)] = []
                            ### the second empty list means there's no need of immediate flushing for the subsequent placement
                            inserted_data = {"ref_cell":ref_cell,"overlapping_cell":leftdrop,"flushing_cell":[]}
                            res[pM][cM][str(cnt)].append(inserted_data)
                            cnt_pattern += 1
                            print("psize:{},csize:{}".format(psize,csize))
                            print("cnt:{}".format(cnt))
                            print("(ref_y,ref_x):{}".format((ref_y,ref_x)))
                            #showGrid(grid) 
    print("sum of number of no flushing patterns in placements of a overlappinng mixer on a mixer : {}".format(cnt_pattern))
    for i in range(len(Mixer)):
        c = 0
        for j in range(len(Mixer)):
            tmp = 0
            for cnt in range(7):
                if str(cnt) in res[Mixer[i]][Mixer[j]] :
                    c += len(res[Mixer[i]][Mixer[j]][str(cnt)])
                    tmp += len(res[Mixer[i]][Mixer[j]][str(cnt)])
            print("parent - child : {} - {} ,count {}".format(Mixer[i],Mixer[j],tmp))
        print("parent mixer : {} ,sum of count : {}".format(Mixer[i],c))
    ### generating patterns that contains flushing
    for p in range(len(Mixer)):
        for c in range(len(Mixer)):
            ### p-cのペアごとに纏めてresに追加
            res_buffer = {Mixer[p]:{Mixer[c]:{}}}
            for cnt in range(7):
                if str(cnt) in res[Mixer[p]][Mixer[c]]:
                    NoFlushingPatterns = copy.deepcopy(res[Mixer[p]][Mixer[c]][str(cnt)])
                    for item in NoFlushingPatterns:
                        if item["flushing_cell"] == [] :
                            if len(item["overlapping_cell"])==1:
                                continue
                            alt = copy.deepcopy(item["overlapping_cell"])
                            ### 単体だけのflushは出来ないcell
                            rmalt = IntermediateCells(alt)
                            for i in range(2**len(alt)):
                                DropLeftCells = []
                                FlushCells = []
                                skip = False
                                for d in range(len(alt)):
                                    if (i & (1<<d)):
                                        DropLeftCells.append(alt[d])
                                    else :
                                        FlushCells.append(alt[d])
                                if len(DropLeftCells)==len(alt) or len(FlushCells)==len(alt):
                                    continue
                                for j in range(len(rmalt)):
                                    if rmalt[j] in FlushCells:
                                        isBad = True
                                        dx = [-1,1,0,0]
                                        dy = [0,0,1,-1]
                                        y,x = rmalt[j]
                                        for way in range(4):
                                           neighbor = [y+dy[way],x+dx[way]]
                                           if neighbor in FlushCells:
                                                isBad = False
                                        if isBad :
                                            ### skip i-th loop
                                            skip = True
                                if skip :
                                    #print(DropLeftCells,FlushCells,sep='\t')
                                    grid = gengrid(Mixer[p])
                                    for sy in range(GridSize):
                                        for sx in range(GridSize):
                                            if [sy,sx] in DropLeftCells:
                                                grid[sy][sx] = 1
                                            if [sy,sx] in FlushCells:
                                               grid[sy][sx] = 0 
                                    #showGrid(grid)
                                    continue
                                else :
                                    snumLeftDrops = str(len(DropLeftCells))
                                    if snumLeftDrops not in res_buffer[Mixer[p]][Mixer[c]]:
                                        res_buffer[Mixer[p]][Mixer[c]][snumLeftDrops] = []

                                    inserted_data = {"ref_cell":item["ref_cell"],"overlapping_cell":DropLeftCells,"flushing_cell":FlushCells}
                                    res_buffer[Mixer[p]][Mixer[c]][snumLeftDrops].append(inserted_data)
                        else :
                            print("You must debug it!!")
                            return
                else :
                    continue
            #print(res_buffer[Mixer[p]][Mixer[c]])
            cnt_flushpattern = 0
            for cnt in range(7):
                if str(cnt) in res_buffer[Mixer[p]][Mixer[c]]:
                    for insert in res_buffer[Mixer[p]][Mixer[c]][str(cnt)]:
                        if str(cnt) not in res[Mixer[p]][Mixer[c]] :
                            res[Mixer[p]][Mixer[c]][str(cnt)] = []
                        ### print(insert)
                        res[Mixer[p]][Mixer[c]][str(cnt)].append(insert)
                        cnt_pattern += 1
                        cnt_flushpattern += 1
            print("parent - child : {} - {},cnt_needflush :{}".format(Mixer[p],Mixer[c],cnt_flushpattern))       
    print("sum of number of need flushing patterns in placements of a overlappinng mixer on a mixer : {}".format(cnt_pattern))

    ### generating patterns of placement of drop on mixer
    res_buffer_r = {}
    cnt = [0 for i in range(6)]
    cntperPM = [0 for i in range(len(Mixer))]
    for pm in range(len(Mixer)):
        PM = Mixer[pm]
        res_buffer_r[PM] = {} 

        grid = gengrid(PM)
        PMCells = []
        for y in range(GridSize):
            for x in range(GridSize):
                if grid[y][x] == 0:
                    cell = [y,x]
                    PMCells.append(cell)

        q = []
        dx = [-1,1,0,0]
        dy = [0,0,1,-1]
        for cell in PMCells:
            cells = [cell]
            q.append(cells)
            print(q)

        ### generate r on M patterns with BFS
        while q:
            r = q.pop(0)
            rSize = len(r)
            if rSize < numCells(PM):
                if str(rSize) not in res_buffer_r[PM]:
                    res_buffer_r[PM][str(rSize)] = []
                insert_data = sorted(r)
                if insert_data not in res_buffer_r[PM][str(rSize)]:
                    res_buffer_r[PM][str(rSize)].append(insert_data)

                taili = rSize-1
                tail = r[taili]
                y,x = tail
                for way in range(4):
                    neighbor = [y+dy[way],x+dx[way]]
                    if (neighbor in PMCells) and (neighbor not in r):
                        nr = copy.deepcopy(r)
                        nr.append(neighbor)
                        q.append(nr)
            else :
                continue
        

        for n in range(6):
            if str(n) in res_buffer_r[PM]:
                module_name = "r"+str(n)
                res[PM][module_name] = []
                for pattern in res_buffer_r[PM][str(n)]:
                    res[PM][module_name].append(pattern)
                    grid = gengrid(PM)
                    for i in range(GridSize):
                        for j in range(GridSize):
                            if [i,j] in pattern:
                                grid[i][j] = 1
                    print(pattern)
                    showGrid(grid)
                    cnt[n] += 1
                    cntperPM[pm] += 1
                    cnt_pattern += 1
        #print("PM当たりのパターン: {}".format(cntperPM[pm]))    
        print("all_patterns : {}".format(cnt_pattern))

        print(res)
    #print(res)
    return
    with open("placement.json","w"):
        str_res = json.dumps(res) 
    
if __name__ == "__main__":
    main()
