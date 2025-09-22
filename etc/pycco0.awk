BEGIN { FS="\"" }
      { sub(/-----.*/,"") }
b4 ~ /^(def|class)[ \t]/ && NF >= 3 { 
        print "\n# " $2; print(b4); b4=""; next}
      { if(b4) print b4; b4=$0 }
  END { print b4 }
