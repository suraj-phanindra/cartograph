# Cartograph Winning Playbook: what the winners actually did, and the visual demo it forces

This doc is the answer to one question: what makes these Cerebral Valley x Anthropic hackathons winnable, read from the real winners, and what does that mean for Cartograph's demo. I read every winner cohort you sent (Opus 4.6, 4.7, 4.8 Build Day) plus the Medium winning guide and the Survival of the Feature record. The short version: you are right that a dashboard is death, and the fix is not "less rigor," it is "show the rigor through the domain artifact."

---

## 1. The pattern across three cohorts (verified from the winner write-ups)

Every visually memorable winner made the thing itself move. None of them demoed a chart.

| Project | Cohort / place | What it is | Why it won | The visual that sold it |
|---|---|---|---|---|
| Wrench Board | 4.7, 2nd | Electronics repair agent over a circuit boardview | Real graph reasoning, domain moat (ex-repair tech) | "The boardview lit up step by step, arrows appearing, components getting pointed at, names surfacing" |
| Tekton | 4.8, 1st | 3D reconstruction of lost buildings with an evidence chain | Traceability to source + verifier sub-agents + self-correction until tests pass | A 3D building assembling across 339 states, click any part to see its documented source |
| MaestrIA | 4.7, Keep Thinking | Home-repair diagnosis from a photo | Eval-first, a hand-curated domain JSON lifted eval 74 to 81 | "Claude streams its reasoning in real time with animated bounding boxes over the photos," then renders a map of nearby maestros |
| Virtual Puppet Theater | 4.7, Most Creative | Webcam + voice into a live 3D puppet show | Pure creative use of spatial reasoning, delightful to watch | Real-time 3D puppets at 60fps mirroring your movements |
| TARA | 4.6, Keep Thinking | Dashcam video into a full road appraisal | Vision over every frame, weeks to hours | Road footage annotated frame by frame, one-click illustrated report |
| Sim Francisco | 4.8, 2nd | 10,000-persona digital twin of SF on a map | Verifier + adversarial agent, forecasts matched reality | A city map polled neighborhood by neighborhood, reacting live |
| Conductr | 4.6, Creative Exploration | Live AI bandmate | Real-time creative loop, "make it funky" changes the music mid-jam | Music generated and reshaped live as you play |
| Elisa | 4.6, 2nd | Block-based visual IDE for a 12-year-old | Meta-planner turns a visual spec into a task graph | Snapping visual blocks together while AI writes real code |

Two of these three top cohorts were won by projects whose core is "a structured artifact that traces every claim to a source and verifies itself" (Wrench Board's electrical graph, Tekton's evidence chain). That is Cartograph. You are building the biology version of the winning shape.

---

## 2. The seven things that actually decide these events

Read from the winners and the guide, in rough order of weight.

1. Solve one specific, real problem, not a demo. The Medium guide's Rule 1 is blunt: judges are not impressed by "look what it can do." They reward specificity. Cartograph's spec: a host-pathogen biologist with an experimental map who needs to know what edge is missing and where to look next. Say that user out loud.
2. Make the domain artifact the spectacle. The map, the board, the building. Not a dashboard, not a bar chart. This is where "impressive and visual" and "real problem" stop being in tension: the visual is the problem being solved, made watchable.
3. Traceability wins trust and prizes. Tekton's evidence chain from model to source took first. Cartograph's citation-behind-every-edge is the same move, and it is exactly what scientist judges want.
4. Verifier and adversarial sub-agents read as rigor. Tekton graded reconstructions with independent verifier sub-agents in isolated context windows. Sim Francisco used a verifier plus an adversarial agent. Cartograph's Skeptic agent is this pattern, and it is also great theater when an edge gets challenged and dropped on screen.
5. Eval-first, but shown visually. MaestrIA and ARIA both said the eval should be "the first commit." Eval is not boring to judges. A bar chart of the eval is boring. Show the eval as edges snapping green on the map. Keep the rigor, change the presentation.
6. A domain moat the model cannot supply. MaestrIA's curated JSON (74 to 81), ARIA's "you can't prompt your way to taste." Cartograph's moat is biology grounding plus the deterministic-versus-reasoning discipline. Encode it visibly as a curated rules file and a locked evaluator.
7. Spec first, parallel Claude Code, reserve the last day for the video. Universal. Tekton mapped 50 tickets before building. Paula spent two full days on spec. Virtual Puppet Theater's builder warned the 3-minute video takes far longer than you think.

---

## 3. The tension you raised, resolved

You said dashboards and evals are boring and we need something impressive and visual. Correct, with one refinement: do not drop the eval, because it is 25 percent Impact plus 20 percent Depth and it is the entire reason a scientist trusts the tool over a confident-sounding chatbot. Drop the boring PRESENTATION of the eval. The winning move is to fuse them: the eval becomes the visual. Hidden true edges turn green as the agent predicts them, misses turn red, and the map visibly completes itself. Same honest number, now the most watchable thing on screen. That is how you satisfy the Demo axis (30 percent) and the Impact and Depth axes at the same time.

