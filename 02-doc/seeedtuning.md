# ReSpeaker 2-Mics Pi HAT V2.0 tuning notes

Context: Raspberry Pi using Seeed Studio **ReSpeaker 2-Mics Pi HAT V2.0 for Raspberry Pi**. Board described as: **TLV320AIC3104 audio codec**, **2 analog microphones**, **3 APA102 RGB LEDs**, **3.5 mm audio jack**, **user button**, and associated NLU software algorithms such as **VAD**, **DOA**, and **KWS**. The practical goal was to reduce noise/hum and obtain usable voice WAV recordings via CLI while using the board's audio output to a directly connected passive/unpowered speaker, not the Raspberry Pi headphone jack.

All generated `.wav` files should go in `~/tmp`.

```bash
mkdir -p ~/tmp
```

## Key hardware/driver discovery

The board in use is **not the older WM8960-based ReSpeaker control model**. The kernel reports the capture device as:

```text
card 0: seeed2micvoicec [seeed2micvoicec], device 0: 1f000a4000.i2s-tlv320aic3x-hifi tlv320aic3x-hifi-0
```

This means the relevant codec driver is the **TLV320AIC3x/TLV320AIC3104 path**, even though the ALSA simple mixer controls expose names such as `PGA`, `Left PGA Mixer Mic2L`, `Right PGA Mixer Mic2R`, `ADC HPF Cut-off`, `AGC`, `HP`, `HP DAC`, etc.

Important lesson: earlier WM8960 assumptions were misleading. The board's mixer control names overlap conceptually with WM8960-style controls, but the codec/driver in this setup is reported as `tlv320aic3x-hifi`.

## Device/card assumptions

In this experiment the ReSpeaker card was card `0`.

Use:

```bash
arecord -l
aplay -l
amixer -c 0 scontrols
amixer -c 0 scontents
```

The card supported **stereo capture**. Direct mono capture failed:

```bash
arecord -D hw:0,0 -f S16_LE -r 16000 -c 1 -d 5 test.wav
```

Error:

```text
arecord: set_params:1377: Channels count non available
```

Therefore capture must be done as stereo (`-c 2`) and then downmixed or channel-selected in software.

Similarly, direct mono playback to `hw:0,0` failed:

```bash
aplay -D hw:0,0 mono.wav
```

Error:

```text
aplay: set_params:1377: Channels count non available
```

Use `plughw:0,0` for playback so ALSA can adapt channel count/rate:

```bash
aplay -D plughw:0,0 ~/tmp/clean.wav
```

## Meaning of `-` in pipelines

In commands like:

```bash
arecord ... - | sox -t wav - -t wav -c 1 - ... | aplay ...
```

`-` means stdin/stdout:

- final `-` in `arecord` means write WAV stream to stdout instead of a file;
- first `-` in `sox -t wav -` means read WAV stream from stdin;
- output `-` in `sox ... -t wav ... -` means write processed WAV stream to stdout;
- `aplay` then reads the WAV stream from stdin.

When SoX outputs to stdout, the output type must be explicit. This failed:

```bash
sox -t wav - -c 1 - highpass 120
```

with:

```text
sox FAIL formats: can't determine type of `-'
```

Correct form:

```bash
sox -t wav - -t wav -c 1 - highpass 120
```

## Controls discovered

Relevant controls from `amixer -c 0 scontrols` / `scontents` included:

```text
PGA
ADC HPF Cut-off
AGC
Left AGC Attack time
Left AGC Decay time
Left AGC Target level
Right AGC Attack time
Right AGC Decay time
Right AGC Target level
Left PGA Mixer Mic2L
Left PGA Mixer Mic2R
Right PGA Mixer Mic2L
Right PGA Mixer Mic2R
Left Line1L Mux
Right Line1R Mux
PCM
HP
HP DAC
Line DAC
```

Relevant observed `ADC HPF Cut-off` enum items:

```text
Disabled
0.0045xFs
0.0125xFs
0.025xFs
```

Relevant observed `PGA` state at one point:

```text
Simple mixer control 'PGA',0
  Capabilities: cvolume cswitch
  Capture channels: Front Left - Front Right
  Limits: Capture 0 - 119
  Front Left: Capture 48 [40%] [24.00dB] [on]
  Front Right: Capture 48 [40%] [24.00dB] [on]
```

## What worked

### 1. Use stereo capture only

Working raw capture/playback:

```bash
arecord -D hw:0,0 -f S16_LE -r 16000 -c 2 -d 5 ~/tmp/raw.wav && \
  aplay -D plughw:0,0 ~/tmp/raw.wav
