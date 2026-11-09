# Final JSS source compliance

The official instructions require ASCII software source, installable code with formatted help, a JSS-format PDF, compatible licensing and exactly reproducible article output on at least one disclosed platform. [JSS author instructions](https://www.jstatsoft.org/authors) · [JSS submission guide](https://www.jstatsoft.org/guides/submission)

| Scope | Closure |
|---|---|
| Installed distribution | Original runtime files remain UTF-8. The 159 Python files include 147 with non-ASCII content. |
| Exact JSS software attachment | The separate ASCII tree contains those 159 Python sources, with the three forced scripts at their source-distribution paths, plus the MIT notice, citation record, build metadata and submission README. The [inventory](jss-software-inventory.json) gives each original and candidate SHA-256. |
| Development-only files | Tests, CI, trace tools and worktree administration remain outside the source attachment. Tests run against the installed candidate. |
| Supplementary source | The ASCII verifier is a launcher. Historical reproduction scripts and immutable source snapshots are acquired and used at their original bytes. Submit the launcher and acquisition instructions separately. Author or editorial confirmation of the attachment treatment remains open. |
| Manuscript and typesetting | LaTeX and BibTeX are ASCII. The official-class PDF is byte-identical to Phase 29. It contains five figures, four tables and 12 clickable bibliographic destinations. Supplementary instructions and links are provided alongside the PDF. |
| Formatted help | Candidate review help covers all 35 subcommands, installation and primary experiment and coverage APIs. |

Run `python scripts/prepare_jss_source.py NEW_SOURCE` under Python 3.12 from a clean checkout. The builder maps common comment punctuation, escapes remaining non-ASCII characters, compares complete ASTs with type comments and compiles the candidate. It fails on any changed AST. This preserves string values and execution structure without rewriting the distribution. Build the candidate using `uv build --out-dir NEW_DIST` in that tree. The source inventory is an attachment receipt rather than an installed dependency.

The ASCII software source gate is closed for the generated attachment. Journal decisions about the linked historical replication source, practical usefulness and final attachments remain open. The existing draft retains author metadata placeholders pending confirmation.
