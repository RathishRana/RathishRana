"""
End-to-End Example
==================
Demonstrates a complete qualitative study from raw transcripts
through to a publication-ready report.

Research question: What are the lived experiences of first-generation
university students navigating financial hardship?

Run with: python -m qualitative_research.example
"""

from qualitative_research import Project
from qualitative_research.corpus import SegmentationStrategy
from qualitative_research.coding import CodingParadigm

# ─────────────────────────────────────────────────────────────────────────────
# 1. Create project
# ─────────────────────────────────────────────────────────────────────────────

project = Project(
    name="First-Gen Student Financial Hardship",
    lead_researcher="Dr Aisha Patel",
)

project.add_sampling_note(
    "Purposive sampling: first-generation university students (neither parent "
    "attended university) currently experiencing financial hardship (self-reported). "
    "Maximum variation on: gender, subject discipline, year of study."
)

# ─────────────────────────────────────────────────────────────────────────────
# 2. Add interview transcripts
# ─────────────────────────────────────────────────────────────────────────────

TRANSCRIPT_P1 = """
INTERVIEWER: Can you tell me about your typical week in terms of finances?

P1: It's stressful. I count every penny. Like, I'll skip lunch some days because
I've run out of money mid-week and I don't want to ask my parents — they already
sacrificed so much to get me here. I feel this enormous weight of gratitude and
guilt at the same time.

INTERVIEWER: Can you say more about that guilt?

P1: My mum cleaned offices to save for my accommodation deposit. If I fail or
drop out, it's not just my failure, it's hers too. So I keep going even when
I'm exhausted. But sometimes I can't focus in lectures because I'm thinking
about the electricity bill.

INTERVIEWER: How does that affect your studies?

P1: I can't afford the textbooks. I use the library but sometimes they're all
checked out. My classmates just buy them on their laptops. I feel like there's
this invisible wall between me and them.
"""

TRANSCRIPT_P2 = """
INTERVIEWER: How do you manage financially as a student?

P2: I work twenty-five hours a week in a café. I'm always exhausted. My grades
aren't what I know they could be but I have no choice. My student loan doesn't
cover my rent, full stop.

INTERVIEWER: Do you access any support from the university?

P2: I didn't know about the hardship fund for two years. Nobody told me. When
I finally applied it felt humiliating — you have to prove you're poor, like
show your bank statements. I nearly didn't bother.

INTERVIEWER: What would help?

P2: Just being seen. Knowing someone on the staff actually knows what it's like
not to have money. All the help stuff is hidden away on websites nobody reads.
"""

TRANSCRIPT_P3 = """
INTERVIEWER: Tell me about your experience as a first-gen student.

P3: I'm proud to be here but it's lonely. Everyone else seems to just know things —
how to talk to tutors, how to network, what to wear to careers events. I didn't
grow up knowing any of that. And I can't afford to attend the networking events anyway
because they're always in the evenings in expensive venues.

INTERVIEWER: Does money affect your sense of belonging?

P3: Absolutely. In seminars people talk about their gap years, their internships abroad.
I worked in a warehouse all summer to pay off my overdraft. I just go quiet.
The invisibility is exhausting. You're constantly code-switching, hiding how
hard things actually are.
"""

doc1 = project.add_interview(
    TRANSCRIPT_P1,
    title="Interview P1",
    participant_id="P1",
    collection_date="2024-10-15",
    context="60-min Zoom interview; participant female, Year 2 Medicine",
)

doc2 = project.add_interview(
    TRANSCRIPT_P2,
    title="Interview P2",
    participant_id="P2",
    collection_date="2024-10-22",
    context="55-min Zoom interview; participant male, Year 3 Engineering",
)

doc3 = project.add_interview(
    TRANSCRIPT_P3,
    title="Interview P3",
    participant_id="P3",
    collection_date="2024-10-29",
    context="65-min in-person interview; participant non-binary, Year 1 Law",
)

print(f"Corpus loaded: {project.corpus}")

# ─────────────────────────────────────────────────────────────────────────────
# 3. Set up coders (two researchers for IRR)
# ─────────────────────────────────────────────────────────────────────────────

coder_a = project.add_coder("Dr Aisha Patel", role="lead researcher")
coder_a.add_reflexivity_note(
    "I am a first-generation university graduate myself. I am aware this may "
    "generate empathy that facilitates rapport but also risks over-identification "
    "with participants. I will bracket these assumptions through regular peer debriefing."
)

