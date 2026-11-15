# Paper 2 story — many roadside boxes, one tiny detector, a hidden upload

This is a complete story by itself. You do not need another paper to understand it. No programs are named here. Read it as if you have never heard of the first roadside paper.

---

## 1. The place

Think of a highway. Along the road sit many small computers on poles. Call each one a **roadside box**.

Each box does two kinds of work at once, in real life:

- It helps cars know about each other (safety messages).
- It also sees **internet-style flows** on the transport network: streams of packets that can be counted (how long, how many packets, and so on).

This story is about those **flows**, not about drawing radio waves. We use a public table of such flows that already has a label: normal, or flood (an attack that tries to drown the box). The table is messy. Many rows are exact copies of each other. If you train on the copies, a computer can look almost perfect and still be cheating. So in this story we **throw away duplicate rows first**, then we work only with the remaining **unique** flows.

There are many more normal rows than attack rows. So “99 percent correct” is easy and mostly meaningless. The number we care about is: **when it is really an attack, how often do we catch it without crying wolf too much?** That is attack-class \(F_1\).

---

## 2. What is going wrong (the actual problem)

The operator wants **every** roadside box to run the **same tiny detector**. Tiny means a very small neural net: a few hundred numbers (weights), small enough to run on the box in a fraction of a millisecond. It looks at one flow and says: probably normal, or probably a flood.

If the operator could put **all unique flows from all boxes into one pile** and train once, that would be the best detector they can get from this table. Call that the **pooled** brain. It is the ceiling, not the enemy.

They **cannot** always make that pile.

**Problem A — the data cannot all leave the box.**  
There are many boxes. Sending every flow to a data center is heavy, and often not allowed. Also, if you send the raw copied table, you leak the cheat we already know about.

**Problem B — each box is blind in a different way.**  
Box 1 might see almost all the floods. Box 2 might see almost none. If each box trains only on what it saw, Box 2’s detector is weak. We want them to **share the lesson**, not the raw flows.

**Problem C — the night upload can name the box.**  
Suppose each box, at night, sends its new brain-numbers (the weights) to a collector over one ordinary secure web path. A watcher on the wire may not read the numbers if they are locked. But the watcher can still see **which pole sent a parcel tonight**. That is a map of the live edge.

Those are three different pains. They need three different tools. One magic protocol will not fix all three.

---

## 3. What we are not trying to fix in this story

- We are not claiming we rebuilt the car radio.
- We are not hiding the cars’ safety messages inside a secret tunnel. Safety messages cannot wait for overlay hops.
- We are not waiting for a night meeting before the box can flag a flood **during the day**. Daytime uses yesterday’s tiny brain, already on the pole, and is fast.
- We are not saying “more accuracy on the copied table.”
- We are not saying a secret lock stops a **lying neighbor** who sends a **wrong** brain on purpose. A lock only hides bits. A liar still sends bits.

---

## 4. The two clocks (day and night)

**Day (fast, each box alone)**  
A flow arrives. The tiny detector already sitting on the box scores it. If the operator also wants a local reaction (slow that flow, or drop it), that is still **this box, now**. No meeting of all boxes. No secret mix. No quantum key. Time scale: milliseconds.

**Night (slow, many boxes)**  
Each box trains a little on **only its own unique flows**. It does **not** send the flows. It sends a small parcel: the **new weights** (about two kilobytes for this tiny net). A trusted collector **averages** those parcels (federated averaging). In the morning, every box installs the same new tiny brain and goes back to daytime.

Night is minutes to hours, not milliseconds.

---

## 5. The night path, step by step (the whole flow)

Imagine ten poles. Night begins.

1. **Local homework.** Each pole trains a few passes on its own unique flows.  
2. **Wrap the homework.** The weights are locked so a casual watcher cannot read the numbers. This is ordinary locking with a key only the **trusted collector** can open. The mix gateway, if used, is trusted to **carry** the locked parcels, not to **open** them. (A second lock on a private trunk can be added later. See §8.)  
3. **Send the parcel toward the collector**, but not always as one named letter.  
4. **The collector opens the parcels it is allowed to open**, averages the brains (or takes a **median** if we fear a liar), and produces one **global** tiny detector.  
5. **The new detector is sent back** to every pole.  
6. **Morning.** Each pole runs that frozen detector on live flows, fast.

That is the whole application loop. Everything else is: how we split the homework, how we send the parcel, and how we treat a liar.

---

## 6. How we share the lesson without sharing the flows

**Pooled.** All unique training rows in one pile. Best attack \(F_1\) we can expect. Upper bound. We still report it so nobody thinks federation “beat the data center” by cheating.

