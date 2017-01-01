import re #sorry jwz
SIZE=2000
CELL_SIZE=256
#begin token types
FUNCTIONCALL='FUNCTIONCALL'
FUNCTIONDEFINE='FUNCTIONDEFINE'
BLOCKDEFINE='BLOCKDEFINE'
WHILELOOP='WHILELOOP'
INPLOOP='INPLOOP'
BREAK='BREAK'
PLUS='PLUS'
MINUS='MINUS'
LEFT='LEFT'
RIGHT='RIGHT'
UP='UP'
DOWN='DOWN'
LITERAL='LITERAL'
IN='IN'
LIVEIN='LIVEIN'
NUMIN='NUMIN'
OUT='OUT'
LIVEOUT='LIVEOUT'
NUMOUT='NUMOUT'
ITERVAL='ITERVAL'
#end token types
SINGLECHARS={'+':PLUS,'-':MINUS,'<':LEFT,'>':RIGHT,'^':UP,'v':DOWN,',':IN,'`':LIVEIN,'~':NUMIN,'.':OUT,'_':LIVEOUT,'=':NUMOUT}
functionCallRegex=re.compile(r'^([A-z]+)([0-9]+)') #matches name1234
nameCodeRegex=re.compile(r'^([A-z]+)[|]([\d\D]+)')
breakRegex=re.compile(r'[&]+')
iterValRegex=re.compile(r'^[|]([0-9]+)')
def funcDefineMatch(code,ind):
  ind+=1
  text=''
  while code[ind]!='}':
    if code[ind]=='{':
      innerMatch=funcDefineMatch(code,ind)
      if innerMatch:
        ind,addToText=innerMatch
        text+='{'+addToText+'}'
      else:
        return None
    else:
      text+=code[ind]
    ind+=1
    if ind>=len(code):
      return None
  return ind,text
def blockDefineMatch(code,ind):
  ind+=1
  text=''
  while code[ind]!='\\':
    if code[ind]=='/':
      innerMatch=blockDefineMatch(code,ind)
      if innerMatch:
        ind,addToText=innerMatch
        text+='/'+addToText+'\\'
      else:
        return None
    else:
      text+=code[ind]
    ind+=1
    if ind>=len(code):
      return None
  return ind,text
def whileLoopMatch(code,ind):
  ind+=1
  text=''
  while code[ind]!=']':
    if code[ind]=='[':
      innerMatch=whileLoopMatch(code,ind)
      if innerMatch:
        ind,addToText=innerMatch
        text+='['+addToText+']'
      else:
        return None
    else:
      text+=code[ind]
    ind+=1
    if ind>=len(code):
      return None
  return ind,text
def inpLoopMatch(code,ind):
  ind+=1
  text=''
  while code[ind]!=')':
    if code[ind]=='(':
      innerMatch=inpLoopMatch(code,ind)
      if innerMatch:
        ind,addToText=innerMatch
        text+='('+addToText+')'
      else:
        return None
    else:
      text+=code[ind]
    ind+=1
    if ind>=len(code):
      return None
  return ind,text
def makeNonZero(string):
  if string:
    return int(string)
  return 0
def getOpFromName(name):
  return {'less':'<','greater':'>','lesseq':'<=','greaterer':'>=','eq':'==','neq':'!='}[name]
def isByte(string):
  return string.strip('0123456789')=='' and int(string)<256
class Token():
  def __init__(self,tokenType,*values):
    self.tokenType=tokenType
    self.values=values
  def __repr__(self):
    return '('+self.tokenType+', '+str(self.values)+')' #(Type, values)
class Tape():
  def __init__(self):
      self.values=[0 for a in range(SIZE)]
      self.currentIndex=0
  def right(self):
    self.currentIndex+=1
    self.currentIndex%=SIZE
  def left(self):
    self.currentIndex-=1
    self.currentIndex%=SIZE
  def increment(self):
    self.values[self.currentIndex]+=1
    self.values[self.currentIndex]%=CELL_SIZE
  def decrement(self):
    self.values[self.currentIndex]-=1
    self.values[self.currentIndex]%=CELL_SIZE
  def getValue(self):
    return self.values[self.currentIndex]
  def setValue(self,value):
    self.values[self.currentIndex]=value #tape of length SIZE
