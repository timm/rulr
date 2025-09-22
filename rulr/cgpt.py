def think(data: Data):
  "Generate scored rules from labeled data."
  best, rest = bestRest(data)
  ranges = [makeRange(data, col, best, rest) for col in data.cols.x]
  for rule in subsets(ranges):
    yield score(rule, best, rest)

def makeRange(data, x, best, rest):
  "Find discriminating range for column x."
  def add(col,v):
    if type(col) is dict: col[v] = 1 + col.get(v,0)
    else: col += [v]

  values1 = [] if x in data.cols.nums else {}
  values2 = [] if x in data.cols.nums else {}
  [add(values1, v) for row in best if (v:=row[x]) != "?"]
  [add(values2, v) for row in rest if (v:=row[x]) != "?"]
  return (bestNum if x in data.cols.nums else bestSym)(
          data.cols.names[x], x, values1, values2)

def bestRest(data):
  "Return best and rest training groups."
  rows = shuffle(data.rows)
  labeled = [label(row) for row in rows[:the.Budget]]
  labeled.sort(key=lambda r: disty(data, r))
  cut = int(the.Budget**.5)
  return labeled[:cut], labeled[cut:]

def bestNum(name, x, good, bad, n=20, d=0.35):
  "Find numeric range that best separates good from bad."
  good, bad = sorted(good), sorted(bad)
  all_vals = sorted(good + bad)
  sd, n1, n2 = stdev(all_vals), len(good), len(bad)
  steps = sorted(set(all_vals[int(i/(n-1)*(len(all_vals)-1))]
                     for i in range(n)))
  mass = lambda nums, x1, x2, n: (chop(nums, x2, True) - chop(nums, x1))/n

  best, out = -1, None
  for i in range(len(steps)):
    for j in range(i+1, len(steps)):
      x1, x2 = steps[i], steps[j]
      if x2 - x1 >= d * sd:
        delta = mass(good, x1, x2, n1) - mass(bad, x1, x2, n2)
        if delta > best: best, out = delta, (x1, x2)
  return round(best, 3), name, x, out


#-------------------------



def chop(a, x, inclusive=False):
  # Returns count of points < x (if not inclusive) or <= x (if inclusive)
  l, r = 0, len(a)
  while l < r:
    m = (l + r) // 2
    if (a[m] <= x if inclusive else a[m] < x): l = m + 1
    else: r = m
  return l

def best_interval_percentiles(nums1, nums2, n=20, d=0.35):
  a           = sorted(nums1 + nums2)
  t           = len(a) // 10
  sd          = (a[9*t] - a[t]) / 2.56
  steps       = sorted(set(a[int(i/(n-1)*(len(a)-1))] for i in range(n)))
  s1,s2,n1,n2 = sorted(nums1), sorted(nums2), len(nums1), len(nums2)
  mass        = lambda s, x1, x2, n: (chop(s, x2, True) - chop(s, x1)) / n
  best, out   = -1, None
  for i in range(len(steps)):
    for j in range(i+1, len(steps)):
      x1, x2 = steps[i], steps[j]
      if x2 - x1 >= d * sd:
        delta = mass(s1, x1, x2, n1) - mass(s2, x1, x2, n2)
        if delta > best: best, out = delta, (x1, x2)
  return out, best
