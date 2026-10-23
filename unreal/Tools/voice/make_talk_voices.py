"""Reads every talk and class aloud: one WAV per slide line in the speaker's own voice, named the way the engine
finds them (VO_talk_<talk>_<nn>.wav, the id's hyphens as underscores; a course's welcome is its _01), plus each class's quiz questions
(VO_quiz_<talk>_<nn>.wav) so a visitor can listen instead of read, and every station's steps in the campus's
reading voice (VO_station_<station>_<nn>.wav, from WalkTheArchive/Data/Stations.json: the words on the step card).

    python3 unreal/Tools/voice/make_talk_voices.py [--talks path/to/talks.json] [--out folder] [--only welcome,intro-vr]
                                                   [--stations path/to/Stations.json | --no-stations] [--lang es]

--lang (or WTA_LANG) reads the lines from the tables build_data.py wrote in that language (DT_Talks, DT_Stations)
in Kokoro's voices for it (Spanish: ef_dora, em_alex), into out/voice/<lang>/; the clip names stay the same.

The voice is Kokoro-82M (Apache 2.0) through kokoro-onnx; the model files are looked for in KOKORO_DIR, else
/home/claude/tts. Lines that already have a WAV with the same words are skipped (a .txt beside each WAV keeps them).
Then copy the folder's WAVs to C:/dev/wta_tools/voiceover on the Unreal machine and run wta_voice.build.run().
"""
import argparse
import json
import os
import sys
import time
import wave

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
DEFAULT_TALKS = os.path.join(ROOT, 'unreal', 'Pipeline', 'content', 'talks.json')
DEFAULT_OUT = os.path.join(ROOT, 'unreal', 'Pipeline', 'out', 'voice')
DEFAULT_STATIONS = os.path.join(ROOT, 'unreal', 'WalkTheArchive', 'Data', 'Stations.json')
NARRATOR = 'af_heart'          # the campus's reading voice (the exhibit cards and the station overviews use it)
DEFAULT_TALK_TABLE = os.path.join(ROOT, 'unreal', 'WalkTheArchive', 'Data', 'Talks.json')

# A language's voices: Kokoro's Spanish set stands in for the English ones by gender; the words come from the
# tables build_data.py wrote in that language (WTA_LANG), so the clips keep their names and the engine finds them.
LANG_VOICES = {'es': {'female': 'ef_dora', 'male': 'em_alex', 'narrator': 'ef_dora', 'kokoro': 'es'}}


def voice_for(voice, lang):
    if lang == 'en' or lang not in LANG_VOICES:
        return voice
    female = voice[1:2] == 'f'
    return LANG_VOICES[lang]['female' if female else 'male']


def kokoro_lang(voice, lang):
    if lang in LANG_VOICES:
        return LANG_VOICES[lang]['kokoro']
    return 'en-us' if voice[:1] == 'a' else 'en-gb'


def clip_name(kind, ident):
    return 'VO_%s_%s' % (kind, ident.replace('-', '_'))


def lines_for(talks, only, lang='en', table=None):
    """Every talk's lines: the words from talks.json in English, from the built DT_Talks rows (already in the
    pack's language) otherwise; the voice from talks.json, swapped for the language's."""
    rows = {}
    if lang != 'en' and table and os.path.exists(table):
        with open(table, 'r', encoding='utf-8') as fh:
            rows = {r['Name']: r for r in json.load(fh)}
    for talk in talks:
        if only and talk['id'] not in only:
            continue
        voice = voice_for(talk.get('speaker', {}).get('voice', 'af_heart'), lang)
        row = rows.get(talk['id'], {})
        if talk.get('kind') == 'course':
            # a course has no slides: its lead's welcome is the one talk clip, read when the course card opens
            intro = row.get('Intro') or talk.get('intro')
            if intro:
                yield clip_name('talk', '%s-01' % talk['id']), intro, voice
        for i, slide in enumerate(talk.get('slides', [])):
            say = (row.get('Slides') or [{}] * (i + 1))[i].get('Say') if row else None
            yield clip_name('talk', '%s-%02d' % (talk['id'], i + 1)), say or slide['say'], voice
        quiz = talk.get('quiz') or {}
        for i, q in enumerate(quiz.get('questions', [])):
            question = (row.get('Quiz') or [{}] * (i + 1))[i].get('Question') if row else None
            yield clip_name('quiz', '%s-%02d' % (talk['id'], i + 1)), question or q['q'], voice


