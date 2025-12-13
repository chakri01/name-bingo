import random
import json

def generate_ticket(names_pool):
    if len(names_pool) < 15:
        raise ValueError("Need at least 15 names")
    
    selected = random.sample(names_pool, 15)
    grid = [[None] * 9 for _ in range(3)]
    
    positions = []
    for row in range(3):
        for col in range(9):
            positions.append((row, col))
    
    col_counts = [0] * 9
    row_counts = [0, 0, 0]
    
    random.shuffle(positions)
    name_idx = 0
    
    for row, col in positions:
        if name_idx >= 15:
            break
        if col_counts[col] < 2 and row_counts[row] < 5:
            grid[row][col] = selected[name_idx]
            col_counts[col] += 1
            row_counts[row] += 1
            name_idx += 1
    
    return grid

def pre_generate_tickets(names_list, count=100):
    tickets = []
    for _ in range(count):
        grid = generate_ticket(names_list)
        tickets.append({"grid": grid})
    return tickets