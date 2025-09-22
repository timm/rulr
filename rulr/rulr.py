#!/usr/bin/env python3 
"""
rulr.py: fast rule learning  
(c) 2025, Tim Menzies <timm@ieee.org>, MIT license.      
[src](http://github.com/timm/rulr) |
[data](http://github.com/timm/moot) 
    
Options:
    
    -h             show help   
    -B Budget=30   when growing theory, how many labels?      
    -C Check=5     budget for checking learned model   
    -F Few=64      sample size of data random sampling     
    -p p=2         distance coeffecient   
    -s seed=1701   random number seed      
    -f file=../../moot/optimize/misc/auto93.csv  data file   
   
"""
from typing import Any, Iterator, Iterable
import traceback, random, time, math, sys, re
   
sys.dont_write_bytecode = True
   
Qty  = int | float
Atom = Qty | str | bool
Row  = list[Atom]
   
big  = 1e32
    
### "o" is a simple struct ----------------------------------------------
def show(x):
  "pretty print dicts with short float displays and quoted strings"
  match x:
    case dict() : x= "{"+' '.join(f":{k} {show(x[k])}" for k in x)+"}"
    case float(): x= int(x) if x == int(x) else f"{x:.3f}"
    case str()  : x= f"'{x}'"
  return x

class o(dict):
  "Dictionaries that support x.key."
  __getattr__ = dict.__getitem__
  __setattr__ = dict.__setitem__
  __repr__    = show

### Labeling --------------------------------------------------------
def label(row:Row) -> Row: 
  "Stub. Ensure row is labeled."
  return row

### Constructors -----------------------------------------------------
def Data(src:Iterable) -> o:
  "Create a data from src."
  rows  = iter(src)
  cols = Cols(next(rows))
  return o(cols = cols, 
           rows = shuffle([colsAdd(cols,row) for row in rows]))

def clone(data:Data, rows=[]) -> o:
  "Replicate sttucture of data. Optionally, add rows."
  return Data([data.cols.names] + rows)

def Cols(lst : list[str]) -> o:
  "From list of names, build the columns."
  all = {c for c,s in enumerate(lst) if s[-1] != "X"}
  y   = {c:lst[c][-1] != "-" for c in all if lst[c][-1] in "-+" }
  return o(
    names = lst, all = all, y = y,
    x     = {c for c in all if c not in y},
    nums  = {c:(big,-big) for c in all if lst[c][0].isupper()})

def colsAdd(cols:Cols, row:Row) -> Row:
  "Update the colum summaries from row."
  cols.nums = {c:(min(v,lo),max(v,hi)) 
               for c,(lo,hi) in cols.nums.items() if (v:=row[c])!="?"}
  return row

### Range generation -------------------------------------------------
def bestNum(name,x,nums1, nums2, n=20, d=0.35):
  "Find the x1,x2 range that most selects for nums1 and least selects for nums2."
  nums1.sort(); nums2.sort();
  a  = sorted(nums1 + nums2)
  sd = stdev(a)
  steps = sorted(set(a[int(i/(n-1)*(len(a)-1))] for i in range(n)))
  s1,s2,n1,n2 = sorted(nums1), sorted(nums2), len(nums1), len(nums2)
  mass  = lambda s, x1, x2, n: (chop(s, x2, True) - chop(s, x1)) / n
  best, out = -1, None
  for i in range(len(steps)):
    for j in range(i+1, len(steps)):
      x1, x2 = steps[i], steps[j]
      if x2 - x1 >= d * sd:
        delta = mass(s1, x1, x2, n1) - mass(s2, x1, x2, n2)
        if delta > best: best, out = delta, (x1, x2)
  return round(best,3), name,x, out

def bestSym(name,x,dict1: dict[str,int], dict2: dict[str,int], *_): 
  "Find the value that most selects for dict1 and least selects for dict2."
  N     = sum(dict1.values()) + sum(dict2.values())
  delta = lambda v: dict1.get(v,0)/N - dict2.get(v,0)/N
  return max((round(delta(v),3),name,x,(v,v)) for v in dict1)

### Rule generation -------------------------------------------------

