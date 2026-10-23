# Guided visits

One librarian leads a group through the campus, each visitor on their own computer (roadmap idea 16).

## Running one

1. Every computer runs Walk the Archive and is on the **same network** (the library's Wi-Fi or a classroom switch).
2. **The guide** presses **V** (or Esc, then *Visit together*), types their name and chooses **Lead a visit**. The
   campus reloads in a few seconds with the guide standing where they stood. The first time, Windows may ask whether
   Walk the Archive may use the network: choose **Allow** on private networks (the guide's computer receives the
   visitors).
3. **Each visitor** presses **V**, types their name and picks the guide's visit from *Visits on this network*, then
   **Join**. If the list stays empty (some networks block the little announcement the guide's computer sends), type
   the address the guide's card shows (for example `192.168.1.23`) under *Or join by address*.
4. The guide starts the tour (T, or *Start the tour* on the card). Every stop the guide shows reaches everyone: each
   visitor walks to their own place round it, and their tour bar says *Stop n of 35 · with <guide>*. Between stops,
   visitors may look around; the next stop brings them back.
5. **G**: the guide gathers everyone round them, wherever they stand. A visitor's G walks them to the guide.
6. To finish, the guide chooses *End the visit* on the card; everyone carries on alone where they are. A visitor can
   leave on their own the same way (*Leave the visit*).

Everyone sees everyone as a figure in their own colour with their name over it; the guide's is brass with a GUIDE
tag. Cards, books, rides, the wax scenes and the staff stay each person's own: opening a book on one computer does not
open it on the others.

## How it works

- The guide's computer is an Unreal listen server on UDP port **7777**; visitors join it as clients
  (`UWTAVisitSubsystem::LeadVisit`, `JoinVisit`).
- The guide's computer announces the visit once a second on UDP port **47790** (broadcast on the local network);
  the visit card lists what it hears. `-WTANoBeacon` turns the announcement off.
- What is shared: the people (their figures, names, seats) and `AWTAGameState` (the stop the guide shows, the last
  gathering). Each computer moves its own player (client-authoritative movement), so a group never fights the
  network over where someone stands.
- Each visitor's place round a stop comes from their slot (the order they joined): two arcs behind and beside the
  stop, facing the same way, each place checked for floor and a clear line to the stop (`UWTAVisitSubsystem::GroupSpot`).

## Testing it on one computer

`Tools\win\visit_qa.ps1` starts two games on this computer: one leads a visit, the other joins it at `127.0.0.1`, and
both run their half of the play test (`WTAPlayTest group_lead` / `group_join`). Screenshots go to
`Saved/QA/visit` (`play_NN_group_guide_*`, `play_NN_group_guest_*`). It keeps the game port on this computer
(`-multihome=127.0.0.1`), so Windows does not ask about the network.

## Not yet

- Voice: a group in one room hears the guide; a remote group needs a call alongside (or a later VoIP step).
- Headsets: the visit works in VR once the VR mode (roadmap 17) is in; nothing in it is desktop-only.
