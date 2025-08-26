from typing import Optional, List
import difflib
import re


def fuzzy_pattern_match(
    text: str,
    pattern: str,
    threshold: float = 0.7
) -> Optional[str]:
    """Find the best fuzzy match for a pattern in text.

    Args:
        text: Text to search in
        pattern: Pattern to search for (without regex syntax)
        threshold: Similarity threshold (0.0 to 1.0)

    Returns:
        Best matching substring or None
    """
    # Split text into potential matches (words, lines, etc.)
    candidates = text.split(' ')

    # Find the best match
    best_match = difflib.get_close_matches(pattern, candidates, n=1, cutoff=threshold)
    return best_match[0] if best_match else None


def fuzzy_regex_search(
    text: str,
    pattern: str,
    threshold: float = 0.7
) -> List[str]:
    """Search for fuzzy matches of a regex pattern.

    Args:
        text: Text to search
        pattern: Regex pattern
        threshold: Similarity threshold

    Returns:
        List of fuzzy matches
    """
    # First try exact regex match
    exact_matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
    if exact_matches:
        return exact_matches

    # If no exact matches, try fuzzy matching
    # Extract the literal parts from the pattern for fuzzy matching
    # This is a simplified approach - you may need to adapt based on your patterns
    literal_parts = re.sub(r'[().*+?^${}[\]|\\]', '', pattern).split()

    matches = []
    for part in literal_parts:
        fuzzy_match = fuzzy_pattern_match(text, part, threshold)
        if fuzzy_match:
            matches.append(fuzzy_match)

    return matches


def fuzzy_pattern_extract(text: str, pattern: str, threshold: float = 0.6) -> Optional[List[str]]:
    """Extract captured groups from fuzzy pattern matching.

    Args:
        text: Text to search in
        pattern: Regex pattern with capture groups
        threshold: Similarity threshold for fuzzy matching

    Returns:
        List of captured groups or None if no match
    """
    # Step 1: Try exact regex match first
    exact_match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if exact_match:
        return list(exact_match.groups())

    # Step 2: Create a more flexible version of the pattern
    flexible_pattern = make_pattern_flexible(pattern)
    flexible_match = re.search(flexible_pattern, text, re.DOTALL | re.IGNORECASE)
    if flexible_match:
        return list(flexible_match.groups())

    # Step 3: Extract the literal parts and search for them
    literal_parts = extract_literal_parts(pattern)

    # Step 4: Find fuzzy matches for each literal part
    fuzzy_matches = []
    for part in literal_parts:
        candidates = get_text_candidates(text)
        best_match = difflib.get_close_matches(part, candidates, n=1, cutoff=threshold)
        if best_match:
            fuzzy_matches.append(best_match[0])

    if not fuzzy_matches:
        return None

    # Step 5: Try to extract data around the fuzzy matches
    return extract_groups_from_fuzzy_matches(text, fuzzy_matches, pattern)


def make_pattern_flexible(pattern: str) -> str:
    """Make a regex pattern more flexible for PDF extraction issues."""
    # Replace literal spaces with flexible whitespace
    flexible = pattern.replace(' ', r'\s*')
    flexible = flexible.replace('\\n', r'\s*')

    # Handle common OCR errors
    char_substitutions = {
        'O': '[O0Qo]',
        '0': '[0Oo]',
        'I': '[I1l|]',
        '1': '[1Il|]',
        'S': '[S5$]',
        'E': '[E3]',
        'T': '[T7]',
        'R': '[R]',  # R is usually stable
        'N': '[N]',  # N is usually stable
    }

    for char, replacement in char_substitutions.items():
        # Only replace characters that are not part of regex syntax
        flexible = re.sub(f'(?<!\\\\){char}(?![+*?{{}}\\]\\)|\\[])', replacement, flexible)

    return flexible


def extract_literal_parts(pattern: str) -> List[str]:
    """Extract literal text parts from a regex pattern."""
    # Remove regex syntax to get literal parts
    # This is a simplified approach - you may need to enhance based on your patterns

    # Remove capturing groups syntax but keep the content
    no_groups = re.sub(r'\(([^)]*)\)', r'\1', pattern)

    # Remove quantifiers and other regex syntax
    literals = re.sub(r'[.*+?^${}[\]|\\]', ' ', no_groups)

    # Split and filter out empty parts
    parts = [part.strip() for part in literals.split() if part.strip() and len(part.strip()) > 2]

    return parts


