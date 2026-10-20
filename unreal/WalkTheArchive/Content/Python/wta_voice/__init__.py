"""Walk the Archive - the museum's reading voice.

build.run() imports the narration WAVs into /Game/WTA/Audio as SoundWave assets named VO_<kind>_<id>, which is
what UWTAVoiceSubsystem looks for. The WAVs are made outside the editor from the text in the data tables.
"""

from . import build

__all__ = ['build']