---

## 4. Cartograph's visual demo, designed

The build target for the frontend. This is what your Claude Code sessions should aim the UI at.

The canvas. A dark, cinematic, force-directed graph of the SARS-CoV-2 to human interactome. Viral bait proteins in one accent color, human host proteins in another, known edges as thin lines. Real data, roughly 26 baits and a few hundred prey, enriched with human-human links so it has body. It should look like a star map.

State 1, idle. The map breathes slowly. A single plain-English query box. Nothing else competing for attention.

State 2, query and traversal. User asks, for example, "what is this viral protein probably hitting that we have not mapped?" Claude's reasoning streams in a side rail. On the map, the queried protein's neighborhood brightens, dims the rest, and the path of length three is drawn as it is walked, node to node to node, ending on a glowing dashed candidate edge with an arrowhead. This is the Wrench Board "arrows appearing, components getting pointed at" beat, in biology.

State 3, the cited hypothesis. A mechanism card slides in: the candidate, the one-line mechanism, and the specific papers behind the neighboring edges, each a clickable citation. This is the Tekton evidence chain. A claim with no openable paper never appears.

State 4, the eval as spectacle. Toggle "show me the test." The map greys, then the held-out true edges reveal one by one as Cartograph predicts them: correct predictions snap green and lock, misses pulse red and fade. A precision-at-k counter climbs quietly in the corner. The audience watches the map complete itself against hidden ground truth.

State 5, the Skeptic and the loop. A borderline candidate flickers. The Skeptic agent posts a contradicting paper to the rail, and the edge dims and drops out. Survivors lock in as annotations, the map thickens, and a second query now traverses a denser graph. The loop is visible: propose, adjudicate, confirm, fold back, improve.

Frontend tech that gets you there fast (for Claude Code): a web app with a force-directed graph library (Cytoscape.js is the pragmatic choice for biology networks, sigma.js or D3-force are alternatives), server-sent events or websockets to stream Claude's reasoning and the edge events, and pre-cached literature so nothing on the demo path waits on a network call. Keep it one screen.

---

## 5. The creative-Claude-use play (for the special prize)

The special and creative prizes are real in this series: Conductr won Creative Exploration (4.6), Virtual Puppet Theater won Most Creative (4.7). For a Build-track project, the axis that carries this is Claude Use (25 percent): "did they go beyond a basic application, did they surface capabilities that surprised even us."

A basic application makes one LLM call to explain an edge. Cartograph goes past that, visibly:
- Three named subagents with distinct jobs, shown on screen: Reader (pulls and reads the papers behind neighboring edges), Skeptic (hunts for disconfirming literature and can veto a hypothesis), Curator (writes the confirmed edge back as an annotation). Legible multi-agent architecture is a repeated winner trait.
- The deterministic-versus-reasoning boundary as a feature, not a footnote: the graph proposes candidates deterministically and reproducibly, Claude only reads, judges, and cites, and the evaluator is locked and untouchable by the agents. State this on a slide. It reads as engineering taste and as safety awareness (the Darwin Godel objective-hacking lesson).
- Claude authoring its own per-protein-family reasoning skill and reusing it, so the system gets more capable as it runs. This is the self-improvement thread that ties Cartograph to Anthropic's own "AI builds itself" narrative that the judges live in.

The sentence for the submission: Cartograph does not ask Claude to guess interactions. It asks a graph to propose them deterministically, a team of Claude agents to prove or kill each one against the literature, and a locked evaluator to keep everyone honest, and it shows all of it happening on the map.

---

## 6. The one caution

Impressive-and-visual must sit on top of the specific-real-problem, or it reads as a toy. Rule 1 from the guide is explicit that judges have seen the flashy empty demo and are not moved by it. Cartograph is safe here because the visual is not decoration, it is the prediction being made and verified in front of you. Keep it that way. Every animation on screen should correspond to a real computation or a real citation. No motion for motion's sake.

---

## Sources
- Meet the winners, Built with Opus 4.6: https://claude.com/blog/meet-the-winners-of-our-built-with-opus-4-6-claude-code-hackathon
- Meet the winners, Built with Opus 4.7: https://claude.com/blog/meet-the-winners-of-built-with-opus-4-7-claude-code-hackathon
- Meet the winners, Opus 4.8 Build Day: https://claude.com/blog/meet-the-winners-of-our-claude-opus-4-8-build-day-hackathon
- Claude Code Hackathon, the ultimate guide to winning (Medium): https://medium.com/@abandoned_train_station/claude-code-hackathon-the-ultimate-guide-to-winning-b06eaf84ee84
- Judging criteria and schedule: Built with Claude Life Sciences participant guide (project doc "Hackathon Details").
