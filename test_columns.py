from PyTib.common import open_file
import os

bad = []
for f in os.listdir('./input'):
    if f.endswith('txt'):
        content = open_file('./input/'+f)
        if content.startswith('མཚན་བྱང་།,པར་གྲངས།,ཤོག་གྲངས།,1,མཆན་གྲངས།,པར་མ།,མཆན།'):
            bad.append(f)
for b in sorted(bad):
    print(b)
print(len(bad))
