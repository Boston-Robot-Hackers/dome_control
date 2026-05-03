# ALSA Mixer Controls

These controls appear to be low-level codec routing, gain, and timing controls
for the ReSpeaker/Seeed audio HAT. The names are mostly signal-path labels:
`Left`/`Right` are stereo channels, `DAC` is playback output, `PGA` is input
gain, `HP` is headphone output, `HPCOM` is headphone common/return output, and
`Line`/`Mic` are input pins.

For loud or distorted Piper speech, start with playback-path controls involving
`DAC`, `HP`, `Line Mixer`, `HPCOM`, or output volume. Avoid increasing `PGA`,
`AGC Target level`, or mic boost controls unless tuning microphone input.

## Jargon

| Term | Meaning |
| --- | --- |
| `ALSA` | Advanced Linux Sound Architecture, the Linux audio driver and mixer system used by `aplay`, `arecord`, `amixer`, and `alsamixer`. |
| `Codec` | The audio chip that converts digital audio to analog output and analog microphone input back to digital samples. |
| `Card` | An ALSA sound device, such as the ReSpeaker HAT. Card numbers appear in `/proc/asound/cards`. |
| `Control` | One adjustable mixer setting exposed by the audio driver. It may be a volume, switch, selector, or timing parameter. |
| `Mixer` | A circuit or software control that combines one or more signal sources into one output path. For example, a headphone mixer can combine DAC playback and input monitoring. |
| `Mux` | Multiplexer. A selector that chooses one source from several possible sources. It is a routing switch, not a volume control. |
| `Bypass` | A route that skips part of the normal signal chain. In these controls it usually sends an input path directly to an output for monitoring. |
| `DAC` | Digital-to-Analog Converter. This is the playback path that turns digital audio, such as Piper speech, into an analog speaker/headphone signal. |
| `ADC` | Analog-to-Digital Converter. This is the capture path that turns microphone audio into digital samples. Not shown in every control name here, but related to capture. |
| `PGA` | Programmable Gain Amplifier. A gain stage for analog inputs, usually microphones or line inputs. Raising it makes captured input louder and can cause clipping. |
| `AGC` | Automatic Gain Control. Automatically adjusts input gain to aim for a target level. Useful for microphones, but high targets can make recordings pump or clip. |
| `Attack time` | How quickly AGC turns gain down after the signal gets too loud. Short attack reacts faster to peaks. |
| `Decay time` | How slowly AGC restores gain after the signal becomes quieter. Long decay changes gain more gradually. |
| `Target level` | The loudness AGC tries to maintain. Higher target means louder capture and more clipping risk. |
| `HP` | Headphone output path. On small audio HATs this may also feed an amplified speaker path depending on board wiring. |
| `HPCOM` | Headphone common output. A codec output/return path used by some headphone or pseudo-differential output configurations. |
| `Line` | Line-level analog input or output. It is usually lower-power than a speaker output and intended for audio signals between devices. |
| `Line1L` / `Line1R` | Left/right pins for the Line1 analog input path. |
| `Mic2L` / `Mic2R` | Left/right pins for a second microphone input path. |
| `DACL1` / `DACR1` | Left/right DAC playback channels feeding a mixer. `L` means left, `R` means right. |
| `PGAL` / `PGAR` | Left/right PGA input channels feeding a mixer. `L` means left, `R` means right. |
| `Capture` | Recording/input side of the audio path, used by microphones and STT. |
| `Playback` | Output side of the audio path, used by Piper speech, WAV playback, speakers, and headphones. |
| `Ramp-up` | A gradual output power increase used to avoid pops/clicks when enabling the audio driver. |

## Output and Playback Routing

