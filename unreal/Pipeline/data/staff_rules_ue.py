"""
Staff answers for the Unreal build that build_data.py cannot take from the web as they are.

The web's presetAnswer() (parts/engine.js) is a chain of regex branches. build_data.py turns the simple ones with
fixed text into DT_StaffRules rows by itself. This file covers the rest:
  - branches whose answer the web computed (who and help per staff member, facts, counts, the earliest exhibit, the
    scenes of a year),
  - branches whose web wording promises something this build does not have yet (riding, painting in the air, the
    hands-on stations, kicking balls), rewritten to say what the player can do here now,
  - branches whose condition is more than one regex (not when asking the way, not a ride, one staff member only).
Each rule names the web branch it stands for ('Web' = the branch's order in presetAnswer; None = Unreal only), so the
builder can report web branches that have no rule. A rule here replaces a generated rule with the same Name.

Fields: Name, Web, Order, Answer, All (regexes that must all match), Not (regexes that must not match), and optionally
MaxWords, StaffOnly, StaffNot, Action, ActionArg, bOffer, OfferLabel, PerStaff (one rule per staff member, named
<Name>-<staff>), Generate ('years': one rule per year of dated exhibits, named <Name>-<year>; 'book_topics': one rule
per book, named <Name>-<NN>-<book>, for a question that also names the book's title, subtitle or section words).
Order < 100 runs before the C++ directions and title matches and >= 100 after, as the web's branches sat before and
after its directions branch (31). Rules with the same Order run by Name.

Placeholders, filled by build_data.py (patterns are ICU regexes, matched case-insensitively):
  {rx:<id>}          the web's RX.<id>              {travel}            asking the way, or to be taken somewhere
  {go}               asking to be taken somewhere   {coaster} {drop} {dive} {anyride}   naming a ride (web whichRide)
  {fact:<id>}        a fact's text                  {source:<id>}       a source's label
  {book:<id>}        a book's title                 {n:<what>}          tokens, badges, books, gallery_items, wax_scenes
  {subjects}         the eight section names        {galleries}         the three gallery names
  {oldest} {newest}  '"<title>," from <year>' of the earliest / latest dated gallery exhibit ({oldest_id} {newest_id})
  {ride_stats:<id>}  the ride's stats sentence      {name} {role} {help} the staff member (PerStaff rules)
"""

NEWEST = r'\b(newest|latest|most recent)\b'
EXHIBIT = r'\bexhibits?\b'
SHOW_NOW = r'{go}|\bshow me\b'
LATER = 'comes in a later build'

PAINT = ('In the 3D Art Studio, Room 101, you’ll paint in the air with brushes like Neon, Ribbon, Chrome and Rainbow, '
         'stamp 3D shapes like stars, hearts and cubes, and spin your work on a turntable. It’s inspired by VR art apps '
         'like Tilt Brush, which XR Showcase featured. Painting itself ' + LATER + '.')
RECOMMEND = 'Three good ones to start with are “{book:vr-program},” “{book:first-job}” and “{book:what-is-xr}”'
SAFETY = ('The rides are virtual, so nothing can hurt you, and the Ocean Dive is the calmest of the three. When riding '
          'opens in a later build, every ride will have a Gentle mode that moves slower.')
RECESS = ('Recess has three rides: the Comet Coaster, the Sky Drop and the Ocean Dive, which open in a later build. '
          'There’s also a soccer goal, a foam-block tower and hidden XR tokens to find.')


def R(name, web, order, answer, all_, **kw):
    rule = {'Name': name, 'Web': web, 'Order': order, 'Answer': answer, 'All': list(all_)}
    rule.update(kw)
    return rule


def offer(action, arg='None', label=''):
    return {'Action': action, 'ActionArg': arg, 'bOffer': True, 'OfferLabel': label}


def run(action, arg='None'):
    return {'Action': action, 'ActionArg': arg}


PLAY = R('R140', 40, 140, 'Out in the Recess Yard there’s a soccer goal with a shootout scoreboard, a foam-block tower '
         'and balls on the grass. Kicking the balls and knocking the tower down come in a later build.', ['{rx:play}'],
         Not=['{anyride}', r'\b(bearing|pendulum|swing time)\b'], StaffNot=['hale'],
         **offer('GoPlace', 'field', 'Take me to the soccer goal'))

