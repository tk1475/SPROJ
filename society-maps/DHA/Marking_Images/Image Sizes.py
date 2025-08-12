import cv2

f = open("New Text Document.txt")
for line in f.readlines():
    data = line.split(':')
    img = cv2.imread(data[0])
    coords = data[1].strip().split(",")
    f = open("Image_Mappings.txt",'a')
    f.write("{}:{},{},{},{},{},{}\n".format(data[0],coords[0],coords[1],coords[2],coords[3],img.shape[0],img.shape[1]))
    f.close()

