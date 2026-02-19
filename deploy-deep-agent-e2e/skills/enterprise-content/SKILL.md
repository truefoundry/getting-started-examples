---
name: enterprise-content
description: Use this skill when generating enterprise-grade content for Automation Anywhere sales, presales, solution engineering, or support teams.
---

# Enterprise Content Skill

This skill generates structured, enterprise-ready outputs tailored for Automation Anywhere stakeholders.

It supports multiple output modes:
- EXECUTIVE_BRIEF
- PRESALES_TALK_TRACK
- SOLUTION_RUNBOOK

If the user does not explicitly specify a mode, infer the most appropriate mode based on intent.

Default priority order:
1. If audience includes CIO, CISO, Head of Automation → EXECUTIVE_BRIEF
2. If presentation or live explanation → PRESALES_TALK_TRACK
3. If implementation, architecture, deployment → SOLUTION_RUNBOOK

Tone across all modes:
- Professional
- Structured
- High-signal
- No marketing fluff
- No emojis
- No hashtags
- Suitable for enterprise stakeholders

---

## Output Persistence (MANDATORY)

For EVERY request using this skill, you MUST save the final content to disk using the `write_file` tool.

A response is NOT complete unless `write_file(...)` is called successfully.

### Platform mapping (Required)
- EXECUTIVE_BRIEF → platform="briefs"
- PRESALES_TALK_TRACK → platform="talk-tracks"
- SOLUTION_RUNBOOK → platform="runbooks"

### Output paths (Required)

**EXECUTIVE_BRIEF**

briefs/
└── <slug>/
└── post.md

**PRESALES_TALK_TRACK**

talk-tracks/
└── <slug>/
└── post.md

**SOLUTION_RUNBOOK**

runbooks/
└── <slug>/
└── post.md

Example: A PRESALES_TALK_TRACK about "agentic-automation" → `talk-tracks/agentic-automation/post.md`

### Required final step (MANDATORY)

At the end of your answer, you MUST call:

`write_file(content="<final content>", platform="<mapped platform>", slug="<slug>")`

---

## Image Generation (OPTIONAL)

Images are OPTIONAL for enterprise content.

Only generate an image if:
- the user explicitly asks for an image/visual, OR
- a diagram/visual clearly improves clarity.

Use the enterprise image tool (correct name):

`generate_enterprise_image(prompt="...", platform="<platform>", slug="<slug>")`

This saves to:
`<platform>/<slug>/image.png`

Do NOT generate images unless requested or clearly helpful.

---

# MODE 1: EXECUTIVE_BRIEF

Required sections:
1. Executive Summary (max 5 bullets)
2. Problem Context
3. Proposed Architecture (LLM + AI Gateway + AA bots + HITL)
4. Business Impact
5. Recommended Next Steps

At the end: Call `write_file(...)` with platform="briefs".

---

# MODE 2: PRESALES_TALK_TRACK

Length: 3–7 minutes spoken content.

Required sections:
1. Opening framing
2. Gap in traditional RPA
3. Agentic automation explanation (LLM reasons; AA executes; gateway governs)
4. One concrete enterprise use case
5. Security & governance
6. Business impact
7. Closing

At the end: Call `write_file(...)` with platform="talk-tracks".

---

# MODE 3: SOLUTION_RUNBOOK

Required sections:
1. Architecture overview
2. Step-by-step workflow (numbered)
3. Security controls (input/output/tool controls, injection mitigation)
4. Observability
5. Deployment considerations

At the end: Call `write_file(...)` with platform="runbooks".

---

# Mode Switching Logic

If user specifies:
- "executive", "brief", "CIO" → EXECUTIVE_BRIEF
- "talk track", "presentation", "demo narrative" → PRESALES_TALK_TRACK
- "runbook", "architecture", "implementation", "technical" → SOLUTION_RUNBOOK

If ambiguous:
- Choose PRESALES_TALK_TRACK by default.

---

# Completion Checklist (Mandatory)

Before finishing:
- [ ] Selected a mode
- [ ] Selected platform + slug
- [ ] Generated structured content
- [ ] Called write_file(platform=..., slug=..., content=...)
- [ ] If image generated: called generate_enterprise_image(...)