class Environment():
  def __init__(self):
    self.tapes=[Tape() for a in range(SIZE)]
    self.tapeIndex=0
    self.functions={}
    self.blocks={}
    self.output=[]
    self.inpInd=0
  def reset(self):
    self.tapes=[Tape() for a in range(SIZE)]
    self.tapeIndex=0
    self.output=[]
  def up(self):
    self.tapeIndex-=1
    self.tapeIndex%=SIZE
  def down(self):
    self.tapeIndex+=1
    self.tapeIndex%=SIZE
  def right(self):
    self.tapes[self.tapeIndex].right()
  def left(self):
    self.tapes[self.tapeIndex].left()
  def increment(self):
    self.tapes[self.tapeIndex].increment()
  def decrement(self):
    self.tapes[self.tapeIndex].decrement()
  def getValue(self):
    return self.tapes[self.tapeIndex].getValue()
  def setValue(self,value):
    self.tapes[self.tapeIndex].setValue(value)
  def addFunction(self,name,interpreter):
    self.functions[name]=interpreter
    for function in self.functions:
      self.functions[function].environment.functions[name]=interpreter
  def getFunction(self,name):
    return self.functions[name]
  def addBlock(self,name,code):
    self.blocks[name]=code
  def getBlock(self,name):
    return self.blocks[name]
  def isFunction(self,name):
    return name in self.functions.keys()
  def isBlock(self,name):
    return name in self.blocks.keys() #array of tapes
  def addToOutput(self):
    self.output.append(self.getValue())
  def getArgs(self,num):
    args=[]
    for addToInd in range(num):
      args.append(self.getValue())
      self.right()
    for subFromInd in range(num):
      self.left()
    return args
  def takeInput(self,size):
    self.inpInd+=1
    self.inpInd%=size
def EOFerror(errorText):
  raise EOFError(errorText)
def analyze(code):
  #precedence
  #function/block calls,define functions/blocks,
  #loops,breaks,itervals,single chars
  tokens=[]
  ind=0
  while ind<len(code):
    functionCallMatch=functionCallRegex.match(code[ind:])
    if functionCallMatch: #if its a function call
      name,args=functionCallMatch.group(1,2)
      tokens.append(Token(FUNCTIONCALL,name,makeNonZero(args)))
      ind+=len(functionCallMatch.group(0))
    elif code[ind]=='{': #function defining
      defineMatch=funcDefineMatch(code,ind)
      nameCode=None
      if defineMatch:
        nameCode=nameCodeRegex.match(defineMatch[1])
      else:
        EOFerror('unmatched { at index '+str(ind)+' of '+code)
      if nameCode:
        tokens.append(Token(FUNCTIONDEFINE,nameCode.group(1),analyze(nameCode.group(2))))
      ind=defineMatch[0]+1
    elif code[ind]=='/': #block defining
      defineMatch=blockDefineMatch(code,ind)
      nameCode=None
      if defineMatch:
        nameCode=nameCodeRegex.match(defineMatch[0])
      else:
        EOFerror('unmatched / at index '+str(ind)+' of '+code)
      if nameCode:
        tokens.append(Token(BLOCKDEFINE,nameCode.group(1),analyze(nameCode.group(2))))
        ind=defineMatch[1]+1
    elif code[ind]=='[':
      whileLoop=whileLoopMatch(code,ind)
      if whileLoop:
        tokens.append(Token(WHILELOOP,analyze(whileLoop[1])))
        ind=whileLoop[0]+1
      else:
        EOFerror('unmatched [ at index '+str(ind)+' of '+code)
    elif code[ind]=='(':
      inpLoop=inpLoopMatch(code,ind)
      if inpLoop:
        tokens.append(Token(INPLOOP,analyze(inpLoop[1])))
        ind=inpLoop[0]+1
      else:
        EOFerror('unmatched ( at index '+str(ind)+' of '+code)
    elif code[ind]=='&':
      count=0
      while code[ind]=='&':
        ind+=1
        count+=1
      tokens.append(Token(BREAK,count))
    elif code[ind]=='|':
      iterValMatch=iterValRegex.match(code[ind:])
      num=iterValMatch.group(1)
      ind+=len(num)+1
      tokens.append(Token(ITERVAL,makeNonZero(num)))
    elif code[ind] in '+-<>^v,`~._=':
      tokenType=SINGLECHARS[code[ind]]
      tokens.append(Token(tokenType))
      ind+=1
    elif code[ind] in '#$':
      if code[ind]=='$':
        tokens.append(Token(LITERAL,ord(code[ind+1])))
        ind+=3
      else:
        ind+=1
        value=''
        while code[ind]!='#':
          value+=code[ind]
          ind+=1
        tokens.append(Token(LITERAL,makeNonZero(value)))
        ind+=1
    elif code[ind]=='@':
      while code[ind]!='\n':
        ind+=1
      ind+=1
    elif code[ind] in '}]0/':
      raise SyntaxError('Unexpected '+code[ind]+' at '+str(ind)+' of '+code)
    else:
      ind+=1
  return tokens
