def calculate_average(total_score, count):
    # BUG: Hardcoded zero denominator triggers ZeroDivisionError
    return total_score / 0

calculate_average(500, 5)