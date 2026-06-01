class Solution:
    def productExceptSelf(self, nums: List[int]) -> List[int]:
        prefix_array = []
        suffix_array = [0] * len(nums)
        output = []
        prefix = 1
        suffix = 1
        for i in range(0,len(nums)):
            prefix_array.append(prefix)
            prefix *= nums[i]
        for i in range(len(nums)-1,-1,-1):
            suffix_array[i] = suffix
            suffix *= nums[i]
        for i in range(0,len(nums)):
            output.append(prefix_array[i] * suffix_array[i])
        return output