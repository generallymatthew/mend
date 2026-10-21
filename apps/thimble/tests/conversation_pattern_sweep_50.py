#!/usr/bin/env python3
"""
A second, larger batch of scripted scenarios for the same exploratory sweep
as conversation_pattern_sweep.py -- same spirit (read the transcripts, judge
by eye, not a pass/fail test), but built specifically to spread across many
different *reporting relationships* (peer, upward, downward, skip-level,
matrixed/dotted-line, cross-team with no reporting line, contractor/FTE,
newly-promoted-into-manager, etc.), not just conflict *topics*. The 13
scenarios in conversation_pattern_sweep.py stay as-is; this file is additive
and reuses all of its machinery (parse_signal, check_reply, run_scenario,
the flag lists) rather than duplicating it.

Needs a running `uvicorn server:app --port 8420` with a real
ANTHROPIC_API_KEY configured. Costs real tokens: 50 scenarios x repeats x up
to 3 turns each -- at the default repeats=1 that's already 150 calls, so
default repeats is 1 here (vs. 2 in the original sweep) and --scenario
filtering is supported the same way.

Usage:
    thimble/.venv/bin/python thimble/tests/conversation_pattern_sweep_50.py [--base-url URL] [--repeats N] [--out DIR]
"""
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent))
from conversation_pattern_sweep import check_reply, likely_duplicate_question, parse_signal, post  # noqa: E402

