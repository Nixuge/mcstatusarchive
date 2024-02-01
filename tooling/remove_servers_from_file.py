# Remove servers in the aa.txt file.
# Only implemented in the memleak branch, basically add all failing servers to it for better testing.

with open("aa.txt", "r") as f:
    toremove = f.readlines()


with open("../servers.json", "r") as f:
    content = f.read()


for server in toremove:
    server = server.replace("\n", "")
    content = content.replace(f'        "{server}",\n', '')

with open("../servers.json", "w") as f:
    f.write(content)