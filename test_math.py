from src.math_utils import divide_numbers

def test_divide():
    assert divide_numbers(10, 2) == 5
    assert divide_numbers(10, 0) == 0