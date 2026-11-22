# Mathbuddy – Knowledge: Textbook mode – feature brief

> Short articles that explain the background behind mental math, with worked examples and reference tables.

Supplements `docs/product-brief.md` (R3 – Knowledge) and `docs/knowledge-brief.md` (Tricks mode). Version 0.1 · 21 November 2026.
All app text is in English. Article texts below are written for Mathbuddy.

---

## Structure

The Knowledge tab has a toggle at the top: **Tricks** (already built, spec 009) and **Textbook** (this feature).

### Textbook overview
A grid of four category tiles, each with its article count:

| Category | Articles |
|---|---|
| Basics | 3 |
| Fractions | 3 |
| Case interview | 7 |
| Estimating & rounding | 4 |

### Category screen
Title and one row per article: article name and difficulty label (Medium or Hard). Tapping a row opens the article. Same design as the Tricks category screen.

### Article screen
From top to bottom:
1. **Back** button and article title.
2. **Overview:** heading "Overview" and a one-line summary.
3. **Main card:** a card title, tags (category and difficulty), and the body text.
4. Optional **note** (small info box).
5. **Examples:** one or more example cards, each with a title and a few lines of worked text.
6. Optional **Reference table:** a card with a title, a short subtitle and a table.
7. Optional **Related tricks:** links to tricks in Tricks mode; tapping one opens that trick.
8. Bottom bar: **previous / next article** within the category with a position indicator ("2 / 7"), and a **Practice** button.

The category screen shows a **✓** next to every article that has been practised (T R10), like in Tricks mode.

### Practice screen
Same flow and design as Tricks practice (`docs/knowledge-brief.md`): choose a level (Easy, Medium, Hard, Pro), then **10 tasks**, **no time limit**, Submit and Skip, green/red feedback, the correct answer shown after a wrong answer or skip, progress "Task 4 / 10", and a result screen with correct answers out of 10, **Practise again** and **Back to article**.
Depending on the task, the answer is typed or chosen from buttons (see "Answer types").

---

## Rules
- **T R1 – Content is fixed.** Categories, articles, examples and tables are supplied content, defined as data (not in Streamlit code) and not stored in the database.
- **T R2 – Content is correct.** Every number in examples and tables is correct (checked by tests where it is a calculation).
- **T R3 – Navigation.** Previous / next stays within the category and is disabled on the first / last article.
- **T R4 – Related tricks.** Every related-trick link points to an existing trick from `docs/knowledge-brief.md`.
- **T R5 – Tricks mode unchanged.** Switching between Tricks and Textbook does not change anything in Tricks mode, including the ✓ "practised" markers.
- **T R6 – Practice tasks.** A practice round has exactly 10 tasks for one article and one level, generated from that article's template and ranges (see "Practice catalogue"). Tasks are generated anew for every round; the same task never appears twice in a row. No time limit.
- **T R7 – Answer types.** Each task has one answer type:
  - **Whole number:** digits with an optional leading minus sign. Thousands separators are not accepted.
  - **Decimal:** digits with one decimal separator ("." or ","), optional minus sign, optional trailing "%" for percentages. No thousands separators. The task states the precision, e.g. "(1 decimal place)". The answer is correct if it equals the exact result rounded to that precision; "8" is accepted for 8.0.
  - **Choice:** 2–4 buttons, exactly one correct. Choosing a button submits the answer.
  - **Estimate:** a whole number; correct if it is within ±10 % of the exact result. The task says "Estimate".
- **T R8 – Answers.** Correct adds one point; wrong and skipped add none; input that does not match the answer type is not evaluated and shows a short hint. After a wrong answer or skip the correct answer is shown (for estimates: the exact result and the accepted range).
- **T R9 – Completed rounds.** A round is completed when all 10 tasks are answered or skipped. Only completed rounds are saved; leaving early saves nothing.
- **T R10 – Practised.** An article shows a ✓ in its category list once at least one round of it has been completed, at any level and with any score. The ✓ is calculated from saved rounds, not stored separately.

