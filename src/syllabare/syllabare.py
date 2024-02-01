#Syllabare: Regular expressions across mapped representations
#Author: Darrell Larsen
#
#Distributed under GNU General Public License v3.0

"""
This module is built on top of re.  See re documentation for information
on special characters, etc, not affected by this module.

This module provides support for conducting regular expression searches
and substitutions over mapped text. When the user provides a mapping
from one set of representations (REP1) to another (REP2), the input 
string is mapped from REP1 onto REP2. The regular expression operation 
is carried out over REP2. In the case of searches, the results are 
mapped back to their position in REP1 and returned as a Syllabare_Match
object, or as the relevant substrings, depending on the return type of
the underlying re function. In the case of substitutions, substituted 
portions are mapped back to characters available in REP1, when possible.
Syllabare_Match objects are designed to behave like re.Match objects, 
with a few additional attributes.  As such, the output of this library 
may usually be handled in the same manner as the output of the standard 
re library. 

By default, syllabare does NOT track boundaries between input 
characters from REP1. Depending on the mapping, this may lead to
unexpected results. In such cases, the use of boundaries can provide
more control over the searches, at the expense of requiring slightly 
more complicated regular expression patterns. To use boundaries, pass in
`boundaries=True` to any function, indicate the boundary delimiter with
the `delimiter` keywork argument (';' by default), and then include the
delimiter in search pattern and/or replacement argument. The delimiter
should not be included in the input string, as it will be added
automatically. Note that when the search string contains characters not 
in REP1, delimiters are only added around characters present in REP1.

TODO:
    provide option for allowing mixed input (i.e., whether to require
    all characters of input string to match keys of mapping or not)

    in the case of sub(n), provide option for indicating failure to
    map substitutions back to REP1 rather than simply outputting
    uncombined string

    add "smart" delimiters - if the chosen delimiter is present in the
    search string, find a different character not present in the search
    string to use, and then replace any instances of the chosen
    delimiter from the pattern and replacement arguments with this new
    character

    _recombine() should be able to map substrings of input back to REP1 
    when no match is found for the entire input by attempting to match
    successively smaller substrings from the input back to REP1. The
    directionality of this search (lr vs rl) should be available as an
    option.

    allow multiple forms of mapping (json, Python dictionary, sequences)

    accept user-provided mapping functions in place of simple mappings
    (see kre)
"""

import re, json

# Make flags from re library accessible 
from re import (A, ASCII, DEBUG, DOTALL, I, IGNORECASE, L, LOCALE, M,
        MULTILINE, T, TEMPLATE, U, UNICODE, VERBOSE, X)

MAPS = {"map": None,
        "reverse": None,
        }

def set_map(json_file):
    with open(json_file, 'r') as f:
        MAPS["map"] = json.load(f)
    MAPS["reverse"] = {value: key for key, value in MAPS["map"].items()}

def validate_map(_map):
    # Disallow duplicate values
    if len(_map.values()) != len(set(_map.values())):
        return False
    else:
        return True

### Public interface

def search(pattern, string, flags=0, boundaries=False, delimiter=';',
        empty_es=True):
    return compile(pattern, flags).search(string, 
            boundaries=boundaries,
            delimiter=delimiter, empty_es=empty_es)

def match(pattern, string, flags=0, boundaries=False, delimiter=';', empty_es=True):
    return compile(pattern, flags).match(string, 
            boundaries=boundaries,
            delimiter=delimiter, empty_es=empty_es)

def fullmatch(pattern, string, flags=0, boundaries=False, delimiter=';', empty_es=True):
    return compile(pattern, flags).fullmatch(string, 
            boundaries=boundaries,
            delimiter=delimiter, empty_es=empty_es)

def sub(pattern, repl, string, count=0, flags=0, boundaries=False, 
        delimiter=';', empty_es=True, syllabify='minimal'):
    """
    Returns unsubstituted characters in the same format as input (i.e.,
    as syllable characters or individual letters) except as affected by 
    the syllabify options.

    syllabify options: 
        'full' (linearize + syllabify entire string)
        'none' (affected characters are output without syllabification)
        'minimal' (affected characters are syllabified prior to output)
        'extended' (will attempt to combine affected characters with
            preceding/following characters to create syllables)
    """
    return compile(pattern, flags).sub(repl, string, count=count,
            boundaries=boundaries, 
            delimiter=delimiter, empty_es=empty_es, 
            syllabify=syllabify)

