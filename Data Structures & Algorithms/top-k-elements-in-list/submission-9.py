class Solution:
    def topKFrequent(self, nums: List[int], k: int) -> List[int]:
        frequency_dict = {}
        buckets = [[] for _ in range(0,len(nums)+1)]
        result = []
        print(buckets)
        for num in nums:
            if num in frequency_dict:
                frequency_dict[num] += 1
            else:
                frequency_dict[num] = 1
        print(frequency_dict)
        for number,frequency in frequency_dict.items():
            buckets[frequency].append(number)
        for num in range(len(buckets)-1,0,-1):
            for value in buckets[num]:
                result.append(value)
                if len(result) == k:
                    return result