RULES = [
    # 4-5 who are you / what can you do, from each staff member's row. Coach Rae's web help invites rides.
    R('R004', 4, 4, 'I’m {name}, the {role} here. I’m a virtual staff member, not a real person. I answer common '
      'questions from what this campus knows.', ['{rx:who}'], PerStaff=True),
    R('R005', 5, 5, '{help}', ['{rx:help}'], PerStaff=True, StaffNot=['rae']),
    R('R005-rae', 5, 5, 'I run the Recess Yard. Ask me about the Comet Coaster, the Sky Drop or the Ocean Dive, or '
      'about the XR tokens hidden around the campus and the badges you can earn.', ['{rx:help}'], StaffOnly=['rae']),
    # 7 Walk the Archive
    R('R007', 7, 7, '{fact:wta}', ['{rx:wta}']),
    # 8 where am I: the web's text without "hands-on" (the stations' hands-on parts come later)
    R('R008', 8, 8, 'You’re in the XRLibraries Campus, a concept made by Ev Holt. The museum tells XRLibraries’ story, '
      'the library holds books about XR, the Workshop School has four rooms for art, science, blueprints and world '
      'building, and recess is out back in the Recess Yard.', ['{rx:where}']),
    # 9 a joke from each staff member
    R('R009-margaret', 9, 9, 'Why do VR headsets make great museum guides? They always help you see the big picture.',
      ['{rx:joke}'], StaffOnly=['margaret']),
    R('R009-rosa', 9, 9, 'Why was the library so tall? It had a lot of stories.', ['{rx:joke}'], StaffOnly=['rosa']),
    R('R009-hale', 9, 9, 'Why did the engineer bring a ladder to the Blueprint Lab? To take the design to the next '
      'level.', ['{rx:joke}'], StaffOnly=['hale']),
    R('R009-rae', 9, 9, 'Why did the roller coaster get good grades? It always stayed on track.', ['{rx:joke}'],
      StaffOnly=['rae']),
    # 11 hours: this build is a desktop app, not the web page on a phone; also "when do you close", "are you open"
    R('R011', 11, 11, 'The campus never closes. It’s open whenever you are.',
      [r'{rx:hours}|\bwhen (do|does|is|are) (you|it|the campus|campus|this place)\b.*\b(open|close|closing)\b|\bare you open\b']),
    # 12 controls: this build's keys (AWTAPlayerController::CreateInputObjects)
    R('R012', 12, 12, 'Walk with W, A, S and D and look around with the mouse. Hold Shift to run and press Space to '
      'jump. Press E or click to open anything that looks interesting, and press Tab to free the cursor so you can '
      'click the floor to walk there. M lists every place on the campus, and T starts the guided tour.',
      ['{rx:move}']),
    # 13-14 painting in the air comes later: the easel's card
    R('R013', 13, 13, 'Let’s paint! I’ll take you to the easel in Room 101. Painting in the air ' + LATER + ', so for '
      'now its card shows how it works.', ['{rx:startPaint}'], **run('OpenStation', 'easel')),
    R('R014', 14, 14, 'A blank canvas is part of painting in the air, which ' + LATER + '. I’ll take you to the easel '
      'in Room 101 so you can see how it works.', ['{rx:blank}'], **run('OpenStation', 'easel')),
    # 15 start a lab test: the station's card (running it yourself comes later)
    R('R015', 15, 15, 'Here’s the titration station in Room 102. Its card walks through finding how concentrated the '
      'mystery acid is; running it yourself ' + LATER + '.', ['{rx:startLab}', r'titration'],
      **run('OpenStation', 'titration')),
    R('R015a', 15, 15, 'Here’s the pendulum in Room 102. Its card explains how timing ten swings measures gravity; '
      'running it yourself ' + LATER + '.', ['{rx:startLab}', r'pendulum'], Not=[r'titration'],
      **run('OpenStation', 'pendulum')),
    R('R015b', 15, 15, 'Here’s the sieve analysis station in Room 102. Its card walks through testing a sand sample, '
      'step by step; running it yourself ' + LATER + '.', ['{rx:startLab}'], Not=[r'titration', r'pendulum'],
      **run('OpenStation', 'sieve')),
    # 16 open a blueprint: walk to the drawing
    R('R016', 16, 16, 'Follow me to the automobile blueprint in Room 103.', ['{rx:openBp}', r'\b(car|automobile)\b'],
      **run('GoPlace', 'bp-car')),
    R('R016a', 16, 16, 'Follow me to the excavator blueprint in Room 103.',
      ['{rx:openBp}', r'\b(excavator|digger|heavy equipment)\b'], **run('GoPlace', 'bp-excavator')),
    R('R016b', 16, 16, 'Follow me to the house blueprint in Room 103.', ['{rx:openBp}', r'\b(house|building)\b'],
      **run('GoPlace', 'bp-house')),
    R('R016c', 16, 16, 'Follow me to the bridge blueprint in Room 103.', ['{rx:openBp}', r'\bbridge\b'],
      **run('GoPlace', 'bp-bridge')),
    R('R016d', 16, 16, 'Follow me to the computer blueprint in Room 103.', ['{rx:openBp}', r'\b(computer|pc)\b'],
      **run('GoPlace', 'bp-computer')),
    # 17 build a model: the bench's card (building it by hand comes later)
    R('R017', 17, 17, 'Here’s the model bench in Room 103, where you’ll put together a rubber-band car or a '
      'two-story building with cross-bracing and then test it. That hands-on part ' + LATER + '.',
      ['{rx:buildModel}'], **run('OpenStation', 'bench')),
    # 19 Room 104 (not when asking the way there)
    R('R019', 19, 19, 'Room 104, the World Builder Studio, shows how a world like this campus gets made. The World '
      'Builder’s Handbook there tells you how to start your own, and the layer table, where you build a mini world one '
      'layer at a time, ' + LATER + '.', ['{rx:worldq}'], Not=['{travel}'],
      **offer('OpenBook', 'world-builder', 'Open the Handbook')),
    # 20 the Science Lab (not a named test, not when asking the way)
    R('R020', 20, 20, 'The Science Lab in Room 102 has three lab stations: a sieve analysis that measures the grain '
      'sizes in sand, an acid–base titration that finds the concentration of a mystery acid, and a pendulum that '
      'measures gravity. Each station’s card walks through how it works.', ['{rx:labq}'],
      Not=['{travel}', r'\b(sieve|psd|titrat|pendulum)'], **offer('GoPlace', 'lab', 'Take me to the lab')),
    # 21 blueprints, short questions only
    R('R021', 21, 21, 'A blueprint is a technical drawing of a design, with every part labeled. The Blueprint Lab, '
      'Room 103, has five on its walls (a car, an excavator, a house, a bridge and a computer), plus a model bench.',
      ['{rx:bpq}'], Not=['{travel}'], MaxWords=4, **offer('GoPlace', 'blueprints', 'Take me to the Blueprint Lab')),
    # 22 3D painting: Mr. Hale always; anyone else who says 3D, air, studio or Tilt
    R('R022', 22, 22, PAINT, ['{rx:paint}'], StaffOnly=['hale'],
      **offer('OpenStation', 'easel', 'Take me to the easel')),
    R('R022a', 22, 22, PAINT, ['{rx:paint}', r'\b(3d|air|studio|tilt)\b'], StaffNot=['hale'],
      **offer('OpenStation', 'easel', 'Take me to the easel')),
    # 23 what is XRLibraries
    R('R023', 23, 23, '{fact:what} Its website is xrlibraries.com.', ['{rx:what}'],
      **offer('OpenItem', 'ca-200', 'Show me where it began')),
    # 24 who runs XRLibraries
    R('R024', 24, 24, '{fact:who} (Source: {source:sjsu}.)', ['{rx:director}', r'xr|librar|run|lead|charge|director']),
    # 25 ride now: riding comes later, so the ride's sign
    R('R025', 25, 25, 'Riding the Comet Coaster ' + LATER + '. Here’s its sign for now.', ['{rx:rideNow}', '{coaster}'],
      **run('OpenRide', 'coaster')),
    R('R025a', 25, 25, 'Riding the Sky Drop ' + LATER + '. Here’s its sign for now.', ['{rx:rideNow}', '{drop}'],
      Not=['{coaster}'], **run('OpenRide', 'drop')),
    R('R025b', 25, 25, 'The Ocean Dive ' + LATER + '. Here’s its sign for now.', ['{rx:rideNow}', '{dive}'],
      Not=['{coaster}', '{drop}'], **run('OpenRide', 'dive')),
    # 26 the hidden tokens (three ride on the rides)
    R('R026', 26, 26, 'There are {n:tokens} glowing XR tokens hidden around the campus: in the museum, the library, '
      'the school hall, every workshop room and the Recess Yard, plus one on each ride, which you can grab once riding '
      'opens in a later build. Look at a token and press E or click to collect it; each one stamps your library '
      'card, and a full card wins a prize at the front desk.', ['{rx:tokens}'],
      **offer('OpenHunt', 'None', 'Show my library card')),
    # 27 badges (the ones this build can award: UWTAProgressSubsystem)
    R('R027', 27, 27, 'There are {n:badges} badges. In this build you can earn First Steps, Museum Explorer, Bookworm, '
      'Ask Away, Living Historian, Good Listener (hear a talk to the end), the workshop badges (finish a station: '
      'Lab Scientist, Model Maker, World Builder, 3D Artist), Certified: Intro to VR (pass the quiz in Room 104), '
      'Trainee (finish a station in the Training Wing), Certified: Dialysis Foundations (finish its five stations '
      'and pass the quiz at the course desk), Creator (finish a station of the 360 storytelling course in Room 101), '
      'Certified: 360 Storytelling (finish its five stations and pass the quiz at the teacher’s desk) and Token '
      'Hunter (find every hidden XR token); the ride and soccer badges arrive with those features in later builds.',
      ['{rx:badges}'], **offer('OpenBadges', 'None', 'Show me the badges')),
    # 28 the Wax Hall (not when asking the way)
    R('R028', 28, 28, '{fact:wax}', ['{rx:wax}'], Not=['{travel}'],
      **offer('GoPlace', 'wax', 'Take me to the Wax Hall')),
    # 29 what happened in <year>: one rule per year
    R('R029', 29, 29, '', [], Generate='years'),
    # 30 history (not when asking the way, not the Wax Hall)
    R('R030', 30, 30, '{fact:history} The Wax Hall acts it all out, scene by scene.', ['{rx:history}'],
      Not=['{travel}', '{rx:wax}'], **offer('GoPlace', 'wax', 'Take me to the Wax Hall')),
    # the two courses (Unreal only): what they are, with the course card to open (asking the way still gets directions)
    R('R036', None, 36, 'Room 101, the 3D Art Studio, runs the creator course, Making a 360 Story: plan the story, set '
      'up the 360 camera, record clear sound, stitch and edit, then share it and keep it, one station each. Finish all '
      'five, then pass the quiz at the teacher’s desk for a certificate.',
      [r'\b(360|storytelling|story ?telling|creator|content[- ]creation)\b', r'\b(course|class|certificate|learn|lesson)\b'],
      Not=['{travel}'], **offer('OpenCourse', 'storytelling', 'Open the course')),
    R('R037', None, 37, 'The Training Wing, past the auditorium, runs the dialysis technician course: hand hygiene, the '
      'machine, the treatment chair, the water and the chart, one station each. Finish all five, then pass the quiz at '
      'the course desk for a certificate.',
      [r'\b(dialysis|technician|training wing|sandi)\b', r'\b(course|class|certificate|learn|train(ing)?)\b'],
      Not=['{travel}'], **offer('OpenCourse', 'dialysis', 'Open the course')),

    # --- after the directions and title matches (the web's branches after 31) -------------------------------------
    # 32 the earliest / latest dated exhibit; "show me" or "take me" goes now. The web left Mr. Hale out ("the first
    # thing here" is a workshop step to him), so he answers only when the question says "exhibit".
    R('R132', 32, 132, 'Follow me. The earliest dated exhibit is {oldest}.', ['{rx:oldest}', SHOW_NOW],
      Not=[NEWEST], StaffNot=['hale'], **run('OpenItem', '{oldest_id}')),
    R('R132a', 32, 132, 'Follow me. The most recent dated exhibit is {newest}.', ['{rx:oldest}', NEWEST, SHOW_NOW],
      StaffNot=['hale'], **run('OpenItem', '{newest_id}')),
    R('R132b', 32, 132, 'The earliest dated exhibit is {oldest}.', ['{rx:oldest}'], Not=[NEWEST], StaffNot=['hale'],
      **offer('OpenItem', '{oldest_id}')),
    R('R132c', 32, 132, 'The most recent dated exhibit is {newest}.', ['{rx:oldest}', NEWEST], StaffNot=['hale'],
      **offer('OpenItem', '{newest_id}')),
    R('R132d', 32, 132, 'Follow me. The earliest dated exhibit is {oldest}.', ['{rx:oldest}', EXHIBIT, SHOW_NOW],
      Not=[NEWEST], StaffOnly=['hale'], **run('OpenItem', '{oldest_id}')),
    R('R132e', 32, 132, 'Follow me. The most recent dated exhibit is {newest}.',
      ['{rx:oldest}', NEWEST, EXHIBIT, SHOW_NOW], StaffOnly=['hale'], **run('OpenItem', '{newest_id}')),
    R('R132f', 32, 132, 'The earliest dated exhibit is {oldest}.', ['{rx:oldest}', EXHIBIT], Not=[NEWEST],
      StaffOnly=['hale'], **offer('OpenItem', '{oldest_id}')),
    R('R132g', 32, 132, 'The most recent dated exhibit is {newest}.', ['{rx:oldest}', NEWEST, EXHIBIT],
      StaffOnly=['hale'], **offer('OpenItem', '{newest_id}')),
    # 33-37 how many (the web's count branch, in its order)
    R('R133', 33, 133, 'Thousands of books line the shelves, and {n:books} of them are open to read right now, on the '
      'featured table and on the ends of the stacks.', ['{rx:count}', r'book'],
      **offer('GoPlace', 'featured', 'Take me to the featured table')),
    R('R134', 34, 134, 'The library has eight sections: {subjects}.', ['{rx:count}', r'section|categor']),
    R('R135', 35, 135, 'The Recess Yard has three rides: the Comet Coaster, the Sky Drop and the Ocean Dive.',
      ['{rx:count}', r'ride'], **offer('GoPlace', 'yard', 'Take me to the yard')),
    R('R136', 36, 136, 'The Wax Hall has {n:wax_scenes} living-history scenes, from 2016 to 2025, with wax figures '
      'that act each one out.', ['{rx:count}', r'scene|wax|figure'],
      **offer('GoPlace', 'wax', 'Take me to the Wax Hall')),
    R('R137', 37, 137, 'The museum has {n:gallery_items} exhibits in three galleries: {galleries}.', ['{rx:count}'],
      **offer('GoPlace', 'g1', 'Take me to Gallery 1')),
    # 38 the sections (Rosa; the others point to her)
    R('R138', 38, 138, 'Our eight sections are {subjects}. Each stack has its featured books on the end facing the '
      'aisle.', ['{rx:sections}'], StaffOnly=['rosa']),
    R('R138a', 38, 138, 'The library has eight sections: {subjects}. Rosa, the reference librarian, can recommend a '
      'book from any of them.', ['{rx:sections}'], StaffNot=['rosa']),
    # 39 a book to read: the web's recommend(), one rule per book (its title, subtitle or section named in the question,
    # first on the shelves wins); with no topic, the starter shelf
    R('R139', 39, 139, '', ['{rx:recommend}|{rx:booksAbout}'], Generate='book_topics'),
    R('R139a', 39, 139, RECOMMEND, ['{rx:recommend}'], **offer('OpenBook', 'what-is-xr', 'Open “{book:what-is-xr}”')),
    R('R139b', 39, 139, RECOMMEND, ['{rx:booksAbout}'], **offer('OpenBook', 'what-is-xr', 'Open “{book:what-is-xr}”')),
    # 40 playing in the yard (not a ride, not the pendulum); Mr. Hale only for the unmistakable yard games
    PLAY,
    R('R140a', 40, 140, PLAY['Answer'], [r'\b(soccer|football|kick\w*|foam blocks?|block tower|merry[- ]?go[- ]?round)\b'],
      StaffOnly=['hale'], **offer('GoPlace', 'field', 'Take me to the soccer goal')),
    # 41 is a ride safe / scary
    R('R141', 41, 141, 'It’s a virtual ride, so you’re safe, but it’s made to feel fast. When riding opens in a later '
      'build, Gentle ride will take it at half speed.', ['{coaster}', '{rx:safety}'], **offer('OpenRide', 'coaster')),
    R('R141a', 41, 141, 'It’s a virtual ride, so you’re safe, but it’s a big drop. When riding opens in a later build, '
      'Gentle ride will lower you slowly.', ['{drop}', '{rx:safety}'], Not=['{coaster}'], **offer('OpenRide', 'drop')),
    R('R141b', 41, 141, 'The Ocean Dive is calm and slow, and nothing down there will hurt you. The dive itself ' +
      LATER + '.', ['{dive}', '{rx:safety}'], Not=['{coaster}', '{drop}'], **offer('OpenRide', 'dive')),
    # 42 how fast / tall / long is a ride
    R('R142', 42, 142, '{ride_stats:coaster}', ['{coaster}', '{rx:stats}'], **offer('OpenRide', 'coaster')),
    R('R142a', 42, 142, '{ride_stats:drop}', ['{drop}', '{rx:stats}'], Not=['{coaster}'], **offer('OpenRide', 'drop')),
    R('R142b', 42, 142, '{ride_stats:dive}', ['{dive}', '{rx:stats}'], Not=['{coaster}', '{drop}'],
      **offer('OpenRide', 'dive')),
    # 43 is it scary (Coach Rae; anyone else who mentions recess or the rides)
    R('R143', 43, 143, SAFETY, ['{rx:safety}'], StaffOnly=['rae'], **offer('OpenRide', 'dive', 'Show me the Ocean Dive')),
    R('R143a', 43, 143, SAFETY, ['{rx:safety}', '{rx:recess}'], StaffNot=['rae'],
      **offer('OpenRide', 'dive', 'Show me the Ocean Dive')),
    # 44 about a ride
    R('R144', 44, 144, 'The Comet Coaster climbs a 19-meter lift hill, drops toward the grass at up to 62 km/h, then '
      'flips you through a loop. Riding it opens in a later build.', ['{coaster}'], **offer('OpenRide', 'coaster')),
    R('R144a', 44, 144, 'The Sky Drop lifts you about 30 meters up, high enough to see the whole campus, then drops you '
      'back down. Riding it opens in a later build.', ['{drop}'], Not=['{coaster}'], **offer('OpenRide', 'drop')),
    R('R144b', 44, 144, 'The Ocean Dive is a guided swim past a coral reef and a kelp forest, with fish schools, a sea '
      'turtle, a whale shark, a manta ray and jellyfish. It’s inspired by ocean VR like Hydrous, a partner listed by '
      'XRLibraries. The dive itself opens in a later build.', ['{dive}'], Not=['{coaster}', '{drop}'],
      **offer('OpenRide', 'dive')),
    # 45 recess (Coach Rae; anyone else who says recess, playground or rides)
    R('R145', 45, 145, RECESS, ['{rx:recess}'], StaffOnly=['rae']),
    R('R145a', 45, 145, RECESS, ['{rx:recess}', r'recess|playground|rides?\b'], StaffNot=['rae']),

    # --- Unreal only: Rosa's chips, which the book search answers poorly ----------------------------------------
    R('R150', None, 150, 'VR replaces everything you see with a computer-made world, so you feel you’re somewhere '
      'else. AR adds digital things to your view of the real world, usually through a phone camera, so you stay where '
      'you are. “{book:what-is-xr}” explains both, and mixed reality too.',
      [r'\b(difference|differences|different|differ|compare|comparison|versus|vs)\b', r'\bvr\b|virtual reality',
       r'\bar\b|augmented'], **offer('OpenBook', 'what-is-xr#1', 'Open “{book:what-is-xr}”')),
    R('R151', None, 151, '“{book:making-360}” walks you through it: plan a story with the people who know it best, '
      'film from a tripod at eye level, record clear sound, keep each scene short, then stitch the footage and share '
      'it.', [r'\b(make|making|film|filming|shoot|shooting|record|recording|create|creating)\b', r'\b360\b'],
      **offer('OpenBook', 'making-360', 'Open “{book:making-360}”')),
]
