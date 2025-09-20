#!/usr/bin/env python3 
"""
rulr.py: fast rule learning  
(c) 2025, Tim Menzies <timm@ieee.org>, MIT license.      
code: http://github.com/timm/rulr   
data: http://github.com/timm/moot  
Options:
    
      -A  Any=4             on init, how many initial guesses?   
      -B  Budget=30         when growing theory, how many labels?      
      -C  Check=5           budget for checking learned model   
      -F  Few=64            sample size of data random sampling     
      -l  leaf=3            min items in tree leaves   
      -p  p=2               distance coeffecient   
      -s  seed=1234567891   random number seed      
      -f  file=../moot/optimize/misc/auto93.csv    data file   
      -h                     show help   
   
"""
from types import SimpleNamespace as o
from typing import Any, Iterator, Iterable
import traceback, random, time, math, sys, re

sys.dont_write_bytecode = True

Qty  = int | float
Atom = Qty | str | bool
Row  = list[Atom]

big  = 1e32

the = o(budget=32,
        data="../../moot/optimize/config/auto93.csv")

#--------------------------------------------------------------------
def label(row:Row) -> Row: return row

def Data(src:Iterable):
  src  = iter(src)
  cols = Cols(next(rows))
  return o(cols = cols, 
           rows = shuffle([addCols(cols,row) for row in rows]))

def clone(data, src=[]):
  return Data([data.cols.names] + src)

def Cols(lst : list[str]) -> o:
  all = {c for c,s in enumerate(lst) if s[-1] !=" X"}
  y = {c:lst[c][0] != "-" for c in all if lst[c][-1] in "-+" })
  return o(
    names=names, all=all, y=y,
    x={c for c in all if c not in y},
    nums={c:(big,-big) for c in all if lst[c][0].isupper())

def colsAdd(cols,row):
  cols.nums = {c:(min(v,lo),max(v,hi)) 
               for c,(lo,hi) in cols.nums.items() if (v:=row[c])!="?"}
  return row

def think(data):
  xy,x = [label(row) for row in rows[:budget]], rows[budget:]
  xy.sort(key=lambda r: disty(data,r))
  n = int(budget**.5)
  best,rest = xy[:n], xy[n:]
  if c in enumerate(all):
    best1 = [x for row in best if (v:=row[c]) != "?"]
    rest1 = [x for row in rest if (v:=row[c]) != "?"]
    if c not in data.cols.y: 
      if c in data.cols.nums:
        print(best_range(best1,rest1))

def best_range(nums1, nums2, n=20, d=0.35):
  a      = sorted(nums1 + nums2)
  t      = len(a) // 10
  sd     = (a[9*t] - a[t]) / 2.56
  steps  = sorted(set(a[int(i/(n-1)*(len(a)-1))] for i in range(n)))
  s1,s2,n1,n2 = sorted(nums1), sorted(nums2), len(nums1), len(nums2)
  mass  = lambda s, x1, x2, n: (chop(s, x2, True) - chop(s, x1)) / n
  best, out = -1, None
  for i in range(len(steps)):
    for j in range(i+1, len(steps)):
      x1, x2 = steps[i], steps[j]
      if x2 - x1 >= d * sd:
        delta = mass(s1, x1, x2, n1) - mass(s2, x1, x2, n2)
        if delta > best: best, out = delta, (x1, x2)
  return out, best

def chop(a, x, inclusive=False):
  # Returns count of points < x (if not inclusive) or <= x (if inclusive)
  l, r = 0, len(a)
  while l < r:
    m = (l + r) // 2
    if (a[m] <= x if inclusive else a[m] < x): l = m + 1
    else: r = m
  return l

def disty(data:Data, row:Row) -> float:
  d,n = 0,0
  for c,best in data.cols.y.items():
    lo,hi = data.cols.nums[c]
    d += abs((row[c] - lo)/(hi-lo+1e-32) - best)**the.p
    n += 1
  return (d/n)**(1/the.p)

def shuffle(lst:list) -> list:
  "shuffle a list, in place"
  random.shuffle(lst); return lst

def coerce(s:str) -> Atom:
  "coerce a string to int, float, bool, or trimmed string"
  for fn in [int,float]:
    try: return fn(s)
    except Exception as _: pass
  s = s.strip()
  return {'True':True,'False':False}.get(s,s)

def csv(file: str ) -> Iterator[Row]:
  "Returns rows of a csv file."
  with open(file,encoding="utf-8") as f:
    for line in f:
      if (line := line.split("%")[0]):
        yield [coerce(s) for s in line.split(",")]

