"""
Check the staff answers without Unreal: every staff member's suggestion chips (and a few common questions) reach the
DT_StaffRules row they are meant to reach, in the order UWTADialogueSubsystem::Ask tries them.

Python's re stands in for ICU (the rules only use syntax both share). The C++ steps between the rule passes (the
directions and the exhibit/book title match) are not simulated, so questions they answer are listed as such.
In the engine, run WTAChatTest (WTAPlayerController.h) to log every answer for real.

Run: python3 unreal/Tests/check_staff_rules.py   (exit code 1 on any problem)
"""
import json
import os
import re
import sys

UNREAL = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA = os.path.join(UNREAL, 'WalkTheArchive', 'Data')
STOP = set(('a an the and or but if of to in on at by for with from into onto over under about as is are was were be been being am do '
            'does did doing done have has had having i me my mine you your yours he him his she her hers it its we us our they them '
            'their this that these those there here what which who whom whose when where why how can could would should will shall '
            'may might must not no please tell show give get got find let lets like just some any much many more most very really '
            'also too so than then such thing things something anything stuff kind sort want wanted need know think say said go '
            'going went come came see look looking one ones ok okay hey hi hello whats wheres hows thats im youre theres does dont '
            'can cant').split())
KEEP2 = {'vr', 'ar', 'xr', 'ai', 'mr', '3d', 'it'}
CPP = 'C++'   # answered by TryGreeting, TryDirections or TryTitleMatch

# (staff, question) -> the rule that must answer it (or CPP).
EXPECT = {
    ('margaret', 'What is XRLibraries?'): 'R023',
    ('margaret', 'When did XRLibraries start?'): 'R030',
    ('margaret', 'Take me to the Wax Hall'): CPP,
    ('margaret', 'What is Project SANDI?'): CPP,
    ('rosa', 'What is the difference between VR and AR?'): 'R150',
    ('rosa', 'How do I make a 360 video?'): 'R151',
    ('rosa', 'Recommend a book'): 'R139a',
    ('rosa', 'What is Freedom to Read?'): CPP,
    ('hale', 'Start painting'): 'R013',
    ('hale', 'Give me a blank canvas'): 'R014',
    ('hale', 'What workshops are there?'): 'R018',
    ('hale', 'How do blueprints work?'): 'R021',
    ('rae', 'Ride the coaster'): 'R025',
    ('rae', 'What’s on the Ocean Dive?'): 'R144b',
    ('rae', 'Where are the hidden tokens?'): 'R026',
    ('rae', 'Is it scary?'): 'R143',
    ('margaret', 'who are you'): 'R004-margaret',
    ('rae', 'what can you do'): 'R005-rae',
    ('rosa', 'tell me a joke'): 'R009-rosa',
    ('margaret', 'when do you close'): 'R011',
    ('hale', 'how do I move'): 'R012',
    ('margaret', 'what happened in 2019'): 'R029-2019',
    ('margaret', 'what is the oldest exhibit'): 'R132b',
    ('hale', 'what is the oldest exhibit'): 'R132f',
    ('rosa', 'recommend a book about oceans'): 'R139-10-oceans-vr',
    ('margaret', 'do you have any books'): 'R139b',
    ('margaret', 'how many exhibits are there'): 'R137',
    ('rosa', 'what sections are there'): 'R138',
    ('rae', 'what sections are there'): 'R138a',
    ('hale', 'can I play soccer'): 'R140a',
    ('rae', 'how fast is the coaster'): 'R142',
    ('rosa', 'where is the library'): CPP,
}


def toks(text):
    text = re.sub(r"[’']", '', text.lower())
    return [w for w in re.sub(r'[^a-z0-9\s]', ' ', text).split() if w not in STOP and (len(w) > 2 or w in KEEP2 or w.isdigit())]


def first_rule(rules, staff, question, lo, hi):
    n = len(toks(question))
    for r in rules:
        if not lo <= r['Order'] <= hi:
            continue
        if (r['StaffOnly'] and staff not in r['StaffOnly']) or staff in r['StaffNot']:
            continue
        if r['MaxWords'] and n > r['MaxWords']:
            continue
        if re.search(r['Pattern'], question.strip(), re.IGNORECASE):
            return r['Name']
    return None


def answer_rule(rules, staff, question):
    """The rule Ask would use, or CPP when no rule before the C++ steps matches and a later pass would not either."""
    if len(toks(question)) <= 2 and re.match(r'^\s*(hi|hello|hey|howdy|yo|good (morning|afternoon|evening))\b', question, re.I):
        return CPP
    early = first_rule(rules, staff, question, -10 ** 9, 99)
    if early:
        return early
    late = first_rule(rules, staff, question, 100, 10 ** 9)
    return late or CPP


def main():
    with open(os.path.join(DATA, 'StaffRules.json'), encoding='utf-8') as f:
        rules = sorted(json.load(f), key=lambda r: (r['Order'], r['Name']))
    with open(os.path.join(DATA, 'Staff.json'), encoding='utf-8') as f:
        staff = json.load(f)
    problems = []
    for r in rules:
        try:
            re.compile(r['Pattern'], re.IGNORECASE)
        except re.error as exc:
            problems.append('%s: bad regex (%s)' % (r['Name'], exc))
    chips = {(s['Name'], c) for s in staff for c in s['Chips']}
    for key in sorted(chips - set(EXPECT)):
        problems.append('chip %s | %s has no expected answer in this test' % key)
    for (sid, question), want in EXPECT.items():
        got = answer_rule(rules, sid, question)
        if got != want:
            problems.append('%s | %s -> %s, expected %s' % (sid, question, got, want))
    for p in problems:
        print('PROBLEM', p)
    print('%d rules, %d questions checked' % (len(rules), len(EXPECT)))
    print('OK: every chip reaches its answer' if not problems else '%d problem(s)' % len(problems))
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