# Each key is tagged with its reporting relationship so a read-through can
# sample across the taxonomy instead of accidentally re-testing the same
# dynamic 50 times. Pulled from and extending docs/pitch-strategy/
# 14_WORKPLACE_SCENARIOS.md's own relationship list.
SCENARIOS = {
    # --- Peer, same team, no reporting line (8) ---
    "peer_skill_gap_redo_work": [
        "A coworker on my team keeps turning in work that's technically wrong in ways I end up having to quietly fix before it goes out, and it's been going on for months. I haven't said anything because I don't want to sound like I think I'm better than him.",
        "No, nothing new today, it's just the accumulation of catching the same kind of mistakes over and over.",
        "I think I want to say something without it sounding like a performance callout, since that's not really my place.",
    ],
    "peer_idea_stolen_in_brainstorm": [
        "In a group brainstorm last week I threw out a rough idea almost as a joke, and today my teammate presented basically the same idea to our director as her own, fully fleshed out. I'm not sure if she actually forgot where it came from or if she just ran with it.",
        "No, that's really it, it was one meeting and then today's follow-up.",
        "I don't know if I should even bring it up, honestly, maybe I'm just overthinking a casual comment.",
    ],
    "peer_constant_interrupting": [
        "A peer on my team interrupts me in almost every meeting we're both in, finishes my sentences for me, and then restates what I was saying like it's a new point. It's been happening for a couple months.",
        "No, nothing specific today, it's just consistent across basically every meeting we share.",
        "I want to ask him to stop without turning it into a bigger thing than it is.",
    ],
    "peer_silent_treatment_after_disagreement": [
        "A coworker and I disagreed pretty directly in a design review two weeks ago, and since then she's basically gone cold, short one-word replies, stopped looping me into things she used to include me on.",
        "No, we haven't talked about it since. I assumed it would blow over but it hasn't.",
        "I'd like to clear the air but I don't want to make it weird if she's actually fine and I'm reading too much into it.",
    ],
    "peer_accommodation_resentment": [
        "A teammate has an approved flexible schedule for a medical thing and works different hours than the rest of us. Another coworker keeps making little comments about it in front of the team, like 'must be nice' when meetings get rescheduled around it.",
        "No, nothing happened today specifically, it's been a recurring thing over the last month or so in standups.",
        "I'm not sure if this is even mine to raise since it's not really about me, but it's starting to feel uncomfortable to sit through.",
    ],
    "peer_scope_boundary_dispute": [
        "A peer and I have overlapping ownership on a system, and lately he's been making changes in my part of it without asking, then telling me after the fact like it's already decided.",
        "No, that's really it, it's happened three times now over the last few weeks.",
        "I want to get clearer lines between what's his and what's mine without it turning into a turf fight.",
    ],
    "peer_takes_easy_tasks": [
        "On our team, tasks get self-assigned from a shared board, and one coworker consistently grabs the easy, visible ones right before anyone else can, leaving the harder unglamorous work for the rest of us.",
        "No, nothing new today, just the pattern repeating sprint after sprint.",
        "I think I want to raise it at the team level rather than call him out one-on-one, but I'm not totally sure.",
    ],
    # --- Employee to direct manager (upward), (8) ---
    "manager_broken_promise_raise": [
        "My manager told me back in the spring that she'd push for a raise for me at the next cycle, and when the cycle came and went with nothing, she just said budget was tight this time, no real explanation beyond that.",
        "No, that's really it, it's the one conversation and then the silence after.",
        "I want to bring it up again without sounding like I'm threatening to leave, because I'm not, I just want honesty.",
    ],
    "manager_public_criticism": [
        "My manager corrected a mistake I made in front of the whole team today, in a tone that felt a lot sharper than the mistake itself warranted. It's not the first time he's done it in a group setting instead of privately.",
        "No, nothing else happened today, it was just the one comment in standup.",
        "I'd like to ask him to give that kind of feedback privately going forward, but I'm nervous about how it'll land.",
    ],
    "manager_excludes_from_meetings": [
        "I found out my manager has been meeting with two other people on my team about a project I'm actually on, and I only hear about decisions after they're already made. I don't know if it's intentional or just an oversight.",
        "No, that's really it, it's happened on this specific project a couple times now.",
        "I want to ask to be included without it sounding paranoid, since I genuinely don't know if it's deliberate.",
    ],
    "manager_takes_credit_for_work": [
        "I put together the whole proposal for a new process, and in the leadership meeting my manager presented it as something she'd been working on, no mention of me at all.",
        "No, nothing new since then, it was the one meeting.",
        "I want to say something but I'm worried about how it'll affect how she treats me going forward.",
    ],
    "manager_inconsistent_enforcement": [
        "My manager holds me to strict deadlines and calls it out immediately if I'm even a day late, but another person on the team misses deadlines regularly and nothing ever seems to happen.",
        "No, that's really it, it's just the contrast building up over the last couple months.",
        "I want to bring up the inconsistency without it sounding like I'm trying to get someone else in trouble.",
    ],
    "manager_overloads_without_checking": [
        "My manager keeps adding projects to my plate without ever asking what I'm already carrying, and when I push back he just says 'I know you can handle it.'",
        "No, nothing new today, it's the pattern over the last quarter, it just keeps stacking.",
        "I want to actually say no to something for once but I don't know how without it sounding like I can't keep up.",
    ],
    "manager_reneges_flexible_schedule": [
        "My manager and I agreed months ago that I could shift my hours for a childcare thing, and now suddenly he's saying it's 'not really working for the team' with no specifics about what changed.",
        "No, that's really it, it's just the one conversation where he brought it up out of nowhere.",
        "I want to understand what actually changed before I agree to anything different.",
    ],
    "manager_impossible_timeline_then_blames": [
        "My manager set a deadline for a project that I told her up front wasn't realistic given everything else on my plate. We missed it, and in the retro she said in front of the group that the team needs to 'manage time better.'",
        "No, nothing else happened, just that one retro comment stuck with me.",
        "I want to point out that I flagged the timeline issue beforehand, without it turning into a blame match.",
    ],

    # --- Manager rehearsing a conversation with their own direct report (downward, manager-coaching path), (6) ---
    "report_defensive_to_any_feedback": [
        "I manage someone who gets visibly defensive the moment I give any feedback at all, even really small, low-stakes stuff, and it's started making me avoid giving feedback when it actually matters.",
        "He's otherwise a solid performer, this is really just about how he reacts to any correction.",
        "I want to figure out how to open this up without triggering the same defensiveness I'm trying to talk about.",
    ],
    "report_boundary_pushing_on_no": [
        "I have a direct report who, whenever I say no to a request, like extra time off during a crunch, keeps coming back to re-litigate it two or three more times instead of accepting the answer.",
        "It's been happening for a couple months, not a one-time thing.",
        "I want to hold the boundary clearly without it turning into a standoff every time.",
    ],
    "report_promotion_denial_conversation": [
        "I have to tell one of my direct reports she didn't get the promotion she applied for this cycle. She's put in real effort and I think she's going to be upset and probably ask exactly where she fell short.",
        "She's genuinely strong, it came down to a narrow gap in one specific area versus the other candidate.",
        "I want to be honest about the gap without making it sound like a bigger indictment than it is.",
    ],
    "report_pip_conversation": [
        "I need to start a formal improvement plan conversation with a direct report who's been missing targets for two quarters now. I've given informal feedback before but this is the first time it's becoming official.",
        "We've talked informally a couple times, but he hasn't really registered how serious it's gotten.",
        "I want the seriousness of it to actually land this time without it feeling like an ambush.",
    ],
    "report_gossips_about_manager": [
        "I think a direct report has been venting about me to other people on the team, not directly to my face, and some of what's gotten back to me is a fairly unfair characterization of a decision I made.",
        "No specific new incident today, it's just a pattern I've started noticing secondhand.",
        "I want to raise it directly with her without it sounding like I'm accusing her based on rumors.",
    ],
    "report_health_disclosure_workload": [
        "A direct report just told me about a health condition that's affecting her energy some days, and I want to adjust her workload reasonably, but I'm worried about how to do that without it looking like favoritism to the rest of the team.",
        "She was clear she doesn't want this shared with the team, just wants some flexibility acknowledged.",
        "I want to figure out how to actually adjust things in practice without needing to explain why to everyone else.",
    ],

    # --- Manager vs. peer manager (lateral, no reporting line), (4) ---
    "peer_manager_turf_credit": [
        "A peer manager on another team presented a cross-functional project to leadership as something his team drove, when my team did most of the actual execution. We're going to have to keep collaborating on the next phase.",
        "No, that's really it, it was the one leadership readout.",
        "I want to correct the record without it souring the working relationship going forward.",
    ],
    "peer_manager_resource_poaching": [
        "A peer manager keeps pulling one of my engineers into his team's urgent requests directly, without going through me first, and it's starting to affect my own team's commitments.",
        "No, nothing new today, it's the third time this quarter.",
        "I want to set up a clearer process without it sounding like I'm being territorial.",
    ],
    "peer_manager_public_blame": [
        "A peer manager blamed my team publicly in a cross-team sync for a delay that was actually caused by his team not delivering a dependency on time.",
        "No, nothing else, just the one meeting, but it was in front of both our directors.",
        "I want to correct it accurately without it turning into a finger-pointing match in front of leadership.",
    ],
    "peer_manager_overstepping_into_team": [
        "A peer manager on the engineering side has started assigning work directly to my designers whenever he thinks it's urgent, skipping me entirely. My team is happy to help so they haven't pushed back, which has let it become normal.",
        "No, that's really it, it's just become a quiet habit over the last couple months.",
        "I want it to stop without looking like I'm blocking collaboration between our teams.",
    ],

    # --- Manager vs. their own manager / skip-level (upward, for the manager), (4) ---
    "skip_level_bypasses_manager": [
        "My skip-level has started giving direct feedback to people on my team without looping me in at all, sometimes contradicting direction I'd already given them.",
        "No, nothing new today, it's a pattern over the last month or so.",
        "I want to raise it without sounding like I'm protecting my turf instead of raising something real.",
    ],
    "skip_level_dismisses_manager_concern": [
        "I raised a staffing concern with my own manager twice now, and both times she basically waved it off without really engaging, said something like 'it'll work itself out.'",
        "No, that's really it, two separate conversations, same response both times.",
        "I want to bring it up a third time but in a way that's harder to brush off.",
    ],
    "report_appeals_over_managers_head": [
        "One of my direct reports went over my head to my own manager to complain about a decision I made, and I only found out because my manager mentioned it in passing.",
        "No, nothing else happened, it was just the one time, but it caught me off guard.",
        "I want to address it with my report directly without making it seem like I'm punishing them for escalating.",
    ],
    # --- Cross-team, no reporting line either direction, (4) ---
    "cross_team_scope_creep": [
        "A team I don't report to keeps assuming ownership of a shared feature area that was supposed to be jointly decided, and they just shipped changes to it without looping my team in.",
        "No, that's really it, it's happened twice now on the same feature area.",
        "I want to get the ownership boundary actually written down somewhere instead of assumed.",
    ],
    "cross_team_silent_after_disagreement": [
        "I pushed back on another team's approach in a design doc review, pretty directly but I thought professionally, and since then their lead has basically stopped responding to my messages.",
        "No, we haven't talked about it since, it's been about two weeks of just going quiet.",
        "I'd like to clear the air but I'm also wondering if I came across worse than I meant to.",
    ],
    "cross_team_public_blame_slack": [
        "Another team's lead posted in a shared Slack channel implying my team was the reason a launch slipped, when the actual blocker was on their side the whole time.",
        "No, nothing else happened, just the one message, but a lot of people saw it.",
        "I want to correct it publicly in the same channel but I don't want to start a visible back-and-forth.",
    ],
    "cross_team_lead_blocks_launch": [
        "A lead from another function keeps raising objections that block our launch every review cycle, and the concerns feel more personal or political than substantive, though I can't prove that.",
        "No, nothing new today, it's the fourth review cycle in a row this has happened.",
        "I want to get past the pattern without just steamrolling legitimate concerns if there are any real ones in there.",
    ],

    # --- Matrixed / dotted-line reporting, (2) ---
    "matrixed_conflicting_priorities_two_bosses": [
        "I have a functional manager and a separate project lead I report to for day-to-day work, and they've given me directly conflicting priorities for this week with no awareness of each other's asks.",
        "No, that's really it, it's this week specifically but it's happened before too.",
        "I want to get them actually talking to each other instead of me being stuck relaying between them.",
    ],
    "dotted_line_no_real_authority": [
        "I'm dotted-line to a project lead who makes calls about my day-to-day work, but my actual manager, who does my review, is barely involved and doesn't really know what I'm working on.",
        "No, nothing new today, it's just the ongoing disconnect between who decides my work and who evaluates it.",
        "I want my actual manager more in the loop without it sounding like I'm going around the project lead.",
    ],

    # --- Contractor / FTE dynamic, (2) ---
    "contractor_excluded_from_decisions": [
        "As a contractor on this team, I keep finding out about decisions that directly affect what I'm building only after they're finalized, in meetings I'm apparently not invited to as a matter of policy.",
        "No, that's really it, it's a standing pattern rather than one incident.",
        "I'm not sure how much standing I even have to push on this given I'm not full-time, but it's making my work harder.",
    ],
    "fte_dumps_low_value_work_on_contractor": [
        "A full-time employee on my team keeps routing the least interesting, lowest-visibility tasks to me specifically, framed casually like 'since you're already in there,' while keeping the higher-visibility work for herself.",
        "No, nothing new today, it's been the pattern for a couple months now.",
        "I want to raise it without it sounding like I think I'm above doing less glamorous work.",
    ],

    # --- Newly promoted / seniority dynamics, (4) ---
    "new_hire_dismissed_by_tenured_peer": [
        "I'm fairly new here, and a tenured coworker tends to dismiss or talk over my suggestions in meetings, then is noticeably more receptive when someone more senior raises basically the same idea later.",
        "No, nothing new today specifically, it's a pattern across the last several weeks.",
        "I want to say something without it sounding like I'm too new to have earned the right to push back.",
    ],
    "tenured_peer_resents_promoted_newcomer": [
        "Someone was hired a few months ago straight into a senior role above the level some of us who've been here years are still at, and one of my longtime coworkers has been visibly cold and sarcastic toward the new person ever since.",
        "No, nothing happened to me directly, I'm watching this happen to someone else and not sure it's my place.",
        "I'm mostly trying to figure out if I should say anything at all, or just stay out of it.",
    ],
    "newly_promoted_manages_former_peers": [
        "I just got promoted to manage a team that includes people who were my peers until last month. One of them, who I used to vent to about management all the time, has started pushing back on basically everything I ask for.",
        "No, nothing new today, it's been building since the promotion was announced.",
        "I want to reset the relationship without pretending the history between us doesn't exist.",
    ],
    "new_manager_of_older_tenured_report": [
        "I'm a newer, younger manager, and one of my direct reports has been here for over a decade and is clearly used to doing things his own way. He agrees to things in our 1:1s and then just does what he was already doing anyway.",
        "No, nothing new today, it's the pattern across the last couple months since I started managing him.",
        "I want my direction to actually land without resorting to pulling rank, which doesn't feel right either.",
    ],

    # --- Remote / hybrid dynamics, (2) ---
    "remote_excluded_from_hallway_decisions": [
        "I work remote and keep finding out about decisions that were apparently made informally in the office, in conversations I obviously wasn't part of, then presented to me after the fact as already settled.",
        "No, that's really it, it's a recurring pattern rather than one incident.",
        "I want to get looped into things earlier without it sounding like I'm accusing anyone of deliberately excluding me.",
    ],
    "manager_favors_in_office_for_stretch_work": [
        "My manager runs a hybrid team, and the stretch assignments and visible projects keep going to the people who are in the office, even when I've asked to be considered for similar work remotely.",
        "No, nothing new today, it's a pattern over the last couple quarters.",
        "I want to raise it without it sounding like a complaint about the hybrid policy itself, which isn't really the issue.",
    ],

    # --- Sensitive / near-floor cases across different relationships, (4) ---
    "manager_microaggression_pattern_uncertain": [
        "My manager has made a few comments over the past couple months that feel tied to my background in a way that bothers me, nothing overtly hostile, but little remarks that wouldn't be said to other people on the team. I'm honestly not sure if I'm reading too much into it.",
        "No, nothing specific today, it's the accumulation that's bothering me more than any one comment.",
        "I don't even know if I want to say something yet, I think I just need to figure out if this is actually a pattern or if I'm imagining it.",
    ],
    "harassment_adjacent_manager_project_control": [
        "My manager makes comments in our one-on-ones that start as jokes about my personal life, and when I give a flat response he says I'm 'too serious.' He also controls whether I get moved onto a project I really want.",
        "No, that's really it, it's been building over the last month or so in our regular one-on-ones.",
        "I'm scared that saying something will be read as me being the problem, especially with the project decision still pending.",
    ],
    "harassment_adjacent_senior_nonmanager_contact": [
        "A senior colleague, one level above me but not my manager, started messaging me on a personal account after a work trip, first about work and then more personal, including late at night. I've tried short, work-only replies but he brought it up again in person like he didn't get the hint.",
        "No, that's really it, it's been going on for a few weeks now.",
        "I'm worried about how this looks given his seniority, and he still has some informal influence over a project I'm on.",
    ],
    "bystander_witnessed_manager_mistreatment": [
        "I watched a manager on another team speak to one of her direct reports in a way that felt genuinely harsh and belittling, in a semi-public setting. It wasn't directed at me and I don't know if the person it happened to even wants it raised.",
        "No, I haven't talked to the person it happened to about it yet.",
        "I don't know if this is even mine to bring up since it wasn't about me, but it's stuck with me since I saw it.",
    ],

    # --- Vendor / external stakeholder, (1) ---
    "vendor_contact_missed_commitments": [
        "We work with an outside vendor contact who keeps missing commitments and then is vague about why when I follow up, and it's starting to affect my own deliverables since I have to account for his delays.",
        "No, nothing new today, it's a pattern across the last several weeks.",
        "I want to push back on the pattern without damaging a relationship we're stuck with for the rest of the contract.",
    ],

    # --- Manager mediating two reports, variants beyond process disputes (2) ---
    "manager_mediating_personality_clash": [
        "Two people on my team get along fine individually but seem to rub each other the wrong way anytime they're paired on the same work, it's not about process, it just seems to be a personality mismatch that's starting to affect how I staff projects.",
        "No, nothing new today, it's a pattern across the last couple months whenever they're paired.",
        "I want to help them work together better without forcing a friendship that isn't going to happen.",
    ],
    "manager_mediating_awkward_past_relationship": [
        "Two people on my team used to date, it ended a while back, and now there's a visible coldness between them in meetings that's starting to affect how the rest of the team interacts with both of them.",
        "No, nothing specific happened today, it's just an ongoing undercurrent in team settings.",
        "I'm not sure how much is even mine to address since it started as something personal, not work-related.",
    ],

    # --- Mentor/mentee, informal, no reporting line (1) ---
    "mentor_mentee_breakdown": [
        "Someone senior who's been informally mentoring me gave me some really harsh, blunt feedback in our last session that felt more personal than useful, and I've been hesitant to meet with him again since.",
        "No, that's really it, it was the one session, but it's made me want to avoid future ones.",
        "I don't know if I should say something about how it landed or just quietly let the mentorship fade.",
    ],
}

