class Solution:
    def longestConsecutive(self, nums: List[int]) -> int:
        nums_set = set(nums)
        max_longest = 0
        for number in nums_set:
            longest = 1
            current = number
            if number - 1 in nums_set:
                continue
            while current + 1 in nums_set:
                longest += 1
                current += 1
            max_longest = max(max_longest,longest)
        return max_longest


