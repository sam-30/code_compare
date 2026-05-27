def add(a, b):
    return a + b

def multiply(x, y):
    return x * y

class Calculator:
    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