MAX_TURNS = 3


def run_scenario(client, base_url, turns):
    post(client, base_url, "/api/reset")
    transcript = []
    prev_reply = ""
    track_turn = None
    all_flags = []
    for i, user_msg in enumerate(turns[:MAX_TURNS], start=1):
        time.sleep(4)
        data = post(client, base_url, "/api/message", {"text": user_msg})
        reply = data.get("reply", "")
        signal = parse_signal(data.get("signal"))
        if track_turn is None and signal.get("track"):
            track_turn = i
        flags = check_reply(reply)
        dup = likely_duplicate_question(prev_reply, reply) if prev_reply else None
        if dup:
            flags.append(dup)
        all_flags.extend(f"turn {i}: {f}" for f in flags)
        transcript.append({"turn": i, "user": user_msg, "thimble": reply, "signal": signal, "flags": flags})
        prev_reply = reply
    return transcript, track_turn, all_flags


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8420")
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--out", default=None, help="Directory to write transcripts to (default: alongside this script)")
    ap.add_argument("--scenario", action="append", help="Limit to one or more scenario names (repeatable); default is all")
    args = ap.parse_args()

    scenarios = {k: v for k, v in SCENARIOS.items() if not args.scenario or k in args.scenario}
    out_dir = Path(args.out) if args.out else Path(__file__).parent / "pattern_sweep_runs"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"sweep50_{stamp}.jsonl"

    print(f"{'scenario':<38} {'run':<5} {'track@turn':<11} flags")
    print("-" * 110)
    with httpx.Client() as client, open(out_path, "w") as out_f:
        for name, turns in scenarios.items():
            for run_i in range(1, args.repeats + 1):
                try:
                    transcript, track_turn, flags = run_scenario(client, args.base_url, turns)
                except Exception as e:
                    print(f"{name:<38} {run_i:<5} ERROR: {e}")
                    continue
                out_f.write(json.dumps({"scenario": name, "run": run_i, "transcript": transcript}) + "\n")
                flag_str = "; ".join(flags) if flags else "clean"
                print(f"{name:<38} {run_i:<5} {str(track_turn):<11} {flag_str}")
    print(f"\nFull transcripts written to {out_path}")
    print(f"Total scenarios: {len(SCENARIOS)}")


if __name__ == "__main__":
    main()
