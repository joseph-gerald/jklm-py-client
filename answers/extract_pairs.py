import json
import os

current_dir = os.path.dirname(__file__)
file_names = os.listdir(current_dir + "/popsauce")
file_names_length = len(file_names)

pairs = []

for index, file_name in enumerate(file_names):
    with open(current_dir + "/popsauce/" + file_name, "r") as f:
        data = f.read()
        data = json.loads(data)

        index += 1
        print(f"{index}/{file_names_length} {file_name}")
        pairs.append((file_name.split(".")[0], data["answer"]))

with open(current_dir + "/popsauce_pairs.txt", "w", encoding="utf-8") as f:
    for pair in pairs:
        f.write(f"{pair[0]}:{pair[1]}\n")