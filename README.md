[![Purpose](https://img.shields.io/badge/purpose-XAI%20%7C%20Optimization-purple?logo=target&logoColor=white)](https://github.com/timm/rulr)
[![Python](https://img.shields.io/badge/language-Python-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?logo=open-source-initiative&logoColor=white)](https://github.com/timm/rulr/blob/main/LICENSE.md)
[![Docs](https://img.shields.io/badge/docs-online-orange?logo=readthedocs&logoColor=white)](https://timm.github.io/rulr/)
[![GitHub](https://img.shields.io/badge/github-repo-black?logo=github&logoColor=white)](https://github.com/timm/rulr)


# Rulr

Fast generator of rules.

## Install

```bash
git clone http://github.com/timm/moot
git clone http://github.com/timm/rulr

cd rulr/rulr
chmod +x rulr.py
./rulr.py -h
```

This should print:

```
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
```

## Example

For a larger example, 19 columns, 50,000+ rows, generated 655,000+ rules. in 16 seconds.

```
time ./rulr.py -f ../../moot/optimize/config/SS-N.csv   --think |wc
```

For a smaller example,
we generated 75 rules, sorted by  harmonic mean of (1-falseAlarm) and recall.
This example has four x columns and 399 rows.
The following output was generated in 0.02 seconds.

```
./rulr.py -f ../../moot/optimize/misc/auto93.csv    --think

Score     (      attr1  col1 lo1, hi1           attr2   col2 lo2,hi2
--------- ----   -----  ---- ---  ----         -------  ---- --- ---

0.000000 [(0.24, 'Model', 3, (71, 73)), (0.0, 'origin', 4,  (3,  3))]
0.000000 [(0.28, 'Model', 3, (80, 82)), (0.067, 'origin', 4, (3, 3))]
0.000000 [(0.4, 'Clndrs', 0, (4, 6)), (0.28, 'Model', 3, (80, 82)), (0.067, 'origin', 4, (3, 3))]
0.000000 [(0.4, 'Clndrs', 0, (4, 6)), (0.76, 'Volume', 1, (97, 140)), (0.28, 'Model', 3, (80, 82)), (0.067, 'origin', 4, (3, 3))]
0.000000 [(0.56, 'Clndrs', 0, (3, 4)), (0.24, 'Model', 3, (71, 73)), (0.0, 'origin', 4, (3, 3))]

...

.888889 [(0.8, 'Volume', 1, (79, 134)), (0.68, 'Model', 3, (80, 82))]
0.888889 [(0.88, 'Volume', 1, (79, 122)), (0.6, 'Model', 3, (77, 81))]
0.936170 [(0.48, 'Clndrs', 0, (4, 6)), (0.88, 'Volume', 1, (79, 122))]
0.936170 [(0.88, 'Volume', 1, (79, 122))]
0.958333 [(0.44, 'Clndrs', 0, (3, 4)), (0.76, 'Volume', 1, (70, 108)), (0.56, 'Model', 3, (76, 82))]
0.958333 [(0.76, 'Volume', 1, (70, 108)), (0.56, 'Model', 3, (76, 82))]
```


