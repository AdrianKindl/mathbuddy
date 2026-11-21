# Mathbuddy – Knowledge section: feature brief

> Learn mental-math tricks step by step, then practise exactly that trick.

Supplements `docs/product-brief.md` (R3 – Knowledge). Version 0.1 · 21 November 2026.
All app text is in English. Explanations below are written for Mathbuddy; they describe well-known arithmetic techniques.

---

## Structure

The Knowledge tab has two modes, switched by a toggle at the top:

| Mode | Content | Release |
|---|---|---|
| **Tricks** | Mental-math tricks grouped by operation | This feature |
| **Textbook** | Background articles (number sense, fractions and percentages, estimating, reference tables) | Later, separate spec |

### Tricks mode – overview screen
- **Operations** grid, one tile per category with its trick count:
  Addition (5), Subtraction (8), Multiplication (8), Division (4), Square numbers (5).

### Category screen
- Title (e.g. "Addition") and a subtitle (e.g. "Addition tricks").
- One row per trick: trick name, difficulty label (Easy, Medium, Hard, Extreme, or a range such as "Medium–Extreme"), and a **✓** once the trick has been practised (K R7).
- Tapping a row opens the trick.

### Trick screen
From top to bottom:
1. **Back** button and trick title.
2. One-sentence description ("Learn how to …").
3. **Example card(s):** a range label (e.g. "Adding 9 to 99"), tags for operation and difficulty, and one fully worked equation. A trick with variants shows one card per variant.
4. Optional **note** (e.g. when the trick works best).
5. **Steps:** numbered steps, each with a short text and a small calculation showing that step on the example.
6. Bottom bar: **previous / next trick** within the category with a position indicator ("2 / 5"), and a **Practice** button.

### Practice screen
1. Choose a level: **Easy, Medium, Hard, Pro** (same buttons as Tests and Trainer), then start.
2. **10 tasks**, one at a time, **no time limit**. Every task is generated from the trick's range for the chosen level (see "Practice levels"), so the trick always applies.
3. Answer field with Submit and Skip, the same green/red feedback as in Tests. After a wrong answer or a skip, the correct answer is shown before the next task.
4. Progress indicator ("Task 4 / 10").
5. After task 10: result screen with correct answers out of 10, and buttons **Practise again** and **Back to trick**.

---

## Rules

- **K R1 – Content is fixed.** Categories, tricks, steps and examples are supplied content, defined in code or a data file. They are not stored in the database.
- **K R2 – Examples are correct.** Every worked example and every step calculation must be arithmetically correct (checked by tests).
- **K R3 – Navigation.** Previous / next stays within the category; it is disabled on the first / last trick.
- **K R4 – Practice tasks.** A practice round has exactly 10 tasks for one trick and one level. Each task follows that trick's range for that level. Tasks are generated anew for every round, and the same task never appears twice in a row. There is no time limit.
- **K R5 – Answers.** Whole-number answers, evaluated as in Tests (MB R3): correct adds one point; wrong and skipped add none; empty or non-numeric input is not evaluated. After a wrong answer or skip, the correct answer is shown.
- **K R6 – Completed rounds.** A round is completed when all 10 tasks have been answered or skipped. Only completed rounds are saved; leaving a round early saves nothing.
- **K R7 – Practised.** A trick shows a ✓ in its category list as soon as at least one round of it has been completed, at any level and with any score. The ✓ is calculated from the saved rounds, not stored separately.

## What the product must remember
Each completed practice round: trick id, level, date and time, number of correct answers. Content is not stored.

## Acceptance scenarios
- **KA1** The overview shows five categories with the trick counts listed above.
- **KA2** Opening Addition shows its five tricks in order with their difficulty labels and no ✓.
- **KA3** "Split one number" shows 56 + 38 = 94 and three steps: 38 → 30 & 8; 56 + 30 = 86; 86 + 8 = 94.
- **KA4** On the first trick of a category, "previous" is disabled; on the last, "next" is disabled.
- **KA5** For every trick, all example and step calculations are correct.
- **KA6** For every trick and level, 1,000 generated practice tasks (fixed seed) all lie in the trick's range for that level, and their answers are whole numbers.
- **KA7** A round always has exactly 10 tasks; answering 7 correctly, 2 wrongly and skipping 1 shows 7 / 10.
- **KA8** Completing one round of "Times 11" shows a ✓ next to it in Multiplication; after restarting the app the ✓ is still there; other tricks have no ✓.
- **KA9** Leaving a round after 5 tasks saves nothing and shows no ✓.

## Out of scope (this feature)
Textbook mode, recommendations, random trick, favourites, feedback buttons, worked solution steps for each practice task (only the correct answer is shown), linking practice results to Profile statistics.

