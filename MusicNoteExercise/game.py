import pygame, pygame.midi, random, asyncio, game
from math import *

altoSaxophone= {
    'instrumentMidi':   65,         # midi saxophone 乐器号码
    'totalNote':        31,         # saxophone 可以吹31个音，如果不用超吹. 程序将生成音符介于0~totalNote-1之间的音符，以半音为步长
    'lowestNote':       49          # saxophone 最低音是升C, 在萨克斯谱上是升A
}
piano = {
    'instrumentMidi':   1,         # midi piano 乐器号码
    'totalNote':        88,        # piano. 程序将生成音符介于0~totalNote-1之间的音符，以半音为步长
    'lowestNote':       0          # piano
}

class Instrument:
    def __init__(self,insrmt:dict) -> None:
        self.inst = insrmt
    @property
    def instrumentMidi(self):
        return self.inst['instrumentMidi']
    @property
    def totalNote(self):
        return self.inst['totalNote']
    @property
    def lowestNote(self):
        return self.inst['lowestNote']

class Mscnote:
    __centC = 60
    __dictNoteU  = [-1, -1,  -0.5, -0.5, 0, 0.5, 0.5, 1, 1,   1.5, 1.5,  2]
    __dictNoteD  = [-1, -0.5,-0.5,  0,   0, 0.5,  1,  1, 1.5, 1.5,  2,   2]
    __dictNUD    = [ 1,  3,  6,  8, 10]     # 这些音需要升降

    def __init__(self, note: int=0, instrument: Instrument=None, scorekey: int=0) -> None:
        self.__note = note
        self.__instrument = Instrument(piano) if instrument == None else instrument
        self.__scorekey = scorekey
    @property
    def notevalue(self):
        return self.__note
    @property
    def instrument(self):
        return self.__instrument
    def setNote(self, note):
        self.__note = note
    
    def scorePosition(self, ud: str='#', scorekey:int=None)->int:
        scoreKey = self.__scorekey if scorekey==None else scorekey
        actNote = self.__note - scoreKey + self.instrument.lowestNote - self.__centC

        octID = 0 if (0 <= actNote < 12) else floor(actNote/12)
        actNote = actNote%12

        if '#' in ud:  Npst  = self.__dictNoteU[actNote] + octID * 3.5; Nud = '#' if actNote in self.__dictNUD else ''
        if 'b' in ud:  Npst  = self.__dictNoteD[actNote] + octID * 3.5; Nud = 'b' if actNote in self.__dictNUD else ''

        if actNote in [0, 5] and ud == '*#':       Npst = Npst - 0.5; Nud = '#'  #TBD
        if actNote in [4, 11] and ud == '*b':      Npst = Npst + 0.5; Nud = 'b'

        return (Npst, Nud)

