import os
def create_directory(dir_name):
    if not os.path.exists(dir_name):
        print ('Creating directory: ', dir_name)
        os.makedirs(dir_name)

from PIL import Image,ImageDraw,ImageFont

sep = 30
Width = 20
class Cell: 
    global sep,Width,draw
    def __init__(self,y,x,color="",state=""): 
        ### バルブ
        draw.rectangle([(x+sep,y),(x+sep+Width,y+Width-1)],fill = "#8FBC8F",outline = "Black",width=1)
        draw.rectangle([(x+sep,y+2*sep),(x+sep+Width,y+2*sep+Width)],fill = "#8FBC8F",outline = "Black",width=1)
        draw.rectangle([(x,y+sep),(x+Width-1,y+sep+Width)],fill = "#8FBC8F",outline = "Black",width=1)
        draw.rectangle([(x+2*sep,y+sep),(x+2*sep+Width,y+sep+Width)],fill = "#8FBC8F",outline = "Black",width=1) 
        
        self.color = color if color else "#dcdcdc"
        self.state = state if state else ""
        draw.rectangle([(x+sep,y+Width),(x+sep+Width,y+2*sep)],fill = self.color)
        draw.rectangle([(x+Width,y+sep),(x+2*sep,y+sep+Width)],fill = self.color)
        dropfontsize = 10
        dropfont = ImageFont.truetype("Menlo for Powerline.ttf", dropfontsize)
        fromy,fromx = x+sep,y+sep 
        toy,tox = fromy+Width,fromx+Width
        draw.text(((fromx+tox)//2-4,(fromy+toy)//2-4),self.state,font=dropfont,fill="Black")

        self.sy = y 
        self.sx = x 
        self.ey = y+2*sep+Width 
        self.ex = x+2*sep+Width 

    def change(self,color,state):
        self.color = color 
        self.state = state 
        draw.rectangle([(self.sx+sep,self.sy+Width),(self.sx+sep+Width,self.sy+2*sep-1)],fill = self.color)
        draw.rectangle([(self.sx+Width,self.sy+sep),(self.sx+2*sep-1,self.sy+sep+Width)],fill = self.color)
        dropfontsize = 10
        dropfont = ImageFont.truetype("Menlo for Powerline.ttf", dropfontsize)
        fromy,fromx = self.sy+sep,self.sx+sep 
        toy,tox = fromy+Width,fromx+Width
        draw.text(((fromx+tox)//2-4,(fromy+toy)//2-4),self.state,font=dropfont,fill="Black")


def getCoveringCell(RefCell,orientation=""): 
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

Grid = []    
draw = None
def genGrid(Vsize,Hsize): 
    global draw,sep,Width
    img = Image.new("RGB",(2*sep*Hsize+2*Width,2*sep*Vsize+2*Width),"White")
    draw = ImageDraw.Draw(img)
    Grid = []
    for i in range(Vsize): 
        row = []
        for j in range(Hsize): 
            y = i*2*sep 
            x = j*2*sep 
            cell = Cell(y,x) 
            row.append(cell)
        Grid.append(row) 
    return Grid,img

import random
from pathlib  import Path
def PMDImage(filename,ColorList,TimeStep,Vsize,Hsize,PMDState,NodeInfo,AtTopOfPlacedMixer,WaitingProvDrops,ImageOut=False):
    global Width,Sep,draw
    if not ImageOut: 
        return 
    grid,img = genGrid(Vsize,Hsize)
    draw = ImageDraw.Draw(img)
    drop = []
    for i in range(Vsize): 
        for j in range(Hsize): 
            if PMDState[i][j] == 0: 
                continue 
            elif PMDState[i][j] <0:
                name = "" 
                color = "" 
                hash = abs(PMDState[i][j])
                if NodeInfo[str(hash)].kind == "Mixer": 
                    idx = int(NodeInfo[str(hash)].name[1:])
                    name = "d"+str(idx)
                    color = ColorList[idx]
                else : 
                    name = NodeInfo[str(hash)].name 
                    color = "Gray"
                #draw.rounded_rectangle([(fromx,fromy),(tox,toy)],radius = 5,fill = color,outline = 'Black',Width=3) 
                fromy,fromx = (2*i+1)*sep,(2*j+1)*sep
                toy,tox = fromy+Width,fromx+Width
                #draw.rectangle([(fromx,fromy),(tox,toy)],fill = color,outline = 'Black',width=3)
                grid[i][j].change(color,name)

            elif PMDState[i][j] > 0 :
                hash = PMDState[i][j]
                Node = NodeInfo[str(hash)]
                cells = getCoveringCell(Node.RefCell,Node.orientation)
                skip = False
                for y,x in cells: 
                    if PMDState[y][x] != hash : 
                        skip = True 
                if skip : 
                    continue 
            else: 
                continue 
            for hash in WaitingProvDrops: 
                Node = NodeInfo[str(hash)]
                Children = Node.ChildrenHash 
                skip = False
                for y,x in getCoveringCell(Node.RefCell,Node.orientation): 
                    if PMDState[y][x]<0 and abs(PMDState[y][x]) not in Children: 
                        skip = True
                if skip : 
                    continue
                else: 
                    MixerIdx = int(Node.name[1:])
                    color = ColorList[MixerIdx]
                    cells = getCoveringCell(Node.RefCell,Node.orientation)
                    sy,sx  = Node.RefCell 
                    ey,ex = cells[len(cells)-1]

                    fromy,fromx =sy*2*sep+Width ,sx*2*sep+Width
                    toy,tox = grid[ey][ex].ey-Width,grid[ey][ex].ex-Width
                    diff = 5
                    draw.rounded_rectangle([(fromx-diff,fromy-diff),(tox+diff,toy+diff)],radius = 15,outline = color,width=10)
                    fontsize = 15 
                    font = ImageFont.truetype("Menlo for Powerline.ttf", fontsize)
                    draw.text(((fromx+tox)//2-9,(fromy+toy)//2+5),Node.name,font=font,fill="Black")

            for hash in AtTopOfPlacedMixer: 
                Node = NodeInfo[str(hash)]
                Children = Node.ChildrenHash 
                skip = False
                for y,x in getCoveringCell(Node.RefCell,Node.orientation): 
                    if PMDState[y][x]<0 and abs(PMDState[y][x]) not in Children: 
                        skip = True
                if skip : 
                    continue
                else: 
                    MixerIdx = int(Node.name[1:]) 
                    color = ColorList[MixerIdx] 
                    cells = getCoveringCell(Node.RefCell,Node.orientation)
                    sy,sx  = Node.RefCell 
                    ey,ex = cells[len(cells)-1]

                    fromy,fromx =sy*2*sep+Width ,sx*2*sep+Width
                    toy,tox = grid[ey][ex].ey-Width,grid[ey][ex].ex-Width
                    draw.rounded_rectangle([(fromx,fromy),(tox,toy)],radius = 15,outline = color,width=10)
                    fontsize = 15 
                    font = ImageFont.truetype("Menlo for Powerline.ttf", fontsize)
                    draw.text(((fromx+tox)//2-9,(fromy+toy)//2-9),Node.name,font=font,fill="Black")
    create_directory("image")
    path = Path("image/",filename+".png")
    img.save(path)

def ProcessImage(filename,Vsize,Hsize,ColorList,TimeStep,FlushCount,PMD,Mixer,NodeInfo):
    global Width,Sep,draw
    grid,img = genGrid(Vsize,Hsize)
    draw = ImageDraw.Draw(img)
    drop = []
    for i in range(Vsize): 
        for j in range(Hsize): 
            if PMD[i][j] == 0: 
                continue 
            elif PMD[i][j] <0:
                name = "" 
                color = "" 
                hash = abs(PMD[i][j])
                if NodeInfo[str(hash)].kind == "Mixer": 
                    idx = int(NodeInfo[str(hash)].name[1:])
                    name = "d"+str(idx)
                    color = ColorList[idx]
                else : 
                    name = NodeInfo[str(hash)].name 
                    color = "Gray"
                #draw.rounded_rectangle([(fromx,fromy),(tox,toy)],radius = 5,fill = color,outline = 'Black',Width=3) 
                fromy,fromx = (2*i+1)*sep,(2*j+1)*sep
                toy,tox = fromy+Width,fromx+Width
                #draw.rectangle([(fromx,fromy),(tox,toy)],fill = color,outline = 'Black',width=3)
                grid[i][j].change(color,name)

    for hash in Mixer:
        Node = NodeInfo[str(hash)]
        Children = Node.ChildrenHash 
        MixerIdx = int(Node.name[1:])
        color = ColorList[MixerIdx]
        cells = getCoveringCell(Node.RefCell,Node.orientation)
        sy,sx  = Node.RefCell 
        ey,ex = cells[len(cells)-1]

        fromy,fromx =sy*2*sep+Width ,sx*2*sep+Width
        toy,tox = grid[ey][ex].ey-Width,grid[ey][ex].ex-Width
        draw.rounded_rectangle([(fromx,fromy),(tox,toy)],radius = 15,outline = color,width=10)
        fontsize = 15 
        font = ImageFont.truetype("Menlo for Powerline.ttf", fontsize)
        draw.arc([(fromx+sep,fromy+sep),(tox-sep,toy-sep)],30,0,fill="Black",width=5)
        tri_x,tri_y= tox-sep,(fromy+toy)//2
        draw.regular_polygon((tri_x,tri_y,(9)),3,rotation=75,fill="Black")
        draw.text(((fromx+tox)//2-9,(fromy+toy)//2-9),Node.name,font=font,fill="Black")

    S = "T={},F={}".format(TimeStep,FlushCount)
    fontsize = 20
    font = ImageFont.truetype("Menlo for Powerline.ttf", fontsize)
    draw.text((2*sep*Hsize+2*Width-(fontsize+100),2*sep*Vsize+2*Width-(fontsize)),S,font=font,fill="Black")
    create_directory("image")
    path = Path("image/","result"+filename+".png")
    img.save(path)

