class Solution:
    def hasDuplicate(self, nums: List[int]) -> bool:
        unique_values = set(nums)
        return len(unique_values) != len(nums)