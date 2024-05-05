import pygame, pygame.midi, random, asyncio, math, threading
#import pyaudio

#__NoteN	    = ["#A","B","C","#C","D","#D","E","F","#F","G","#G","A"]

altoSaxophone= {
    'instrumentMidi':   65,         # midi saxophone 乐器号码
    'totalNote':        31,         # saxophone 可以吹31个音，如果不用超吹. 程序将生成音符介于0~totalNote-1之间的音符，以半音为步长
    'lowestNote':       49          # saxophone 最低音是升C, 在萨克斯谱上是升A
}
piano = {
    'instrumentMidi':   1,         # midi piano 乐器号码
    'lowestNote':       0,         # piano
    'totalNote':        88         # piano. 程序将生成音符介于0~totalNote-1之间的音符，以半音为步长
}

def playIn(player,score,velocity):
    for i in range(len(score)):
        player.note_on(60+score[i][0], 100); 
        pygame.time.wait(int(500/velocity*score[i][1])); 
        player.note_off(60+score[i][0])
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
    __dictNoteU  = [-1, -1,  -0.5, -0.5, 0, 0.5, 0.5, 1, 1,   1.5, 1.5,  2] # 以#号表示的半音音阶，-1，-1， 表示下加一线的C和#C的音符位置
    __dictNoteD  = [-1, -0.5,-0.5,  0,   0, 0.5,  1,  1, 1.5, 1.5,  2,   2] # 以b号表示的半音音阶，-1，-0.5， 表示下加一线表示C，下加一间表示bD
    __dictNUD    = [ 1,  3,  6,  8, 10]     # 这些音需要升降

    def __init__(self, note: int=0, scorekey: int=0) -> None:
        self.__note = note
        self.__scorekey = scorekey
    
    @property
    def notevalue(self):
        return self.__note
    
    @notevalue.setter
    def notevalue(self, note):
        self.__note = note

    def scorePosition(self, ud: str='#', scorekey:int=None) -> dict[int,str]:
        scoreKey = self.__scorekey if scorekey==None else scorekey
        actNote = self.__note - scoreKey - self.__centC

        octID, actNote = divmod(actNote,12)     # octID表示哪个八度，actNote 是八度内的哪个音

        if '#' in ud:  Npst  = self.__dictNoteU[actNote] + octID * 3.5; Nud = '#' if actNote in self.__dictNUD else ''
        if 'b' in ud:  Npst  = self.__dictNoteD[actNote] + octID * 3.5; Nud = 'b' if actNote in self.__dictNUD else ''

        if actNote in [0, 5] and ud == '*#':       Npst = Npst - 0.5; Nud = '#'
        if actNote in [4, 11] and ud == '*b':      Npst = Npst + 0.5; Nud = 'b'

        return (Npst, Nud)