def subn(pattern, repl, string, count=0, flags=0, boundaries=False, 
        delimiter=';', empty_es=True, syllabify='minimal'):
    """
    Similar to sub(), but returns tuple with count as second element.
    """
    return compile(pattern, flags).subn(repl, string, count=count, 
            boundaries=boundaries,
            delimiter=delimiter, empty_es=empty_es, 
            syllabify=syllabify)

def split(pattern, string, maxsplit=0, flags=0, boundaries=False, 
        delimiter=';', empty_es=True):
    return compile(pattern, flags).split(string, maxsplit=maxsplit, 
            boundaries=boundaries, delimiter=delimiter, empty_es=empty_es,)

def findall(pattern, string, flags=0, boundaries=False, delimiter=';', empty_es=True):
    return compile(pattern, flags).findall(string, 
            boundaries=boundaries,
            delimiter=delimiter, empty_es=empty_es,)

def finditer(pattern, string, flags=0, boundaries=False, delimiter=';', empty_es=True):
    return compile(pattern, flags).finditer(string, 
            boundaries=boundaries,
            delimiter=delimiter, empty_es=empty_es,)

def compile(pattern, flags=0):
    return _compile(pattern, flags)

def purge():
    # note that this will purge all regular expression caches, 
    # not just those created through syllabare
    re.purge()

def escape(pattern):
    return re.escape(pattern)

### Private interface

def _compile(pattern, flags):
    return Syllabare_Pattern(pattern, flags)

