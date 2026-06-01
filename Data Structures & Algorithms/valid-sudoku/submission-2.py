
class Solution: 
    def isValidSudoku(self, board: List[List[str]]) -> bool:
        rows = {}
        columns = {}
        boxes = {}   
        for row_number in range(0,len(board)):
            rows[row_number] = []
            for column_number in range(0,len(board)):
                number = board[row_number][column_number]
                box_id = (row_number // 3, column_number // 3)
                if number == ".":
                    continue
                if box_id in boxes:
                    if number in boxes[box_id]:
                        return False
                    else:
                        boxes[box_id].append(number)
                else:
                    boxes[box_id] = [number]
                if row_number in rows:
                    if number in rows[row_number]:
                        return False
                    else:
                        rows[row_number].append(number)
                else:
                    rows[row_number] = [number]
                if column_number in columns:
                    if number in columns[column_number]:
                        return False
                    else:
                        columns[column_number].append(number)
                else:
                    columns[column_number] = [number]
        return True
                    
                    
                    





        