async def main():
    pygame.init()

    if True:
        instru          = Instrument(altoSaxophone)     # 乐器设定

        notePlayLength  = 500                           # 音符播放时长，毫秒 ms
        Timer           = 4000                          # 等待用户输入时间，超过Timer时间，会自动播放，播放完毕后展示下一个音符
        TimerStep       = 500                           # 增加或减少时间的步长

        playList        = ['#', 'b', '*#', '*b']
        playMode        = 0                             # 难度系数，0只有原音和升号，1会强制将随机C和F设置为#B和#E，2会在1的基础上随机将B和E设置为bC和bF

        # 设置midi设备和channel
        midiDev = 1
        midiChn = 121

        # 设置谱号。如果是C调乐器C调谱号则为0，否则是C与谱号间的差，以半音为单位。例如，萨克斯是bE调乐器bE调谱，则下移9个半音
        scoreKey = -9

        # 配色方案
        BKGCL  = (245, 232, 222)     # 背景颜色
        NoteCL = (60, 80,120)        # 音符颜色
        LineCL = (50, 130, 50)       # 线的颜色
        CntCL  = (100, 60, 170)      # 显示信息颜色，例如计数器，时钟等

        # 绘图参数
        size = (1920, 1080)          # 屏幕大小
        initPoint = (400, 600)      # 最高的五线谱线的起始点
        lineLenth = 800             # 五线谱长度
        tempLenth = 200             # 加线的长度
        lineWth = 5                 # 谱线粗
        noteSize = 50               # 音符大小，和谱线间隔一样。
        noteStem = 200              # 符杆

        noteCntPst = (80, 80)       # 音符计数的显示位置
        infoPst    = (800, 80)      # 信息显示位置

        fontTM = pygame.font.SysFont('arial', 48)     # play mode display font
        fontUD = pygame.font.SysFont('arial', 60)     # note #,b display font
        fontCT = pygame.font.SysFont('arial', 100)    # number of notes shown font

    # 设置窗口大小
    screen = pygame.display.set_mode(size)#, pygame.locals.NOFRAME)

    # 设置窗口标题
    icon = pygame.image.load("saxophone.jpg")
    pygame.display.set_caption("随机音符训练", "saxophone.ico")
    pygame.display.set_icon(icon)
    # 初始化Pygame
    pygame.midi.init()
    player = pygame.midi.Output(midiDev)
    player.set_instrument(instru.instrumentMidi)

    # 进场音乐, 以中央C为0，每半音一个计数，速度是120BPM
    blues = [(-11,1),(-11,1),(-14,1),(-17,0.66),(-19,0.33),(-14,0.66),(-11,0.33)]
    goinghome = [(14,1), (16,2),(19,3)] #going home
    takefive = [(2,0.66), (7,0.33), (10,0.66), (12,0.33), (13,0.66), (14,0.33), (13,0.66), (12,0.33), (10,1), (2,1), (5,1), (7,3)] #take five
    playThread  = threading.Thread(target=playIn, args=(player, takefive, 1.6))
    playThread.start()

    # 初始音符和更新条件
    updateNote = True; FirstNote = True
    TIMER_EVENT = pygame.USEREVENT
    NoteNum = 0
    lastPress = pygame.time.get_ticks()

    # 循环
    done = False
    while not done:
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  
                done = True
            elif event.type == pygame.KEYUP:    # 按键后，或超过Timer时间后，自动播放、切换。按pagedown和pageup改变计时器
                match event.key:
                    case pygame.K_DOWN:     Timer = Timer if Timer<=TimerStep else Timer-TimerStep
                    case pygame.K_UP:       Timer += TimerStep
                    case pygame.K_LEFT:         playMode = len(playList)-1  if playMode==0               else playMode-1
                    case pygame.K_RIGHT:        playMode = 0                if playMode==len(playList)-1 else playMode+1
                    case pygame.K_ESCAPE:       done = True;   break
                    case _:             
                        if pygame.time.get_ticks() - lastPress < notePlayLength*1.5:        break                   # 按键太快，不做处理，播放时长的1.5倍
                        else:       lastPress = pygame.time.get_ticks();     updateNote = True

            elif event.type == TIMER_EVENT:     updateNote = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if pygame.time.get_ticks() - lastPress < notePlayLength*1.5:   break                              # 按键太快，不做处理，播放时长的1.5倍
                elif event.button in [1, 3]:     lastPress = pygame.time.get_ticks();     updateNote = True       # 鼠标左右键是1，3，中键是2，滚动是4，5

        if updateNote:
            if not FirstNote:
                player.note_on(curNote.notevalue, midiChn); 
                pygame.time.delay(notePlayLength); 
                player.note_off(curNote.notevalue, midiChn)
            FirstNote = False
            pygame.time.set_timer(TIMER_EVENT,Timer)

        # 填充窗口颜色
        screen.fill(BKGCL)

        if updateNote == True:     # 如果允许绘制新的，则绘制新音符
            noteDsp = random.randint(0, playMode)
            curNote = Mscnote(note=0, scorekey=scoreKey)
            curNote.notevalue = random.randint(instru.lowestNote, instru.lowestNote + instru.totalNote)
            NoteNum += 1
            (noteLine, UD)  = curNote.scorePosition(playList[noteDsp]);    textUD = fontUD.render(UD, True, NoteCL)
            updateNote == False

        # 绘制五线谱的线
        lineLst = range(int(noteLine),5) if noteLine < 0 else ( range(int(noteLine) + 1) if noteLine > 4 else range(5) )
                    # 下加线                                    # 上加线                                        # 如果不要加线

        for i in lineLst:
            start = (initPoint[0],             initPoint[1] - noteSize*i)  if i in range(5) else (initPoint[0]+lineLenth/2 - tempLenth/2, initPoint[1] - noteSize*i) 
            end   = (initPoint[0] + lineLenth, initPoint[1] - noteSize*i)  if i in range(5) else (initPoint[0]+lineLenth/2 + tempLenth/2, initPoint[1] - noteSize*i)
            pygame.draw.line(screen, LineCL, start, end, lineWth)

        img = 'clef1.png';        clefimg  = pygame.image.load(img);        screen.blit(clefimg, (initPoint[0], initPoint[1]-300))

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
        textTM = fontTM.render('Timer ' + str(Timer/1000) + ' s, playmode: ' + str(playList[0:playMode+1]) , True, CntCL)

        screen.blit(textUD, (NoteRect[0] - 40, NoteRect[1]-50))         # 升降号显示
        screen.blit(textCT, noteCntPst)                                 # 音符计数
        screen.blit(textTM, infoPst)                                    # 信息显示
        updateNote = False

        #textTr = fontUD.render(str(playList) + '* 表示强行将E表示成bF或强行将F表示为#E', True, CntCL)
        #screen.blit(textTr, (200, size[1]-200))         # 升降号显示

        # 更新窗口
        pygame.display.update()
        playThread.join()
    # 退出Pygame

