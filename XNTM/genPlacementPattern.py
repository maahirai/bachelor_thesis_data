import json
import sys

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
    else :
        return size[idx]

### for debug
def showGrid(grid):
    for y in range(GridSize):
        for x in range(GridSize):
            print("%2d"%(grid[y][x]),end=" ")
        print("\n")
def main():
    Mixer = ["6h","6v","4"]
    reagent = ["1r","2r","3r","4r","5r"]
    res = {}
    cnt_pattern = 0
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
                                ### cells that overlapp with parentmixer
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
                            showGrid(grid) 
    print("sum of number of no flushing patterns in placements of a overlappinng mixer on a mixer : {}".format(cnt_pattern))
    for i in range(len(Mixer)):
        c = 0
        for j in range(len(Mixer)):
            for cnt in range(1,7):
                if str(cnt) in res[Mixer[i]][Mixer[j]] :
                    c += len(res[Mixer[i]][Mixer[j]][str(cnt)])
        print("parent mixer {} :count {}".format(Mixer[i],c))
    #print(res)
    return
    with open("placement.json","w"):
        str_res = json.dumps(res) 

if __name__ == "__main__":
    main()