class Syllabare_Pattern:
    def __init__(self, pattern, flags):
        self.pattern = pattern #original, unlinearized
        self.flags = flags
        self.linear = self.pattern # REDUNDANT - TO BE REMOVED
        self.Pattern = re.compile(self.pattern, flags) # re.Pattern obj
        self.groups = self.Pattern.groups

        # Extract from compiled non-linearized string so access format
        # can match input format
        self._re = re.compile(self.pattern)
        self.groupindex = self._re.groupindex

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "syllabare.compile(%s)" % repr(self.pattern)

    def search(self, string, *args, boundaries=False, delimiter=';', empty_es=True):
        ls, pos_args, _ = self._process(string, *args,
                boundaries=boundaries, delimiter=delimiter)

        match_ = self.Pattern.search(ls.linear, *pos_args)

        if match_:
            return _make_match_object(self.pattern, string, match_,
                    *args,
                    boundaries=boundaries,
                    delimiter=delimiter, empty_es=empty_es,
                    )
        else:
            return match_

    def match(self, string, *args, boundaries=False, delimiter=';', empty_es=True):
        ls, pos_args, iter_span = self._process(string, *args,
                boundaries=boundaries, delimiter=delimiter)
       
        for span in iter_span:
            match_ = self.Pattern.match(ls.linear, *span)
            if match_:
                return _make_match_object(self.pattern, string, match_,
                        *args,
                        boundaries=boundaries,
                        delimiter=delimiter, empty_es=empty_es,
                        )
        else:
            return match_

    def fullmatch(self, string, *args, boundaries=False, delimiter=';', empty_es=True):
        ls, pos_args, iter_span = self._process(string, *args,
                boundaries=boundaries, delimiter=delimiter)

        for span in iter_span:
            match_ = self.Pattern.fullmatch(ls.linear, *span)
            if match_:
                return _make_match_object(self.pattern, string, match_,
                        *args,
                        boundaries=boundaries,
                        delimiter=delimiter, empty_es=empty_es,
                        )
        else:
            return match_

    def sub(self, repl, string, count=0, boundaries=False, 
            delimiter=';', empty_es=True, syllabify='minimal'):
        """
        Returns unsubstituted characters in the same format as input (i.e.,
        as syllable characters or individual letters) except as affected by 
        the syllabify options.

        syllabify options: 
            'none' (affected characters are output without syllabification)
            'minimal' (affected characters are syllabified prior to output)
            'extended' (will attempt to combine affected characters with
                the immediately preceding/following characters to create 
                syllables when it minimizes stand-alone Korean letters)
            'full' (linearize + syllabify entire string; deletes
                    boundaries prior to syllabifying string)
        """
        # Linearize string
        ls = Mapping(string, 
                boundaries=boundaries,
                delimiter=delimiter,
                    )
        
        # Find the spans where substitutions will occur.
        matches = self.finditer(ls.linear)

        # Iterate over matches to extract subbed spans from delimited string

        # For each affected syllable, store the number of subs it is
        # involved in, and the initial and final indices of the affected
        # characters in both the linear and mapped del spans. 
        subs = dict()
        # Strutucture: subs = {1: {'num_subs': int, 
        #                           'del_span': tuple(start, end),
        #                           'linear_span': tuple(start, end)},
        #                      2: {...}, 
        #                      ...}
        
        i = 0 # number non-overlapping sub spans (no increment for shared syllable)
        for n, match_ in enumerate(matches):
            # limit matches to number indicated by count (0=no limit)
            if 0 < count <= n:
                break
            span = match_.span()

            # Case of empty string match at end of string
            if span[0] == len(ls.linear):
                start = len(ls.linear)
            # Normal case
            else:
                start = ls.lin2del[span[0]]
            end = ls.lin2del[span[1]-1]+1

            # Were there multiple subs from the same syllable?
            if i > 0 and subs[i-1]['del_span'][1] > start:
                # increment number of subs for this syllable
                subs[i-1]['num_subs'] += 1

                # update the end pos of the affected del_span
                subs[i-1]['del_span'] = (
                        subs[i-1]['del_span'][0], end)

                # update the end pos of the associated linear_span
                subs[i-1]['linear_span'] = (
                        subs[i-1]['linear_span'][0], span[1])
            else:
                subs[i] = dict()
                sub = subs[i]
                sub['num_subs'] = 1
                sub['del_span'] = (start, end)
                sub['linear_span'] = span
                i += 1

        # Keep track of extra letters in the subbed syllables which
        # preceded/followed the actual substitution
        for sub in subs.values():
            sub_start, sub_end = sub['linear_span']

            # Case: string-final empty string match
            if sub_start == len(ls.linear):
                syl_start = len(ls.linear)
            # Normal case
            else:
                syl_start = ls._get_syl_start(sub_start)
            syl_end = ls._get_syl_end(sub_end-1)

            pre_sub_letters = ls.linear[syl_start:sub_start]
            post_sub_letters = ls.linear[sub_end:syl_end]

            sub['extra_letters'] = (pre_sub_letters,post_sub_letters)

        # Extract the text from the unchanged indices so we can return them
        # without change. (If we use tools.syllabify to reconstruct the entire
        # string, inputs like 가ㅎ (linearized to ㄱㅏㅎ) would be returned 
        # as 갛 even if they weren't matches for substitution. We want to 
        # avoid this.) 
        safe_text = []
        for n in range(len(subs) + 1):
            start = 0 if n == 0 else subs[n-1]['del_span'][1]
            end = len(ls.delimited) if n == len(subs) else subs[n]['del_span'][0]
            safe_text.append(ls.delimited[start:end])

        # Carry out substitutions one by one* to identify the indices of each 
        # changed section. *Multiple subs affecting same syllable are
        # carried out at same time.
        extra = 0 # Tracks added/substracted number of letters after sub
        prev_string = ls.linear
        num_subs = 0 # For carrying out subs incrementally
        for sub in subs.values():
            # Carry out next substitution(s)
            num_subs = num_subs + sub['num_subs']
            subbed_string = self.Pattern.sub(repl, ls.linear,
                    count=num_subs)

            # Calculate the start and end indices of the inserted substitution
            sub_start = sub['linear_span'][0] + extra
            extra += len(subbed_string) - len(prev_string)
            sub_end = sub['linear_span'][1] + extra

            # Combine the substitution(s) with the extra letters from
            # affected syllables
            syl_text = sub['extra_letters'][0]
            syl_text += subbed_string[sub_start:sub_end]
            syl_text += sub['extra_letters'][1]
            sub['subbed_syl'] = syl_text

            prev_string = subbed_string

        # Attempt to construct Hangul characters to the desired degree of 
        # syllabification.
        output = ''
        for n in range(len(safe_text)):
            output += safe_text[n]
            if n < len(subs):
                new_text = subs[n]['subbed_syl']
                if syllabify == 'minimal': 
                    output += _recombine(new_text)
                elif syllabify == 'extended':
                    new_text = Mapping(new_text).linear
                    if safe_text[n+1]:
                        post = safe_text[n+1][0]
                        safe_text[n+1] = safe_text[n+1][1:]
                        post = _recombine(post)
                        new_text += post
                    if output:
                        pre = output[-1]
                        output = output[:-1]
                        post = _recombine(pre)
                        new_text = pre + new_text
                    output += _recombine(new_text)
                else:
                    output += new_text

        # Remove the delimiter from the output
        # This should precede 'full' syllabify option
        if boundaries == True:
            output = output.replace(delimiter, '')

        if syllabify == 'full':
            output = _recombine(Mapping(output).linear)

        if syllabify == 'none':
            pass

        return output

    def subn(self, repl, string, count=0, boundaries=False, 
            delimiter=';', empty_es=True, syllabify='minimal'):
        
        # Must limit substitutions to max of count if != 0
        res = self.findall(string,
            boundaries=boundaries, delimiter=delimiter,
            empty_es=empty_es)
        if res:
            sub_count = len(res)
        else:
            sub_count = 0
        if 0 < count < sub_count:
            sub_count = count

        return (self.sub(repl, string, count=count, 
            boundaries=boundaries, delimiter=delimiter,
            empty_es=empty_es, syllabify=syllabify), 
            sub_count)

    def split(self, string, maxsplit=0, boundaries=False, 
            delimiter=';', empty_es=True):
        raise NotImplementedError 

    def findall(self, string, *args, boundaries=False, delimiter=';', empty_es=True):
        ls, pos_args, _ = self._process(string, *args,
                boundaries=boundaries, delimiter=delimiter)

        match_ = self.Pattern.findall(ls.linear, *pos_args)

        # For all patterns found, find their position in the original text
        # and return the syllable(s) they are part of
        if match_:
            pos = pos_args[0]
            match_list = []
            for item in match_:
                # Because we've already linearized the string, we don't
                # pass in boundaries or delimiter here.
                sub_match = self.search(ls.linear, pos)

                source_string_span = _get_regs(sub_match, ls)[0]
                match_list.append(
                        string[source_string_span[0]:source_string_span[1]]
                        )

                # Update start pos for next iteration.
                pos = sub_match.span()[1]

                # Was the match an empty string?
                if sub_match.span()[0] == sub_match.span()[1]:
                    # Increment pos manually
                    pos += 1
                    # Ensure syllable-internal empty strings matches
                    # remain empty, if wanted
                    if empty_es == True:
                        match_list[-1] = ''

            return match_list
        else:
            return None

    def finditer(self, string, *args, boundaries=False, delimiter=';', empty_es=True):
        ls, pos_args, _ = self._process(string, *args,
                boundaries=boundaries, delimiter=delimiter)

        match_ = self.Pattern.finditer(ls.linear, *pos_args)

        # For all re.Match objects in match_
        if match_:
            pos = pos_args[0]
            match_list = []
            for item in match_:
                sub_match = self.search(ls.linear, pos)
                match_list.append(_make_match_object(self.pattern, string, 
                    sub_match, *args, boundaries=boundaries,
                    delimiter=delimiter, empty_es=empty_es))
                pos = sub_match.span()[1]

                # Was the match an empty string?
                if sub_match.span()[0] == sub_match.span()[1]:
                    # Increment pos manually
                    pos += 1
            return iter(match_list)
        else:
            return None

    def _process(self, string, *args, boundaries, delimiter):
        """
        Perform processes common to search, match, fullmatch, findall,
        and finditer
        """
        ls = Mapping(string, boundaries=boundaries, delimiter=delimiter)
        pos_args, iter_span = self._process_pos_args(ls, *args)

        return ls, pos_args, iter_span

    def _process_pos_args(self, _linear, *args):
        """
        Map the pos and endpos args to their corresponding linear positions.

        When boundaries == True, pos and endpos expand to include boundaries

        Returns:
            tuple: pos and endpos, mapped to position in linear string
            iter_span (tuple of tuples): tuples of indices for `match` 
                and `fullmatch` to iterate through, if any (empty if no
                pos arg was provided)
        """
        output = []
        map_ = _linear.lin2orig
        orig_size = len(_linear.original)
        iterate = True
        iter_span = []

        ### Fill in missing args
        # No pos arg?
        if len(args) == 0:
            iterate = False
            args = [0]
        # No endpos arg? 
        if len(args) == 1:
            args = [args[0], len(map_)]

        ### Limit pos / endpos to string length
        for arg in args:
            if 0 <= arg < orig_size:
                output.append(map_.index(arg))
            # >= length of string?
            elif arg >= orig_size:
                output.append(len(map_)) 
            # Less than 0?
            else:
                output.append(0)
        
        if iterate == True:
            # which indices should be iterated through?
            for n, item in enumerate(map_[output[0]:], output[0]):
                if item == map_[output[0]]:
                    iter_span.append(tuple([n, output[1]]))
                else:
                    break
        else:
            iter_span.append(output)


        # If pos is preceded by a boundary marker, expand to include it
        # No need to do this for endpos
        if output[0] > 0:
            if map_[output[0]-1] == None:
                output[0] -= 1
                if iterate == True:
                    iter_span = [tuple(output)] + iter_span

        return tuple(output), tuple(iter_span)

