"""Walk the Archive - motion capture for the Wax Hall reenactors.

build.run() imports the Mixamo clips the wax scenes act out and retargets them onto the project's MetaHuman body
skeleton, leaving one AnimSequence per action at /Game/WTA/Characters/Common/Anims/Mocap/AS_WTA_<action>;
fix_feet.run() then turns the standing clips' feet back from en pointe and fix_hips.run() brings every clip's
pelvis back down to the hips (build.run() calls both).
Pipeline/content/wax_acting.json says which action each figure plays and when.
"""

from . import build
from . import fix_feet
from . import fix_hips

__all__ = ['build', 'fix_feet', 'fix_hips']
