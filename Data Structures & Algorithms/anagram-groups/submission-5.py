class Solution:
    def groupAnagrams(self, strs: List[str]) -> List[List[str]]:
        sorted_dict = {}
        for word in strs:
            sorted_word = "".join(sorted(word))
            if sorted_word in sorted_dict:
                sorted_dict[sorted_word].append(word)
            else:
                sorted_dict[sorted_word] = [word]
        return list(sorted_dict.values())