import json
import re

with open("pc_tools/tokenizer.json", "r") as f:
    t = json.load(f)

vocab = t["model"]["vocab"]
inv_vocab = {v: k for k, v in vocab.items()}

n_vocab = 32000
blob = []
off = [0]

for i in range(n_vocab):
    if i in inv_vocab:
        token = inv_vocab[i]
        
        # byte fallback token check
        match = re.match(r"^<0x([0-9A-Fa-f]{2})>$", token)
        if match:
            # this is a byte token!
            b = bytes([int(match.group(1), 16)])
            blob.extend(b)
            off.append(len(blob))
        else:
            # replace U+2581 with a space
            token = token.replace("\u2581", " ")
            
            # encode to utf-8
            b = token.encode("utf-8")
            blob.extend(b)
            off.append(len(blob))
    else:
        off.append(len(blob))

with open("src/generated/vocab.h", "w") as f:
    f.write("#ifndef VOCAB_H\n#define VOCAB_H\n")
    f.write(f"#define VOCAB_N {n_vocab}\n")
    f.write(f"static const unsigned char VOCAB_BLOB[{len(blob)}] = {{\n  ")
    for i, b in enumerate(blob):
        f.write(f"{b},")
        if (i + 1) % 20 == 0:
            f.write("\n  ")
    f.write("\n};\n")
    f.write(f"static const unsigned int VOCAB_OFF[{n_vocab + 1}] = {{\n  ")
    for i, o in enumerate(off):
        f.write(f"{o},")
        if (i + 1) % 20 == 0:
            f.write("\n  ")
    f.write("\n};\n#endif\n")