## What the product must remember
Each completed textbook practice round: article id, level, date and time, number of correct answers. Article content is not stored. Trick practice rounds from spec 009 stay as they are.

## Acceptance scenarios
- **TA1** The Textbook overview shows four categories with 3, 3, 7 and 4 articles.
- **TA2** Opening "Case interview" lists its seven articles in the order below with their difficulty labels.
- **TA3** "Order of operations" shows the overview, the main card, the note and the example "Calculate 3 + 4 × 2" with result 11.
- **TA4** "Fractions, decimals and percentages" shows the reference table with all 17 rows from 1/2 to 1/12.
- **TA5** On the first article of a category "previous" is disabled; on the last, "next" is disabled.
- **TA6** In "Compatible numbers" (Estimating & rounding), the related-trick link opens the trick "Compatible numbers" in Addition.
- **TA7** Switching to Textbook and back to Tricks keeps all ✓ markers.
- **TA8** For every article and level, 1,000 generated tasks (fixed seed) follow the article's template and ranges, and their correct answer matches the answer type (whole numbers stay whole, choices have exactly one correct option).
- **TA9** Answer types: for a decimal task with 1 decimal place and exact result 66.666…, "66.7", "66,7" and "66.7%" are correct, "66.6" is wrong, "abc" is not evaluated. For an estimate of 7,341 ÷ 83 (exact 88.45…), 80 and 97 are correct, 79 and 98 are wrong. For a whole-number task, "-12" is read as −12.
- **TA10** A round always has 10 tasks; 6 correct, 3 wrong and 1 skipped shows 6 / 10.
- **TA11** Completing one round of "Rule of 72" shows a ✓ next to it in Case interview; after restarting the app the ✓ is still there; no other article has a ✓, and Tricks ✓ markers are unchanged.
- **TA12** Leaving a round after 5 tasks saves nothing.

## Out of scope
Favourites, feedback buttons, a "For you" section, worked solution steps for each practice task (only the correct answer is shown), any article not listed below, linking practice results to Profile statistics.

---

## Article catalogue

### Basics

**B1 – Order of operations** · Medium
- Overview: Brackets, exponents, multiplication/division, addition/subtraction – the universal order.
- Card "Why the order matters": Without a shared order, the same expression could give different results. 3 + 4 × 2 is 11, not 14, because multiplication comes before addition. The agreed order is: (1) brackets, from the inside out; (2) exponents, i.e. powers and roots; (3) multiplication and division, equal rank, left to right; (4) addition and subtraction, equal rank, left to right. A common mistake is to think multiplication always comes before division, or addition before subtraction. Each pair has equal rank and is worked from left to right.
- Note: Multiplication and division have equal rank – work left to right. The same holds for addition and subtraction. So 8 ÷ 2 × 4 = 16 (not 1): 8 ÷ 2 = 4, then 4 × 4 = 16. Likewise 10 − 3 + 2 = 9 (not 5).
- Example "Calculate 3 + 4 × 2": Step 1: no brackets or exponents. Step 2: multiplication first: 4 × 2 = 8. Step 3: addition: 3 + 8 = 11. The result is 11, not 14.

**B2 – Rules for negative numbers** · Medium
- Overview: How negative numbers behave in the four operations – and why minus times minus is plus.
- Card "Rules for all four operations":
  - Addition: adding a negative number is the same as subtracting its positive value. 5 + (−3) = 5 − 3 = 2.
  - Subtraction: subtracting a negative number is the same as adding. 5 − (−3) = 5 + 3 = 8. Think of it as taking away a debt.
  - Multiplication and division: equal signs give a positive result, different signs a negative one. (−4) × (−3) = +12 and (−4) × 3 = −12.
  - Why minus times minus is plus: if 3 people each owe you 4 $, that is 12 $ of debt to you: (−4) × 3 = −12. If those 3 debts are removed, you gain 12 $: (−4) × (−3) = +12.
