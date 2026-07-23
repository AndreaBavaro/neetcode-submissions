class Solution:
    def groupAnagrams(self, strs: List[str]) -> List[List[str]]:
        word_dict = {}
        for word in strs:
            sorted_word = "".join(sorted(word))
            if sorted_word in word_dict:
                word_dict[sorted_word].append(word)
            else:
                word_dict[sorted_word] = [word]
        return list(word_dict.values())
                