coder_b = project.add_coder("Dr Ben Okafor", role="independent coder")
coder_b.add_reflexivity_note(
    "I come from a professional-class background and did not experience financial "
    "hardship as a student. I may under-code experiences I have not personally "
    "encountered. I will flag uncertainties explicitly in my rationale notes."
)

# ─────────────────────────────────────────────────────────────────────────────
# 4. Build codebook with full definitions
# ─────────────────────────────────────────────────────────────────────────────

cb = project.codebook

financial_stress = cb.create_code(
    name="financial stress",
    definition="Expressions of anxiety, worry, or cognitive burden directly related to money.",
    inclusion_criteria="Must reference money, cost, financial resources, or economic state.",
    exclusion_criteria="General academic stress not linked to finances.",
    example_anchor="I count every penny. I can't focus because I'm thinking about the electricity bill.",
    paradigm=CodingParadigm.DESCRIPTIVE,
    created_by="Dr Aisha Patel",
)

guilt_obligation = cb.create_code(
    name="guilt and obligation",
    definition="Sense of debt, responsibility, or guilt tied to family sacrifice.",
    inclusion_criteria="References to parental sacrifice, duty, letting family down.",
    exclusion_criteria="General academic pressure without familial framing.",
    example_anchor="If I fail it's not just my failure, it's hers too.",
    paradigm=CodingParadigm.EMOTION,
    created_by="Dr Aisha Patel",
)

invisible_wall = cb.create_code(
    name="class invisibility",
    definition="Experiences of social exclusion, othering, or class-based otherness.",
    inclusion_criteria="Comparisons with peers, feeling different, hiding socioeconomic status.",
    example_anchor="There's this invisible wall between me and them.",
    paradigm=CodingParadigm.IN_VIVO,
    created_by="Dr Aisha Patel",
)

material_constraint = cb.create_code(
    name="material constraint",
    definition="Concrete resource deprivations affecting study (textbooks, food, time).",
    inclusion_criteria="Specific material lacks: food, books, transport, equipment, time from work.",
    example_anchor="I can't afford the textbooks. I skip lunch some days.",
    paradigm=CodingParadigm.DESCRIPTIVE,
    created_by="Dr Aisha Patel",
)

support_invisibility = cb.create_code(
    name="support system failure",
    definition="Institutional failures to make support visible, accessible, or dignified.",
    inclusion_criteria="Unawareness of support, humiliating processes, inaccessible information.",
    example_anchor="I didn't know about the hardship fund for two years.",
    paradigm=CodingParadigm.DESCRIPTIVE,
    created_by="Dr Aisha Patel",
)

code_switching = cb.create_code(
    name="identity code-switching",
    definition="Effortful performance of a different class identity to fit in.",
    inclusion_criteria="References to masking, pretending, hiding, being silent.",
    example_anchor="You're constantly code-switching, hiding how hard things actually are.",
    paradigm=CodingParadigm.IN_VIVO,
    created_by="Dr Aisha Patel",
)

aspiration = cb.create_code(
    name="aspirational persistence",
    definition="Motivation and resilience despite hardship, linked to pride and goals.",
    inclusion_criteria="Language of continuing, pride, being here, not giving up.",
    example_anchor="I'm proud to be here.",
    paradigm=CodingParadigm.PROCESS,
    created_by="Dr Aisha Patel",
)

# ─────────────────────────────────────────────────────────────────────────────
# 5. Code segments (Coder A)
# ─────────────────────────────────────────────────────────────────────────────

segs_p1 = doc1.segments
segs_p2 = doc2.segments
segs_p3 = doc3.segments

# P1 turn 2: stress and guilt
coder_a.code(cb, "financial stress", segs_p1[1].segment_id, doc1.document_id,
             rationale="'count every penny', 'skip lunch' — explicit financial anxiety")
coder_a.code(cb, "guilt and obligation", segs_p1[1].segment_id, doc1.document_id,
             rationale="'enormous weight of gratitude and guilt' — clear emotion code")
coder_a.code(cb, "material constraint", segs_p1[1].segment_id, doc1.document_id,
             rationale="skipping food = material deprivation")

# P1 turn 3: guilt elaboration
coder_a.code(cb, "guilt and obligation", segs_p1[2].segment_id, doc1.document_id,
             rationale="'if I fail it's not just my failure' — family obligation framing")
coder_a.code(cb, "aspirational persistence", segs_p1[2].segment_id, doc1.document_id,
             rationale="'I keep going even when exhausted' — persistence")

# P1 turn 4: textbooks / class boundary
coder_a.code(cb, "material constraint", segs_p1[3].segment_id, doc1.document_id,
             rationale="can't afford textbooks")