- Example "Practical calculations": (−7) + (−5) = −12 (two debts add up). (−8) − (−3) = −8 + 3 = −5. (−6) × 4 = −24 (different signs → negative). (−20) ÷ (−5) = 4 (equal signs → positive).
- Reference table "Sign rules" (signs of products and quotients): (+) × (+) → +; (+) × (−) → −; (−) × (+) → −; (−) × (−) → +.

**B3 – Calculating with decimals** · Medium
- Overview: Adding, subtracting, multiplying and dividing decimals – and the decimal-point shift.
- Card "The four operations with decimals":
  - Addition and subtraction: line up the decimal points, then add or subtract as usual. Fill in trailing zeros if needed: 3.5 + 2.75 becomes 3.50 + 2.75 = 6.25.
  - Multiplication: ignore the decimal points, multiply the whole numbers, count the decimal places in both factors and set the point. 1.2 × 0.3: 12 × 3 = 36, 2 decimal places → 0.36.
  - Powers of ten: dividing moves the point left (45.6 ÷ 10 = 4.56); multiplying moves it right (0.037 × 100 = 3.7).
- Note: Every decimal is a fraction (0.75 = 75/100 = 3/4) and every percentage is a decimal (12.5 % = 0.125). Switching between decimals, fractions and percentages is a core mental-math skill: if one form makes a calculation hard, switch to another.
- Example "Multi-step calculation": Calculate 2.5 × 3.2 − 1.4. Step 1: 25 × 32 = 800, 2 decimal places → 8.00. Step 2: 8.00 − 1.4 = 6.6.

### Fractions

**F1 – Fractions, decimals and percentages** · Medium
- Overview: The reference: 1/2 to 1/12 with all conversions.
- Card "Learn by heart": Knowing the common conversions between fractions, decimals and percentages saves a lot of time. These are the ones used most in mental math. Memorise the ones you meet most often and derive the rest.
- Note: Thirds (0.333…, 0.666…), sixths (0.1666…, 0.8333…) and twelfths (0.0833…) are repeating decimals. Round to the precision your task needs.
- Reference table "Common conversions" (Fraction · Decimal · Percent):
  1/2 · 0.5 · 50 % — 1/3 · 0.333… · 33.3 % — 2/3 · 0.666… · 66.7 % — 1/4 · 0.25 · 25 % — 3/4 · 0.75 · 75 % — 1/5 · 0.2 · 20 % — 2/5 · 0.4 · 40 % — 3/5 · 0.6 · 60 % — 4/5 · 0.8 · 80 % — 1/6 · 0.1666… · 16.7 % — 5/6 · 0.8333… · 83.3 % — 1/8 · 0.125 · 12.5 % — 3/8 · 0.375 · 37.5 % — 5/8 · 0.625 · 62.5 % — 7/8 · 0.875 · 87.5 % — 1/10 · 0.1 · 10 % — 1/12 · 0.0833… · 8.3 %

**F2 – Comparing fractions** · Medium
- Overview: Cross-multiply to compare: a/b vs c/d → compare a × d with b × c.
- Card "The cross-multiplication trick": To compare a/b and c/d without a common denominator, cross-multiply: work out a × d and b × c. If a × d > b × c, then a/b > c/d. This works because you are effectively comparing both fractions over the common denominator b × d.
- Example "Compare 3/7 and 5/11": 3 × 11 = 33 and 5 × 7 = 35. Since 33 < 35, 3/7 < 5/11.

