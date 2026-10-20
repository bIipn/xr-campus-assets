"""Walk the Archive - motion capture for the Wax Hall reenactors.

build.run() imports the Mixamo clips the wax scenes act out and retargets them onto the project's MetaHuman body
skeleton, leaving one AnimSequence per action at /Game/WTA/Characters/Common/Anims/Mocap/AS_WTA_<action>.
Pipeline/content/wax_acting.json says which action each figure plays and when.
"""

from . import build

__all__ = ['build']