class Mapping:
    """
    Contains three levels of representation of the input, maps between
    the levels, and methods for navigation, string extraction, and
    mapping representation.

    - levels:
        original: input string without alteration
        delimited: same as original if boundaries == False; otherwise, 
            input string with delimiters placed around Korean characters
            (both syllables and letters)
        linear: linearized form of delimited; i.e., Korean characters
            are all replaced with Korean letter sequences
    - maps: 
        del2orig,
            'This is ;한;글;'
        lin2del, 
        del2lin_span, 
        lin2orig
    - example
        - levels:
            original: 'This is 한글ㅋㅋ'
            delimited: 'This is ;한;글;ㅋ;ㅋ;'
            linear: 'This is ;ㅎㅏㄴ;ㄱㅡㄹ;ㅋ;ㅋ;'
        - maps:
            - Note that maps *to* original level map delimiters to None.
            del2orig: (0,1,2,3,4,5,6,7,None,8,None,9,None,10,None,11,None)
                       T,h,i,s, ,i,s, ,;...,한,;...,글,;...,ㅋ,;...,ㅋ,;...
            lin2del: (0,1,2,3,4,5,6,7,8,9,9,9,10,11,11,11,12,13,14,15,16)
                      T,h,i,s, ,i,s, ,;,ㅎ,ㅏ,ㄴ,;,ㄱ,ㅡ,ㄹ,;ㅋ,;,ㅋ,;
            lin2orig: (0,1,2,3,4,5,6,7,None,8,8,8,None,9,9,9,None,10,None,11,None)
        - span maps:
            - Note that span maps *to* original level map delimiters to
              indices of the form (n, n) (where start=end).
            del2lin_span:
                    ((0,1), #T
                    (1,2), #h
                    (2,3), #i
                    (3,4), #s
                    (4,5), # 
                    (5,6), #i
                    (6,7), #s
                    (7,8), # 
                    (8,9), #;
                    (9,12), #한 -> ㅎㅏㄴ
                    (12,13), #;
                    (13,16), #글 -> ㄱㅡㄹ
                    (16,17), #;
                    (17,18), ㅋ
                    (18,19), #;
                    (19,20), ㅋ
                    (20,21), #;


    Developer notes: 
    - new levels and their mappings should be created simultaneously
    - abbreviations: {delimiter: del; original: orig; linear: lin}
        - use abbreviations exclusively within functions
        - use full name as class attribute
    """
    def __init__(self, string, boundaries=False, delimiter=';'):
        self.boundaries = boundaries
        self.delimiter = delimiter

        # levels of representation and mappings
        self.original = string
        self.delimited, self.del2orig = self._delimit()
        self.linear, self.lin2del = self._linearize()
        self.lin2orig = tuple(self.del2orig[n] for n in self.lin2del)
        self.del2lin_span = self._get_del2lin_span()
        self.del2orig_span = self._get_del2orig_span()
        self.lin2orig_span = self._get_lin2orig_span()
        self.lin2del_span = self._get_lin2del_span()
        self.orig2del_span = self._get_orig2del_span()
        self.orig2lin_span = self._get_orig2lin_span()

    def validate_delimiter(self) -> None:
        """
        When boundaries == True, checks whether choice of delimiter is
        present in string.
        
        This method should only be called on the 'string' input; it
        should not be called on the 'pattern' input.
        """
        if self.boundaries == True and self.delimiter in self.original:
            raise ValueError('Delimiter must not be present in original string')

    def _delimit(self): # returns (del_str, tuple(del2orig_))
        del_str = ''
        del2orig_ = []
        orig_idx = 0
        just_saw_delimiter = False

        for char_ in self.original:
            if char_ in MAPS["map"].keys():
                
                # add delimiter in front of Korean syllable
                if self.boundaries==True and not just_saw_delimiter:
                    del_str += self.delimiter
                    del2orig_.append(None)

                # add the character
                del_str += char_
                del2orig_.append(orig_idx)

                # add delimiter symbol at end of Korean syllable
                if self.boundaries==True:
                    del_str += self.delimiter
                    del2orig_.append(None)

            else:
                del_str += char_
                del2orig_.append(orig_idx)

            orig_idx += 1
            just_saw_delimiter = (del_str[-1] == self.delimiter)

        return (del_str, tuple(del2orig_))

    def _linearize(self): # returns (lin_str, tuple(lin2del_))
        """
        Linearizes delimited string by splitting up Korean syllables into 
        individual Korean letters.

        Outputs:
            lin_str (str): linearized version of delimited string
            lin2del_ (tuple): index of character positions in delimited string
        """

        lin_str = ''
        lin2del_ = []
        lin2orig_str = []
        lin_idx = 0

        for char_ in self.delimited:
            if char_ in MAPS["map"].keys():
                # append the linearized string
                for letter in MAPS["map"][char_]:
                    lin_str += letter
                    lin2del_.append(lin_idx)

                lin2orig_str.append(char_)

            else:
                lin_str += char_
                lin2del_.append(lin_idx)
            lin_idx += 1
        return (lin_str, tuple(lin2del_))

    def _get_del2lin_span(self): # returns tuple(span_map)
        span_map = []
        start = 0
        mapped_idx = 0

        for n in range(len(self.lin2del)+1):
            # Case: end of string
            if n == len(self.lin2del):
                span_map.append((start, n))

            # Case: from same syllable as previous
            elif self.lin2del[n] == mapped_idx:
                pass

            # Case: from start of syllable
            else:
                span_map.append((start, n))
                start = n
                mapped_idx += 1

        return tuple(span_map)

    def _get_del2orig_span(self): # returns tuple(span_map)
        span_map = []
        end_idx = 0

        for idx in self.del2orig:
            if idx != None:
                end_idx = idx + 1
                span_map.append((idx, end_idx))
            else:
                span_map.append((end_idx, end_idx))

        return tuple(span_map)

    def _get_lin2orig_span(self):
        span_map = []
        for n in range(len(self.lin2orig)):
            span_map.append(self.del2orig_span[self.lin2del[n]])
        
        return tuple(span_map)

    def _get_lin2orig_span_old(self): # DELETE AFTER TEST
        span_map = []
        end_idx = 0

        for idx in self.lin2orig:
            if idx != None:
                end_idx = idx+1
                span_map.append((idx, end_idx))
            else:
                span_map.append((end_idx, end_idx))

        return tuple(span_map)

    def _get_lin2del_span(self):
        span_map = []
        end_idx = 0

        for idx in self.lin2del:
            if idx != None:
                end_idx = idx+1
                span_map.append((idx, end_idx))
            else:
                span_map.append((end_idx, end_idx))

        return tuple(span_map)

    # Forward maps
    def _get_orig2del_span(self): #Revise - no need for span in this direction
        span_map = []
        map_ = self.del2orig
        _pam = map_[::-1]

        for n in range(len(self.original)):
            start = map_.index(n)
            end = len(map_) - _pam.index(n)
            span_map.append((start, end))

        return tuple(span_map)

    def _get_orig2lin_span(self):
        span_map = []
        map_ = self.lin2orig
        _pam = map_[::-1]

        for n in range(len(self.original)):
            start = map_.index(n)
            end = len(map_) - _pam.index(n)
            span_map.append((start, end))

        return tuple(span_map)

    def _get_syl_span(self, idx):
        return self.del2lin_span[self.lin2del[idx]]

    def _get_syl_start(self, idx):
        return self._get_syl_span(idx)[0]

    def _get_syl_end(self, idx):
        return self._get_syl_span(idx)[1]

    def show_original_alignment(self):
        print('Index\tOriginal\torig2del_span\tdel2orig\tdel2orig_span\tDelimited\tdel2lin_span\tLinear')
        for n, idx in enumerate(self.del2orig):
            orig_idx = idx if idx != None else ''
            orig_str = '' if orig_idx == '' else self.original[orig_idx]
            start, end = self.del2lin_span[n]
            print(f'{n}|{orig_idx}', '\t', orig_str, '\t\t',
                    '\t' if self.del2orig[n] == None else
                            self.orig2del_span[self.del2orig[n]], '\t',
                    self.del2orig[n], '\t\t',
                    self.del2orig_span[n], '\t', self.delimited[n],
                    '\t\t', self.del2lin_span[n], '\t',
                    self.linear[start:end])

    def show_linear_alignment(self):
        print('Index\tLinear\tlin2del\tlin2del_span\tDelimited\tlin2orig\tlin2orig_span\tOriginal')
        for n, span_ in enumerate(self.lin2orig_span):
            d2o_span = self.del2orig_span[self.lin2del[n]]
            print(n, '\t', self.linear[n], '\t', self.lin2del[n], '\t', self.lin2del_span[n],
                    '\t', self.delimited[slice(*self.lin2del_span[n])],
                    '\t\t', self.lin2orig[n], '\t\t', span_,'\t', self.original[slice(*span_)])

