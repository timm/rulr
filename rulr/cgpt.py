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
