#!/usr/bin/env python3 
"""
rulr.py: fast rule learning  
(c) 2025, Tim Menzies <timm@ieee.org>, MIT license.      
[src](http://github.com/timm/rulr) |
[data](http://github.com/timm/moot) 
    
Options:
    
    -h             show help   
    -B Budget=30   when growing theory, how many labels?      
    -F Few=64      sample size of data random sampling     
    -b bins=20     divisions of numerics (max-min)/b
    -d delta=0.35  Cohen's delta. ignore deltas less than d*sd
    -p p=2         distance coeffecient   
    -r repeats=10  loop counter for rule generation
    -s seed=1701   random number seed      
    -f file=../../moot/optimize/misc/auto93.csv  data file   
   
"""
from typing import Iterator, Iterable, Any
import random, time, math, sys, re
   
sys.dont_write_bytecode = True
   
Qty  = int | float
Atom = Qty | str | bool
Row  = list[Atom]
Rows = list[Row]
   
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
  rows = iter(src)
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
def bestNum(name:str, x:int, good:list[Qty], bad:list[Qty]) -> tuple:
  "Find numeric range that best separates good from bad."
  good, bad  = sorted(good), sorted(bad)
  all_vals   = sorted(good + bad)
  steps      = sorted(set(all_vals))
  sd, n1, n2 = stdev(all_vals), len(good), len(bad)
  mass       = lambda nums, x1, x2, n: (chop(nums, x2, True) - chop(nums, x1))/n
  best, out  = -1, None
  for i in range(len(steps)):
    for j in range(i+1, len(steps)):
      x1, x2 = steps[i], steps[j]
      if x2 - x1 >= the.delta * sd:
        delta = mass(good, x1, x2, n1) - mass(bad, x1, x2, n2)
        if delta > best: best, out = delta, (x1, x2)
  return round(best, 3), name, x, out

def bestSym(name,x,dict1: dict[str,int], dict2: dict[str,int]): 
  "Find the value that most selects for dict1 and least selects for dict2."
  N     = sum(dict1.values()) + sum(dict2.values())
  delta = lambda v: dict1.get(v,0)/N - dict2.get(v,0)/N
  return max((round(delta(v),3),name,x,(v,v)) for v in dict1)

### Rule generation -------------------------------------------------
def think(data: Data) -> Iterator[tuple]:
  "Generate scored rules from labeled data."
  best, rest = bestRest(data)
  ranges = [makeRange(data, col, best, rest) for col in data.cols.x]
  for rule in subsets(ranges):
    yield score(rule, best, rest)

def makeRange(data:Data, x:int, best, rest) -> tuple:
  "Find discriminating range for column x."
  def add(col,v):
    if type(col) is dict: col[v] = 1 + col.get(v,0)
    else: col += [int(v/r)*r]  # avoid spurious deltas

  if x in data.cols.nums:
     lo,hi = data.cols.nums[x]
     r = (hi-lo)/the.bins + 1e-32
     values1,values2= [],[]
  else:
     values1,values2= {},{}
  [add(values1, v) for row in best if (v:=row[x]) != "?"]
  [add(values2, v) for row in rest if (v:=row[x]) != "?"]
  return (bestNum if x in data.cols.nums else bestSym)(
          data.cols.names[x], x, values1, values2)

def bestRest(data: Data) -> tuple[Rows,Rows]:
  "Return best and rest training groups."
  rows = shuffle(data.rows)
  labeled = [label(row) for row in rows[:the.Budget]]
  labeled.sort(key=lambda r: disty(data, r))
  cut = int(the.Budget**.5)
  return labeled[:cut], labeled[cut:]

def score(rule:tuple, best:list, rest:list) -> float:
  "Return harmonic mean of recall and false alarm."
  best1  = [row for row in best if selects(rule,row)]
  rest1  = [row for row in rest if selects(rule,row)]
  recall = len(best1) / len(best)
  pf     = len(rest1) / len(rest)
  return 2*recall*(1-pf) / (recall + (1 - pf)), rule

def selects(rule: tuple, row:Row) -> bool:
  "Returns true if rule selects for row."
  return all(select(row,x,lo,hi) for _,_,x,(lo,hi) in rule)

def select(row:Row, x:int, lo:Any, hi:Any) -> bool:
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

# What is "true" (used by the coerce function)?
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

def mid(a: list[Qty]) -> float: 
  "Return average."
  return sum(a) / len(a)

def stdev(a: list[Qty]) -> float:
  "Return standard deviation."
  l=len(a)
  if l<2 :          return 0
  if l<4 :          return (a[ -1] - a[0]) / 4
  if l<10: n=l//4;  return (a[3*n] - a[n]) / 1.35
  else   : n=l//10; return (a[9*n] - a[n]) / 2.56

def subsets(xs: list) -> list[list]:
  "Return all subsets of xs."
  out = []
  for x in xs: out += [s+[x] for s in out] + [[x]]
  return out

def chop(a:list, x:Any, inclusive=False) -> int:
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
  for _ in range(the.repeats):
    for g,rule in sorted(think(data)):
      print(f"{g:3f}",rule)

### Start-up --------------------------------------------------------
the = o(**{k:coerce(v) for k,v in re.findall(r"(\w+)=(\S+)",__doc__)})

def rulrMain(settings, funs):
  for n,s in enumerate(sys.argv):
   if (fn := funs.get(f"eg{s.replace('-', '_')}")):
     random.seed(settings.seed)
     fn()
   else:
     for key in settings:
       if s=="-"+key[0]: 
         settings[key] = coerce(sys.argv[n+1])

if __name__ == "__main__": rulrMain(the,globals())
  