def _make_match_object(pattern, string, Match, *args, boundaries=False, 
        delimiter=';', empty_es=True):
    # TODO: need to pass in flags as well
    """
    Instantiates a Syllabare_Match object

    Args:
        pattern: original (unlinearized) pattern
        string: original (unlinearized) string
        Match: re.Match object

    Returns:
        Syllabare_Match object
    """
    # Extract pos, endpos args, if provided
    pos_args = [0, len(string)] # re defaults
    if args:
        for n, arg in enumerate(args):
            pos_args[n] = arg

    ls = Mapping(string, boundaries=boundaries, delimiter=delimiter)
    lp = Mapping(pattern)
    match_obj = Syllabare_Match(
            re = compile(pattern),
            string = string,
            linear = ls.linear,
            pos = pos_args[0],
            endpos = pos_args[1],
            regs = _get_regs(Match, ls),
            Match = Match,
            string_mapping = ls,
            pattern_mapping = lp,
            empty_es = empty_es,
            )
    return match_obj 


def _get_regs(Match, linear_obj):
    # TODO: update doc
    """
    Map the index positions of the match to their corresponding 
    positions in the source text

    Args:
        Match: re.Match object carried out over the linearized text
        linear_obj: Mapping object

    Returns:
        list: a list containing the corresponding span positions in the
            original (non-linearized) text
    """
    regs = []
    l = linear_obj
    for span in Match.regs:
        # (-1, -1) used for groups that did not contibute to the match
        if span == (-1, -1):
            regs.append(span)
            continue

        # Did it match a string-initial empty string?
        elif span == (0, 0):
            regs.append(span)
            continue

        # Did it match a string-final empty string?
        elif span == (len(Match.string), len(Match.string)):
            idx = len(l.original)
            regs.append((idx, idx))
            continue

        else:
            span_start = l.lin2orig_span[span[0]][0]

            # re.MATCH object's span end is index *after* final character,
            # so, we need to subtract one to get the index of the character 
            # to map back to the original, then add one to the result to 
            # get the index after this character
            span_end = l.lin2orig_span[span[1]-1][1]
            regs.append((span_start, span_end))
    
    return tuple(regs)

