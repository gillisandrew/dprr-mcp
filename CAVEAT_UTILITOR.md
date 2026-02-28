# Caveat Utilitor: Interpreting DPRR Query Results

The Digital Prosopography of the Roman Republic (DPRR) aggregates prosopographical data on the political elite of the Roman Republic. It enables queries across magistracies, priesthoods, family relationships, and status assertions that would otherwise require laborious manual cross-referencing. However, no database can be better than its sources, and DPRR inherits the biases, gaps, and interpretive layers of the scholarship on which it rests.

This document warns researchers against treating DPRR query results as unmediated historical fact.

---

## 1. A Database of Secondary Sources

DPRR is not built from ancient evidence. It aggregates modern secondary sources — principally Broughton's *Magistrates of the Roman Republic* (1951–1986), supplemented by Rüpke's *Fasti Sacerdotum*, Zmeskal's *Adfinitas* (2009), and over thirty additional modern compilations (Bradley 2020). Each of these works embodies its author's editorial judgments about inclusion, exclusion, and the resolution of ambiguous ancient testimony.

Broughton's decisions about which magistrates to include, how to handle contradictions between Livy and the *fasti*, and when to mark entries as uncertain are locked into DPRR's data model. Where Broughton excluded a figure for insufficient evidence, that person cannot be recovered from DPRR without returning to primary sources. The project was explicitly designed not to conduct independent primary source research (Bradley 2020).

DPRR encodes uncertainty through boolean flags, but this notation cannot represent the full spectrum of scholarly disagreement. A question mark on a date may conceal a debate spanning decades of journal articles with fundamentally incompatible reconstructions.

**Every query result should be understood as "according to Broughton (or Zmeskal, or Rüpke), as digitised by the DPRR team" — not as "according to the ancient sources."**

---

## 2. Elite Bias

DPRR covers only the political upper strata of Roman society: senators, magistrates, priests, and equestrians who appear in the secondary literature. The database documents a few thousand individuals out of a population that numbered in the millions.

Women held no Republican magistracies and appear in DPRR almost exclusively through relationship assertions — as daughters, wives, and mothers of male office-holders. Freedmen, non-Italian provincials, and the urban plebs are absent by design. Mouritsen (2001) demonstrated that structural barriers excluded ordinary people from the political participation that generates prosopographical records.

The ancient sources themselves are not a random sample. Literary texts survive because they were copied; inscriptions survive where stone endured. Figures who left no literary or epigraphic trace are underrepresented even among the elite.

---

## 3. Absence Does Not Prove Non-Occurrence

The most dangerous fallacy awaiting DPRR users is the argument from silence — inferring that because a person does not appear in the database holding a particular office, they never held it.

For most magistracies in most periods of the Republic, silence is not evidential. The *fasti* are fragmentary; Broughton's MRR synthesises rather than exhausts; and ancient historians routinely omitted magistrates they considered unremarkable.

Career data in DPRR exhibits what statisticians call informative censoring: a person's record may end because they genuinely held no further office, because documentation was lost, or because they died, were exiled, or fell from favour — and we cannot reliably distinguish these mechanisms.

For certain well-documented magistracies in the late Republic (e.g., the consulship after c. 200 BC), absence is more meaningful. For most lesser magistracies, priesthoods, and earlier periods, it is not.

**A query returning zero results for a person's quaestorship means only that DPRR's sources do not record it. It does not mean the person was never quaestor.**

---

## 4. Nomenclatural Ambiguity

Roman naming conventions create fundamental identification problems. Salomies (1992) catalogued seventeen distinct nomenclatural variants that adoption alone could produce, and crucially, any type of name change caused by adoption can also occur without adoption having taken place. A name that appears to indicate a family connection may reflect coincidence, freedman nomenclature, or conventions we do not fully understand.

Zmeskal (2009), whose *Adfinitas* is itself a DPRR source, acknowledged that genealogical reconstruction from onomastic data is inherently uncertain. Family trees rest on probabilistic inference about naming patterns, not on documented pedigrees. A relationship assertion in DPRR may represent a scholarly hypothesis with varying degrees of confidence, not an established fact.

Brunt (1982) demonstrated that no ancient definition of *nobilis* or *novus homo* exists. Status labels in DPRR encode modern scholarly convention as if it were ancient social fact.

---

## 5. Temporal Unevenness

DPRR's coverage is radically uneven across the Republic's five centuries. The late Republic (c. 133–31 BC) is densely documented thanks to Cicero, Sallust, Caesar, and extensive epigraphy. The middle Republic (c. 264–133 BC) depends heavily on Livy and fragmentary *fasti*. The early Republic (509–264 BC) rests on traditions of questionable historicity. Develin (1979) mapped patterns in office-holding for 366–49 BC, but these patterns describe only the visible elite.

Any quantitative analysis that spans these periods without controlling for differential documentation risks producing artifacts of source survival rather than historical trends. Flower (2010) argues that the Republic underwent fundamental institutional transformations — the introduction of the secret ballot (c. 139 BC), the formalisation of the *cursus honorum* (*lex Villia*, 180 BC) — that make cross-period comparison perilous.

---

## 6. What Prosopography Cannot Capture

Hölkeskamp (2010) argued that the prosopographical tradition reduced political life to networks of patronage and family connection, missing the symbolic, ritual, and consensual dimensions of Republican politics. DPRR's relationship assertions encode kinship and political connections but cannot represent the ideological, economic, and cultural forces that drove Republican political competition (Brunt 1988).

Clientage networks were constantly shifting rather than the fixed structures that database relationships imply. Prosopographical data should be supplemented with cultural, institutional, and ideological analysis.

---

## Summary

| Risk | Mitigation |
|---|---|
| Treating DPRR as primary evidence | Always cite the underlying secondary source (Broughton, Zmeskal, etc.) |
| Argument from silence | Never infer non-occurrence from non-appearance; state the limits of the evidence |
| Elite bias | Acknowledge that DPRR documents a tiny, privileged fraction of Roman society |
| Nomenclatural false positives | Treat identification and kinship assertions as hypotheses, not facts |
| Temporal conflation | Control for differential documentation when comparing across periods |
| Quantitative overreach | Do not calculate rates or probabilities without discussing sample bias |

---

## Bibliography

Bradley, John. "A Prosopography as Linked Open Data: Some Implications from DPRR." *Digital Humanities Quarterly* 14, no. 2 (2020).

Broughton, T. R. S. *The Magistrates of the Roman Republic.* 3 vols. New York: American Philological Association, 1951–1986.

Brunt, P. A. "Nobilitas and Novitas." *Journal of Roman Studies* 72 (1982): 1–17.

Brunt, P. A. *The Fall of the Roman Republic and Related Essays.* Oxford: Clarendon Press, 1988.

Develin, R. *Patterns in Office-Holding, 366–49 B.C.* Brussels: Latomus, 1979.

Flower, Harriet I. *Roman Republics.* Princeton: Princeton University Press, 2010.

Hölkeskamp, Karl-J. *Reconstructing the Roman Republic: An Ancient Political Culture and Modern Research.* Princeton: Princeton University Press, 2010.

Mouritsen, Henrik. *Plebs and Politics in the Late Roman Republic.* Cambridge: Cambridge University Press, 2001.

Salomies, Olli. *Adoptive and Polyonymous Nomenclature in the Roman Empire.* Helsinki: Societas Scientiarum Fennica, 1992.

Zmeskal, Klaus. *Adfinitas: Die Verwandtschaften der senatorischen Führungsschicht der römischen Republik von 218–31 v. Chr.* 2 vols. Passau: Stutz, 2009.