| Control | Brief meaning |
| --- | --- |
| `HPCOM PGA Bypass` | Routes the PGA/input path directly to the headphone common output, bypassing normal DAC playback. Usually leave off unless monitoring input. |
| `Left DAC Mux` | Selects which digital audio source feeds the left DAC/playback channel. |
| `Right DAC Mux` | Selects which digital audio source feeds the right DAC/playback channel. |
| `Left HP Mixer DACL1` | Sends left DAC playback into the left headphone mixer. Important for normal left speaker/headphone output. |
| `Left HP Mixer DACR1` | Sends right DAC playback into the left headphone mixer, effectively cross-feeding right playback to left output. |
| `Right HP Mixer DACL1` | Sends left DAC playback into the right headphone mixer, effectively cross-feeding left playback to right output. |
| `Right HP Mixer DACR1` | Sends right DAC playback into the right headphone mixer. Important for normal right speaker/headphone output. |
| `Left HP Mixer PGAL Bypass` | Sends left PGA/input directly into the left headphone mixer. Usually input monitoring, not TTS playback. |
| `Left HP Mixer PGAR Bypass` | Sends right PGA/input directly into the left headphone mixer. Usually input monitoring, not TTS playback. |
| `Right HP Mixer PGAL Bypass` | Sends left PGA/input directly into the right headphone mixer. Usually input monitoring, not TTS playback. |
| `Right HP Mixer PGAR Bypass` | Sends right PGA/input directly into the right headphone mixer. Usually input monitoring, not TTS playback. |
| `Left HPCOM Mixer DACL1` | Sends left DAC playback into the left headphone-common mixer. Can affect output level/routing. |
| `Left HPCOM Mixer DACR1` | Sends right DAC playback into the left headphone-common mixer. Cross-feed path. |
| `Right HPCOM Mixer DACL1` | Sends left DAC playback into the right headphone-common mixer. Cross-feed path. |
| `Right HPCOM Mixer DACR1` | Sends right DAC playback into the right headphone-common mixer. Can affect output level/routing. |
| `Left HPCOM Mixer PGAL Bypass` | Sends left PGA/input directly into left headphone-common output. Usually input monitoring. |
| `Left HPCOM Mixer PGAR Bypass` | Sends right PGA/input directly into left headphone-common output. Usually input monitoring. |
| `Right HPCOM Mixer PGAL Bypass` | Sends left PGA/input directly into right headphone-common output. Usually input monitoring. |
| `Right HPCOM Mixer PGAR Bypass` | Sends right PGA/input directly into right headphone-common output. Usually input monitoring. |
| `Left HPCOM Mux` | Selects what drives the left headphone-common output path. |
| `Right HPCOM Mux` | Selects what drives the right headphone-common output path. |
| `Left Line Mixer DACL1` | Sends left DAC playback into the left line-output mixer. Can affect speaker/line output. |
| `Left Line Mixer DACR1` | Sends right DAC playback into the left line-output mixer. Cross-feed path. |
| `Right Line Mixer DACL1` | Sends left DAC playback into the right line-output mixer. Cross-feed path. |
| `Right Line Mixer DACR1` | Sends right DAC playback into the right line-output mixer. Can affect speaker/line output. |
| `Left Line Mixer PGAL Bypass` | Sends left PGA/input directly to left line output. Usually input monitoring. |
| `Left Line Mixer PGAR Bypass` | Sends right PGA/input directly to left line output. Usually input monitoring. |
| `Right Line Mixer PGAL Bypass` | Sends left PGA/input directly to right line output. Usually input monitoring. |
| `Right Line Mixer PGAR Bypass` | Sends right PGA/input directly to right line output. Usually input monitoring. |

## Input and Microphone Routing

| Control | Brief meaning |
| --- | --- |
| `PGA` | Programmable Gain Amplifier for analog input capture. Higher values make microphone/input louder and can cause clipping. |
| `Left Line1L Mux` | Selects how the left Line1L input pin is routed into the codec input path. |
| `Left Line1R Mux` | Selects how the left Line1R input pin is routed into the codec input path. |
| `Right Line1L Mux` | Selects how the right Line1L input pin is routed into the codec input path. |
| `Right Line1R Mux` | Selects how the right Line1R input pin is routed into the codec input path. |
| `Left PGA Mixer Line1L` | Routes Line1L into the left PGA/input mixer. Affects capture/input monitoring. |
| `Left PGA Mixer Line1R` | Routes Line1R into the left PGA/input mixer. Affects capture/input monitoring. |
| `Right PGA Mixer Line1L` | Routes Line1L into the right PGA/input mixer. Affects capture/input monitoring. |
| `Right PGA Mixer Line1R` | Routes Line1R into the right PGA/input mixer. Affects capture/input monitoring. |
| `Left PGA Mixer Mic2L` | Routes Mic2L into the left PGA/input mixer. Likely relevant to microphone capture. |
| `Left PGA Mixer Mic2R` | Routes Mic2R into the left PGA/input mixer. Likely relevant to microphone capture. |
| `Right PGA Mixer Mic2L` | Routes Mic2L into the right PGA/input mixer. Likely relevant to microphone capture. |
| `Right PGA Mixer Mic2R` | Routes Mic2R into the right PGA/input mixer. Likely relevant to microphone capture. |

## Automatic Gain Control

| Control | Brief meaning |
| --- | --- |
| `Left AGC Attack time` | How quickly left-channel AGC reduces gain when input is too loud. Shorter attack clamps peaks faster. |
| `Right AGC Attack time` | How quickly right-channel AGC reduces gain when input is too loud. Shorter attack clamps peaks faster. |
| `Left AGC Decay time` | How slowly left-channel AGC restores gain after the signal gets quieter. |
| `Right AGC Decay time` | How slowly right-channel AGC restores gain after the signal gets quieter. |
| `Left AGC Target level` | Desired left-channel input level for AGC. Higher target means louder captured audio and more clipping risk. |
| `Right AGC Target level` | Desired right-channel input level for AGC. Higher target means louder captured audio and more clipping risk. |

## Output Timing

| Control | Brief meaning |
| --- | --- |
| `Output Driver Power-On time` | Delay used while powering up the output driver, mainly to reduce pops/clicks. Not a volume control. |
| `Output Driver Ramp-up step` | Step size/speed for ramping output up during power-on, mainly pop/click control. Not a volume control. |