```

At first, this produced hum/no voice or silence depending on mixer state. After tuning, voice became audible.

### 2. Use the ALSA meter to diagnose capture before relying on files

Most useful diagnostic command:

```bash
arecord -D hw:0,0 -vv -f S16_LE -r 16000 -c 2 -d 5 /dev/null
```

Interpretation learned:

- flat/no movement: capture path dead or no signal;
- moving very little: mic path alive but gain too low;
- pinned/maxed: ADC/input path saturating or gain too high;
- one meter is normal in this ALSA view even with stereo capture; it may be a combined/simple meter.

In the working path, the meter moved and stayed below max after raising `PGA` to about `50%`.

### 3. Input gain: `PGA`

The main input gain knob is `PGA`.

Useful commands:

```bash
amixer -c 0 sset 'PGA' 50%
```

`50%` made the meter move and stay below max. `40%` was too quiet in one test. `60%`/`65%` were used for proving signal existed and increasing raw voice audibility, but higher analog gain also increases hum/noise. `70%` was suggested only as a temporary diagnostic, not a final setting.

Observed practical baseline:

```bash
amixer -c 0 sset 'PGA' 50%
```

or, if too quiet but not pinned:

```bash
amixer -c 0 sset 'PGA' 55%
amixer -c 0 sset 'PGA' 65%
```

Final tuning tradeoff: use the lowest `PGA` that gives clearly visible meter motion and audible voice without pinning. Then do digital filtering/gain in SoX.

### 4. Mic routing

Initial mixer state had:

```text
Left PGA Mixer Mic2L: on
Left PGA Mixer Mic2R: off
Right PGA Mixer Mic2L: off
Right PGA Mixer Mic2R: on
```

That is the natural left-mic-to-left-channel/right-mic-to-right-channel routing.

For testing, all mic routes were enabled:

```bash
amixer -c 0 sset 'Left PGA Mixer Mic2L' on
amixer -c 0 sset 'Left PGA Mixer Mic2R' on
amixer -c 0 sset 'Right PGA Mixer Mic2L' on
amixer -c 0 sset 'Right PGA Mixer Mic2R' on
```

This confirmed routing and signal path. Later, using both channels mixed to mono was preferred for general use because the user position changes and one mic can sound better only because of seating/geometry.

### 5. Differential input mode improved clarity

The controls existed:

```text
Left Line1L Mux
Right Line1R Mux
```

They were initially observed as `single-ended`. Switching to differential mode improved voice clarity:

```bash
amixer -c 0 sset 'Left Line1L Mux' differential
amixer -c 0 sset 'Right Line1R Mux' differential
```

Result: voice sounded clearer; hum remained but was acceptable/reduced somewhat.

This was a major useful setting.

### 6. Hardware high-pass filter helped slightly

Hardware high-pass filter setting:

```bash
amixer -c 0 sset 'ADC HPF Cut-off' '0.025xFs'
```

Result: hum was maybe reduced a little; voice remained OK.

Earlier setting `on` was not as precise because this control is enum-based. Use the enum item explicitly.

### 7. Speaker/output gain path

The speaker was connected directly to the ReSpeaker board output, not the Pi headphone jack. Playback of `/usr/share/sounds/alsa/Front_Center.wav` using `plughw:0,0` worked, proving output path was functional:

```bash
aplay -D plughw:0,0 /usr/share/sounds/alsa/Front_Center.wav
```

However, raw playback was initially too soft until output levels were restored/increased.

Useful output-volume commands:

```bash
amixer -c 0 sset 'HP DAC' 118
amixer -c 0 sset 'HP' 9
amixer -c 0 sset 'PCM' 127
amixer -c 0 sset 'Line DAC' 118
```

Result: playback got louder again. Not extremely loud, but acceptable. Hum also became clearly audible because output gain increased.

### 8. SoX cleanup pipeline

The best simple software cleanup pipeline used both mics mixed to mono, high-pass, low-pass, and normalization/headroom.

General-purpose working command:

```bash
arecord -D hw:0,0 -f S16_LE -r 16000 -c 2 -d 5 ~/tmp/raw.wav && \
  sox ~/tmp/raw.wav ~/tmp/clean.wav remix -m 1,2 highpass 120 lowpass 4000 gain -n -3 && \
  aplay -D plughw:0,0 ~/tmp/clean.wav
```

This sounded better than raw. It uses both mics:

```text
remix -m 1,2
```

Left-only version:

```bash
sox ~/tmp/raw.wav ~/tmp/clean-left.wav remix 1 highpass 120 lowpass 4000 gain -n -3
```

Right-only version:

```bash
sox ~/tmp/raw.wav ~/tmp/clean-right.wav remix 2 highpass 120 lowpass 4000 gain -n -3
```

The left mic sounded slightly better in the user's seating position, but that was likely positional. Final preference: use both mics mixed to mono for stability.

A stronger final refinement to reduce low-frequency hum and tighten speech band:

```bash
arecord -D hw:0,0 -f S16_LE -r 16000 -c 2 -d 5 ~/tmp/raw.wav && \
  sox ~/tmp/raw.wav ~/tmp/clean.wav remix -m 1,2 highpass 200 lowpass 3500 gain -n -3 && \
  aplay -D plughw:0,0 ~/tmp/clean.wav