def get_text_candidates(text: str) -> List[str]:
    """Get potential candidates from text for fuzzy matching."""
    # Split by various delimiters to get potential matches
    candidates = []

    # Split by whitespace and newlines
    candidates.extend(text.split())

    # Split by lines
    candidates.extend(text.split('\n'))

    # Get n-grams of words (sequences of 2-3 words)
    words = text.split()
    for i in range(len(words) - 1):
        candidates.append(' '.join(words[i:i+2]))  # 2-grams
        if i < len(words) - 2:
            candidates.append(' '.join(words[i:i+3]))  # 3-grams

    # Remove duplicates and filter by length
    candidates = list(set(c for c in candidates if len(c) > 1))

    return candidates


def extract_groups_from_fuzzy_matches(text: str, fuzzy_matches: List[str], original_pattern: str) -> List[str]:
    """Extract capture groups based on fuzzy matches."""
    # Find the positions of fuzzy matches in the original text
    match_positions = []
    for match in fuzzy_matches:
        # Find the best position for this match in the text
        pos = find_best_position(text, match)
        if pos is not None:
            match_positions.append((pos, match))

    if not match_positions:
        return None

    # Sort by position
    match_positions.sort(key=lambda x: x[0])

    # Try to extract data between/around the matches
    groups = []

    # For your specific SECTION LETTER pattern
    if "SECTION" in fuzzy_matches and "LETTER" in fuzzy_matches:
        # Look for a single letter after "LETTER"
        for match_pos, match_text in match_positions:
            if "LETTER" in match_text:
                # Look for a letter after this position
                after_text = text[match_pos + len(match_text):match_pos + len(match_text) + 50]
                letter_match = re.search(r'[A-Z]', after_text)
                if letter_match:
                    groups.append(letter_match.group())
                    break

    return groups if groups else None


def find_best_position(text: str, target: str) -> Optional[int]:
    """Find the best position of target in text using fuzzy matching."""
    # Try exact match first
    pos = text.find(target)
    if pos != -1:
        return pos

    # Try case-insensitive
    pos = text.lower().find(target.lower())
    if pos != -1:
        return pos

    # Use sliding window for fuzzy matching
    best_ratio = 0
    best_pos = None

    for i in range(len(text) - len(target) + 1):
        substring = text[i:i + len(target)]
        ratio = difflib.SequenceMatcher(None, target.lower(), substring.lower()).ratio()
        if ratio > best_ratio and ratio > 0.6:  # Threshold
            best_ratio = ratio
            best_pos = i

    return best_pos


