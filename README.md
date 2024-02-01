# syllabare
Regular expressions across mapped representations.

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

## Documentation

Most functionality is documented in the [re documentation](https://docs.python.org/3/library/re.html).

Documentation on the unique features of syllabare is available in the [wiki](https://github.com/darrelllarsen/syllabare/wiki), where you will (eventually) also find discussion of inherent differences between `re` and `syllabare`, and how syllabare addresses them. (At present, see the [Special Considerations](https://github.com/darrelllarsen/kre/wiki#special-considerations-differences-from-re) section of the related project, kre, for relevant discussion.) *It is strongly recommended that users familiarize themselves with these differences.*
