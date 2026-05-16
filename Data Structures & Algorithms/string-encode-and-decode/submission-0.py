class Solution:

    def encode(self, strs: List[str]) -> str:
        encoded_string = ""
        for word in strs:
            delimiter = str(len(word)) + "-"
            encoded_string += delimiter + word
        return encoded_string

    def decode(self, s: str) -> List[str]:
        decoded_word_list = []
        word_delimiter = ""
        i = 0
        while i < len(s):
            if s[i] == "-":
                word_length = int(word_delimiter)
                decoded_word_list.append(s[i+1: i+1+word_length])
                word_delimiter = ""
                i += 1 + word_length
            else:
                word_delimiter += s[i]
                i += 1
        return decoded_word_list

        