def think(data: Data):
  "Make rules from best range of each x column from a few labeled rows."
  rows = data.rows = shuffle(data.rows)
  xy,x = [label(row) for row in rows[:the.Budget]], rows[the.Budget:]
  xy.sort(key = lambda r: disty(data,r))
  cut = int(the.Budget**.5)
  best,rest = xy[:cut], xy[cut:]
  ranges = []
  for x in data.cols.x: 
    catch1 = [] if x in data.cols.nums else {}
    catch2 = [] if x in data.cols.nums else {}
    [add(catch1,row[x]) for row in best]
    [add(catch2,row[x]) for row in rest]
    ranges += [(bestNum if x in data.cols.nums else bestSym)(
               data.cols.names[x],x,catch1,catch2)]
  for rule in subsets(ranges):
    yield score(rule,best,rest)
   
def score(rule,best,rest):
  "Return harmonic mean of recall and false alarm."
  best1  = [row for row in best if selects(rule,row)]
  rest1  = [row for row in rest if selects(rule,row)]
  recall = len(best1) / len(best)
  pf     = len(rest1) / len(rest)
  return 2*recall*(1-pf) / (recall + (1 - pf)), rule

def selects(rule,row):
  "Returns true if rule selects for row."
  return all(select(row,x,lo,hi) for _,_,x,(lo,hi) in rule)

def select(row,x,lo,hi):
  "Returns true if range selects for row."
  if (v:=row[x])=="?": return True
  return lo <= v <= hi

### Distance functions -----------------------------------------------
def disty(data:Data, row:Row) -> float:
  "Best range of y values to best point."
  d,n = 0,0
  for c,best in data.cols.y.items():
    lo,hi = data.cols.nums[c]
    d += abs((row[c] - lo)/(hi-lo+1e-32) - best)**the.p
    n += 1
  return (d/n)**(1/the.p)

### Misc utils ------------------------------------------------------
def shuffle(lst:list) -> list:
  "Shuffle a list, in place"
  random.shuffle(lst); return lst

Maybe={'True' :True, 'true' :True, 'Y':True, 'y':True,
       'False':False,'false':False,'N':False,'n':False}

def coerce(s:str) -> Atom:
  "Coerce a string to int, float, bool, or trimmed string"
  for fn in [int,float]:
    try: return fn(s)
    except Exception as _: pass
  s = s.strip()
  return Maybe.get(s,s)

def csv(file: str ) -> Iterator[Row]:
  "Returns rows of a csv file."
  with open(file,encoding="utf-8") as f:
    for line in f:
      if (line := line.split("%")[0]):
        yield [coerce(s) for s in line.split(",")]

def mid(a): 
  "Return average."
  return sum(a) / len(a)

def stdev(a):
  "Return standard deviation."
  l=len(a)
  if l<2 :          return 0
  if l<4 :          return (a[ -1] - a[0]) / 4
  if l<10: n=l//4;  return (a[3*n] - a[n]) / 1.35
  else   : n=l//10; return (a[9*n] - a[n]) / 2.56

def subsets(xs):
  "Return all subsets of xs."
  out = []
  for x in xs: out += [s+[x] for s in out] + [[x]]
  return out

def add(col,x):
  "Increment dictionaries or lists with x."
  if x != "?":
    if type(col) is dict: col[x] = 1 + col.get(x,0)
    else: col += [x] 

def chop(a, x, inclusive=False):
  "Returns number of points <= x (if inclusive) or < x (otherwise)."
  l, r = 0, len(a)
  while l < r:
    m = (l + r) // 2
    if (a[m] <= x if inclusive else a[m] < x): l = m + 1
    else: r = m
  return l

### Demos -----------------------------------------------------------
def eg_h(): print(__doc__,end="")

def eg__the(): print(the)
  
def eg__data(): print(Data(csv(the.file)).cols)

def eg__think():
  data = Data(csv(the.file))
  for _ in range(5):
    for g,rule in sorted(think(data)):
      print(f"{g:3f}",rule)

### Start-up --------------------------------------------------------
the = o(**{k:coerce(v) for k,v in re.findall(r"(\w+)=(\S+)",__doc__)})
   
if __name__ == "__main__":
  for n,s in enumerate(sys.argv):
    if (fn := globals().get(f"eg{s.replace('-', '_')}")):
      random.seed(the.seed)
      fn()
    else:
      for key in the:
        if s=="-"+key[0]: 
          the[key] = coerce(sys.argv[n+1])
