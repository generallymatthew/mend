# Chatbot Usage for Social Dynamics: What the Data Actually Shows

Research pass answering: is there public data showing a lot of people already
use ChatGPT/Claude/Gemini to navigate social dynamics (relationship advice,
interpersonal conflict, how to handle a person) — the exact use case Mend
targets, just handled by a general-purpose chatbot instead of a
purpose-built tool? Sources below **were fetched and read directly**
(OpenAI's full usage paper, Anthropic's affective-use report, Pew) on
2026-10-19 — not secondhand summaries, unlike the caveat on `19` and `20`.

## 1. The headline finding

No company publishes a category called "social dynamics negotiation" or
"conflict navigation." The closest proxies, read directly from primary
sources:

- **OpenAI** (Chatterji et al., *How People Use ChatGPT*, Sept 2025, n≈1.1M
  sampled conversations, May 2024–July 2025): **1.9% of all ChatGPT
  messages** fall under *Relationships and Personal Reflection* (one of 24
  subcategories, under the *Self-Expression* topic). Defined loosely —
  examples given are "what should I do for my 10th anniversary?" and "I
  want you to be my AI girlfriend," so it blends reflection/companionship
  with actual interpersonal-conflict asks, not a clean match.
- **Anthropic** (*How People Use Claude for Support, Advice, and
  Companionship*): **2.9% of all Claude.ai usage** is "affective
  conversations," broken into Interpersonal Advice, Coaching, Counseling,
  Companionship, and Roleplay. **Interpersonal Advice** — "navigating
  relationships and personal dynamics" — is the closest literal match to
  Mend's use case of any published taxonomy bucket, but Anthropic only
  reports the 2.9% aggregate, not Interpersonal Advice alone.
- **Gemini**: no public usage-category breakdown exists. Google has not
  published anything comparable.

At face value, 1.9-2.9% sounds small. It isn't, once you look at volume:

## 2. Why the small percentage is actually a large number

- ChatGPT: **700M+ weekly active users**, **18B messages/week** as of July
  2025 (OpenAI paper, Fig. 3-4). 1.9% of messages on relationships/personal
  reflection ≈ **~340M messages/week** on that topic alone, globally.
  Even a conservative read (some share of that is pure chitchat, not
  advice-seeking) still implies tens of millions of distinct people per
  week going to a general-purpose chatbot for something adjacent to "how do
  I handle a person/relationship."
- Non-work usage overall is **73% of all ChatGPT traffic as of June 2025**,
  up from 53% a year earlier (Table 1) — the growth curve is bending toward
  personal use, not away from it.
- Cross-platform corroboration (Pew Research, "Americans and AI 2026,"
  published June 2026): **27% of U.S. adult internet users** report
  "significant emotional or social interactions" with an LLM (ChatGPT,
  Gemini, Claude, Copilot lumped together — not split by product). Roughly
  **half of U.S. adults now use AI chatbots at all**, up from a third in
  2024. Among 18-29 year-olds specifically: **1 in 5** have used a chatbot
  for emotional support or advice, and **23% have confided in a chatbot
  before telling a human being**.
- Same Pew survey (fielded Feb 17-23, 2026), broken out by age for the
  narrower "use chatbots for emotional support or advice" question —
  confirmed directly from Pew's own chart, exact numbers: **18-29: 20%,
  30-49: 13%, 50-64: 4%, 65+: 2%**. Sharp age gradient — this is a young-
  adult-concentrated behavior, not evenly distributed across the user
  base.

## 3. Evidence the results are poor (the "with poorer results" half)

- Anthropic's own write-up flags that people are turning to models as
  "on-demand coaches, advisors, counselors, and even partners in romantic
  roleplay" — i.e., the model is being asked to do relationship mediation
  work it wasn't designed or evaluated for.