```

This reduces hum more aggressively but can make voice thinner. It should be A/B tested against the `highpass 120 lowpass 4000` version.

### 9. `gain -n` normalization and clipping warning

Using SoX normalization:

```bash
gain -n
```

once produced:

```text
sox WARN dither: dither clipped 1 samples; decrease volume?
```

This warning is minor if only a few samples clip. To avoid clipping, use headroom:

```bash
gain -n -3
```

This became part of the working pipeline.

## What did not work / false starts

### 1. Mono capture directly from `arecord`

Failed:

```bash
arecord -D hw:0,0 -f S16_LE -r 16000 -c 1 -d 5 ~/tmp/test.wav
```

Error:

```text
Channels count non available
```

Conclusion: use stereo hardware capture and downmix with SoX.

### 2. Mono playback directly to `hw:0,0`

Failed:

```bash
aplay -D hw:0,0 ~/tmp/mono.wav
```

Error:

```text
Channels count non available
```

Conclusion: use `plughw:0,0` for playback or convert to stereo first.

### 3. Incorrect SoX stdout syntax

Failed:

```bash
arecord -D hw:0,0 -f S16_LE -r 16000 -c 2 -d 4 - | \
  sox -t wav - -c 1 - highpass 120 | \
  aplay -D plughw:0,0
```

Error:

```text
sox FAIL formats: can't determine type of `-'
aplay: read_header:2931: read error
```

Fixed by specifying output type:

```bash
sox -t wav - -t wav -c 1 - highpass 120
```

### 4. AGC target setting failed via `amixer sset`

Turning AGC on worked:

```bash
amixer -c 0 sset 'AGC' on
```

But attempts to set AGC target by value failed because `amixer` parsed negative dB values as options:

```bash
amixer -c 0 sset 'Left AGC Target level' '-10dB'
amixer -c 0 sset 'Right AGC Target level' '-10dB'
```

Errors:

```text
amixer: invalid option -- '1'
amixer: invalid option -- '0'
amixer: invalid option -- 'B'
```

Unquoted also failed:

```bash
amixer -c 0 sset 'Left AGC Target level' -10dB
```

Trying an integer index also failed:

```bash
amixer -c 0 sset 'Left AGC Target level' 2
```

Error:

```text
amixer: Invalid command!
```

Conclusion: do not rely on AGC in this CLI path. It may boost noise/pump anyway. Recommended final setting:

```bash
amixer -c 0 sset 'AGC' off
```

### 5. Early WM8960-oriented advice was wrong for this hardware

Commands and mental model assuming WM8960 were not reliable because `arecord -l` revealed `tlv320aic3x-hifi`.

Examples of early assumptions to avoid:

- treating the board as WM8960-based;
- expecting friendly `Capture`, `Mic Boost`, `ADC` controls;
- assuming mono capture support;
- assuming the ReSpeaker V2.0 behaves like older ReSpeaker 2-mic boards or docs.

### 6. Listening position/distance matters a lot

At about 2 m, the board produced hum/noise with weak or absent voice in raw recordings. At 10–20 cm, voice became audible and tunable.

Conclusion: this board can support voice-recognition pipelines, VAD/KWS/DOA experiments, etc., but raw WAV quality at far-field distance is poor without DSP. The board's NLU-related labels (VAD, DOA, KWS) imply software processing, not clean raw far-field audio.

## Current recommended baseline state

Apply this after reboot or if state is lost:

```bash
mkdir -p ~/tmp

# Input/capture gain: start here, adjust 50-65% by meter and clipping.
amixer -c 0 sset 'PGA' 50%

# Mic routing: both mics available to both channels for robust testing/general mono mix.
amixer -c 0 sset 'Left PGA Mixer Mic2L' on
amixer -c 0 sset 'Left PGA Mixer Mic2R' on
amixer -c 0 sset 'Right PGA Mixer Mic2L' on
amixer -c 0 sset 'Right PGA Mixer Mic2R' on

# Differential input mode: improved clarity.
amixer -c 0 sset 'Left Line1L Mux' differential
amixer -c 0 sset 'Right Line1R Mux' differential

# Hardware high-pass filter.
amixer -c 0 sset 'ADC HPF Cut-off' '0.025xFs'

# AGC off: avoids pumping/noise boosting; target setting was problematic via sset.
amixer -c 0 sset 'AGC' off

