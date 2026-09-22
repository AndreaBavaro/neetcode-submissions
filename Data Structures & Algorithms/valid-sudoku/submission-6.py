class Solution: 
    def isValidSudoku(self, board: List[List[str]]) -> bool:
        boxes = {}
        rows = {}
        columns = {}
        
        for row_index, row in enumerate(board):
            if row_index not in rows:
                rows[row_index] = set()
                
            for column_index, column in enumerate(row):
                number = board[row_index][column_index]  # 1. Read the cell first
                
                if number == ".":                        # 2. Skip empty cells
                    continue
                
                box_number = (row_index // 3) * 3 + (column_index // 3)
                
                if column_index not in columns:
                    columns[column_index] = set()
                if box_number not in boxes:
                    boxes[box_number] = set()
                
                # 3. Check for duplicates
                if number in rows[row_index] or number in columns[column_index] or number in boxes[box_number]:
                    return False
                
                # 4. Record the seen number
                rows[row_index].add(number)
                columns[column_index].add(number)
                boxes[box_number].add(number)
                
        return True