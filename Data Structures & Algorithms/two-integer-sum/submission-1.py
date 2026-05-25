class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        seen = {}
        for index, num in enumerate(nums):
            difference = target - num
            if difference in seen:
                return [seen[difference], index]
            else:
                seen[num] = index