---

## Trick catalogue

Format per trick: **difficulty** · description · example · steps · note · *practice range* (for K R6).

### Addition

**A1 – Split one number** · Medium
Add faster by splitting the smaller number into tens and ones.
Example: 56 + 38 = 94
1. Split the smaller number: 38 → 30 & 8
2. Add the tens: 56 + 30 = 86
3. Add the ones: 86 + 8 = 94

**A2 – Split both numbers** · Medium
Add from left to right by splitting both numbers into place values.
Example: 123 + 291 = 414
1. Split both: 123 → 100 & 20 & 3; 291 → 200 & 90 & 1
2. Add matching places: 200 + 100 = 300; 20 + 90 = 110; 3 + 1 = 4
3. Add the results: 300 + 110 + 4 = 414

**A3 – Compatible numbers** · Medium
Find a part of one number that makes a round number with the other.
Example: 25 + 78 = 103
1. Find the compatible part: 25 + 75 → 100
2. Take that part away from the other number: 78 − 75 = 3
3. Add the rest: 100 + 3 = 103
Note: works best when the round number is a large multiple of 10.

**A4 – Give and take** · Medium
Round one number up, add, then take the extra away again.
Example: 585 + 242 = 827
1. Round up to a multiple of 10: 585 + 15 = 600
2. Add the other number: 600 + 242 = 842
3. Take away what you added: 842 − 15 = 827

**A5 – The 9 trick** · Medium–Extreme
When a number ends in 9 (99, 999), add 1, add, then subtract 1.
Variants (one example card each):
- 9 to 99 · Medium: 29 + 15 = 44 → 29 + 1 = 30; 30 + 15 = 45; 45 − 1 = 44
- 199 to 999 · Hard: 299 + 146 = 445 → 300 + 146 = 446; 446 − 1 = 445
- 1,999 to 9,999 · Extreme: 3,999 + 2,450 = 6,449 → 4,000 + 2,450 = 6,450; 6,450 − 1 = 6,449
Note: there are variants depending on how many 9s the number ends with.

### Subtraction

**S1 – Split one number** · Medium
Split the number you subtract into tens and ones.
Example: 72 − 51 = 21 → 51 → 50 & 1; 72 − 50 = 22; 22 − 1 = 21

**S2 – Split both numbers** · Medium
Subtract place by place.
Example: 467 − 123 = 344 → 400 − 100 = 300; 60 − 20 = 40; 7 − 3 = 4; 300 + 40 + 4 = 344
Note: only works when every digit of the larger number is at least as big as the matching digit of the smaller one; otherwise use S6.

**S3 – Count up to a round number** · Medium
Ask what you must add to the smaller number to reach the larger one.
Example: 100 − 47 = 53 → 47 + ? = 100; ? = 53
Note: best when the first number is a round multiple of 10 (100, 1,000 …).

**S4 – Compensate** · Medium
Subtract a round number, then add back the difference.
Example: 228 − 97 = 131
1. Pick a round number above the subtrahend: 97 + 3 = 100
2. Subtract it: 228 − 100 = 128
3. Add the difference back: 128 + 3 = 131

**S5 – Add the same to both** · Medium
Add the same amount to both numbers so the second becomes round.
Example: 94 − 18 = 76 → 18 + 2 = 20; 94 + 2 = 96; 96 − 20 = 76

**S6 – Avoid borrowing** · Medium
Make the subtrahend smaller in the place that would need borrowing, then correct.
Example: 325 − 134 = 191
1. Split both: 325 → 300 & 20 & 5; 134 → 100 & 30 & 4
2. Find the problem place: tens 20 < 30
3. Lower that place: 134 − 10 = 124
4. Subtract without borrowing: 325 − 124 = 201
5. Subtract the amount you removed: 201 − 10 = 191

**S7 – Subtract from 1,000** · Medium
Take every digit from 9 and the last digit from 10.
Example: 1,000 − 728 = 272 → 9 − 7 = 2; 9 − 2 = 7; 10 − 8 = 2 → 272
Note: if the number ends in 0, drop the 0 on both sides first, then add it back (1,000 − 730 → 100 − 73 = 27 → 270).

**S8 – Count up in steps** · Medium
Count up from the smaller number to the larger one via round numbers.
Example: 120 − 57 = 63 → 57 + 3 = 60; 60 + 40 = 100; 100 + 20 = 120; 3 + 40 + 20 = 63

### Multiplication

**M1 – Times 5** · Medium · halve, then times 10.
Example: 8 × 5 = 40 → 8 ÷ 2 = 4; 4 × 10 = 40

