"""Estimated caption timing helpers; not word-level forced alignment."""
import array, math, re
RATE=48000

def clock(t, ass=False):
    units=100 if ass else 1000
    total=round(t*units)
    h,total=divmod(total,3600*units);m,total=divmod(total,60*units);s,part=divmod(total,units)
    return f'{h}:{m:02d}:{s:02d}.{part:02d}' if ass else f'{h:02d}:{m:02d}:{s:02d},{part:03d}'

def pauses(data):
    samples=array.array('h',data)
    block=RATE//50
    result=[]; start=None
    for i in range(0,len(samples),block):
        section=samples[i:i+block]
        rms=math.sqrt(sum(x*x for x in section)/max(1,len(section)))
        t=i/RATE
        if rms<260:
            if start is None: start=t
        elif start is not None:
            if t-start>=.10: result.append((start+t)/2)
            start=None
    return result

def closest(expected, choices, lower, upper):
    near=[p for p in choices if lower<p<upper and abs(p-expected)<.5]
    return min(near,key=lambda p:abs(p-expected)) if near else max(lower,min(expected,upper))

def text_chunks(text):
    tokens=list(re.finditer(r'\S+',text))
    out=[];start=0
    for i,word in enumerate(tokens):
        n=i-start+1
        if n>=10 or (n>=5 and word.group().endswith(('؟','.','؛',':','!'))):
            out.append((' '.join(t.group() for t in tokens[start:i+1]),tokens[start].start(),word.end()))
            start=i+1
    if start<len(tokens):
        tail=(' '.join(t.group() for t in tokens[start:]),tokens[start].start(),tokens[-1].end())
        if out and len(tokens)-start<3:
            last=out.pop();tail=(last[0]+' '+tail[0],last[1],tail[2])
        out.append(tail)
    return out

def wrap(text):
    words=text.split()
    if len(text)<=52:return text
    choices=[(' '.join(words[:i]),' '.join(words[i:])) for i in range(1,len(words))]
    first,second=min(choices,key=lambda pair:abs(len(pair[0])-len(pair[1])))
    return first+'\n'+second
