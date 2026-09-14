class Solution:
    def productExceptSelf(self, nums: List[int]) -> List[int]:
        prefix_array = [1] * len(nums)
        suffix_array = [1] * len(nums)
        final_array = [1] * len(nums)
        current_prefix = 1
        current_suffix = 1
        for i in range(1,len(nums)):
            current_prefix *= nums[i-1]
            prefix_array[i] = current_prefix
        for i in range(len(nums)-2, -1, -1):
            current_suffix *= nums[i+1]
            suffix_array[i] = current_suffix
        for i in range(0,len(nums)):
            final_array[i] = prefix_array[i] * suffix_array[i]
        return final_array