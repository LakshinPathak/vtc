# Paper 2 — how BB84 can sit in the night path

This note only adds a key-agreement step to the standalone Paper 2 story. It does not replace the tiny detector, the mix, or the average. Read `PAPER2_STORY.md` first.

BB84 is key agreement on a special link. After it, ordinary AES uses that key. BB84 is not encryption by itself. It is not garlic. It is not federated averaging. It is not the tiny detector.

---

## One night, nine steps

BB84 appears **once**, at **step 5**, on a **named private trunk** between the mix gateway and the collector.

1. Night starts. Each pole trains a little on **its own unique flows**. No BB84.
2. **Inner lock (stays).** The pole locks the **weights** with an ordinary lock that only the **collector** can open. Not flows. Not safety messages. The mix gateway cannot read the numbers.
3. That locked parcel goes toward a mix gateway on a **classical** path: named path, onion without mix, or garlic bundle. This is “who spoke.”
4. The mix gateway holds an **already-mixed** bundle of **still-locked** parcels (or a singleton, if there was no mix). The highway watcher problem is already decided here.
5. **BB84, only here.** Mix gateway and collector run BB84 on that named trunk and mint night key \(K\).
6. **Second lock, trunk only.** Ordinary **AES with \(K\)** wraps the already-mixed blob for this hop. It does not replace step 2. It protects a tapper on the **trunk**, who already knows this link is gateway-to-collector.
7. The collector opens AES-\(K\), then opens each pole lock, then **averages** the brains, or takes a **median** if a pole may be lying. No BB84 inside this step.
8. The collector produces one **global** tiny detector.
9. Morning. Each pole installs that frozen detector and goes back to the **day** path (fast, local, no BB84).

---

## Inner caveats (must stay in the story)

**Pole-level lock stays.** Story step 2 is kept. AES on the trunk is a **second** layer for that hop only. Dropping the inner lock would let the mix gateway see the weights. We do not do that.

**Authenticated classical channel.** BB84 needs the two trunk ends to authenticate their classical talk (basis comparison and error check). We assume a **pre-shared secret or MAC** between mix gateway and collector. Without that, BB84 is not a protocol, it is a demo. Reviewers will ask. Say it.

**Trust at the gateway.** The gateway is a **named, fixed** point. It sees the mixed bundle. We trust it to **deliver and mix**, not to **read contents**. Contents stay under the pole-level lock until the collector. We are not anonymous from the collector. We are not claiming the gateway is honest-and-curious-proof if someone later removes step 2.

**Downlink.** Steps 8–9 (new brain back to the poles) are not BB84 in this note.

---

## Where BB84 must not appear

- Pole straight to collector (that names the pole and fights garlic).
- Before the mix (job “who spoke” is still open).
- On the day path (milliseconds, frozen tiny detector only).
- Inside averaging or median (that is the liar problem).
- Inside training on unique flows.

---

## What results move, and what must not

BB84 does **not** move:

- attack \(F_1\) (catching floods)
- AttAcc (naming who spoke on the wire)
- pooled vs local vs federated comparison
- garlic vs onion-without-mix vs named path
- how much a median helps against a liar

The only new thing it **could** produce later is **QBER** (error rate) against a toy eavesdropper **on that trunk**. That would be an optional figure, captioned as simulation, with AttAcc **unchanged**.

---

## Claims that would be fake

1. A circuit toolkit as “quantum encryption of TinyML.”
2. BB84 as garlic (mix / who spoke).
3. BB84 as poison defense (liar).
4. Quantum safety messages / quantum CAM.
5. BB84 improving attack \(F_1\).
6. BB84 from each pole to the collector.
7. Calling the simulated poles real hardware.

---

## Go / no-go

Do not simulate BB84 until **all** of this already exists:

- unique rows only (duplicates dropped first)
- pooled vs local vs fair federated vs skewed federated
- median against one lying pole
- naming comparison: garlic, onion without mix, named path

Someone must then **ask** for the trunk simulation. Even then the simulator stays **outside** the averaging loop. It outputs only a **key** and a **QBER**. It does not train. It does not mix. It does not label floods.