**Local.** Each pole trains only on its slice. We test every local brain on the **same leftover test rows** that no pole was allowed to train on. We report the average and how much they disagree. This is the “no sharing” baseline.

**Federated average, fair split (IID).** Unique training rows are dealt so each pole sees a similar mix of floods and normal. Each night they send weights, not rows. If this attack \(F_1\) gets **close** to pooled, federation worked.

**Federated average, unfair split (skew).** Almost all unique flood rows sit on one or two poles. The others mostly see normal traffic. This is more like a real road. Federation should look **worse** than pooled. That drop is a result, not a failure to hide.

**Median instead of average.** If one pole sends garbage weights, the average is pulled. The median of each number in the brain is harder to pull. That is the answer to a **lying** pole. It is not the answer to “who sent the parcel.”

We never put the leftover test rows into a pole’s homework. We never train on duplicate copies. We never score success with “accuracy” as the headline.

---

## 7. How the parcel travels (who spoke)

Locking the numbers (wrap) is not the same as hiding **who posted**.

**Ordinary named path (HTTPS-style).** One letter, one path. A watcher who sees that path often knows which pole it was. Delivery is simple. Naming is easy.

**Onion, no waiting, no dummy letters.** The letter takes extra hops. If one path is cut, another hop may still get it there. So **delivery** can get better. But if the watcher sees the **first** hop leave the pole, they still know who started it. Extra hops are not a disguise by themselves.

**Garlic.** The pole waits a short time, packs its real letter with **dummy letters** attributed to other poles, and sends a **bundle**. The watcher who sees the bundle sees a **group**, not a singleton. They can guess, but they are less sure. The wait costs time. Dummy letters cost extra bytes.

**The rule we will prove, in words.**  
Onion can help **arrival**. Garlic is what helps **not being named**, and only when the bundle is not a single letter. If we add hops but never mix, we must not call that garlic.

The collector at the end is **trusted**. It is allowed to open the real contents. We do not claim we are anonymous **from the collector**. We claim we are harder to name **on the wire**.

---

## 8. Optional extra lock on a private trunk (BB84, in this story only)

Three jobs again, in human words:

- **Who spoke?** Mix (garlic).  
- **Can they read the numbers?** A lock.  
- **Are the numbers honest?** Median.

A method called **BB84** is a way for **two ends of a special link** to agree on a fresh random key while noticing if someone is tapping that special link. After they share the key, they still lock the numbers with an ordinary lock that uses that key. BB84 is **not** the mix. BB84 is **not** the tiny detector. BB84 is **not** the median.

If we put BB84 from **every pole straight to the collector**, the special link itself points at the pole. That fights garlic.

If we use BB84 at all in this story, it sits **after** the mix, on a **named private trunk**: mix gateway to collector. Poles still send classical bundles that are **already locked for the collector**. The two trunk ends must already share a way to authenticate their classical BB84 messages (a pre-shared secret or MAC). BB84 then mints a night key. Ordinary AES with that key is a **second** wrap for the trunk hop only. Watchers on the highway mix still see garlic. Watchers on that trunk already know it is gateway-to-collector. They are a different enemy (reading bits on that hop, not naming poles). The gateway is trusted to deliver, not to read.

This extra lock **does not** change “how often we catch floods.” It **does not** replace garlic’s naming score. It can wait. The core story stands without it.

---

## 9. What “winning” looks like in this story

Winning is not “we beat the pooled brain.”

Winning is:

- We dropped copies before we pretended to be many poles.  
- Pooled, local, fair-federation, and unfair-federation all sit in **one** comparison, with attack \(F_1\) on leftover unique test rows.  
- Fair-federation is **near** pooled, or we admit the gap.  
- Unfair-federation is **worse**, like a real road.  
- A liar hurts the average; median hurts less; we do **not** say garlic stopped the liar.  
- On the wire, named path and onion-without-mix name the pole about as often as the watcher sees the path; garlic names less only when the bundle has more than one letter.  
- We say the poles in the study are **simulated** from unique rows of one public table, not twenty real poles we installed.

---

## 10. One picture of the whole story

```
DAY (fast)
  flow --> tiny detector already on the pole --> local decision

NIGHT (slow)
  pole trains on its own unique flows
       --> wrap the WEIGHTS
       --> named path / extra hops / mixed bundle
       --> trusted collector averages (or median)
       --> new tiny detector returns to every pole
```

**In one breath.** Many roadside boxes want one tiny flood-detector without shipping their flows. At night they send brains, not data. Mixing the parcels makes it harder to see which pole studied tonight. Averaging shares the lesson. A median fights a liar. A special key-agreement on a private trunk can lock bits after the mix, and it is optional.

That is Paper 2, from scratch.
