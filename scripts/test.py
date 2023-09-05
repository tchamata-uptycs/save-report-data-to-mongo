a = (2,3)

try:
    b,c = a
    print(b,c)
    print(type(c))
    print(type(b))
except:
    b=a
    print(type(a))
    print(type(b))

