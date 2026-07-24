# Hackathon #1 Reflection
**Author:** Lameck  
**Word Count:** ~220  
**Date:** 2026-07-24

---

## Reflection

The biggest technical hurdle our team faced during Hackathon #1 was data quality — specifically, reconciling three different data sources that used inconsistent date formats and location naming conventions. One dataset used depot abbreviations (NBI, MSA), another used full city names, and a third used numeric codes. When we attempted to merge the tables, we got a DataFrame with nearly 40% null values — not because data was missing, but because the join keys didn't match.

We resolved it in two steps. First, we created a mapping dictionary that standardised all location references to a single format before merging. Second, we used `pd.merge` with `how='outer'` to surface unmatched rows explicitly, which helped us catch edge cases we hadn't anticipated. The lesson was that data preparation deserves as much planning as the analysis itself.

On teamwork, the main thing I would do differently is establish a shared data schema at the very start — before anyone writes a line of analysis code. We lost approximately two hours to fixing merge conflicts that a 10-minute alignment conversation at the beginning would have prevented. In the next hackathon, I would advocate for a brief "data contract" document that every team member signs off on before work is divided, specifying column names, types, and value conventions. Analysis is fast when the foundation is clean.

