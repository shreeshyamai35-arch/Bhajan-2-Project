---
name: bhajan-production
description: "End-to-end workflow to turn a singer's raw recorded vocal into a professional devotional bhajan using AI (vocal-to-accompaniment via Suno), with Hindi/Braj pronunciation control, devotional arrangement, and streaming-ready mastering. Use when producing Shyam/Krishna/devotional bhajans from a recorded vocal."
tags: [bhajan, devotional, suno, vocal-to-accompaniment, SAG, mastering, hindi, music-production]
platforms: [linux, macos, windows]
triggers:
  - make a bhajan
  - bhajan production
  - devotional song from vocal
  - turn my vocal into a song
  - Suno bhajan prompt
  - master a bhajan
  - Shyam bhajan
---

# Bhajan Production (Vocal-First / SAG Workflow)

Everything here is a GUIDELINE. The final judge is the ear of the producer.
NO COMPROMISE on final production quality — if AI output fails the quality
gate, regenerate or fix manually. Do not ship "good enough."

CORE PRINCIPLE:
The singer's real voice and emotion are the product. We do NOT clone or
replace the voice. We record the real vocal and let AI build the music
around it (Singing Accompaniment Generation, "SAG").

---

## 0. The Golden Path (at a glance)

```
1. Lyrics ready  ->  2. Prep (meter + phonetics)
3. Record vocal WITH a click/loop (most important step)
4. Clean the vocal (noise + light tuning)
5. Suno: upload vocal -> "Add Instrumentals" -> devotional style prompt
6. Generate 10-15 versions -> pick best by ear
7. Export stems -> tweak arrangement if needed
8. Mix + master to -14 LUFS -> QC gate -> release
```

The ONLY manual-on-website step is clicking Generate/Download on Suno
(it blocks scripted access). Everything else can be assisted/automated.

---

## 1. Lyrics Prep (before touching a mic)

- **Meter (chhand)**: Mark stressed syllables and line breaks. This decides
  the melody rhythm and how the taal (rhythm cycle) will sit.
- **Section map**: Bhajans usually go:
  `[Aalap/Intro] -> [Sthayi/Mukhda (hook)] -> [Antara (verse)] -> repeat Sthayi`
  This is the devotional equivalent of intro/chorus/verse.
- **Phonetic sheet**: Rewrite tricky devotional words the way they must be
  SUNG, so the AI's pronunciation stays correct (see Section 6).

---

## 2. Choosing the Melody (tune)

The melody is the soul. Two ways, in order of authenticity:

1. **Human-hummed (best)**: Singer hums/sings the tune. This is what we
   record in Step 3. Most authentic for devotional feel.
2. **AI-suggested candidates**: If no tune exists, generate melody ideas on
   Suno from lyrics + style, pick one by ear, then have the singer sing it.

Common devotional taals to specify later: **Keherwa (8 beats)** and
**Dadra (6 beats)** for medium bhajans; slow bhajans/aartis can be free or
Keherwa. Tempo range: roughly 70-110 BPM for classic Shyam bhajans.

---

## 3. Recording the Vocal — THE make-or-break step

The #1 reason AI music does NOT match a vocal is **tempo drift**. If the
singer speeds up/slows down, AI cannot lock a beat. Fix this at the source:

- **Sing to a click or a loop.** Put a metronome OR a simple tabla/dholak
  loop (Keherwa/Dadra) in one earphone and sing on top of it. This keeps
  tempo constant so AI can build music that fits.
- **Know your BPM and key.** Decide the tempo before recording. Note it —
  you will feed it to Suno.
- **Clean signal**: quiet room, pop filter, no fan/AC hum. A phone works,
  but a ~₹1500-3000 USB/condenser mic (e.g. AT2020 class) is much better.
- **Dry vocal only**: no reverb/effects while recording. Effects get baked
  in and ruin AI matching.
- **Multiple takes**: record 2-3 clean takes; keep the one with best emotion
  AND best timing. Emotion matters most in devotional music.

Deliverable of this step: one clean, dry, in-tempo solo vocal (WAV preferred).

---

## 4. Clean the Vocal

- **Noise removal**: Audacity (free) or Adobe Podcast "Enhance" (free) to
  strip background noise/hum.
- **Light pitch correction**: Melodyne — correct only clear off-notes.
  PRESERVE meend/gamak (the slides and ornaments) — do NOT flatten them.
  Aggressive Auto-Tune kills the devotional feel; keep it subtle/natural.
- **Trim silences**, remove clicks/breaths that distract.

Do NOT over-process. The AI music step needs a natural, expressive vocal.

---

## 5. Generate the Music (Suno, vocal-first)

Suno feature: upload your own track, then **Add Instrumentals** builds the
music around it. (Add Instrumentals works on uploaded tracks / generated
instrumentals.)

### 5.1 Style prompt formula (adapt per song)

```
Genre + Mood + Instruments + Tempo/Key + Vocal handling + Dynamics
```

Bhajan example (put in Style field, up to ~1000 chars):
```
Traditional Hindi devotional bhajan, temple/satsang atmosphere, deeply
emotional and serene. Harmonium, tabla, dholak, bansuri (bamboo flute),
tanpura drone, soft strings, subtle manjira (finger cymbals). Keherwa taal,
around 90 BPM, key to match the uploaded vocal. Keep the lead vocal front
and centered, acoustic warm production, gentle build. Chorus/backing
voices only on the sthayi (hook).
```

