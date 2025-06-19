"""
Latin Macronizer Core Logic Test Suite
=====================================

This test suite validates the core macronization logic of the Latin Macronizer.
Tests cover:
- Accurate macronization of common Latin phrases
- Proper handling of punctuation and capitalization
- Integration with external tools (RFTagger for POS tagging, Morpheus for morphological analysis)
- Database-driven macron lookup functionality

All external dependencies (RFTagger, Morpheus, file I/O) are mocked to ensure:
- Fast test execution
- Reliable test results independent of system configuration
- Focused testing on core macronization algorithms

Test cases include famous Latin phrases to verify expected macronization behavior.
"""

import pytest
from unittest.mock import patch, mock_open

# Adjust sys.path to allow macronizer to be imported
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from macronizer import Macronizer
import textwrap

# Sample data provided by the user
TEST_CASES = [
    ("arma virumque cano", "arma virumque canō"),
    ("et tu, brute?", "et tū, brūte?"),
    ("veni vidi vici", "venī vīdī vīcī"),
    ("Gallia est omnis divisa in partes tres.", "Gallia est omnis dīvīsa in partēs trēs."), # Added another common one
    ("Caesar, Caesaris", "Caesar, Caesaris") # Test with punctuation and capitalization
]

# This is a simplified mock for RFTagger's output.
# RFTagger writes lines like: word\tTAG
# For these tests, we might not need perfect tags, just *some* tags,
# or ensure the tagging process doesn't fail.
# A more sophisticated mock would write plausible tags based on input.
# This content must match the exact sequence of tokens (words and punctuation)
# written to RFTagger, including handling of enclitics and sentence-final newlines.
# MOCK_RFTAGGER_OUTPUT_CONTENT = textwrap.dedent("""\
#     arma	TAG_Placeholder
#     que	TAG_Placeholder
#     virum	TAG_Placeholder
#     cano	TAG_Placeholder
#     et	TAG_Placeholder
#     tu	TAG_Placeholder
#     ,\tPUNCT_Placeholder
#     brute	TAG_Placeholder
#     ?\tPUNCT_Placeholder
#     \n
#     veni	TAG_Placeholder
#     vidi	TAG_Placeholder
#     vici	TAG_Placeholder
#     Gallia	TAG_Placeholder
#     est	TAG_Placeholder
#     omnis	TAG_Placeholder
#     divisa	TAG_Placeholder
#     in	TAG_Placeholder
#     partes	TAG_Placeholder
#     tres	TAG_Placeholder
#     .\tPUNCT_Placeholder
#     \n
#     Caesar	TAG_Placeholder
#     ,\tPUNCT_Placeholder
#     Caesaris	TAG_Placeholder
#     """)

RFTAGGER_MOCKS_PER_CASE = {
    "arma virumque cano": textwrap.dedent("""\
        arma\tTAG
        que\tTAG
        virum\tTAG
        cano\tTAG
        """),
    "et tu, brute?": textwrap.dedent("""\
        et\tTAG
        tu\tTAG
        ,\tPUNCT
        brute\tTAG
        ?\tPUNCT
        \n
        """),
    "veni vidi vici": textwrap.dedent("""\
        veni\tTAG
        vidi\tTAG
        vici\tTAG
        """),
    "Gallia est omnis divisa in partes tres.": textwrap.dedent("""\
        Gallia\tTAG
        est\tTAG
        omnis\ta-s---fn-
        divisa\tTAG
        in\tTAG
        partes\tTAG
        tres\tTAG
        .\tPUNCT
        \n
        """),
    "Caesar, Caesaris": textwrap.dedent("""\
        Caesar\tTAG
        ,\tPUNCT
        Caesaris\tTAG
        """)
}


@pytest.mark.parametrize("sample_input, expected_output", TEST_CASES)
@patch('macronizer.os.remove')
@patch('macronizer.os.system')
@patch('macronizer.mkstemp')
@patch('macronizer.open', new_callable=mock_open) # Mock all file operations
def test_macronizer_logic_with_mocked_binaries(mock_file_open, mock_mkstemp, mock_os_system, mock_os_remove, sample_input, expected_output):
    """Test core macronizer logic with mocked external dependencies (RFTagger, Morpheus)"""
    print(f"🧪 Testing macronizer core logic: '{sample_input}' → '{expected_output}'")
    
    # Configure os.system to always return 0 (success)
    mock_os_system.return_value = 0
    # Configure os.remove to do nothing (as files aren't really created)
    mock_os_remove.return_value = None

    # Configure mkstemp to return mock file descriptors and names
    # It's called for input to binaries and output from binaries
    # Example: RFTagger input/output, Morpheus input/output
    # We need to handle multiple calls to mkstemp if they occur.
    # Let's make it return distinct mock filenames for simplicity.
    mock_mkstemp.side_effect = [
        (1, 'mock_temp_file_1.tmp'), (2, 'mock_temp_file_2.tmp'),
        (3, 'mock_temp_file_3.tmp'), (4, 'mock_temp_file_4.tmp'),
        (5, 'mock_temp_file_5.tmp'), (6, 'mock_temp_file_6.tmp') # Add more if needed
    ]

    # Configure the mock_open behavior:
    # - When RFTagger's output file (e.g., mock_temp_file_2.tmp) is read, return mock tags.
    # - When Morpheus's output file is read, return minimal/empty output to avoid errors.
    #   (Ideally, Morpheus mock would be more sophisticated if testing unknown words).
    def mock_file_open_side_effect(filename, mode='r', encoding=None):
        if 'r' in mode:
            if filename == 'mock_temp_file_2.tmp': # RFTagger output
                current_mock_data = RFTAGGER_MOCKS_PER_CASE[sample_input]
                return mock_open(read_data=current_mock_data)()
            elif filename == 'mock_temp_file_4.tmp': # Morpheus output (cruncher)
                 # Minimal valid Morpheus output for known words if it tries to parse them.
                 # For truly unknown words, it would be empty.
                 # This part is tricky as crunchwords might not be called if DB is comprehensive.
                return mock_open(read_data="")() 
            elif filename == 'macrons.txt': # If USE_DB=False or DB is missing
                # This should not be hit if DB_NAME ('macronizer.db') is found and USE_DB is True.
                # For robustness, provide minimal content if it were to be read.
                return mock_open(read_data="# mock macrons.txt\n")()
            else: # Default for other reads (like stdin for Morpheus if not from file)
                return mock_open(read_data="")()
        else: # For 'w' mode
            return mock_open()() # Return a standard mock file object for writing

    mock_file_open.side_effect = mock_file_open_side_effect
    
    # Ensure that the database is used. If macronizer.db is missing, it might try to use macrons.txt
    # or fail. The test assumes macronizer.db is present and valid as per setup.
    # We are mocking os.system, so --initialize won't run if called.
    print("🔧 Setting up mocked macronizer instance with external binary dependencies")
    
    macronizer_instance = Macronizer()
    
    # Call the macronize method with default options relevant to basic macronization
    print("⚙️  Running macronization with standard options")
    actual_output = macronizer_instance.macronize(
        text=sample_input,
        domacronize=True,
        alsomaius=False,   # Keep false to simplify expected output
        performutov=False, # Keep false
        performitoj=False, # Keep false
        markambigs=False   # API returns plain text
    )
    
    assert actual_output == expected_output
    print(f"✅ Macronization test passed - Output matches expected result")
