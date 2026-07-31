def divide_numbers(a, b):
    return a / b

def test_divide():
    # To trigger an intentional failure for your repair bot, use b=0:
    assert divide_numbers(10, 0) == 0