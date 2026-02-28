# Caveat Utilitor: Risks, Biases, and Fallacies in the DPRR Data

> *"One of the major problems facing any historian is the question of the representativeness of source material."*
> — Verboven, Carlier, and Dumolyn (2007)

The Digital Prosopography of the Roman Republic (DPRR) is a powerful research tool that aggregates prosopographical data on the political elite of the Roman Republic. It enables queries across magistracies, priesthoods, family relationships, and status assertions that would otherwise require laborious manual cross-referencing. However, no database can be better than its sources, and DPRR inherits — and in some cases compounds — the biases, gaps, and interpretive layers of the scholarship on which it rests.

This document warns researchers against treating DPRR query results as unmediated historical fact. The risks fall into six broad categories: **source-chain mediation**, **survivorship and elite bias**, **the fallacy of the argument from silence**, **nomenclatural ambiguity**, **temporal unevenness**, and **reductive flattening of political culture**.

---

## 1. Source-Chain Mediation: A Database of Secondary Sources

DPRR is not built from ancient evidence. It aggregates modern secondary sources — principally Broughton's *Magistrates of the Roman Republic* (1951–1986), supplemented by Rüpke's *Fasti Sacerdotum*, Zmeskal's *Adfinitas* (2009), Pina Polo's work on electoral defeats, and over thirty additional modern compilations (Bradley 2020). Each of these works embodies its author's editorial judgments about inclusion, exclusion, and the resolution of ambiguous ancient testimony.

This creates what might be called **derivative bias**: the data passes through multiple layers of scholarly interpretation before reaching the user. Broughton's decisions about which magistrates to include, how to handle contradictions between Livy and the *fasti*, and when to mark entries as uncertain are "locked in" to DPRR's data model. Where Broughton excluded a figure for insufficient evidence, that person cannot be recovered from DPRR without returning to primary sources (Bradley 2020). The project was explicitly designed not to conduct independent primary source research.

DPRR encodes uncertainty through question marks and italics, but this notation cannot represent the full spectrum of scholarly disagreement. A question mark on a date may conceal a debate spanning decades of journal articles with fundamentally incompatible reconstructions (Bradley 2020).

**Practical implication:** Every DPRR query result should be understood as "according to Broughton (or Zmeskal, or Rüpke), as digitized by the DPRR team" — not as "according to the ancient sources."

---

## 2. Survivorship and Elite Bias

### 2.1 The Database Documents an Elite of the Elite

DPRR explicitly covers only the political upper strata of Roman society: senators, magistrates, priests, and equestrians who appear in the secondary literature. This is a design choice, not an oversight, but users must not forget it. The database documents perhaps a few thousand individuals out of a population that numbered in the millions.

Stone (1971) identified this as an inherent limitation of prosopography itself: "the biases of official sources on which biographies rely lead to a partial view of reality." The method produces what he called an "elitist, cynical, and conformist perspective on leadership."

### 2.2 Women Are Nearly Invisible

Women held no Republican magistracies and therefore appear in DPRR almost exclusively through relationship assertions — as daughters, wives, and mothers of male office-holders. Their independent political, economic, and social roles are systematically absent from the data model (Flower 1996).

### 2.3 Non-Elite Actors Are Absent by Design

Mouritsen (2001) demonstrated that structural barriers — property thresholds, tribal assignments, assembly design, the practical impossibility of travel to Rome for rural citizens — excluded ordinary people from the political participation that generates prosopographical records. Freedmen, freedwomen, non-Italian provincials, and the urban plebs are almost entirely absent from DPRR. Easton (2024) documents how municipal freedmen, who lacked private patronal networks, left minimal documentary traces; conclusions about Roman social mobility that ignore this invisible majority rest on accidental preservation patterns, not representative samples.

### 2.4 Literary and Epigraphic Survival Bias

The ancient sources themselves are not a random sample. Literary texts survive because they were copied; inscriptions survive where stone endured. Van der Blom (2010, 2016) shows how Cicero's rhetorical works disproportionately preserve the memory of famous orators and historical *exempla*, creating an archive where the eloquent few dominate while the silent many vanish. Figures who left no rhetorical trace are underrepresented even among the elite.