- **Traced to primary source**: Wheatley Institute (BYU) and Institute
  for Family Studies, *Secret Soulmates: How AI Romantic Companions Are
  Impacting Real-Life Romantic Relationships in Young Adulthood* (May
  2026, n=2,431 U.S. adults ages 18-30 who are dating, engaged, or
  married). Full report: https://wheatley.byu.edu/0000019e-1cfd-da4c-a5ff-befd20b10001/secret-soulmates-report
  — **1 in 7 (15%)** of partnered young adults regularly chat with an AI
  built to behave like a romantic partner; a further 20%+ had at least
  "experimented" with it. Among regular users, **69% want to keep the
  extent of it hidden from their real partner**; separately, **~30% said
  their partner has no idea at all**, 11% "only somewhat aware," 14%
  "mostly but not fully aware." Regular use was linked to a **46% decrease
  in the likelihood of being in a stable relationship.** That's a strong,
  now-primary-sourced signal the tool is being used in a way that damages
  rather than repairs the relationship it's nominally helping with.
- **Traced to primary source**: Hily (dating app), *Is Your AI Use a
  Dating Dealbreaker?* survey, n=3,500 Gen Z and Millennial daters in the
  US. Full report: https://hily.com/data/survey-is-your-ai-use-a-dating-dealbreaker/
  — exact figure: **69% of Gen Z ("nearly 7 in 10") and 60% of
  Millennials ("6 in 10") say they wouldn't date someone who relies on AI
  to understand their own feelings.** Related findings on the same page:
  75% of Gen Z (vs. 70% of Millennials) say using AI to "analyze a
  relationship conflict" is a dealbreaker — directly on-point for Mend's
  use case, since that's explicitly the conflict-navigation behavior, not
  general AI use. Survey date/methodology beyond sample size and
  population isn't disclosed on the page.
- Structural reason to expect poor results: general-purpose chatbots have
  no mechanism for hearing both sides, no persistent memory of the
  relationship across sessions (ChatGPT/Gemini/Claude.ai conversations are
  siloed unless the user manually re-feeds context), and are optimized for
  being agreeable to the person typing — a known sycophancy problem when
  the task is actually "tell me what I'm getting wrong in how I'm treating
  this other person."

## 4. What's still missing (the gap Mend's data story needs to fill)

- No taxonomy bucket isolates "conflict/negotiation" from "relationship
  reflection/companionship" — so the true addressable number for Mend's
  specific wedge (helping someone navigate a live interpersonal conflict,
  not just vent or roleplay) is not directly measurable from published
  data. **1.9-2.9% is a ceiling-adjacent proxy, not a precise figure.**
- No source splits usage by device (phone vs. desktop) at all, for any of
  the three. If the claim needs to be phone-specific, that's not
  answerable from existing public data — would need a custom survey or app
  review mining pass.
- No source directly compares outcomes (resolved vs. unresolved, relationship
  harmed vs. helped) across ChatGPT/Claude/Gemini users for this use case.
  The BYU and Hily numbers are suggestive of poor outcomes but weren't
  designed to measure "chatbot conflict mediation quality" as their primary
  question.

## 5. Claim checked and rejected — do not use

A separate AI session produced a pitch-ready-looking stat: **"~40% of
workers use generative AI to buffer workplace communication"**, sourced to
a "Workhuman Human-AI Collaboration Report." Checked directly (2026-10-19)
and this does not hold up — no Workhuman publication returns that figure
for that claim. What's actually out there: Workhuman reports 42% of
employees "use generative AI in workflows weekly" (a general-use number,
not specific to tone-buffering, Slack-message-rewriting, or rephrasing
feedback), and a separate, unrelated survey (Resume Now) found 14% use AI
for writing emails/messages — a different company, different question,
different number. **Do not cite "40% of workers use AI to navigate
workplace communication" anywhere in Mend's pitch material** — it appears
to be a fabricated or badly conflated stat from an AI-generated source
list, not a real finding.

The same pass also re-confirmed two numbers that *do* hold up: the Pew
age-breakdown figures now in Section 1, and that OpenAI's usage paper is
also indexed as **NBER Working Paper 34255** (see Section 6) — same paper
already cited here, just a second valid link for it.

## 6. Mini-study: pulled a real sample, here's what it shows

Ran the sketch from earlier against the actual Google Play review pages
for all three apps (2026-10-19). Methodology actually used: opened the
"See all reviews" panel for ChatGPT, Claude by Anthropic, and Google
Gemini on Google Play, scrolled to load reviews under the default
"Most relevant" sort, and read the extracted page text — **~35 reviews
each for ChatGPT and Claude, ~15 for Gemini (~85 total)**. Not the
keyword-targeted pull originally sketched (Play's review UI doesn't
support in-review text search, so there's no way to pre-filter for
"relationship"/"conflict"/"coworker" mentions before reading) — this was
a straight read of the top of each app's review feed instead.