class Interpreter():
  def __init__(self,code,inp=[],parsed=False):
    if parsed:
      self.analyzedCode=code
    else:
      self.analyzedCode=analyze(code)
    self.environment=Environment()
    self.inp=inp
  def resetEnvironment(self):
    self.environment.reset()
  def runCode(self,inp=None,analyzedCode=None,iterVals=[]):
    if analyzedCode==None:
      analyzedCode=self.analyzedCode
    if inp==None:
      inp=self.inp
    assert(type(analyzedCode)==list)
    for token,values in [(token,token.values) for token in analyzedCode]:
      if token.tokenType==FUNCTIONCALL:
        name=values[0]
        argsNum=values[1]
        args=self.environment.getArgs(argsNum)
        if name in self.environment.functions.keys():
          function=self.environment.getFunction(name)
          function.runCode(args)
          functionOut=function.environment.output
          if functionOut==[]:
            self.environment.setValue(0)
          else:
            self.environment.setValue(functionOut[0])
          function.resetEnvironment()
        elif name in self.environment.blocks.keys():
          block=self.environment.getBlock(name)
          out=self.runCode(args,block)
          if out!=None:
            if out!=1:
              return out-1
            return None
        elif name in ['less','greater','lesseq','greatereq','eq','neq']:
          op=getOpFromName(name)
          num1,num2=args[-2:]
          self.environment.setValue(int(eval('num1{}num2'.format(op))))
      elif token.tokenType==FUNCTIONDEFINE:
        self.environment.addFunction(values[0],Interpreter(values[1],[],True))
      elif token.tokenType==BLOCKDEFINE:
        self.environment.addBlock(values[0],Interpreter(values[1]))
      elif token.tokenType==WHILELOOP:
        while self.environment.getValue()!=0:
          self.runcode(None,values[0])
      elif token.tokenType==INPLOOP:
        for iterVal in inp:
          self.runCode(inp,values[0],iterVals+[iterVal])
      elif token.tokenType==BREAK:
        return values[0]
      elif token.tokenType==PLUS:
        self.environment.increment()
      elif token.tokenType==MINUS:
        self.environment.decrement()
      elif token.tokenType==LEFT:
        self.environment.left()
      elif token.tokenType==RIGHT:
        self.environment.right()
      elif token.tokenType==UP:
        self.environment.up()
      elif token.tokenType==DOWN:
        self.environment.down()
      elif token.tokenType==LITERAL:
        self.environment.setValue(values[0])
      elif token.tokenType==IN:
        self.environment.takeInput(len(inp))
        self.environment.setValue(inp[self.environment.inpInd])
      elif token.tokenType==LIVEIN:
        liveInput=input('')
        while len(liveInput)==1: #get nonempty string
          print('Error: non length one string')
          liveInput=input('')
        self.environment.setValue(ord(liveInput))
      elif token.tokenType==NUMIN:
        numericInput=input('')
        while not isByte(numericInput): #get num that fits in a byte
          print('Error: not a number or doesn\'t fit in a byte')
          numericInput=input('')
        self.environment.setValue(int(numericInput))
      elif token.tokenType==OUT:
        self.environment.addToOutput()
      elif token.tokenType==LIVEOUT:
        print(chr(self.environment.getValue()),end='')
      elif token.tokenType==NUMOUT:
        print(str(self.environment.getValue()),end='')
      elif token.tokenType==ITERVAL:
        self.environment.setValue(iterVals[values[0]])
fileName=input('filename.ext')
file=open(fileName,'r')
code=file.read()
inp=[]
inp='string'
if type(inp)==str:
  inp=[ord(char) for char in inp]
interpreter=Interpreter(code,inp)
interpreter.runCode()
output=interpreter.environment.output
print(', '.join([str(out) for out in output]))
print(''.join([chr(out) for out in output]))