Verboven, Carlier, and Dumolyn (2007) warn that "any prosopography making direct use of primary source material will be dependent on indices," and despite the publication of countless indices, "millions of documents in various archives remain unindexed." When indexing occurs, it is "mostly limited to a selection of apparently important names."

---

## 3. The Argument from Silence: What Absence Does Not Prove

The most dangerous fallacy awaiting DPRR users is the **argument from silence** — inferring that because a person does not appear in the database holding a particular office, they never held it.

### 3.1 When Is Silence Evidential?

Lange (1966) established that a valid argument from silence requires three conditions:

1. An extant document in which no reference to the event appears;
2. Knowledge that the author of that document **intended to provide an exhaustive list** of all events in the relevant class;
3. The assumption that the event is of a type the author **would not have overlooked** if it had occurred.

For most magistracies in most periods of the Republic, none of these conditions is reliably met. The *fasti* are fragmentary; Broughton's MRR synthesizes rather than exhausts; and ancient historians routinely omitted magistrates they considered unremarkable.

McGrew (2014) formalizes this in Bayesian terms: the critical quantity is the probability that evidence would be absent given the hypothesis is true, P(~E|H). Unless we can confidently establish that alternative explanations for the silence — lost sources, editorial selectivity, genre conventions — have low probability, the absence of a record carries little evidential weight. McGrew identifies a cognitive bias toward **representativeness** that leads researchers to overweight silence.

### 3.2 Informative Censoring

The statistical parallel is instructive. Nguyen et al. (2012) demonstrate that in survival analysis, **informative censoring** — where the reason a subject drops out of observation is correlated with the outcome being studied — produces systematically biased estimates. The standard assumption that censored individuals have the same probability of subsequent events as those remaining under observation is violated.

Career data in DPRR exhibits precisely this problem. A person's record may end because:

- **(a)** they genuinely held no further office (the event of interest);
- **(b)** documentation was lost through accident (non-informative censoring);
- **(c)** they died, were exiled, or fell from political favor — events correlated with career outcomes (informative censoring).

We cannot distinguish these mechanisms, and there is "no definitive way to test whether censoring is non-informative" (Nguyen et al. 2012).

### 3.3 When Absence *Can* Be Informative

Wallach (2019) argues that inference from absence is justified when three conditions hold: the material being sought has **high survivability**, an **intensive localized search** has been conducted, and human presence leaves a **strong, distinctive footprint**. For certain well-documented magistracies in the late Republic (e.g., the consulship after c. 200 BC), these conditions may approximately hold. For most lesser magistracies, priesthoods, and earlier periods, they do not.

**Practical implication:** A SPARQL query returning zero results for a person's quaestorship means only that DPRR's sources do not record it. It does not mean the person was never quaestor.

---

## 4. Nomenclatural Ambiguity and Identification Problems

### 4.1 Adoption and Polyonymy

Roman naming conventions create fundamental identification problems that propagate through every prosopographical database. Salomies (1992) catalogs **seventeen distinct nomenclatural variants** that adoption alone could produce. Crucially, "not only can an adoption be translated several ways in nomenclature but any type of change of name caused by adoption can also occur without adoption having taken place." A name change that *appears* to indicate a family connection may reflect coincidence, freedman nomenclature, or conventions we do not fully understand.

### 4.2 Kinship Reconstruction

Zmeskal (2009), whose *Adfinitas* is itself a DPRR source, systematically reconstructed senatorial kinship networks for 218–31 BC. But as both Salomies and Zmeskal acknowledge, genealogical reconstruction from onomastic data is inherently uncertain. Family trees in prosopography rest on probabilistic inference about naming patterns, not on documented pedigrees. A relationship assertion in DPRR may represent a scholarly hypothesis with varying degrees of confidence, not an established fact.

### 4.3 The *Nobilitas* Problem

Brunt (1982) demonstrated that **no ancient definition of *nobilis* or *novus homo* exists**. The boundary between "noble" and "new man" was more porous and contested than modern classification implies. Prosopographical databases that assign status labels to individuals encode modern scholarly convention as if it were ancient social fact.

