import os
def create_directory(dir_name):
    if not os.path.exists(dir_name):
        print ('Creating directory: ', dir_name)
        os.makedirs(dir_name)

def Translate(name): 
    subscript = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
    return name.translate(subscript)

from PIL import Image,ImageDraw,ImageFont

sep = 30
Width = 20
class Cell: 
    global sep,Width,draw
    def __init__(self,y,x,color="",state=""): 
        ### バルブ
        draw.rectangle([(x+sep,y),(x+sep+Width,y+Width)],fill = "#8FBC8F",outline = "Black",width=1)
        draw.rectangle([(x+sep,y+2*sep),(x+sep+Width,y+2*sep+Width)],fill = "#8FBC8F",outline = "Black",width=1)
        draw.rectangle([(x,y+sep),(x+Width,y+sep+Width)],fill = "#8FBC8F",outline = "Black",width=1)
        draw.rectangle([(x+2*sep,y+sep),(x+2*sep+Width,y+sep+Width)],fill = "#8FBC8F",outline = "Black",width=1) 
        
        self.color = color if color else "Gainsboro"
        self.state = state if state else ""
        draw.rectangle([(x+sep,y+Width+1),(x+sep+Width,y+2*sep-1)],fill = self.color)
        draw.rectangle([(x+Width+1,y+sep),(x+2*sep-1,y+sep+Width)],fill = self.color)
        dropfontsize = 15
        dropfont = ImageFont.truetype("Times New Roman.ttf", dropfontsize)
        fromy,fromx = x+sep,y+sep 
        toy,tox = fromy+Width,fromx+Width
        #draw.text(((fromx+tox)//2-11,(fromy+toy)//2-9),Translate(self.state),font=dropfont,fill="Black")

        self.sy = y 
        self.sx = x 
        self.ey = y+2*sep+Width 
        self.ex = x+2*sep+Width 

    def change(self,color,state):
        self.color = color 
        self.state = state 
        draw.rectangle([(self.sx+sep,self.sy+Width+1),(self.sx+sep+Width,self.sy+2*sep-1)],fill = self.color)
        draw.rectangle([(self.sx+Width+1,self.sy+sep),(self.sx+2*sep-1,self.sy+sep+Width)],fill = self.color)
        dropfontsize = 15
        dropfont = ImageFont.truetype("Times New Roman.ttf", dropfontsize)
        fromy,fromx = self.sy+sep,self.sx+sep 
        toy,tox = fromy+Width,fromx+Width
        #draw.text(((fromx+tox)//2-11,(fromy+toy)//2-9),Translate(self.state),font=dropfont,fill="Black")
        draw.text(((fromx+tox)//2-9,(fromy+toy)//2-9),self.state,font=dropfont,fill="Black")

def genGrid(Vsize,Hsize): 
    global draw,sep,Width
    img = Image.new("RGB",(2*sep*Hsize+2*Width,2*sep*Vsize+3*Width),"White")
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

class SlideCell: 
    global draw,SlideCellWidth,blank
    def __init__(self,y,x,color="",state=""): 
        self.color = color if color else "White"
        #self.color = color if color else "Gainsboro"
        self.state = state if state else ""
        draw.rectangle([(x,y),(x+SlideCellWidth,y+SlideCellWidth)],fill = self.color,outline="Black")
        dropfontsize = 15
        dropfont = ImageFont.truetype("Times New Roman.ttf", dropfontsize)
        fromy,fromx = x+sep,y+sep 
        toy,tox = fromy+Width,fromx+Width
        #draw.text(((fromx+tox)//2-11,(fromy+toy)//2-9),Translate(self.state),font=dropfont,fill="Black")

        self.sy = y
        self.sx = x
        self.ey = y+SlideCellWidth
        self.ex = x+SlideCellWidth

    def change(self,color,state):
        self.color = color 
        self.state = state 
        draw.rectangle([(self.sx,self.sy),(self.sx+SlideCellWidth,self.sy+SlideCellWidth)],fill = self.color,outline="Black")
        dropfontsize = 15
        dropfont = ImageFont.truetype("Times New Roman.ttf", dropfontsize)
        fromy,fromx = self.sy,self.sx
        toy,tox = fromy+SlideCellWidth,fromx+SlideCellWidth
        #draw.text(((fromx+tox)//2-11,(fromy+toy)//2-9),Translate(self.state),font=dropfont,fill="Black")
        draw.text(((fromx+tox)//2-9,(fromy+toy)//2-9),self.state,font=dropfont,fill="Black")

SlideCellWidth,blank =40,10
def genSlideGrid(Vsize,Hsize): 
    global draw,SlideCellWidth,blank
    img = Image.new("RGB",(Hsize*SlideCellWidth+2*blank,(Vsize+1)*SlideCellWidth+blank),"White")
    draw = ImageDraw.Draw(img)
    Grid = []
    for i in range(Vsize): 
        row = []
        for j in range(Hsize): 
            y = i*SlideCellWidth+blank
            x = j*SlideCellWidth+blank
            cell = SlideCell(y,x) 
            row.append(cell)
        Grid.append(row) 
    return Grid,img 

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


import random
from pathlib  import Path
def PMDImage(filename,ColorList,TimeStep,Vsize,Hsize,PMDState,NodeInfo,AtTopOfPlacedMixer,WaitingProvDrops,ImageOut=False):
    global Width,Sep,draw
    MixerColorList,ReagentColorDict = ColorList
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
                    #name = "d"+str(idx)
                    color = MixerColorList[idx]
                else : 
                    name = NodeInfo[str(hash)].name[1:]
                    color = "Gainsboro"
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
            #for hash in WaitingProvDrops: 
            #    Node = NodeInfo[str(hash)]
            #    Children = Node.ChildrenHash 
            #    skip = False
            #    for y,x in getCoveringCell(Node.RefCell,Node.orientation): 
            #        if PMDState[y][x]<0 and abs(PMDState[y][x]) not in Children: 
            #            skip = True
            #    if skip : 
            #        continue
            #    else: 
            #        MixerIdx = int(Node.name[1:])
            #        color = MixerColorList[MixerIdx]
            #        cells = getCoveringCell(Node.RefCell,Node.orientation)
            #        sy,sx  = Node.RefCell 
            #        ey,ex = cells[len(cells)-1]

            #        fromy,fromx =sy*2*sep+Width ,sx*2*sep+Width
            #        toy,tox = grid[ey][ex].ey-Width,grid[ey][ex].ex-Width
            #        diff = 5
            #        draw.rounded_rectangle([(fromx-diff,fromy-diff),(tox+diff,toy+diff)],radius = 15,outline = color,width=10)
            #        fontsize = 22
            #        font = ImageFont.truetype("Times New Roman.ttf", fontsize)
            #        #draw.text(((fromx+tox)//2-14,(fromy+toy)//2+3),Node.name,font=font,fill="Black")

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
                    color = MixerColorList[MixerIdx] 
                    cells = getCoveringCell(Node.RefCell,Node.orientation)
                    sy,sx  = Node.RefCell 
                    ey,ex = cells[len(cells)-1]

                    fromy,fromx =sy*2*sep+Width ,sx*2*sep+Width
                    toy,tox = grid[ey][ex].ey-Width,grid[ey][ex].ex-Width
                    draw.rounded_rectangle([(fromx,fromy),(tox,toy)],radius = 15,outline = color,width=10)
                    fontsize = 16
                    font = ImageFont.truetype("Times New Roman.ttf", fontsize)
                    #draw.text(((fromx+tox)//2-10,(fromy+toy)//2-12),Translate(Node.name),font=font,fill="Black")
                    draw.text(((fromx+tox)//2-8,(fromy+toy)//2-10),Node.name[1:],font=font,fill="Black")
                    
                    mix = True
                    for child in Children: 
                        if NodeInfo[str(child)].state != "OnlyProvDrop": 
                            mix = False 
                        if mix : 
                            draw.arc([(fromx+sep-Width/2,fromy+sep),(tox-sep+Width/2,toy-sep)],30,0,fill="Black",width=5)
                            tri_x,tri_y= tox-sep+Width*0.44,(fromy+toy)//2
                            draw.regular_polygon((tri_x,tri_y,(9)),3,rotation=75,fill="Black")

    create_directory("image")
    path = Path("image/",filename+".png")
    img.save(path)

def PMDSlideImage(filename,ColorList,TimeStep,Vsize,Hsize,PMDState,NodeInfo,AtTopOfPlacedMixer,WaitingProvDrops,ImageOut=False):
    global draw,SlideCellWidth 
    MixerColorList,ReagentColorDict = ColorList
    if not ImageOut: 
        return 
    grid,img = genSlideGrid(Vsize,Hsize)
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
                    #name = "d"+str(idx)
                    color = MixerColorList[idx]
                else : 
                    key = NodeInfo[str(hash)].name 
                    if key[0] == "M":
                        print("アストロゼネ",key,NodeInfo[str(hash)].ProvNum,NodeInfo[str(hash)].size,NodeInfo[str(hash)].kind)
                    #color = "Gainsboro"
                    color = ReagentColorDict[key]
                    ### 何も書かない
                    name = ""
                #draw.rounded_rectangle([(fromx,fromy),(tox,toy)],radius = 5,fill = color,outline = 'Black',Width=3) 
                #fromy,fromx = (2*i+1)*sep,(2*j+1)*sep
                #toy,tox = fromy+Width,fromx+Width
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
                    color = MixerColorList[MixerIdx]
                    cells = getCoveringCell(Node.RefCell,Node.orientation)
                    sy,sx  = Node.RefCell 
                    ey,ex = cells[len(cells)-1]

                    fromy,fromx =grid[sy][sx].sy ,grid[sy][sx].sx
                    toy,tox = grid[ey][ex].ey,grid[ey][ex].ex
                    w = 10
                    half = w//2
                    #draw.rounded_rectangle([(fromx+1,fromy+1),(tox-1,toy-1)],radius = 15,outline = color,width=5)
                    draw.rounded_rectangle([(fromx+1,fromy+1),(tox-1,toy-1)],radius = 15,outline = color,width=10)
                    fontsize = 16
                    font = ImageFont.truetype("Times New Roman.ttf", fontsize)
                    #draw.text(((fromx+tox)//2-8,(fromy+toy)//2-10),Node.name[1:],font=font,fill="Black")

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
                    color = MixerColorList[MixerIdx] 
                    cells = getCoveringCell(Node.RefCell,Node.orientation)
                    sy,sx  = Node.RefCell 
                    ey,ex = cells[len(cells)-1]
                    fromy,fromx =grid[sy][sx].sy ,grid[sy][sx].sx
                    toy,tox = grid[ey][ex].ey,grid[ey][ex].ex
                    w = 10

                    ### 見やすく
                    cx,cy = (tox+fromx)//2,(fromy+toy)//2
                    mdf = 4
                    #fontsize = 16
                    fontsize = 32
                    div = 2.1
                    draw.rectangle([(cx-SlideCellWidth//div+mdf,cy-SlideCellWidth//div+mdf),(cx+SlideCellWidth//div-mdf,cy+SlideCellWidth//div-mdf)],fill = "White",width=0)

                    draw.rounded_rectangle([(fromx+1,fromy+1),(tox-1,toy-1)],radius = 15,outline = color,width=10)
                    font = ImageFont.truetype("Times New Roman.ttf", fontsize)
                    draw.text(((fromx+tox)//2-12-mdf,(fromy+toy)//2-13-mdf),Node.name[1:],font=font,fill="Black")
                    
                    mix = True
                    for child in Children: 
                        if NodeInfo[str(child)].state != "OnlyProvDrop": 
                            mix = False 
                        if mix : 
                            cx,cy = (tox+fromx)//2,(fromy+toy)//2
                            draw.arc([(cx-SlideCellWidth//2,cy-SlideCellWidth//2),(cx+SlideCellWidth//2,cy+SlideCellWidth//2)],30,0,fill="Black",width=3)
                            tri_x,tri_y= cx+SlideCellWidth//2,(fromy+toy)//2
                            draw.regular_polygon((tri_x,tri_y,(9)),3,rotation=75,fill="Black")

    create_directory("image")
    path = Path("image/",filename+".png")
    img.save(path)

def ProcessImage(filename,Vsize,Hsize,ColorList,TimeStep,FlushCount,PMD,Mixer,NodeInfo):
    global Width,Sep,draw
    MixerColorList,ReagentColorDict = ColorList
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
                    #name = "d"+str(idx)
                    color = MixerColorList[idx]
                else : 
                    name = NodeInfo[str(hash)].name[1:]
                    color = "Gainsboro"
                #draw.rounded_rectangle([(fromx,fromy),(tox,toy)],radius = 5,fill = color,outline = 'Black',Width=3) 
                fromy,fromx = (2*i+1)*sep,(2*j+1)*sep
                toy,tox = fromy+Width,fromx+Width
                #draw.rectangle([(fromx,fromy),(tox,toy)],fill = color,outline = 'Black',width=3)
                grid[i][j].change(color,name)

    for hash in Mixer:
        Node = NodeInfo[str(hash)]
        Children = Node.ChildrenHash 
        MixerIdx = int(Node.name[1:])
        color = MixerColorList[MixerIdx]
        cells = getCoveringCell(Node.RefCell,Node.orientation)
        sy,sx  = Node.RefCell 
        ey,ex = cells[len(cells)-1]

        fromy,fromx =sy*2*sep+Width ,sx*2*sep+Width
        toy,tox = grid[ey][ex].ey-Width,grid[ey][ex].ex-Width
        draw.rounded_rectangle([(fromx,fromy),(tox,toy)],radius = 15,outline = color,width=10)
        fontsize = 16
        font = ImageFont.truetype("Times New Roman.ttf", fontsize)
        draw.arc([(fromx+sep-Width/2,fromy+sep),(tox-sep+Width/2,toy-sep)],30,0,fill="Black",width=5)
        tri_x,tri_y= tox-sep+Width*0.44,(fromy+toy)//2
        draw.regular_polygon((tri_x,tri_y,(9)),3,rotation=75,fill="Black")
        #draw.text(((fromx+tox)//2-10,(fromy+toy)//2-12),Translate(Node.name),font=font,fill="Black")
        draw.text(((fromx+tox)//2-8,(fromy+toy)//2-10),Node.name[1:],font=font,fill="Black")
        

    S = "T={},F={}".format(TimeStep,FlushCount)
    fontsize = 40
    font = ImageFont.truetype("Times New Roman.ttf", fontsize)
    draw.text((0,2*sep*Vsize+2*Width-(fontsize)+Width//2+5),S,font=font,fill="Black")
    #2*sep*Hsize+2*Width-(fontsize*10)
    create_directory("image")
    path = Path("image/","result"+filename+".png")
    img.save(path)

def ProcessSlideImage(filename,Vsize,Hsize,ColorList,TimeStep,FlushCount,PMD,Mixer,NodeInfo):
    global SlideCellWidth,draw,blank
    MixerColorList,ReagentColorDict = ColorList
    SlideCellWidth = 40
    grid,img = genSlideGrid(Vsize,Hsize)
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
                    #name = "d"+str(idx)
                    color = MixerColorList[idx]
                else : 
                    key = NodeInfo[str(hash)].name
                    #color = "Gainsboro"
                    color = ReagentColorDict[key]
                    ### 何も書かない
                    name = ""
                    #color = "White"
                #draw.rounded_rectangle([(fromx,fromy),(tox,toy)],radius = 5,fill = color,outline = 'Black',Width=3) 
                #fromy,fromx = (2*i+1)*sep,(2*j+1)*sep
                #toy,tox = fromy+Width,fromx+Width
                #draw.rectangle([(fromx,fromy),(tox,toy)],fill = color,outline = 'Black',width=3)
                grid[i][j].change(color,name)

    for hash in Mixer:
        Node = NodeInfo[str(hash)]
        Children = Node.ChildrenHash 
        MixerIdx = int(Node.name[1:])
        color = MixerColorList[MixerIdx]
        cells = getCoveringCell(Node.RefCell,Node.orientation)
        sy,sx  = Node.RefCell 
        ey,ex = cells[len(cells)-1]
        
        fromy,fromx =grid[sy][sx].sy ,grid[sy][sx].sx
        toy,tox = grid[ey][ex].ey,grid[ey][ex].ex
        ### 見やすく
        #fontsize = 16
        fontsize = 32
        mdf = 4
        div = 2.1
        cx,cy = (tox+fromx)//2,(fromy+toy)//2
        draw.rectangle([(cx-SlideCellWidth//div+mdf,cy-SlideCellWidth//div+mdf),(cx+SlideCellWidth//div-mdf,cy+SlideCellWidth//div-mdf)],fill = "White",width=0)

        draw.rounded_rectangle([(fromx+1,fromy+1),(tox-1,toy-1)],radius = 15,outline = color,width=10)
        font = ImageFont.truetype("Times New Roman.ttf", fontsize)
       
        tri_x,tri_y= cx+SlideCellWidth//2,(fromy+toy)//2
        #draw.arc([(cx-SlideCellWidth//2,cy-SlideCellWidth//3),(cx+SlideCellWidth//2,cy+SlideCellWidth//3)],30,0,fill="Black",width=3)
        draw.regular_polygon((tri_x,tri_y,(9)),3,rotation=75,fill="Black")
        draw.arc([(cx-SlideCellWidth//2,cy-SlideCellWidth//2),(cx+SlideCellWidth//2,cy+SlideCellWidth//2)],30,0,fill="Black",width=3)
        #draw.text(((fromx+tox)//2-10,(fromy+toy)//2-12),Translate(Node.name),font=font,fill="Black")
        draw.text(((fromx+tox)//2-12-mdf,(fromy+toy)//2-13-mdf),Node.name[1:],font=font,fill="Black")
        

    S = "T={},F={}".format(TimeStep,FlushCount)
    fontsize = 40
    font = ImageFont.truetype("Times New Roman.ttf", fontsize)
    draw.text((0,Hsize*SlideCellWidth+blank),S,font=font,fill="Black")
    #2*sep*Hsize+2*Width-(fontsize*10)
    create_directory("image")
    path = Path("image/","result"+filename+".png")
    img.save(path)