**F3 – The fraction trap: 0 < x < 1** · Hard
- Overview: Squaring makes it smaller, the square root makes it bigger. (1/2)² = 1/4, but √(1/4) = 1/2.
- Card "Reversed intuitions": For numbers between 0 and 1, our intuition about operations is reversed. Squaring makes them smaller, not bigger: (1/2)² = 1/4. Taking the square root makes them bigger, not smaller: √(1/4) = 1/2. Multiplying by a proper fraction also makes the result smaller, because you take "a part of a part".
- Note: This is one of the most common traps in standardised tests and mental-math challenges. Whenever you see an exponent or a root, first check: is the number between 0 and 1?
- Example "The ordering rule": Let x = 0.5. Then x² = 0.25 (smaller than x) and √x ≈ 0.707 (bigger than x). For every number with 0 < x < 1: x² < x < √x.

### Case interview

**C1 – Successive percentage changes** · Hard
- Overview: Chain the multipliers – 20 % up, then 10 % down = 1.20 × 0.90 = 1.08.
- Card "Chained multipliers": For successive percentage changes, multiply the individual multipliers. A 20 % increase followed by a 10 % decrease gives 1.20 × 0.90 = 1.08, a net increase of 8 %. Never add or subtract percentages that refer to different bases.
- Note: For small rates (under 10 %) you can add them as an approximation: 3 % + 4 % + 2 % ≈ 9 % in total. The error is small because the cross terms (such as 0.03 × 0.04) are negligible.
- Example "Three years of growth": Revenue grows by 10 %, then 20 %, then 5 %. Total multiplier: 1.10 × 1.20 × 1.05 = 1.386, a total increase of 38.6 % over three years.

**C2 – The rule of 72** · Medium
- Overview: 72 ÷ growth rate ≈ doubling time.
- Card "Doubling time in seconds": To estimate how long an investment or metric takes to double at a constant growth rate, divide 72 by the rate (as a whole number). At 8 % growth, doubling takes about 72 ÷ 8 = 9 years. This works because ln(2) ≈ 0.693, and 72 is a handy approximation of 69.3 with many divisors.
- Note: For tripling time use 114 instead of 72. At 6 % growth: 114 ÷ 6 = 19 years to triple.
- Example "Market growth": A market grows by 6 % per year. Doubling time: 72 ÷ 6 = 12 years. If the market is worth 10 bn $ today, it will be worth about 20 bn $ in 12 years.

**C3 – Margin vs markup** · Hard
- Overview: Margin = markup / (1 + markup). Don't mix them up.
- Card "Margin vs markup": Margin and markup both express profit, but on different bases. Margin = profit / revenue (profit as a share of the selling price). Markup = profit / cost (profit as a share of the cost). Conversion: margin = markup / (1 + markup), or equivalently markup = margin / (1 − margin).
- Example "Applied example": A product costs 60 $ and sells for 100 $. Profit = 40 $. Margin = 40 / 100 = 40 %. Markup = 40 / 60 = 66.7 %. Both describe the same 40 $ profit, measured against different bases.
- Reference table "Margin to markup": 20 % → 25 % · 25 % → 33.3 % · 33.3 % → 50 % · 40 % → 66.7 % · 50 % → 100 %.

**C4 – Percentage change** · Medium
- Overview: % change = (new − old) / old × 100.
- Card "Always divide by the starting value": Percentage change = (new value − old value) / old value × 100. The denominator is always the original value. A positive result is an increase, a negative one a decrease. This is the formula used most often in case interviews.
- Note: Always use the OLD value as the base. If revenue falls from 100 m $ to 80 m $, the drop is 20 % (not 25 %). If it then rises back to 100 m $, that is a 25 % increase from 80 m $.
- Example "Revenue change": Revenue rose from 80 m $ to 92 m $. Change = (92 − 80) / 80 × 100 = 12 / 80 × 100 = 15 % increase.