---

## 5. Temporal Unevenness and Periodization

### 5.1 The Documentation Gradient

DPRR's coverage is radically uneven across the Republic's five centuries. The late Republic (c. 133–31 BC) is densely documented thanks to Cicero, Sallust, Caesar, and extensive epigraphy. The middle Republic (c. 264–133 BC) depends heavily on Livy and fragmentary *fasti*. The early Republic (509–264 BC) rests on traditions of questionable historicity. Develin (1979) mapped patterns in office-holding for 366–49 BC, but these patterns describe only the visible elite; countless magistrates left no trace.

Any quantitative analysis that spans these periods without controlling for differential documentation risks producing artifacts of source survival rather than historical trends.

### 5.2 The "Single Republic" Fallacy

Flower (2010) argues that the traditional periodization into Early, Middle, and Late Republic masks **fundamental institutional transformations** that reshaped political competition. She proposes six distinct republics, each with different rules governing access to power. The introduction of the secret ballot around 139 BC, for instance, fundamentally altered aristocratic control over elections — magistrates elected by secret ballot "were not able to command the same confidence that their ancestors had" (Flower 2010). Treating the Republic as a monolith and comparing prosopographical data across centuries conflates fundamentally different political systems.

Beck (2005) traced the evolution of the *cursus honorum* from informal norms to legal regulation (*lex Villia*, 180 BC), showing how the "hierarchisation of the *honores* went hand in hand with the development of strata within the elite." Career trajectories that appear as fixed rules in databases were in fact evolving social conventions with significant regional and temporal variation.

---

## 6. Reductive Flattening of Political Culture

### 6.1 What Prosopography Cannot Capture

Hölkeskamp (2010) argues that the prosopographical tradition achieved a "solidification and sterilisation of ancient history" by reducing political life to networks of patronage and family connection. What this misses:

- **Ephemeral coalitions.** Clientage networks were "constantly shifting" rather than the fixed structures that database relationships imply.
- **Consensus culture.** The Republic was "sustained by deep-rooted culture of consensus at all levels" — a shared political idiom that cannot be captured in office-holding data.
- **Symbolic and ritual dimensions.** Triumphs, funerary processions, monumental building, and oratorical performance constituted "politics visible and audible" (Hölkeskamp 2010). Flower (1996) showed that aristocratic wax ancestor masks (*imagines*) were central mechanisms of elite power entirely invisible to prosopographical databases.

### 6.2 The Patronage Myth

Brunt (1988) argued that prosopography's focus on vertical ties of social obligation overlooked that rival politicians appealed to diverse constituencies — Italians, men of property, peasants, soldiers, urban plebs — rather than relying solely on personal coteries. DPRR's relationship assertions encode kinship and political connections but cannot represent the ideological, economic, and cultural forces that actually drove Republican politics.

Stone (1971) charged prosopography with **determinism**: the method risks portraying structural forces like class or family networks as overwhelmingly predictive of outcomes, "downplaying personal choice and contingency."

---

## 7. Comparative Misapplication

Researchers tempted to benchmark Roman social mobility against modern data should exercise extreme caution. Long and Ferrie (2013) studied intergenerational occupational mobility in Britain and the United States since 1850 using extensive census data, tax records, and direct occupational reporting. Roman prosopographical data offers none of these: sample sizes are incomparably smaller, categories are not formalized, and the surviving record is not a random sample. Schurer (2002) documents the quantitative limitations even of early modern census-type material, warning against treating incomplete historical records as if they possessed the properties of designed statistical surveys.

Any claim about rates of social mobility, career advancement probabilities, or elite closure derived from DPRR data should be accompanied by explicit discussion of the non-representativeness of the sample and the impossibility of calculating meaningful confidence intervals.

---

## Summary of Recommendations

