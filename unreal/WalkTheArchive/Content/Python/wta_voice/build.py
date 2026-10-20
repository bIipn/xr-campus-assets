"""Imports the museum's narration into /Game/WTA/Audio.

One WAV per thing the museum can read aloud, named VO_<kind>_<id> after the row it reads (the id with its
hyphens turned to underscores, since an asset name cannot hold a hyphen): VO_exhibit_ca_200, VO_wax_wax_2016,
VO_station_sieve. UWTAVoiceSubsystem builds the same name from a row id and loads it.

The voice is Kokoro-82M (Apache 2.0), run outside the editor; make_narration.py collects the text from
WalkTheArchive/Data/*.json so the words are exactly the ones on the card.

Run it from the editor's Python console:  import wta_voice; wta_voice.build.run()
"""

import os
import unreal

WAV_FOLDER = r'C:\dev\wta_tools\voiceover'
AUDIO_PATH = '/Game/WTA/Audio'


def run(wav_folder=WAV_FOLDER):
    if not os.path.isdir(wav_folder):
        raise RuntimeError('no narration at ' + wav_folder)
    tasks = []
    for name in sorted(os.listdir(wav_folder)):
        if not name.lower().endswith('.wav'):
            continue
        task = unreal.AssetImportTask()
        task.set_editor_property('filename', os.path.join(wav_folder, name))
        task.set_editor_property('destination_path', AUDIO_PATH)
        task.set_editor_property('destination_name', os.path.splitext(name)[0])
        task.set_editor_property('automated', True)
        task.set_editor_property('replace_existing', True)
        task.set_editor_property('save', False)
        tasks.append(task)
    if not tasks:
        raise RuntimeError('no WAVs in ' + wav_folder)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)

    made = []
    for task in tasks:
        made.extend(str(p) for p in task.get_editor_property('imported_object_paths'))
    # Narration is speech: one channel, and it should not duck or loop.
    for path in made:
        sound = unreal.load_asset(path.split('.')[0])
        if isinstance(sound, unreal.SoundWave):
            sound.set_editor_property('looping', False)
            sound.set_editor_property('sound_group', unreal.SoundGroup.SOUNDGROUP_VOICE)
    unreal.EditorAssetLibrary.save_directory(AUDIO_PATH, False, True)
    unreal.log('[wta_voice] imported %d clips to %s' % (len(made), AUDIO_PATH))
    return made