**C5 – Weighted averages** · Medium
- Overview: Average = Σ(weight × value) / Σ(weights).
- Card "Not all data points are equal": A weighted average takes the relative importance (weight) of each value into account. Multiply each value by its weight, add up the products and divide by the total weight. This is essential for blended rates, portfolio returns and segment-weighted metrics.
- Note: In case interviews, always check whether segments have different weights before averaging. A simple average of segment margins can be very misleading when segment sizes differ a lot.
- Example "Blended margin": Product A: 60 % of revenue at 30 % margin. Product B: 40 % of revenue at 20 % margin. Blended margin = 0.60 × 30 % + 0.40 × 20 % = 18 % + 8 % = 26 %.

**C6 – The break-even equation** · Medium
- Overview: Q = fixed costs / (price − variable costs).
- Card "Where revenue meets costs": The break-even point is where total revenue exactly equals total cost. Break-even quantity Q = fixed costs / (price per unit − variable cost per unit). The denominator (price − variable cost) is the contribution margin per unit: how much each unit sold contributes to covering fixed costs.
- Note: Interviewers often ask what happens when prices or costs change. A 10 % price increase on a 50 $ product raises the contribution margin by 5 $ (from 20 $ to 25 $) and lowers break-even by 20 % (from 25,000 to 20,000 units).
- Example "Launching a new product": Fixed costs: 500,000 $. Price per unit: 50 $. Variable cost: 30 $. Contribution margin: 20 $. Break-even: 500,000 ÷ 20 = 25,000 units.

**C7 – Calculating with large numbers** · Medium
- Overview: K × K = M, M × K = B, M × M = T.
- Card "Calculating with abbreviations": When working with large numbers, use abbreviations: K = thousand, M = million, B = billion, T = trillion. Multiplication rules: K × K = M, M × K = B, M × M = T, B × K = T. Focus on the coefficients and track the order of magnitude separately.
- Example "Market size estimate": 300 M people × 50 K $ average income = 300 × 50 × (M × K) = 15,000 B = 15 T $ GDP. Coefficients: 300 × 50 = 15,000. Magnitudes: M × K = B. So 15,000 B = 15 T $.
- Reference table "Rules for large numbers" (row × column): K × K = M, K × M = B, K × B = T; M × K = B, M × M = T, M × B = —; B × K = T, B × M = —, B × B = —.

### Estimating & rounding

**E1 – Rounding & estimating** · Medium
- Overview: Round to the leading digits for fast, approximate results.
- Card "Leading-digit strategy": Front-end estimation focuses on the leading (leftmost) digits of each number to get a quick approximate result. Round each number to its highest place value, do the operation and adjust if needed. It is the fastest way to a rough reference value.
- Note: For a single calculation, round to the nearest value. In chains of calculations, balance the rounding: round some numbers up and others down so the errors partly cancel out.
- Example "Estimate 487 + 623": Round to hundreds: 500 + 600 = 1,100. The exact result is 1,110 – the estimate is very close. For more accuracy, adjust: the remainders are −13 + 23 = 10, so the refined estimate is 1,110.

**E2 – Compatible numbers** · Medium
- Overview: Replace awkward values with nearby, easy ones.
- Card "Easy substitutes": Compatible numbers are pairs that are easy to calculate in your head. Replace awkward numbers with nearby easy ones. When dividing, choose numbers that divide evenly. When multiplying, choose numbers ending in 0 or 5. The key is to pick substitutes close enough to the original to give a useful estimate.
- Examples: "Estimate 7,341 ÷ 83": Replace with 7,200 ÷ 80 = 90. The exact result is about 88.4 – the compatible-number estimate is excellent. "Estimate 49 × 51": Both are close to 50: 50 × 50 = 2,500. The exact result is 2,499.
- Related tricks: Compatible numbers (Addition), Count up to a round number (Subtraction).