| Risk | Mitigation |
|---|---|
| Treating DPRR as primary evidence | Always cite the underlying secondary source (Broughton, Zmeskal, etc.), not "DPRR says" |
| Argument from silence | Never infer non-occurrence from non-appearance; state the limits of the evidence |
| Elite bias | Acknowledge that DPRR documents a tiny, privileged fraction of Roman society |
| Nomenclatural false positives | Treat identification and kinship assertions as hypotheses, not facts |
| Temporal conflation | Control for differential documentation when comparing across periods |
| Reductive network analysis | Supplement prosopographical data with cultural, institutional, and ideological analysis |
| Quantitative overreach | Do not calculate rates or probabilities without discussing sample bias and censoring |

---

## Bibliography

Beck, Hans. *Karriere und Hierarchie: Die römische Aristokratie und die Anfänge des cursus honorum in der mittleren Republik.* Berlin: Akademie Verlag, 2005.

Bradley, John. "A Prosopography as Linked Open Data: Some Implications from DPRR." *Digital Humanities Quarterly* 14, no. 2 (2020).

Broughton, T. R. S. *The Magistrates of the Roman Republic.* 3 vols. New York: American Philological Association, 1951–1986.

Brunt, P. A. "Nobilitas and Novitas." *Journal of Roman Studies* 72 (1982): 1–17.

Brunt, P. A. *The Fall of the Roman Republic and Related Essays.* Oxford: Clarendon Press, 1988.

Develin, R. *Patterns in Office-Holding, 366–49 B.C.* Brussels: Latomus, 1979.

Easton, Jeffrey A. *Municipal Freedmen and Intergenerational Social Mobility in Roman Italy.* Leiden: Brill, 2024.

Flower, Harriet I. *Ancestor Masks and Aristocratic Power in Roman Culture.* Oxford: Clarendon Press, 1996.

Flower, Harriet I. *Roman Republics.* Princeton: Princeton University Press, 2010.

Hölkeskamp, Karl-J. *Reconstructing the Roman Republic: An Ancient Political Culture and Modern Research.* Princeton: Princeton University Press, 2010.

Lange, John. "The Argument from Silence." *History and Theory* 5 (1966): 288–301.

Long, Jason, and Joseph P. Ferrie. "Intergenerational Occupational Mobility in Great Britain and the United States since 1850." *American Economic Review* 103, no. 4 (2013): 1109–1137.

McGrew, Timothy. "The Argument from Silence." *Acta Analytica* 29 (2014): 215–228.

Mouritsen, Henrik. *Plebs and Politics in the Late Roman Republic.* Cambridge: Cambridge University Press, 2001.

Nguyen, Clarissa D., et al. "Censoring in Survival Analysis: Potential for Bias." *Statistics in Medicine* 31 (2012): 2105–2113.

Salomies, Olli. *Adoptive and Polyonymous Nomenclature in the Roman Empire.* Helsinki: Societas Scientiarum Fennica, 1992.

Schurer, Kevin. "Missing, Biased, and Unrepresentative: The Quantification of the Limitations of Early Census-Type Material." *Historical Methods* 35, no. 4 (2002): 174–186.

Stone, Lawrence. "Prosopography." *Daedalus* 100, no. 1 (1971): 46–79.

Van der Blom, Henriette. *Cicero's Role Models: The Political Strategy of a Newcomer.* Oxford: Oxford University Press, 2010.

Van der Blom, Henriette. *Oratory and Political Career in the Late Roman Republic.* Cambridge: Cambridge University Press, 2016.

Verboven, Koenraad, Myriam Carlier, and Jan Dumolyn. "A Short Manual to the Art of Prosopography." In *Prosopography: Approaches and Applications. A Handbook*, edited by K. S. B. Keats-Rohan. Oxford: Unit for Prosopographical Research, 2007.

Wallach, Efraim. "Inference from Absence: The Case of Archaeology." *Humanities and Social Sciences Communications* 6 (2019): 84.

Wiseman, T. P. *New Men in the Roman Senate, 139 B.C.–A.D. 14.* Oxford: Oxford University Press, 1971.

Zmeskal, Klaus. *Adfinitas: Die Verwandtschaften der senatorischen Führungsschicht der römischen Republik von 218–31 v. Chr.* 2 vols. Passau: Stutz, 2009.