# Output path/volume for board output.
amixer -c 0 sset 'HP DAC' 118
amixer -c 0 sset 'HP' 9
amixer -c 0 sset 'PCM' 127
amixer -c 0 sset 'Line DAC' 118
```

Then verify meter:

```bash
arecord -D hw:0,0 -vv -f S16_LE -r 16000 -c 2 -d 5 /dev/null
```

Target meter behavior:

- moves with speech/taps;
- not flat;
- not pinned;
- stays below max at normal speech distance.

If meter barely moves, raise `PGA`:

```bash
amixer -c 0 sset 'PGA' 55%
amixer -c 0 sset 'PGA' 65%
```

If meter pins/clips or hum dominates, lower `PGA`:

```bash
amixer -c 0 sset 'PGA' 45%
amixer -c 0 sset 'PGA' 40%
```

## Current recommended record/listen commands

### Raw record/listen

```bash
arecord -D hw:0,0 -f S16_LE -r 16000 -c 2 -d 5 ~/tmp/raw.wav && \
  aplay -D plughw:0,0 ~/tmp/raw.wav
```

### Cleaned, balanced speech version

```bash
arecord -D hw:0,0 -f S16_LE -r 16000 -c 2 -d 5 ~/tmp/raw.wav && \
  sox ~/tmp/raw.wav ~/tmp/clean.wav remix -m 1,2 highpass 120 lowpass 4000 gain -n -3 && \
  aplay -D plughw:0,0 ~/tmp/clean.wav
```

### More aggressive hum reduction

```bash
arecord -D hw:0,0 -f S16_LE -r 16000 -c 2 -d 5 ~/tmp/raw.wav && \
  sox ~/tmp/raw.wav ~/tmp/clean.wav remix -m 1,2 highpass 200 lowpass 3500 gain -n -3 && \
  aplay -D plughw:0,0 ~/tmp/clean.wav
```

### Compare left/right mics from same raw recording

```bash
arecord -D hw:0,0 -f S16_LE -r 16000 -c 2 -d 5 ~/tmp/raw.wav

sox ~/tmp/raw.wav ~/tmp/clean-left.wav remix 1 highpass 120 lowpass 4000 gain -n -3
sox ~/tmp/raw.wav ~/tmp/clean-right.wav remix 2 highpass 120 lowpass 4000 gain -n -3

aplay -D plughw:0,0 ~/tmp/clean-left.wav
aplay -D plughw:0,0 ~/tmp/clean-right.wav
```

### Pipeline version without intermediate file

Working syntax:

```bash
arecord -D hw:0,0 -f S16_LE -r 16000 -c 2 -d 5 - | \
  sox -t wav - -t wav -c 1 - remix -m 1,2 highpass 120 lowpass 4000 gain -n -3 | \
  aplay -D plughw:0,0
```

But file-based commands are easier to debug and were preferred once `~/tmp` was chosen.

## Practical interpretation of results

Observed behavior and likely cause:

- `arecord -vv` flat: capture path/state wrong or no signal.
- `arecord -vv` moving very little: gain too low, mic path alive.
- `arecord -vv` pinned: gain/input mode too hot; reduce `PGA`, check differential mode.
- raw file contains hum but little/no voice: input gain/distance/SNR issue.
- raw file silent on Mac too: capture was not recording voice; not merely playback issue.
- `Front_Center.wav` plays but recorded files are quiet: playback works; capture/input or gain issue.
- speaker output soft: increase `HP DAC`, `HP`, `PCM`, `Line DAC` as above.
- hum acceptable after output increase: continue with SoX filtering; do not over-chase via analog gain.

## Board-level conclusion

The ReSpeaker 2-Mics Pi HAT V2.0 with TLV320AIC3104 and two analog microphones is best understood as a voice-input development board intended for software pipelines such as VAD, DOA, and KWS. It is not a clean, far-field, raw WAV recording device by default.

The two microphones are useful for software processing and positional robustness, but raw stereo should generally be downmixed or channel-selected. In this experiment, using both mics via `remix -m 1,2` was preferred for general use. Single-mic selection can sound better depending on user position.

For raw capture, distance matters strongly. Testing and tuning should be done at 10-30 cm first. At around 2 m, voice SNR is poor and hum/ambient noise dominate unless additional DSP is used.

The best achieved approach was:

1. stereo capture at 16 kHz, 16-bit;
2. differential input mode;
3. `PGA` around 50-65%, tuned by meter;
4. hardware ADC HPF set to `0.025xFs`;
5. AGC off;
6. both mics mixed to mono;
7. SoX highpass/lowpass and normalization with headroom;
8. playback through `plughw:0,0` with board output gain restored.

Next likely improvement beyond this experiment would be real noise suppression such as RNNoise or WebRTC noise suppression, rather than additional ALSA mixer tweaking.
