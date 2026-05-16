class Solution:
    def topKFrequent(self, nums: List[int], k: int) -> List[int]:
        nums_dict = {}
        for number in nums:
            if number in nums_dict:
                nums_dict[number] += 1
            else:
                nums_dict[number] = 1
        return heapq.nlargest(k, nums_dict, key=lambda x: nums_dict[x])