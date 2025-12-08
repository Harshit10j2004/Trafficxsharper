import glob

location = "/home/ubuntu/exp"
v1 = v2 = v3 = v4 = v5 = v6 = v7 = 0
count = 0

for file_path in glob.glob(f"{location}/*.txt"):
    print(file_path)
    with open(file_path) as f:
        line = f.read().strip()
        parts = line.split(",")
        values = parts[1:]

        x1, x2, x3, x4, x5, x6, x7 = map(float, values)

        v1 += x1
        v2 += x2
        v3 += x3
        v4 += x4
        v5 += x5
        v6 += x6
        v7 += x7

    count=count+1

if count > 0:
    v1 /= count
    v2 /= count
    v3 /= count
    v4 /= count
    v5 /= count
    v6 /= count
    v7 /= count

print("Averages:")
print(v1, v2, v3, v4, v5, v6, v7)