def debug() -> None:
    """public debug method for development use."""
    pattern = r"(?:SECTION\nLETTER:\n)(.*)"
    text = r"""SECTION\nLETTER:\nB SHEET\nNUMBER:\n3 4\nOF SHEET SYSTEM LAYOUT"""

    # Test the fuzzy extraction
    result = fuzzy_pattern_extract(text, pattern, threshold=0.6)
    print(f"Fuzzy extraction result: {result}")

    # Test with the full text
    full_text = """46 47 IFD1012ARPB2 I F F R D O 1 N 01 T 2 D CR O P O B R 2 I A FD N 1 T 0 I- 1 R 2 E A C R I P R X C 1\nANTI-RECIRC CARRIER CHECK\nRESET\nRELEASE\nFRONT DOOR FRONT DOOR PART\nORC- G 0 D 1G R D 01 R E 0 S 1 2 -D .4 5HMI ANTI-R C E H C E I C R K C PART IFD1 P 0 R 1 E 2 S F E D N P T PE31 BK04 NORTH\n120.15.35.52 IFD1012FDPPE30\nGDR01PWS6\nHOT CON 24 T V R D O C L POWER BK04 BK04 G G D D R R 0 0 1 1 E S S B 1 K . 0 1 8 6 G G D D R R 0 0 1 1 E B S K 1 0 .1 5 6 GD G R D 0 R 1 0 E 1 S R 1 F . 2 16\n192.168.1.68 192.168.1.105 192.168.1.152\nIFD.1029 IFD.1012 GDR01PWS17 GDR01BK04\n24VDC GDR01ES1.16\nCONTROL POWER 192.168.1.104\nGDR01PWS23\nCONT 2 R 4 O V L D P C I O F W D. E 10 R 30 IFA.1011 I A FD N 1 T 0 I- 1 R 0 E A C R I P R B C 1 IF R D E C 1 A A 0 R R 1 R 0 D C I O E R R O P R B1 I A FD N 1 T C 0 I H - 1 R E 0 E C A C K R I P R E C 1\nX RESET RELEASE\nREAR DOOR REAR DOOR PART BK03\nANTI-RECIRC PART PRESENT\nTFD.1031 CHECK IFD1010RDPPE31\nIFD1010RDPPE30\nIFD.1010\nBK03\nGDR01PWS24 BK03\n24VDC GDR01SBK15\nCONTROL POWER GDR01ES2.13 GDR01SBK07 GDR01BK03 GDR01RF1\nTFA.1032 IFD.1033 VCFD.1009 192.168.1.75 GDR01ES1.16 GDR01ES1.16 GDR01ES1.16\nGDR01SBK06 192.168.1.67 192.168.1.103 192.168.1.151\nGDR01ES1.15 VCFD.1008 ORC-01GDR01-D2HMI GDR01PWS16 GDR01BK02\nG G 1 D 9 D 2 R R . 0 0 1 1 1 6 E S 8 S . B 1 1 K . . 6 0 1 5 5 5 CO G 1 N D 9 T 2 R 2 R . 0 1 4 O 1 6 V L P 8 D W . P C 1 O S .6 W 1 6 5 ER VCFD.1 V 0 C 0 F 7 D.1006 1 G G 2 D D 0 2 R R .1 4 0 0 5 V 1 1 . D P E 3 W S C 5 1 . S 4 .5 3 9 CONT 2 R G 4 O D V L R D 0 P C 1 O M W R E 0 R 4PX1 1 G 9 G D 2 D R .1 0 R 6 1 0 8 E 1 . S M 1 1 . R 1 .1 0 0 6 5 2 PX1 GDR01MR06PX1\nGDR01SBK04 HOT CONTROL POWER MAINTENANCE MAINTENANCE MAINTENANCE\nGDR01ES1.15 VCFD.1005 RAIL #4 RAIL #5 RAIL #6\n192.168.1.64\nWb GDR01PWS14 VCFD.1004 CLOSED CLOSED CLOSED\n24VDC GDR01BK01\nCONTROL POWER GDR01ES1.15\nWa GDR01P1 VCFD.1003 192.168.1.101 BK02 BK02 BK02\nPOWER ORC-01GDR01-ES1 GDR01PWS13 GDR01SBK03\nDISTRIBUTION 120.15.35.11 24VDC GDR01ES1.15\nPANEL CONTROL POWER 192.168.1.63\nIFA.1002\nORC-01GDR01-C1EN0 GDR01PWS1\nGDR01MR01PX1 GDR01MR02PX1 GDR01MR03PX1\nGDR01ES1.3 24VDC\nMAINTENANCE MAINTENANCE MAINTENANCE\n120.15.35.47 HOT CONTROL POWER\nRAIL #1 RAIL #2 RAIL #3\nGDR01PWS2 ORC-01GDR01-D1HMI CLOSED CLOSED CLOSED\n24VDC GDR01ES1.4\nTFA.1001\nHOT CONTROL POWER 120.15.35.48\nGDR01PWS12\n24VDC BK01 BK01 BK01\nCONTROL POWER\nGDR01SBK02\nGDR01PWS11 TFD.1000 GDR01ES1.14\n24VDC 192.168.1.62\nCONTROL POWER GDR01A1\nGDR01SBK01 INTEGRATED DRIVE\nGDR01ES1.14 CONTACTOR PANEL\n192.168.1.61 GM-MEVS-NAAX GM ENGINEER:\nALLEN\nBAKER DESIGN SOURCE:\nINDICON DESIGN LEADER:\nDAMON\nHUDSON II PROGRAMS:\nBT1CX PACKAGE FRICTION CONVEYOR GDR01\nDESCRIPTION: DOORS OFF (LH) SYSTEM/TOOL NO: RELEASE DAT E: REVISION S\nLETTER:\nDATE: ECTION\nLETTER:\nB SHEET\nNUMBER:\n3 4\nOF SHEET SYSTEM LAYOUT\nDESCRIPTION: DRAWING NUMBER:\nWD-OR-FDS_GDR01 THIS MATERIAL IS THE PROPERTY OF GENERAL MOTORS COMPANY. NO RIGHTS ARE GRANTED TO\nUSE SUCH MATERIAL FOR ANY PURPOSE OTHER THAN THE FURNISHING OF SERVICES AND SUPPLIES."""

    result_full = fuzzy_pattern_extract(full_text, pattern, threshold=0.6)
    print(f"Full text fuzzy extraction result: {result_full}")


if __name__ == "__main__":
    debug()