DESCRIBE THE ARC, not just instruments:
```
Begins with a soft harmonium + tanpura aalap. Tabla and dholak enter gently
on the mukhda. Antara stays intimate. Final sthayi swells with light chorus
and dholak, then settles to a calm harmonium outro.
```

- **NO artist names / trademarks.** Describe the sound, not a person.
- State the **BPM and key** to match your recorded vocal.
- Use **Exclude Styles** for anything unwanted (e.g. "EDM, autotune,
  electric guitar, western drum kit").

### 5.2 Metatags (in the lyrics field, in [brackets])

Devotional-friendly tags:
```
STRUCTURE:  [Aalap] [Intro] [Sthayi] [Mukhda] [Antara] [Instrumental]
            [Interlude] [Outro] [Harmonized Chorus]
VOCAL:      [Soulful] [Devotional] [Emotional] [Breathy] [Legato]
            [Vibrato] [Call and Response] [Choir]
INSTRUMENTS:[Harmonium] [Tabla] [Dholak] [Bansuri Flute] [Tanpura Drone]
DYNAMICS:   [Building Energy] [Gentle swell] [Quiet arrangement]
            [Emotional Climax] [Slow Down]
```
Keep to 5-8 tags per section. Do not contradict ([Quiet] + [Explosive]).

### 5.3 Generate like recording takes

- Generate **10-15 variations** — treat them as studio takes.
- Pick the best by ear (tempo lock, instrument authenticity, emotion).
- Expect ~1 great result per several tries. Regenerate freely.
- If the melody drifts from the vocal, re-check that the vocal was in tempo.

---

## 6. Hindi / Braj / Rajasthani Phonetic Cheat-Sheet

AI singers pronounce, they don't read. Once generated, pronunciation is
baked in — fix it in the text BEFORE generating. Spell words as they SOUND.

Common devotional names/words (respell so the AI sings them right):

| Intended | Write as | Note |
|---|---|---|
| श्याम / Shyam | Shyaam | long "aa" |
| राधे / Radhe | Raa-dhe | soft dh |
| गोविंद / Govind | Go-vind | |
| कृष्ण / Krishna | Krish-na | avoid "Krisnaa" |
| मुरली / Murli | Mur-lee | |
| बाँके बिहारी | Baanke Bihaari | nasal + long aa |
| खाटू श्याम | Khaatoo Shyaam | |
| हरे / Hare | Ha-re | not "hair" |
| मोहन / Mohan | Mo-han | |
| गिरधर | Gir-dhar | |
| जय / Jai | Jai (rhymes "eye") | not "jay" |
| श्री / Shri | Shree | |
| भजन / Bhajan | Bha-jan | |

DELIVERY CONTROL:
- Vowel stretch for held notes: "Shyaa-aa-aam", "Raa-dhe-e"
- Ellipses for pauses: "Jai... Shri... Shyaam"
- ALL CAPS for louder/intense lines
- Test difficult names in a short 30-second clip FIRST.

---

## 7. Arrangement Tweaks (optional, for premium tracks)

- Export **stems** from Suno (individual instrument tracks).
- In a DAW (Reaper ~$60, or free options), rebalance instruments, or
  **replace weak AI instruments with real samples** (real tabla/dholak/
  harmonium loops) for flagship releases where authenticity must be perfect.
- Keep the lead (real) vocal untouched and dominant.

---

## 8. Mix & Master

- **Mix**: balance vocal above music; vocal should sit clearly on top.
  Light reverb suited to a temple/hall feel — not drowning the voice.
- **Master to streaming loudness**: target around **-14 LUFS** (YouTube/
  Spotify friendly). Tools: LANDR (~$4/master), BandLab Mastering (free),
  or iZotope Ozone for manual control.
- Check no clipping; leave true-peak headroom (about -1 dBTP).

---

## 9. Quality Gate (nothing ships until it passes)

VOCAL & MUSIC:
- [ ] Vocal is in tempo with the music (no drift, no floating)
- [ ] Melody follows the singer, AI did not invent a different tune
- [ ] Emotion/bhaav is intact (ornaments preserved, not over-tuned)
- [ ] Instruments sound authentic enough for devotional context

PRONUNCIATION:
- [ ] All deity names pronounced correctly (Shyaam, Raadhe, etc.)
- [ ] No baked-in mispronunciation anywhere

AUDIO:
- [ ] Loudness ~ -14 LUFS, no clipping, clean low end
- [ ] Vocal clearly on top of the mix
- [ ] Intro/outro clean, no abrupt cuts

RELEASE:
- [ ] Correct key/tempo documented for reuse
- [ ] Title, deity, and lyric credit set

If ANY box fails: fix or regenerate. No compromise on final production.

---

## 10. Cost & Reality Notes

- Running cost per song is very low (Suno subscription share + ~$4 master),
  versus 10,000-50,000 for traditional studio production.
- The two hard limits to remember:
  1. **Tempo drift** in recording breaks AI matching — always sing to a
     click/loop.
  2. **Suno generation/download is manual** (blocks scripts) — AI writes
     the prompt and does everything after the stems come back.
- For a flagship/premium bhajan, plan for real-instrument overdubs and a
  manual mix pass. Everyday releases can stay fully AI-assisted.
