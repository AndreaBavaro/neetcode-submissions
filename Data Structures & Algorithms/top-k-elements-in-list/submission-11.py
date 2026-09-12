class Solution:
    def topKFrequent(self, nums: List[int], k: int) -> List[int]:
        k_frequent = []
        buckets = [[]for _ in range(len(nums))]
        frequency_dict = {}
        for number in nums:
            if number in frequency_dict:
                frequency_dict[number] += 1
            else:
                frequency_dict[number] = 1
        for number in frequency_dict:
            buckets[(frequency_dict[number]-1)].append(number)
        for i in range(len(buckets) - 1, -1, -1):
            for number in buckets[i]:
                k_frequent.append(number)
                if len(k_frequent) == k:
                    return k_frequent