async def game():
    instru          = Instrument(altoSaxophone)     # 乐器设定

    notePlayLength  = 500                           # 音符播放时长，毫秒 ms
    Timer           = 4000                          # 等待用户输入时间，超过Timer时间，会自动播放，播放完毕后展示下一个音符
    TimerStep       = 500                           # 增加或减少时间的步长

    playList        = ['#', 'b', '*#', '*b']
    playMode        = 0                             # 难度系数，0只有原音和升号，1会强制将随机C和F设置为#B和#E，2会在1的基础上随机将B和E设置为bC和bF

    # 设置midi设备和channel
    midiDev = 0
    midiChn = 121

    # 设置谱号。如果是C调乐器C调谱号则为0，否则是C与谱号间的差，以半音为单位。例如，萨克斯是bE调乐器bE调谱，则下移9个半音
    scoreKey = -9

    # 配色方案
    BKGCL = (205, 202, 203)     # 背景颜色
    NoteCL = (20,50,100)        # 音符颜色
    LineCL = (50, 150, 50)      # 线的颜色
    CntCL = (116, 60, 60)       # 显示信息颜色，例如计数器，时钟等

    # 绘图参数
    initPoint = (600, 800)      # 最高的五线谱线的起始点
    lineLenth = 800             # 五线谱长度
    tempLenth = 200             # 加线的长度
    lineWth = 5                 # 谱线粗
    noteSize = 50               # 音符大小，和谱线间隔一样。
    noteStem = 200              # 符杆

    noteCntPst = (80, 80)       # 音符计数的显示位置
    infoPst    = (800, 80)     # 信息显示位置

    # 初始化Pygame
    pygame.init()

    pygame.midi.init()
    player = pygame.midi.Output(midiDev)
    player.set_instrument(instru.instrumentMidi)

    clock = pygame.time.Clock()     # 设置fps需要

    fontTM = pygame.font.SysFont('arial', 48)     # play mode display font
    fontUD = pygame.font.SysFont('arial', 60)     # note #,b display font
    fontCT = pygame.font.SysFont('arial', 100)    # number of notes shown font

    # 设置窗口大小
    size = (1920, 1080)
    screen = pygame.display.set_mode(size)#, pygame.locals.FULLSCREEN)

    # 设置窗口标题
    pygame.display.set_caption("随机音符训练")

    # 初始音符和更新条件
    curNote = Mscnote(note=0, instrument=instru, scorekey=scoreKey)
    #curNote.setNote(random.randint(0, curNote.instrument.totalNote))
    firstNote = True
    updateNote = False
    TIMER_EVENT = pygame.USEREVENT
    pygame.time.set_timer(TIMER_EVENT, Timer)
    NoteNum = 1

    lastPress = pygame.time.get_ticks()

    # 循环
    done = False
    while not done:
        clock.tick(10)
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  
                done = True
            elif event.type == pygame.KEYUP:    # 按键后，或超过Timer时间后，自动播放、切换。按pagedown和pageup改变计时器
                match event.key:
                    case pygame.K_PAGEDOWN:     Timer = Timer if Timer<=TimerStep else Timer-TimerStep
                    case pygame.K_PAGEUP:       Timer += TimerStep
                    case pygame.K_LEFT:         playMode = len(playList)-1  if playMode==0               else playMode-1
                    case pygame.K_RIGHT:        playMode = 0                if playMode==len(playList)-1 else playMode+1
                    case pygame.K_ESCAPE:       done = True;   break
                    case _:             
                        if pygame.time.get_ticks() - lastPress < 1e3:        break                   # 按键太快，不做处理，1e3的毫秒，就是1秒
                        else:       lastPress = pygame.time.get_ticks();     updateNote = True

            elif event.type == TIMER_EVENT:     updateNote = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if pygame.time.get_ticks() - lastPress < 1e3:   break                        # 按键太快，不做处理，1e3的毫秒，就是1秒
                elif event.button in [1, 3]:     lastPress = pygame.time.get_ticks();     updateNote = True       # 鼠标左右键是1，3，中键是2，滚动是4，5

            if updateNote:
                # curNote是0~31，+ instrument['lowestNote'] 是把第0个音映射到乐器的最低音。 萨克斯最低的音在midi里面号码是49，#C
                player.note_on(curNote.notevalue + curNote.instrument.lowestNote, midiChn); pygame.time.delay(notePlayLength); player.note_off(curNote.notevalue + curNote.instrument.lowestNote, midiChn)                 
                pygame.time.set_timer(TIMER_EVENT,Timer)

        # 填充窗口颜色
        screen.fill(BKGCL)

        if updateNote == True or firstNote == True:     # 如果允许绘制新的，则绘制新音符
            noteDsp = random.randint(0, playMode)
            curNote.setNote(random.randint(0, curNote.instrument.totalNote))
            NoteNum += 1
            (noteLine, UD)  = curNote.scorePosition(playList[noteDsp]);    textUD = fontUD.render(UD, True, NoteCL)

        # 绘制五线谱的线
        if noteLine < 0:    ll = range(int(noteLine),5)
        elif noteLine > 4:  ll = range(int(noteLine) + 1)
        else:               ll = range(5)

        for i in ll:
            start = (initPoint[0],             initPoint[1] - noteSize*i)  if i in range(5) else (initPoint[0]+lineLenth/2 - tempLenth/2, initPoint[1] - noteSize*i) 
            end   = (initPoint[0] + lineLenth, initPoint[1] - noteSize*i)  if i in range(5) else (initPoint[0]+lineLenth/2 + tempLenth/2, initPoint[1] - noteSize*i)
            pygame.draw.line(screen, LineCL, start, end, lineWth)

        NoteRect = (initPoint[0]+lineLenth/2, initPoint[1] - (noteLine+0.5)*noteSize + 2 , noteSize*1.6, noteSize-lineWth)

        # 符杆方向
        if noteLine > 2:        NoteHandX = NoteRect[0] + lineWth;                NoteHandY = NoteRect[1] + NoteRect[3]-noteSize/2 + noteStem  # 左下
        else:                   NoteHandX = NoteRect[0] + NoteRect[2] - lineWth;  NoteHandY = NoteRect[1] + NoteRect[3]-noteSize/2 - noteStem  # 右上

        # 画音符和符杆
        pygame.draw.ellipse(screen, NoteCL, NoteRect, 0)
        pygame.draw.line(screen, NoteCL, (NoteHandX, NoteRect[1] + NoteRect[3]-noteSize/2), (NoteHandX+15, NoteHandY), 10 )
        
        # 画升降号
        textCT = fontCT.render(str(NoteNum), True, CntCL)

        # 游戏模式和定时器显示
        textTM = fontUD.render('Timer ' + str(Timer/1000) + ' s, playmode: ' + str(playMode) , True, CntCL)

        screen.blit(textUD, (NoteRect[0] - 40, NoteRect[1]-50))         # 升降号显示
        screen.blit(textCT, noteCntPst)                                 # 音符计数
        screen.blit(textTM, infoPst)                                    # 信息显示
        updateNote = False;        firstNote = False; ll=[]
        # 更新窗口
        pygame.display.update()

    # 退出Pygame