**Result: zero of the ~85 reviews mentioned relationship advice, workplace
conflict, or any social-dynamics use case at all.** Every single review
was about app mechanics: usage/rate limits, subscription pricing,
login/sync bugs, voice mode glitches, image generation quirks, customer
support quality. Not one mentioned what the person was actually trying to
accomplish with the chatbot in a social/relational sense.

**Why this is a real finding, not a failed pull**: "Most relevant" /
most-helpful-voted app store reviews systematically select for complaints
about the product failing to do its job (crashes, paywalls, limits) —
that's what gets upvoted as "helpful" by other frustrated users hitting
the same bug. A review that says "I used this to figure out how to talk
to my coworker" has no reason to get upvoted and isn't the kind of thing
people are motivated to write unprompted. **App store reviews are
structurally the wrong instrument for this question** — they measure
product friction, not use-case content. This matches a real pattern:
people are far more likely to complain publicly about a rate limit than
to publicly admit what they asked the bot to help them say to their
partner.

**Implication for Mend's data story**: the OpenAI/Anthropic
self-reported-by-the-company numbers (Section 1) are still the best
available evidence, specifically *because* they're drawn from private
conversation samples, not public reviews — the self-reporting problem
runs the opposite direction there (people are more honest/specific with
a chatbot than in a public review, if anything). If a device-specific,
conflict-isolated number is still needed, the right instrument is a
private survey/diary study, not public review mining — reviews won't
surface this use case no matter how large the sample gets.

## 7. Sources (fetched and read directly, 2026-10-19 unless noted)

- Chatterji, Cunningham, Deming, Hitzig, Ong, Shan, Wadman. *How People Use
  ChatGPT.* OpenAI, Sept 15 2025.
  https://cdn.openai.com/pdf/a253471f-8260-40c6-a2cc-aa93fe9f142e/economic-research-chatgpt-usage-paper.pdf
  — also indexed as NBER Working Paper 34255:
  https://www.nber.org/papers/w34255 and listed at Harvard Kennedy School:
  https://www.hks.harvard.edu/publications/how-people-use-chatgpt
- Anthropic. *How People Use Claude for Support, Advice, and
  Companionship.* https://anthropic.com/news/how-people-use-claude-for-support-advice-and-companionship
- Anthropic Economic Index, January 2026 report.
  https://www.anthropic.com/research/anthropic-economic-index-january-2026-report
- Pew Research Center. *Americans and AI 2026: Chatbots, Smart Devices and
  Views on Impact.* Survey fielded Feb 17-23, 2026; report published June
  17, 2026.
  https://www.pewresearch.org/internet/2026/06/17/americans-and-ai-2026-chatbots-smart-devices-and-views-on-impact/
  — age-breakdown chart (20%/13%/4%/2% by age band) confirmed directly at
  https://www.pewresearch.org/chart/1-in-5-adults-under-30-say-they-get-emotional-support-from-chatbots-higher-than-for-older-adults/
- CNBC. "OpenAI says just 1.9% of conversations on ChatGPT are about
  relationships." Oct 6 2025.
  https://www.cnbc.com/2025/10/06/openai-just-1point9percent-of-conversations-on-chatgpt-are-about-relationships.html
- Wheatley Institute (BYU) & Institute for Family Studies. *Secret
  Soulmates: How AI Romantic Companions Are Impacting Real-Life Romantic
  Relationships in Young Adulthood.* May 2026.
  https://wheatley.byu.edu/0000019e-1cfd-da4c-a5ff-befd20b10001/secret-soulmates-report
  (press summary: https://www.prnewswire.com/news-releases/secret-soulmates-1-in-7-young-adults-in-committed-relationships-still-chat-with-an-ai-romantic-companion-302776086.html)
- Hily. *Is Your AI Use a Dating Dealbreaker?* Survey report, n=3,500.
  https://hily.com/data/survey-is-your-ai-use-a-dating-dealbreaker/
- **Rejected**: "~40% of workers use AI to buffer workplace communication"
  (claimed source: Workhuman Human-AI Collaboration Report) — checked
  directly, does not hold up. See Section 5. Do not cite.