def station_lines(path, only, lang='en'):
    """Every station's steps, read by the narrator: VO_station_<id>_<nn> (the table is in the pack's language)."""
    if not path or not os.path.exists(path):
        return
    narrator = LANG_VOICES[lang]['narrator'] if lang in LANG_VOICES else NARRATOR
    with open(path, 'r', encoding='utf-8') as fh:
        rows = json.load(fh)
    for row in rows:
        if only and row['Name'] not in only:
            continue
        for i, text in enumerate(row.get('StepTexts') or []):
            yield clip_name('station', '%s-%02d' % (row['Name'], i + 1)), text, narrator


def main():
    ap = argparse.ArgumentParser()
    pack = os.environ.get('WTA_CLIENT')
    pack_talks = os.path.join(pack, 'talks.json') if pack else ''
    ap.add_argument('--talks', default=os.environ.get('WTA_TALKS') or (pack_talks if pack_talks and os.path.exists(pack_talks) else DEFAULT_TALKS))
    ap.add_argument('--out', default=DEFAULT_OUT)
    ap.add_argument('--only', default='')
    ap.add_argument('--stations', default=DEFAULT_STATIONS)
    ap.add_argument('--no-stations', action='store_true')
    ap.add_argument('--lang', default=os.environ.get('WTA_LANG') or 'en', help='the pack\'s language (es): its voices, its words from the built tables; clips go to out/voice/<lang>')
    ap.add_argument('--talk-table', default=DEFAULT_TALK_TABLE, help='the built DT_Talks rows (the words in the pack\'s language)')
    args = ap.parse_args()
    lang = args.lang.strip().lower()
    if lang != 'en':
        assert lang in LANG_VOICES, 'no voices for %s (LANG_VOICES has %s)' % (lang, ', '.join(LANG_VOICES))
        if args.out == DEFAULT_OUT:
            args.out = os.path.join(DEFAULT_OUT, lang)
    only = {s.strip() for s in args.only.split(',') if s.strip()}
    with open(args.talks, 'r', encoding='utf-8') as fh:
        talks = json.load(fh)['talks']
    os.makedirs(args.out, exist_ok=True)
    todo = []
    lines = list(lines_for(talks, only, lang, args.talk_table)) + ([] if args.no_stations else list(station_lines(args.stations, only, lang)))
    for name, text, voice in lines:
        txt = os.path.join(args.out, name + '.txt')
        wav = os.path.join(args.out, name + '.wav')
        if os.path.exists(wav) and os.path.exists(txt) and open(txt, encoding='utf-8').read() == voice + '|' + text:
            continue
        todo.append((name, text, voice))
    print('clips to read:', len(todo), flush=True)
    if not todo:
        return 0
    import numpy as np
    from kokoro_onnx import Kokoro
    model_dir = os.environ.get('KOKORO_DIR', '/home/claude/tts')
    k = Kokoro(os.path.join(model_dir, 'kokoro-v1.0.onnx'), os.path.join(model_dir, 'voices-v1.0.bin'))
    total, t0 = 0.0, time.time()
    for n, (name, text, voice) in enumerate(todo):
        samples, rate = k.create(text, voice=voice, speed=1.0, lang=kokoro_lang(voice, lang))
        # a short breath of silence either side, so lines never start or stop clipped
        pad = np.zeros(int(rate * 0.12), dtype=samples.dtype)
        samples = np.concatenate([pad, samples, pad])
        pcm = (np.clip(samples, -1, 1) * 32767).astype('<i2')
        with wave.open(os.path.join(args.out, name + '.wav'), 'wb') as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
            w.writeframes(pcm.tobytes())
        with open(os.path.join(args.out, name + '.txt'), 'w', encoding='utf-8') as fh:
            fh.write(voice + '|' + text)
        total += len(samples) / rate
        print('  %d/%d %s %.1fs' % (n + 1, len(todo), name, len(samples) / rate), flush=True)
    print('done: %d clips, %.1f s of speech in %.0f s' % (len(todo), total, time.time() - t0), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
