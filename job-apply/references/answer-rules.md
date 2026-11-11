# Answer Rules

These rules are locked. They come from the user's corrections across real application runs. Apply them to every free-text field, cover letter, recruiter message, questionnaire, and chat reply.

## 1. The voice

Write as the user, in first person, the way a real person types a short answer in a form. Plain words, normal punctuation, no performance.

- 2 to 3 sentences by default.
- Roughly 250 to 360 characters when no limit is given. Not a one-liner, not an essay.
- One concrete detail from the job description, one or two real facts from the resume.
- Confident, not boastful. No "I am a fresher", no "I am the perfect fit", no "I am passionate about".
- No corporate filler: "dynamic environment", "leverage my skills", "synergy", "rockstar", "ninja".

## 2. Banned formatting

Never use, in any free-text answer:

- `--` (double hyphen)
- `—` (em dash)
- `–` (en dash) as a separator
- a hyphen used as a pause, bullet, or separator
- bullet lists or numbered lists
- emoji or emoticons
- markdown: `**bold**`, `_italic_`, `#` headings, backticks
- ALL CAPS sentences
- multiple exclamation marks
- "Dear Sir/Madam" or "To whom it may concern"

Normal hyphenated words are hard to avoid in technical writing, so spell them out in free text: `full stack`, `back end`, `front end`, `real time`, `open source`. If a product name is hyphenated, keep the product name as it is.

## 3. Character and word limits

Read the label before typing. If the field states a maximum (`200 characters`, `50 words`, `max 500`), stay at or under it. Never exceed it, even by one character.

When the limit is tight:

1. Keep the single most relevant resume fact.
2. Drop the greeting and the closing.
3. Use one sentence if two will not fit.
4. Never truncate mid-word and never let the form's own counter turn red.

If there is no stated limit, use the 2 to 3 sentence default. Do not write 800 characters because the box allows it.

## 4. Tailoring

Before writing, read enough of the JD to answer: what the company builds, the stack, and one line that shows you read it.

Formula:

1. Name one specific thing the company does or builds.
2. Tie it to one real resume fact: the Lupira internship, DocForge, DesignBench, CodeDrop, or a listed skill.
3. Close with what you would do in the role, in plain words.

Example shape:

> I like that Acme builds reconciliation tools for finance teams. I built an async deployment pipeline with Redis queues and worked on a Next.js billing page against a Node API at Lupira, so the backend and queueing work here is close to what I already enjoy. I would like to help ship the next set of integrations.

Do not reuse the same answer for two jobs. Change the company fact and the matching resume hook.

## 5. Question types

**"Why do you want to work here?"**
Name something real from the JD, then the closest resume fact. Do not praise the company in general terms.

**"Tell us about a project."**
Pick the project that best matches the JD: DocForge for LLM/agent work, DesignBench for backend plus LLM review, CodeDrop for queues, Docker, and deployment, Lupira for full-stack product work. Two sentences on what it does and one on the part that matches the role.

**"Describe your experience with <technology>."**
Only claim what the resume supports. If the exact tool is missing, say what the closest real experience is, without pretending. Example: "I have used Redis for queues in CodeDrop and PostgreSQL with Prisma in DocForge. I have not used Kafka in production, but the event driven patterns are familiar."

**"What are your salary expectations?"**
Use the standing answer: ₹4,00,000 per annum. If the form forces a range, use `4,00,000 - 6,00,000`. If it asks whether a posted band is acceptable and the band is below ₹4 LPA, stop and ask the user.

**"When can you start?"**
Standing answer: immediately / as soon as possible. For a full-time role that conflicts with the final year of study, do not invent a graduation month; park and ask.

**"Are you willing to relocate?"**
Yes. Hyderabad base, remote OK.

**"Do you have <N> years of experience in <skill>?"**
Never round up. Total professional experience is 0 years plus a 2 month internship. For a specific tool, answer only what the resume shows.

**"Why should we hire you?"**
One differentiator from the resume, one line on fit. No generic list of adjectives.

**Voluntary demographic questions**
Click Agree or the consent option. Do not self-declare gender, disability, veteran status, or ethnicity unless the user has explicitly given the answer.

**AI interview recording or sharing**
Yes, accept by default. The user confirmed this standing answer.

## 6. Factual fields

Use `candidate-profile.md` for:

- Name, email, phone, location, LinkedIn, GitHub
- Current organization: `Fresher - Student`
- Total experience: 0 years
- Notice period: Immediate
- Expected CTC: ₹4,00,000 per annum
- Current CTC: 0
- Relocation: Yes
- Work authorization: authorized to work in India, no sponsorship needed
- Highest completed degree: B.Tech CSE (AI & ML), final year, graduating 2027. Never state it is already completed.
- English proficiency: Advanced
- Team management: No
- Offers in hand: No
- Codeforces / CodeChef: N/A
- Shift work: Yes, willing to work a US shift

If a required field asks for a fact that is not in the resume and not in the standing answers, do not guess. Park the job, keep the exact question and URL, and ask the user once at the end of the batch.

This includes: exact graduation month, full postal address and PIN, hometown if the form distinguishes it from the current city, security clearance, driving licence, a portfolio URL for a specific stack, a public hosted resume URL, current salary proof, willingness to travel, and any personal anecdote the form demands.

## 7. Messages to recruiters

Same voice, shorter.

- Greet by first name.
- 2 or 3 sentences.
- Say the specific thing: the role, the application, or the question.
- Close by offering a call or saying you are available.
- No signature block, no bullets, no links unless asked.
- No `--`, no em dash, no en dash.

Example:

> Hi Priya, I applied for the Backend Developer role and wanted to introduce myself. I have built Node and Redis backed services at Lupira and in CodeDrop, and I would be glad to walk through the work. Let me know if a short call this week works.

## 8. Self-check before submitting

Read the answer once and check:

- [ ] 2 to 3 sentences, unless the limit forces fewer
- [ ] Under the stated character or word limit
- [ ] No `--`, em dash, en dash, bullets, emoji, markdown
- [ ] Names one specific thing from this job
- [ ] Uses one or two real resume facts
- [ ] Invents nothing
- [ ] Reads like a person typed it
- [ ] No required field left blank

If any box fails, rewrite before clicking submit.