**M2 – Times 8** · Medium · double three times.
Example: 7 × 8 = 56 → 14 → 28 → 56

**M3 – Times 9** · Medium · times 10, then subtract the number.
Example: 12 × 9 = 108 → 120 − 12 = 108

**M4 – Times 11** · Easy–Extreme · variants:
- 1 to 9 · Easy: repeat the digit: 3 × 11 = 33
- 10 to 18 · Medium: put the digit sum between the digits: 17 × 11 → 1 + 7 = 8 → 187
- 19 to 99 · Hard: if the digit sum is 10 or more, write its ones digit in the middle and carry 1 to the left: 57 × 11 → 5 + 7 = 12 → 627
- 100 to 999 · Extreme: keep the outer digits and write the sums of neighbouring digits in between (with carries): 243 × 11 → 2 | 2+4 | 4+3 | 3 → 2,673
Note: variants depend on the size of the number.

**M5 – Times 12** · Hard · put a 0 in front; from left to right, double each digit and add its right neighbour; combine with carries.
Example: 384 × 12 = 4,608 → 0384; (0×2)+3 = 3; (3×2)+8 = 14; (8×2)+4 = 20; (4×2)+0 = 8 → 3 | 14 | 20 | 8 → 4,608

**M6 – Times 13** · Hard · same as M5, but triple each digit.
Example: 437 × 13 = 5,681 → 0437; 4; 15; 16; 21 → 5,681

**M7 – Times 25** · Medium · times 100, then halve twice.
Example: 13 × 25 = 325 → 1,300 → 650 → 325

**M8 – Times 99** · Medium · times 100, then subtract the number.
Example: 7 × 99 = 693 → 700 − 7 = 693

### Division

**D1 – Divide by 5** · Medium · double, then divide by 10.
Example: 45 ÷ 5 = 9 → 45 × 2 = 90; 90 ÷ 10 = 9

**D2 – Divide by 8** · Medium · halve three times.
Example: 32 ÷ 8 = 4 → 16 → 8 → 4. Note: if you know dividing by 2 and 4, this will not surprise you.

**D3 – Cancel zeros** · Medium · remove the same number of trailing zeros from both numbers.
Example: 8,000 ÷ 200 = 40 → 80 ÷ 2 = 40

**D4 – Simplify** · Medium · divide both numbers by a common factor first.
Example: 48 ÷ 8 = 6 → 48 ÷ 4 = 12; 8 ÷ 4 = 2; 12 ÷ 2 = 6

### Square numbers

**Q1 – Between 10 and 25** · Extreme
Example: 19² = 361
1. Add the ones digit to the number: 19 + 9 = 28
2. Times 10: 28 × 10 = 280
3. Square the ones digit: 9² = 81
4. Add: 280 + 81 = 361

**Q2 – Between 25 and 75** · Extreme
Example: 47² = 2,209
1. Subtract 25: 47 − 25 = 22
2. Times 100: 2,200
3. Distance from 50: 50 − 47 = 3
4. Square it: 3² = 9
5. Add: 2,200 + 9 = 2,209

**Q3 – Between 75 and 125** · Extreme · variants:
- 75 to 99: 96² = 9,216 → distance below 100: 4; 96 − 4 = 92; 92 × 100 = 9,200; 4² = 16; 9,200 + 16 = 9,216
- 101 to 125: 106² = 11,236 → distance above 100: 6; 106 + 6 = 112; 112 × 100 = 11,200; 6² = 36; 11,200 + 36 = 11,236

**Q4 – Ending in 5** · Medium–Hard · multiply the number before the 5 by the next number, then append 25.
Variants: 15 to 95: 85² → 8 × 9 = 72 → 7,225 · 105 to 995: 205² → 20 × 21 = 420 → 42,025

**Q5 – Round to the nearest ten** · Hard
Example: 83² = 6,889
1. Round up: 83 + 7 = 90
2. Round down by the same amount: 83 − 7 = 76
3. Multiply: 90 × 76 = 6,840
4. Square the amount: 7² = 49
5. Add: 6,840 + 49 = 6,889

---

## Practice levels

Ranges are inclusive. Every generated task must be one where the trick applies; results are whole numbers, and subtraction results are at least 1.

