class Solution:
    def encode(self, strings: List[str])-> str:
        encoded_string = ""
        for string in strings:
            delimiter = str(str(len(string)) + "+")
            encoded_string += delimiter + string
        return encoded_string
    
    def decode(self, string: str) -> List[str]:
        decoded_strings = []
        i = 0
        substring_length = ""
        while i < len(string):
            if string[i] != "+":
                substring_length += string[i]
                i += 1
            else:
                decoded_strings.append(string[i+1:i+int(substring_length)+1])
                i = i + int(substring_length) + 1
                substring_length = ""
        return decoded_strings


