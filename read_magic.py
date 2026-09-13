with open("projects/s3-tiny-stories/pc_tools/stories15M_q4.bin", "rb") as f:
    magic = f.read(4)
    print("File magic:", magic.hex(), list(magic))