class Syllabare_Match:
    """
    The Syllabare_Match class is intended to mimic the _sre.SRE_Match object,
    but to provide results based on the positions of the Match objects
    in the original input rather than the linearized input which is fed
    to the re module functions. In essence, it converts a _sre.SRE_Match
    object into a new one by replacing the positional arguments of
    letters to their corresponding index positions in the unlinearized
    text.
    A few additional methods are defined to allow the user to obtain data on
    both the original and modified strings created by syllabare.
    """
    def __init__(self, endpos = None, pos = 0, re = None, regs = None,
            string = None, linear = None, Match=None,
            string_mapping=None, pattern_mapping=None, empty_es=True):
       
        # underlying re.Match object 
        # contains same attributes as above but for linearized string
        self.Match = Match 
        self.empty_es = empty_es

        self.string = string
        self.pos = pos #int
        # re, _re are based on non-linearized pattern
        self.re = re # Syllabare_Pattern object (syllabare.compile)
        self._re = self.re.Pattern #SRE_Pattern (re.compile)
        self.regs = regs #tuple
        self.endpos =  endpos # int
        self.lastindex = Match.lastindex
        self.lastgroup = self._get_lastgroup()
   
        #Supplemental in Syllabare
        self.linear = linear
        self.string_mapping = string_mapping
        self.pattern_mapping = pattern_mapping

    def __repr__(self):
        return "<Syllabare.Syllabare_Match object; span=%r, match=%r>" % (
                self.span(), self.group(0))

    def __getitem__(self, group):
        return self.group(group)


    def expand() -> str:
        """
        expand(template) -> str.
        Return the string obtained by doing backslash substitution
        on the string template, as done by the sub() method.

        NOTE: not well documented. Example use:
        number = re.match(r"(\d+)\.(\d+)", "24.1632")
        print(number.expand(r"Whole: \1 | Fractional: \2"))
        (output) 'Whole: 24 | Fractional: 1632'

        TODO: When implementing, will need to add argument for degrees 
        of syllabification, as with sub() function.
        
        TODO: Will need to treat linearization of pattern different from
        string. Need to maintain identifiers of named groups such as  
        (?P<숫자>\d+) 
        """
        raise NotImplementedError 
    
    def group(self, *args) -> str or tuple:
        """
        group([group1, ...]) -> str or tuple.
        Return subgroup(s) of the match by indices or names.
        For 0 returns the entire match.
        """
        res = []

        if not args:
            args = [0,]
        for arg in args:
            idx = arg
            # convert named groups to group indices
            if isinstance(idx, str):
                idx = self.re.groupindex[idx]
            # non-matching capture group?
            if self.regs[idx] == (-1, -1):
                res.append(None)
            # empty string match? (see discussion on special treatment)
            elif self.empty_es == True and self.Match.group(idx) == '':
                res.append('')
            else:
                res.append(self.string[slice(*self.regs[idx])])

        if len(res) == 1:
            return res[0]
        else:
            return tuple(res)

    def groupdict(self, default=None) -> dict:
        """
        groupdict([default=None]) -> dict.
        Return a dictionary containing all the named subgroups of the 
        match, keyed by the subgroup name. The default argument is used
        for groups that did not participate in the match
        """
        inv_map = {value: key for key, value in
                self.re.groupindex.items()}

        apply_default = lambda d: default if d == None else d

        return {inv_map[n]: apply_default(self.group(n)) for n in inv_map.keys()}

    def groups(self, default=None) -> tuple:
        """
        groups([default=None]) -> tuple.
        Return a tuple containing all the subgroups of the match, from
        1. The default argument is used for groups that did not 
        participate in the match
        """
        g = []
        for n in range(1, len(self.regs)):
            if self.group(n) == None:
                g.append(default)
            else:
                g.append(self.group(n))
        return tuple(g)

    def span(self, *args) -> tuple:
        """
        span([group]) -> tuple.
        For MatchObject m, return the 2-tuple (m.start(group),
        m.end(group)).
        """
        if args:
            idx = args[0]
            if isinstance(idx, str):
                idx = self.re.groupindex[idx]
        else:
            idx = 0
        return self.regs[idx]

    def start(self, *args) -> int:
        """
        start([group=0]) -> int.
        Return index of the start of the substring matched by group.
        """
        return self.span(*args)[0]

    def end(self, *args) -> int:
        """
        end([group=0]) -> int.
        Return index of the end of the substring matched by group.
        """
        return self.span(*args)[1]

    def _get_lastgroup(self):
        # No named capture groups? Return None
        if len(self.groupdict()) == 0:
            return None

        # Inverse map of dictionary
        inv_map = {value: key for key, value in
                self.re.groupindex.items()}
        
        # Last matched capturing group not in dictionary
        # -> not a named group.
        if self.lastindex not in inv_map.keys():
            return None

        # Return the name of the last named matched capturing group
        else:
            return inv_map[self.lastindex]

def _recombine(chars):
    # PRELIMINARY VERSION FOR TEST
    # NEEDS TO BE ABLE TO RECOMBINE MULTIPLE KEYS
    if chars in MAPS["reverse"].keys():
        return MAPS["reverse"][chars]
    else:
        return chars
