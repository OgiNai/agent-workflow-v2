def gsnm():

    un = input("Enter a number:")
    
    def gn(n):
        if n == 0:
            return 0
        elif n == 1:
            return 1
        else:
            return gn(n-1) + gn(n-2)

    return f"Guess what is the number {gn(un)}"