coder_a.code(cb, "class invisibility", segs_p1[3].segment_id, doc1.document_id,
             rationale="'invisible wall' — in-vivo, peer comparison")

# P2 turn 2: work-study conflict
coder_a.code(cb, "material constraint", segs_p2[1].segment_id, doc2.document_id,
             rationale="25hrs work, loan doesn't cover rent = material constraint")
coder_a.code(cb, "financial stress", segs_p2[1].segment_id, doc2.document_id,
             rationale="'always exhausted' from financial necessity")

# P2 turn 3: support failure
coder_a.code(cb, "support system failure", segs_p2[2].segment_id, doc2.document_id,
             rationale="didn't know about hardship fund for 2 years — systemic failure")
coder_a.code(cb, "class invisibility", segs_p2[2].segment_id, doc2.document_id,
             rationale="'prove you're poor' — humiliation / othering by institution")

# P3 turn 3: belonging / code-switching
coder_a.code(cb, "class invisibility", segs_p3[2].segment_id, doc3.document_id,
             rationale="gap year / internship comparisons — class othering")
coder_a.code(cb, "identity code-switching", segs_p3[2].segment_id, doc3.document_id,
             rationale="'go quiet', 'invisibility exhausting', code-switching in-vivo")
coder_a.code(cb, "aspirational persistence", segs_p3[0].segment_id, doc3.document_id,
             rationale="'I'm proud to be here' — aspirational framing despite hardship")

# ─────────────────────────────────────────────────────────────────────────────
# 6. Double-code subsample (Coder B) for reliability
# ─────────────────────────────────────────────────────────────────────────────

double_coded_segments = [
    segs_p1[1].segment_id,
    segs_p1[2].segment_id,
    segs_p2[2].segment_id,
    segs_p3[2].segment_id,
]

# P1 turn 2
coder_b.code(cb, "financial stress", segs_p1[1].segment_id, doc1.document_id,
             rationale="counting pennies, skipping meals = financial stress")
coder_b.code(cb, "guilt and obligation", segs_p1[1].segment_id, doc1.document_id,
             rationale="gratitude/guilt dyad referenced explicitly")
coder_b.code(cb, "material constraint", segs_p1[1].segment_id, doc1.document_id,
             rationale="skipping lunch = food insecurity")

# P1 turn 3
coder_b.code(cb, "guilt and obligation", segs_p1[2].segment_id, doc1.document_id,
             rationale="parental sacrifice framing")
coder_b.code(cb, "aspirational persistence", segs_p1[2].segment_id, doc1.document_id,
             rationale="'I keep going'")

# P2 turn 3 — slight disagreement: Coder B does not apply class_invisibility
coder_b.code(cb, "support system failure", segs_p2[2].segment_id, doc2.document_id,
             rationale="institutional information failure clearly coded")
# (Coder B misses class_invisibility here — will show in discrepancy analysis)

# P3 turn 3
coder_b.code(cb, "class invisibility", segs_p3[2].segment_id, doc3.document_id,
             rationale="peer comparison, social exclusion")
coder_b.code(cb, "identity code-switching", segs_p3[2].segment_id, doc3.document_id,
             rationale="explicit code-switching reference")

# ─────────────────────────────────────────────────────────────────────────────
# 7. Check reliability
# ─────────────────────────────────────────────────────────────────────────────

print("\n--- RELIABILITY ---")
rel = project.check_reliability(
    segment_ids=double_coded_segments,
    raters=["Dr Aisha Patel", "Dr Ben Okafor"],
)
print(f"Krippendorff's α: {rel.krippendorffs_alpha:.3f}")
for p in rel.pairwise:
    print(f"  {p.rater_a} × {p.rater_b}: κ={p.cohens_kappa:.3f} ({p.interpretation})")
print(f"Assessment: {rel.recommendation[:80]}...")

# ─────────────────────────────────────────────────────────────────────────────
# 8. Check saturation
# ─────────────────────────────────────────────────────────────────────────────

print("\n--- SATURATION ---")
sat = project.check_saturation(
    document_order=[doc1.document_id, doc2.document_id, doc3.document_id]
)
print(sat.recommendation)

# ─────────────────────────────────────────────────────────────────────────────
# 9. Build themes (Phase 3–5: Braun & Clarke)
# ─────────────────────────────────────────────────────────────────────────────

analyzer = project.analyzer

analyzer.add_familiarisation_note(
    "Data immersion: financial hardship is intertwined with identity and belonging. "
    "The emotional register is striking — guilt, exhaustion, pride co-exist."
)

