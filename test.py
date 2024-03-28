import os

src = "E01-SOL37-100-G3"
# for root, dirs, files in os.walk("/Volumes/Shares-1/Studio/Photo/Catalog"):
#     for file in files:
#         if src in file:
#             print(root, file)


from search_file import search_file

a = search_file(src)

for i in a:
    print(a)