**E3 – Order of magnitude** · Medium
- Overview: Check the number of digits to catch big mistakes.
- Card "Thinking in powers of ten": An order-of-magnitude check asks: "How many digits should the result have?" Multiplying a 3-digit number by a 2-digit number should give 4 or 5 digits. This kind of plausibility check catches errors where you are off by a factor of 10 or more.
- Note: In multiplication, the product of an m-digit and an n-digit number has either (m + n − 1) or (m + n) digits. In addition, the sum has as many digits as the larger number, or one more.
- Example "Checking a product": You calculate 34 × 78 and get 26,520. Check: 2-digit × 2-digit should give a 3- or 4-digit result. 26,520 has 5 digits – something is wrong. The correct result is 2,652.

**E4 – Casting out nines** · Hard
- Overview: Check calculations with the single-digit digit sum.
- Card "The single-digit digit-sum check": Casting out nines is an old method for checking calculations. Add the digits of a number until you get a single digit (the digital root). For every correct multiplication, the digital root of the product equals the digital root of the product of the two digital roots. If they don't match, the calculation is wrong.
- Note: Casting out nines cannot detect errors that are multiples of 9 (such as swapped digits). It catches about 89 % of random single-digit errors – good, but not perfect.
- Example "Check 47 × 83 = 3,901": Digital root of 47: 4 + 7 = 11 → 1 + 1 = 2. Digital root of 83: 8 + 3 = 11 → 1 + 1 = 2. Product of the roots: 2 × 2 = 4. Digital root of 3,901: 3 + 9 + 0 + 1 = 13 → 1 + 3 = 4. Both give 4, so the result is probably correct.

---


## Practice catalogue

Ranges are inclusive. Every intermediate and final result must be exact where the answer type is whole number; divisions always divide evenly unless the task asks for an estimate. "Dec 1" means a decimal answer with 1 decimal place.

### Basics

| Article | Type | Easy | Medium | Hard | Pro |
|---|---|---|---|---|---|
| B1 Order of operations | Whole | a + b × c, numbers 2–9 | a × b − c × d or a + b × c − d, numbers 2–12, result ≥ 0 | (a + b) × c − d ÷ e, numbers 2–20, d divisible by e, result ≥ 0 | (a − b) × (c + d) − e × f ÷ g, numbers 2–20, all steps whole, result ≥ 0 |
| B2 Negative numbers | Whole | a + (−b) or a − (−b), 1–20 | (−a) ± (−b) or (−a) × b, 1–12 | products and quotients with signs, factors 2–20, quotients exact | (−a) × (−b) − (−c) × d, numbers 2–15 |
| B3 Decimals | Dec 2 | a ± b, one decimal place each, 0.1–9.9 | a ± b with two decimal places, or × / ÷ 10, 100 | a × b, one decimal place each, 0.1–9.9 | a × b − c, one decimal place each, 0.1–9.9 |

### Fractions

| Article | Type | Easy | Medium | Hard | Pro |
|---|---|---|---|---|---|
| F1 Fractions ↔ decimals ↔ % | Dec 1 (percent) / Dec 3 (decimal) / Choice | halves, quarters, fifths, tenths → percent | eighths → percent or decimal | thirds, sixths, twelfths → percent (Dec 1) or decimal (Dec 3); or decimal → fraction (Choice of 4) | percent of a number using the table, e.g. 37.5 % of 320 (Whole), multiples chosen so the result is whole |
| F2 Comparing fractions | Choice: "a/b", "c/d", "Equal" | proper fractions, denominators 2–9, values differ by ≥ 0.1 | denominators 5–12, differ by 0.02–0.1 | denominators 7–20, differ by < 0.05, sometimes equal (equivalent fractions) | denominators 11–30, differ by < 0.02, sometimes equal |
| F3 The fraction trap | Choice | x from {0.25, 0.36, 0.49, 0.64, 0.81}: which is larger, x² or x? | same x: which is larger, √x or x? | x from {0.04 … 0.81} or {1.21, 1.44, 2.25, 4}: which is larger, x² or √x? | same x values: order x², x, √x from smallest to largest (Choice of 4 orderings) |

### Case interview

