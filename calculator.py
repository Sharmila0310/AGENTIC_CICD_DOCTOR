def add(a, b):
    # Intentional bug
    return a - b

def test_add():
    assert add(2, 3) == 5