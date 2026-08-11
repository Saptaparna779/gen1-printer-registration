# Validation Audit Rubric
Used to score how trustworthy a Fix Validation Agent's report is --
NOT whether the underlying code fix is good. This is a check on the
checker: does the report's score actually reflect the real evidence, or
does it overstate/understate confidence based on incomplete or
misread evidence?

## What this rubric is NOT
This is not a second opinion on whether the code fix itself is correct.
Re-deriving your own fix-quality score defeats the purpose -- the point
is to verify the FIRST agent's report is internally consistent and
accurately grounded in what the evidence actually shows, using your own
independent read of that evidence.

| Score Range | Meaning |
|---|---|
| 90-100 | Report's claims are fully supported by the underlying evidence; score matches the confidence_rubric.md bands correctly; no material coverage gaps were missed or misreported |
| 70-89 | Report is broadly accurate but has a minor discrepancy -- e.g. a citation that doesn't quite match the rule it points to, or a coverage claim that's technically true but incompletely explained |
| 40-69 | Report has at least one material discrepancy between its claims and the actual evidence -- e.g. claims a test passed when the results file shows otherwise, or omits a real coverage gap |
| 0-39 | Report's score is fundamentally unsupported by the evidence, or the report fabricated citations/results not present in the source files |

## Independent verification, not report-grading
Do not take the Fix Validation Agent's report's claims at face value.
For each claim in the report (e.g. "TC-GOAR-8-01 passed"), independently
check the underlying evidence file yourself (e.g.
reports/<TICKET-KEY>_test_results.txt) to confirm it's actually true.
Only flag a discrepancy if your own independent read of the evidence
disagrees with the report's claim.

## What counts as a material discrepancy
- A cited test case ID or business rule clause that doesn't exist in the
  source file, or exists but doesn't say what the report claims it says.
- A claimed pass/fail status that doesn't match the actual test results file.
- An acceptance criterion or scenario type that has no test case, but
  the report doesn't flag it as a gap.
- A score that doesn't match its own stated justification against the
  confidence_rubric.md bands (e.g. justification describes a 70-89-level
  situation but the score given is 95).
