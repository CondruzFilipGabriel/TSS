# General directions for functional testing

Look for tests based on expected behavior.

Search for:
- valid inputs
- invalid inputs
- expected outputs
- expected errors
- visible side effects

Look for input groups that should produce the same behavior.

Look for:
- minimum valid values
- maximum valid values
- values just below limits
- values just above limits
- empty or missing values when relevant

Look for important input relations:
- inputs that must appear together
- inputs that cannot appear together
- inputs that change behavior only in specific combinations

Look for different observable outcomes and the inputs that should produce them.

Prefer:
- valid vs invalid cases
- edge cases
- special input combinations
- similar inputs that should produce different results