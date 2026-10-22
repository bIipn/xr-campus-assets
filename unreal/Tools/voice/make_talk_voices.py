"""Reads every talk and class aloud: one WAV per slide line in the speaker's own voice, named the way the engine
finds them (VO_talk_<talk>_<nn>.wav, the id's hyphens as underscores), plus each class's quiz questions
(VO_quiz_<talk>_<nn>.wav) so a visitor can listen instead of read.

    python3 unreal/Tools/voice/make_talk_voices.py [--talks path/to/talks.json] [--out folder] [--only welcome,intro-vr]

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


def clip_name(kind, ident):
    return 'VO_%s_%s' % (kind, ident.replace('-', '_'))


def lines_for(talks, only):
    for talk in talks:
        if only and talk['id'] not in only:
            continue
        voice = talk.get('speaker', {}).get('voice', 'af_heart')
        for i, slide in enumerate(talk.get('slides', [])):
            yield clip_name('talk', '%s-%02d' % (talk['id'], i + 1)), slide['say'], voice
        quiz = talk.get('quiz') or {}
        for i, q in enumerate(quiz.get('questions', [])):
            yield clip_name('quiz', '%s-%02d' % (talk['id'], i + 1)), q['q'], voice


def main():
    ap = argparse.ArgumentParser()
    pack = os.environ.get('WTA_CLIENT')
    pack_talks = os.path.join(pack, 'talks.json') if pack else ''
    ap.add_argument('--talks', default=os.environ.get('WTA_TALKS') or (pack_talks if pack_talks and os.path.exists(pack_talks) else DEFAULT_TALKS))
    ap.add_argument('--out', default=DEFAULT_OUT)
    ap.add_argument('--only', default='')
    args = ap.parse_args()
    only = {s.strip() for s in args.only.split(',') if s.strip()}
    with open(args.talks, 'r', encoding='utf-8') as fh:
        talks = json.load(fh)['talks']
    os.makedirs(args.out, exist_ok=True)
    todo = []
    for name, text, voice in lines_for(talks, only):
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
        samples, rate = k.create(text, voice=voice, speed=1.0, lang='en-us' if voice[:1] == 'a' else 'en-gb')
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
