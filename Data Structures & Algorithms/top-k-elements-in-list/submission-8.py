class Solution:
    def topKFrequent(self, nums: List[int], k: int) -> List[int]:
        freq_dict = {}
        buckets = [[] for _ in range(len(nums) + 1)]   
        result = []     
        for num in nums:
            if num in freq_dict:
                freq_dict[num] += 1
            else:
                freq_dict[num] = 1
        for value, frequency in freq_dict.items():
            buckets[frequency].append(value)
        for frequency in range(len(nums), 0, -1):
            for value in buckets[frequency]:
                result.append(value)
                if len(result) == k:
                    return result