| Trick | Easy | Medium | Hard | Pro |
|---|---|---|---|---|
| A1 Split one number | 11–49 + 11–49 | 20–99 + 20–99 | 100–999 + 20–99 | 100–999 + 100–999 |
| A2 Split both numbers | 10–99 + 10–99 | 100–499 + 100–499 | 100–999 + 100–999 | 1,000–9,999 + 1,000–9,999 |
| A3 Compatible numbers | 25, 50 or 75 + (its complement to 100 + 1–9) | 2-digit + (its complement to 100 + 1–20) | 3-digit multiple of 25 + (complement to 1,000 + 1–99) | 3-digit + (complement to 1,000 + 1–999) |
| A4 Give and take | 2-digit ending 6–9 + 2-digit | 3-digit within 25 below a hundred + 3-digit | 3-digit within 50 below a hundred + 3-digit | 4-digit within 50 below a thousand + 4-digit |
| A5 The 9 trick | 19–89 ending 9 + 1–9 | 19–89 ending 9 + 10–99 | 199–999 ending 99 + 100–999 | 1,999–9,999 ending 999 + 1,000–9,999 |
| S1 Split one number | 2-digit − 1-digit | 2-digit − 2-digit | 3-digit − 2-digit | 3-digit − 3-digit |
| S2 Split both numbers (no borrowing) | 2-digit | 3-digit | 4-digit | 5-digit |
| S3 Count up to a round number | 100 − 2-digit | 200–900 (hundreds) − 2- or 3-digit | 1,000 − 3-digit | 2,000–9,000 (thousands) − 3- or 4-digit |
| S4 Compensate | 2-digit − 18–99 ending 8–9 | 3-digit − 2-digit ending 7–9 | 3-digit − 197–999 ending 97–99 | 4-digit − 3-digit ending 95–99 |
| S5 Add the same to both | 2-digit − 2-digit ending 8–9 | 2-digit − 2-digit ending 6–9 | 3-digit − 2-digit ending 5–9 | 3-digit − 3-digit ending 95–99 |
| S6 Avoid borrowing | 2-digit, borrowing in the ones | 3-digit, one borrowing place | 3-digit, two borrowing places | 4-digit, one or two borrowing places |
| S7 Subtract from 1,000 | 100 − 11–99 | 1,000 − 101–999 | 10,000 − 1,001–9,999 | 100,000 − 10,001–99,999 |
| S8 Count up in steps | 2-digit − 2-digit crossing a ten | 101–199 − 2-digit crossing 100 | 3-digit − 3-digit crossing a hundred | 4-digit − 3-digit crossing a thousand |
| M1 Times 5 | even 2–20 × 5 | even 22–98 × 5 | 11–99 × 5 | 100–999 × 5 |
| M2 Times 8 | 2–12 × 8 | 13–50 × 8 | 51–150 × 8 | 151–999 × 8 |
| M3 Times 9 | 2–12 × 9 | 13–99 × 9 | 100–999 × 9 | 1,000–9,999 × 9 |
| M4 Times 11 | 1–9 × 11 | 10–99 with digit sum ≤ 9 × 11 | 10–99 with digit sum ≥ 10 × 11 | 100–999 × 11 |
| M5 Times 12 | 2–12 × 12 | 13–99 × 12 | 100–999 × 12 | 1,000–9,999 × 12 |
| M6 Times 13 | 2–12 × 13 | 13–99 × 13 | 100–999 × 13 | 1,000–9,999 × 13 |
| M7 Times 25 | 2–12 × 25 | 13–40 × 25 | 41–199 × 25 | 200–999 × 25 |
| M8 Times 99 | 2–12 × 99 | 13–99 × 99 | 100–999 × 99 | 1,000–9,999 × 99 |
| D1 Divide by 5 | result 2–10 | result 11–100 | result 101–1,000 | result 1,001–10,000 |
| D2 Divide by 8 | result 2–10 | result 11–50 | result 51–200 | result 201–1,000 |
| D3 Cancel zeros | a0 ÷ b0, a and b 1-digit | a00 ÷ b0, result whole | a000 ÷ b00, result whole | 2-digit a000 ÷ 2-digit b00, result whole |
| D4 Simplify | both even, divisor 4–9, result 2–9 | common factor 2–5, divisor 10–20, result 2–12 | 3-digit ÷ 2-digit, common factor 2–9, result 2–20 | 4-digit ÷ 2-digit, common factor 2–9, result 11–99 |
| Q1 Between 10 and 25 | 11–15 | 16–20 | 21–25 | 11–25 |
| Q2 Between 25 and 75 | 45–55 | 35–65 | 30–70 | 26–74 |
| Q3 Between 75 and 125 | 95–105 (not 100) | 90–110 (not 100) | 80–120 (not 100) | 76–125 (not 100) |
| Q4 Ending in 5 | 15–45 | 55–95 | 105–495 | 505–995 |
| Q5 Round to the nearest ten | 11–29 | 31–59 | 61–99 | 101–199 |

Square tasks exclude multiples of 10 except where stated.

---

## Open points
- Textbook mode content (separate spec).
