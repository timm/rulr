#!/usr/bin/env python3 
"""
rulr.py: fast rule learning  
(c) 2025, Tim Menzies <timm@ieee.org>, MIT license.      
[src](http://github.com/timm/rulr) |
[data](http://github.com/timm/moot) 
    
Options:
    
    -h             show help   
    -B Budget=30   when growing theory, how many labels?      
    -D Dull=0.01   when remaining mass dull, extend ranges 
    -F Few=64      sample size of data random sampling     
    -T Top=12      max number of subsets to explore 
    -b bins=20     divisions of numerics (max-min)/b
    -d delta=0.35  Cohen's delta. ignore deltas less than d*sd
    -p p=2         distance coeffecient   
    -r repeats=10  loop counter for rule generation
    -s seed=1701   random number seed      
    -f file=../../moot/optimize/misc/auto93.csv  data file   
   
"""
from typing import Iterator, Iterable, Any
import traceback, random, time, math, sys, re
   
sys.dont_write_bytecode = True
   
Qty  = int | float
Atom = Qty | str | bool
Row  = list[Atom]
Rows = list[Row]
Col  = "Num" | "Sym"

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

### Column Objects (from ezr) -------------------------------------------
def Num(at=0, s=" ") -> "Num": 
  "Create a numeric column summarizer"
  return o(it=Num, at=at, txt=s, n=0, mu=0, m2=0, sd=0, 
           hi=-big, lo=big, more = 0 if s[-1] == "-" else 1)

def Sym(at=0, s=" ")-> "Sym": 
  "Create a symbolic column summarizer"
  return o(it=Sym, at=at, txt=s, n=0, has={})
 
def add(x: o, v: Any) -> Any:
  "Incrementally update Syms, Nums, or Data"
  if v == "?": return v
  x.n += 1
  if x.it is Sym: 
    x.has[v] = 1 + x.has.get(v,0)
  elif x.it is Num:
    x.lo, x.hi = min(v, x.lo), max(v, x.hi)
    d     = v - x.mu
    x.mu += d / x.n
    x.m2 += d * (v - x.mu)
    x.sd  = 0 if x.n < 2 else (max(0,x.m2)/(x.n-1))**.5
  elif x.it is Data:
    x.rows.append([add(col, v[col.at]) for col in x.cols.all])
  return v

def norm(num: o, v: float) -> float:  
  "Normalize a value to 0..1 range"
  return v if v=="?" else (v - num.lo) / (num.hi - num.lo + 1E-32)

### Labeling --------------------------------------------------------
def label(row:Row) -> Row: 
  "Stub. Ensure row is labeled."
  return row

### Constructors -----------------------------------------------------
def Data(src:Iterable) -> o:
  "Create a data from src."
  rows = iter(src)
  data = o(it=Data, cols = Cols(next(rows)), rows = [])
  [add(data,row) for row in rows]
  return data

def clone(data: o, rows=[]) -> o:
  "Replicate structure of data. Optionally, add rows."
  return Data([data.cols.names] + rows)

def Cols(lst : list[str]) -> o:
  "From list of names, build the columns."
  y_cols, x_cols, all_cols = [], [], []
  for c, s in enumerate(lst):
    if s[-1] != "X":
      col = (Num if s[0].isupper() else Sym)(c, s)
      all_cols.append(col)
      (y_cols if col.txt[-1] in "-+" else x_cols).append(col)
  
  return o(names = lst, all = all_cols, y = y_cols, x = x_cols)

def distysort(data: o, rows=None) -> list[Row]:
  "Sort rows by distance to best y-values"
  return sorted(rows or data.rows, key=lambda r: disty(data,r))

def disty(data: o, row: Row) -> float:
  "Distance from row to best y-values"
  d, n = 0, 0
  for col in data.cols.y:
    d += abs(norm(col, row[col.at]) - col.more)**the.p
    n += 1
  return (d/n)**(1/the.p)

### Range generation -------------------------------------------------
def bestNum(name:str, x:int, good:list[Qty], bad:list[Qty]) -> tuple:
  "Find numeric range that best separates good from bad."
  good, bad  = sorted(good), sorted(bad)
  all_vals   = sorted(good + bad)
  steps      = sorted(set(all_vals))
  all_num    = Num()
  [add(all_num, v) for v in all_vals]
  sd, n1, n2 = all_num.sd, len(good), len(bad)
  mass       = lambda nums, x1, x2, n: (chop(nums, x2, True) - chop(nums, x1))/n
  best, out  = -1, None
  for i in range(len(steps)):
    for j in range(i+1, len(steps)):
      x1, x2 = steps[i], steps[j]
      if x2 - x1 >= the.delta * sd:
        x1, x2 = tail_extend(all_vals, x1, x2)
        delta = mass(good, x1, x2, n1) - mass(bad, x1, x2, n2)
        if delta > best: best, out = delta, (x1, x2)
  return round(best, 3), name, x, out

def tail_extend(xs:list[Qty], x1:float, x2:float):
  "Extend x1,x2 to -inf,+inf if tails are below threshold."
  n = len(xs)
  left  = chop(xs, x1) / n
  right = (n - chop(xs, x2, True)) / n
  if left  < the.Dull: x1 = -big
  if right < the.Dull: x2 =  big
  return x1, x2

def bestSym(name,x,dict1: dict[str,int], dict2: dict[str,int]): 
  "Find the value that most selects for dict1 and least selects for dict2."
  N     = sum(dict1.values()) + sum(dict2.values())
  delta = lambda v: dict1.get(v,0)/N - dict2.get(v,0)/N
  return max((round(delta(v),3),name,x,(v,v)) for v in dict1)

### Rule generation -------------------------------------------------
def think(data: o) -> Iterator[tuple]:
  "Generate scored rules from labeled data."
  best, rest = bestRest(data)
  ranges = [makeRange(data, col, best, rest) for col in data.cols.x]
  ranges = sorted(ranges)[-the.Top:]
  print(ranges)
  for rule in subsets(ranges):
    yield score(rule, best, rest)

def makeRange(data: o, col: o, best, rest) -> tuple:
  "Find discriminating range for column."
  values1, values2 = (Num(), Num()) if col.it is Num else (Sym(), Sym())
  
  if col.it is Num:
    # Binned values with side-effect of populating values1/values2
    r = (col.hi - col.lo)/the.bins + 1e-32
    good = [add(values1, int(v/r)*r) for v in [row[col.at] for row in best]]
    bad  = [add(values2, int(v/r)*r) for v in [row[col.at] for row in rest]]
    return bestNum(col.txt, col.at, good, bad)
  else:
    [add(values1, row[col.at]) for row in best]
    [add(values2, row[col.at]) for row in rest]
    return bestSym(col.txt, col.at, values1.has, values2.has)

def bestRest(data: o) -> tuple[Rows,Rows]:
  "Return best and rest training groups."
  rows = shuffle(data.rows[:])
  labeled = distysort(data, [label(row) for row in rows[:the.Budget]])
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
     try: 
       random.seed(settings.seed); fn()
     except Exception as e: 
       print("Error:", e); traceback.print_exc()
   else:
     for key in settings:
       if s=="-"+key[0]: 
         settings[key] = coerce(sys.argv[n+1])

if __name__ == "__main__": rulrMain(the,globals())