# Phase 3: Candidate themes
t1 = analyzer.create_theme(
    name="The Weight of Gratitude",
    code_names=["financial stress", "guilt and obligation", "aspirational persistence"],
    central_concept="Financial hardship is emotionally mediated by family obligation and pride",
    researcher="Dr Aisha Patel",
)
t1.add_quote(
    "I keep going even when I'm exhausted. But sometimes I can't focus in lectures "
    "because I'm thinking about the electricity bill.",
    participant="P1",
)
t1.add_negative_case(
    "P3 expresses pride without guilt framing — suggests obligation is not universal; "
    "may be moderated by degree of visible parental sacrifice."
)

t2 = analyzer.create_theme(
    name="Material Poverty, Epistemic Exclusion",
    code_names=["material constraint", "support system failure"],
    central_concept="Concrete resource deprivation compounds institutional knowledge gaps",
    researcher="Dr Aisha Patel",
)
t2.add_quote(
    "I can't afford the textbooks. I use the library but sometimes they're all checked out. "
    "My classmates just buy them on their laptops.",
    participant="P1",
)
t2.add_quote(
    "I didn't know about the hardship fund for two years. Nobody told me.",
    participant="P2",
)
t2.add_negative_case(
    "P1 does access the library — not entirely excluded; resourcefulness and workarounds exist."
)

t3 = analyzer.create_theme(
    name="The Invisible Tax of Class",
    code_names=["class invisibility", "identity code-switching"],
    central_concept="Class difference exacts a continuous cognitive and emotional toll",
    researcher="Dr Aisha Patel",
)
t3.add_quote(
    "You're constantly code-switching, hiding how hard things actually are. "
    "The invisibility is exhausting.",
    participant="P3",
)
t3.add_quote(
    "There's this invisible wall between me and them.",
    participant="P1",
)
t3.add_negative_case(
    "P2 does not use code-switching language; may resist or not conceptualise experience "
    "this way — or may have greater economic confidence despite hardship."
)

# Phase 5: Finalise
analyzer.finalise_theme(
    "The Weight of Gratitude",
    narrative=(
        "Participants do not experience financial hardship as a purely economic phenomenon. "
        "It is deeply entangled with emotional obligations to families who have sacrificed "
        "materially for their university attendance. This creates a paradoxical affective state: "
        "pride in aspiration co-exists with paralysing guilt. Participants persist despite "
        "hardship not in spite of this guilt but, in part, because of it — the debt of "
        "gratitude functioning as a form of resilience fuel."
    ),
    central_concept="Gratitude-debt as a driver of aspirational persistence under financial hardship",
)

analyzer.finalise_theme(
    "Material Poverty, Epistemic Exclusion",
    narrative=(
        "First-generation students face a double disadvantage: they lack material resources "
        "(food, textbooks, time) and they lack the cultural capital to navigate institutional "
        "support systems. Support mechanisms exist but are invisible by design — buried in websites, "
        "requiring students to already know the language of the university. This constitutes "
        "a form of structural exclusion that compounds material deprivation."
    ),
    central_concept="Structural inaccessibility of support as a second-order form of poverty",
)

analyzer.finalise_theme(
    "The Invisible Tax of Class",
    narrative=(
        "Participants describe a continuous, effortful performance of class identity in order "
        "to pass as 'normal' students. This code-switching — staying silent about the warehouse "
        "job, the electricity bill, the skipped meal — is cognitively and emotionally costly. "
        "The invisibility is not merely social but also cognitive: energy spent hiding is energy "
        "not spent learning."
    ),
    central_concept="Code-switching as an invisible cognitive tax on first-generation students",
)

# ─────────────────────────────────────────────────────────────────────────────
# 10. Quality check
# ─────────────────────────────────────────────────────────────────────────────

print("\n--- QUALITY CHECK ---")
warnings = analyzer.all_warnings()
if warnings:
    for w in warnings:
        print(f"  ⚠  {w}")
else:
    print("  All themes pass quality criteria.")

# ─────────────────────────────────────────────────────────────────────────────
# 11. Generate report
# ─────────────────────────────────────────────────────────────────────────────

project.summary()

project.generate_report(
    "qualitative_report.txt",
    fmt="text",
    reliability_report=rel,
    saturation_result=sat,
)

project.generate_report(
    "qualitative_report.json",
    fmt="json",
    reliability_report=rel,
    saturation_result=sat,
)

print("\nDone. See qualitative_report.txt and qualitative_report.json")