if __name__ == '__main__':
    asyncio.run(main())


''' 待加入判断声音是否正确的处理。pyaudio库用于录音，存到np里以后，做频率分析，与当前音符频率相近则判断正确。
import pyaudio
import numpy as np

chunk = 1024
sample_rate = 44100

p = pyaudio.PyAudio()

stream = p.open(format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            input=True,
            frames_per_buffer=chunk)

while True:
data = stream.read(chunk)
audio_data = np.frombuffer(data, dtype=np.int16)
# 在这里对音频数据进行处理
'''

'''
altoSax = Instrument(altoSaxophone)
for i in range(0,32, 1):
    mt = Mscnote(note=i,instrument=altoSax,scorekey=-9)
    print(i, '\t', mt.notevalue%12, '\t', mt.scorePposition('*b'))
    del mt

CENT_C = 60         # midi映射表，中央C是60，每加减1变化一个半音

def noteTransToPst(curNote: int, ud: str, lowestNote: int, scoreKey: int) -> int:
    
    dictNoteU = [-1,   -1,  -0.5, -0.5, 0, 0.5, 0.5, 1, 1,   1.5, 1.5, 2]
    dictNoteD = [-1, -0.5,  -0.5,  0,   0, 0.5,  1,  1, 1.5, 1.5,  2,  2]

    actNote = curNote - scoreKey + lowestNote - CENT_C

    octID = 0 if (0 <= actNote < 12) else floor(actNote/12)
    actNote = actNote%12

    if '#' in ud:
        pst  = dictNoteU[actNote] + octID * 3.5
    if 'b' in ud:
        pst  = dictNoteD[actNote] + octID * 3.5

    if actNote in [0, 5] and ud == '*#':
        pst = pst - 0.5
    if actNote in [4, 11] and ud == '*b':
        pst = pst + 0.5
    return pst



noteDict = {
    'NoteN':	    ["#A",	"B",	"C",	"#C",	"D",	"#D",	"E",	"F",	"#F",	"G",	"#G",	"A"],
	'NoteU':	    ["#A",	"B",	"#B	",	"#C",	"D",	"#D",	"E",	"#E	",	"#F",	"G",	"#G",	"A"],
	'NoteD':	    ["bB",	"bC",	"C",	"bD	",	"D",	"bE",	"bF",	"F	",	"bG	",	"G",	"bA",	"A"],
	'NPosition':	[7.5,	7.0,	6.5,	6.5,	6.0,	6.0,	5.5,	5.0,	5.0,	4.5,	4.5,	4.0], # 在五线谱上的位置，0为最高线的位置，每1格为一个线或间。
	'ND':	        ['#',	'',	    '',	    '#',	'',	    '#',	'',	    '',	    '#',	'',	    '#',	'' ],
	'UPosition':	[7.5,	7.0,	7.0,	6.5,	6.0,	6.0,	5.5,	5.5,	5.0,	4.5,	4.5,	4.0],
	'UD':	        ['#',	'',	    '#',	'#',	'',	    '#',	'',	    '#',	'#',	'',	    '#',	'' ],
	'DPosition':	[7.0,	6.5,	6.5,	6.0,	6.0,	5.5,	5.0,	5.0,	4.5,	4.5,	4.0,	4.0],
	'DD':	        ['b',	'b',	'',	    'b',	'',	    'b',	'b',	'',	    'b',	'',	    'b',	'' ]
}
'''