| Article | Type | Easy | Medium | Hard | Pro |
|---|---|---|---|---|---|
| C1 Successive % changes | Dec 1 (percent, can be negative) | two changes, ±10 % or ±20 % | two changes, multiples of 5 from 5 to 30, up or down | three changes, multiples of 5 from 5 to 30 | three changes, whole numbers 1–30, up or down |
| C2 Rule of 72 | Whole | doubling time, rate from {2, 3, 4, 6, 8, 9, 12} | doubling time, rate from {2, 3, 4, 6, 8, 9, 12, 18, 24, 36}, or tripling time with 114 and rate from {2, 3, 6} | value after n doubling periods, e.g. 10 bn at 8 % after 18 years = 40 bn, start 5–50 bn | years until the value is 4× or 8× (2 or 3 doubling periods), rates as in Medium |
| C3 Margin vs markup | Dec 1 (percent) | cost and price given (whole $, price − cost divides evenly into a clean %): margin or markup | convert using the table pairs (20↔25, 25↔33.3, 33.3↔50, 40↔66.7, 50↔100) | markup 10–150 % (multiples of 5) → margin | margin 10–60 % (multiples of 5) → markup |
| C4 Percentage change | Dec 1 (percent, can be negative) | old value 50, 100 or 200, change gives a whole % | old 2- or 3-digit value, change gives a whole % | any 2- or 3-digit old and new values | "After a fall of a %, what rise brings it back?", a from 5–50, multiples of 5 |
| C5 Weighted averages | Dec 1 (percent) | two segments, weights 50/50 or multiples of 10, values multiples of 10 | two segments, weights multiples of 10, values 5–50 | three segments, weights multiples of 10 adding up to 100 %, values 5–50 | two or three segments given as absolute sizes (e.g. 300 m and 200 m revenue), values 5–50 |
| C6 Break-even | Whole | fixed costs 1,000–10,000 (multiples of 1,000) and contribution margin 5–50 given directly, divides evenly | price and variable cost given, fixed costs up to 100,000, divides evenly | fixed costs up to 1,000,000, divides evenly | new break-even after a price change of ±5 %, ±10 % or ±20 %, divides evenly |
| C7 Large numbers | Choice of 4 | 1-digit × 1-digit coefficients, K × K or M × K | 2-digit × 1-digit coefficients, any K, M, B pair with a defined result | 3-digit × 2-digit coefficients, including B × K | divisions such as 15 T ÷ 300 M, coefficients chosen so the result is a whole number with a unit |

### Estimating & rounding

| Article | Type | Easy | Medium | Hard | Pro |
|---|---|---|---|---|---|
| E1 Rounding & estimating | Estimate (±10 %) | sum of two 3-digit numbers | sum or difference of two 4-digit numbers | product of two 2-digit numbers | product of a 3-digit and a 2-digit number, or a × b + c |
| E2 Compatible numbers | Estimate (±10 %) | 3-digit ÷ 1-digit | 4-digit ÷ 2-digit, close to an easy pair | 4-digit ÷ 2-digit | 5-digit ÷ 2-digit, or 2-digit × 2-digit near 50 or 100 |
| E3 Order of magnitude | Whole (number of digits) | 2-digit × 1-digit | 2-digit × 2-digit | 3-digit × 2- or 3-digit | 4-digit × 3- or 4-digit, or three factors |
| E4 Casting out nines | Whole (1–9) / Choice ("Correct", "Wrong") | digital root of a 2- or 3-digit number | digital root of a 4- or 5-digit number | "Is a × b = c correct?" with 2-digit factors; wrong results differ by an amount that is not a multiple of 9 | same with a 3-digit and a 2-digit factor |

Notes:
- Digital roots of multiples of 9 are 9.
- Rule-of-72 answers follow the rule (72 ÷ rate), not the exact compound-interest value.
- Percentages are typed without the "%" sign; it is accepted if typed.

---

## Open points
- None. Textbook mode now includes practice (decided 21 November 2026).
