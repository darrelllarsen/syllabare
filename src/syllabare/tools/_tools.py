# Trie implementation from
# https://www.aleksandrhovhannisyan.com/blog/trie-data-structure-implementation-in-python/,
# with addition of longest_match()

class TrieNode:
    def __init__(self, text = ''):
        self.text = text
        self.children = dict()
        self.is_word = False

class PrefixTree:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        current = self.root
        for i, char in enumerate(word):
            if char not in current.children:
                prefix = word[0:i+1]
                current.children[char] = TrieNode(prefix)
            current = current.children[char]
        current.is_word = True
    
    def find(self, word):
        '''
        Returns the TrieNode representing the given word if it exists
        and None otherwise.
        '''
        current = self.root
        for char in word:
            if char not in current.children:
                return None
            current = current.children[char]

        if current.is_word:
            return current

    def __child_words_for(self, node, words):
        '''
        Private helper function. Cycles through all children
        of node recursively, adding them to words if they
        constitute whole words (as opposed to merely prefixes).
        '''
        if node.is_word:
            words.append(node.text)
        for letter in node.children:
            self.__child_words_for(node.children[letter], words)

    def starts_with(self, prefix):
        '''
        Returns a list of all words beginning with the given prefix, or
        an empty list if no words begin with that prefix.
        '''
        words = list()
        current = self.root
        for char in prefix:
            if char not in current.children:
                # Could also just return words since it's empty by default
                return list()
            current = current.children[char]

        self.__child_words_for(current, words)
        return words

    def size(self, current = None):
        '''
        Returns the size of this prefix tree, defined
        as the total number of nodes in the tree.
        '''
        # By default, get the size of the whole trie, starting at the root
        if not current:
            current = self.root
        count = 1
        for letter in current.children:
            count += self.size(current.children[letter])
        return count

    # Supplemental
    def longest_match(self, text):
        word = ''
        current = self.root
        for char in text:
            if char not in current.children:
                return word
            else:
                current = current.children[char]
                if current.is_word:
                    word = current.text
        return word
