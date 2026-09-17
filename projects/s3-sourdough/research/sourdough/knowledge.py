"""Curated knowledge base and question variations for sourdough bread baking.

Designed for micro-language models on microcontrollers (ESP32-S3).
Answers are factual, actionable, and strictly concise (< 60 tokens).
"""

from typing import List, Dict

CATEGORIES = [
    "starter_health",
    "bulk_fermentation",
    "hydration_shaping",
    "scoring_baking",
    "bakers_math",
]

# Each entry has:
# - category: topic
# - questions: list of diverse ways a user might ask this question
# - answer: canonical concise, expert answer
QA_ENTRIES: List[Dict] = [
    # 1. Starter Health & Maintenance
    {
        "category": "starter_health",
        "questions": [
            "Why is there liquid on top of my sourdough starter?",
            "There is a gray liquid on top of my starter. What is it?",
            "What is the dark liquid pooling on my sourdough starter?",
            "My starter has liquid on it, did it go bad?",
            "Why does my starter have a layer of water on top?",
        ],
        "answer": "That liquid is hooch, an alcohol byproduct indicating your starter has run out of food. Pour it off for a milder taste or stir it back in for extra tang, then feed your starter equal parts flour and water.",
    },
    {
        "category": "starter_health",
        "questions": [
            "My sourdough starter smells like acetone or nail polish remover.",
            "Why does my starter smell like vinegar or rubbing alcohol?",
            "My sourdough starter has a strong sharp chemical smell.",
            "Is it normal for a starter to smell like paint thinner?",
            "How do I fix a starter that smells like acetone?",
        ],
        "answer": "An acetone smell means your starter is hungry and producing excessive acetic acid. Discard down to a small seed (e.g. 20g) and feed it at a higher ratio, such as 1:2:2 or 1:5:5 with unbleached flour.",
    },
    {
        "category": "starter_health",
        "questions": [
            "My sourdough starter is not rising. What is wrong?",
            "Why is my starter sluggish and taking over 12 hours to double?",
            "How can I make my sourdough starter rise faster?",
            "My starter won't double after feeding.",
            "What causes a slow or weak sourdough starter?",
        ],
        "answer": "Sluggish starters are usually too cold or need whole grains. Keep your starter warm at 75°F to 80°F (24°C to 27°C) and incorporate 20% to 50% whole rye or whole wheat flour to provide essential micronutrients.",
    },
    {
        "category": "starter_health",
        "questions": [
            "How do I know if my sourdough starter has mold?",
            "Can mold grow on a sourdough starter?",
            "There is pink or orange streaks in my starter. Is it safe?",
            "What does bad mold look like on a starter?",
            "Can I scrape mold off the top of my starter?",
        ],
        "answer": "If you see fuzzy growth or pink or orange discoloration, toss the starter completely. Harmful mold spores penetrate the entire liquid jar. Sanitize the jar thoroughly and start a fresh batch.",
    },
    {
        "category": "starter_health",
        "questions": [
            "How do I store my sourdough starter in the refrigerator?",
            "Can I keep my starter in the fridge when not baking?",
            "How often do I feed a refrigerated sourdough starter?",
            "What is the best way to put starter on hold?",
            "How do I maintain my starter if I only bake on weekends?",
        ],
        "answer": "Feed your starter equal parts flour and water, let it rise for one hour to start fermenting, then seal loosely and refrigerate. Feed it once a week to keep the colony active and healthy.",
    },
    {
        "category": "starter_health",
        "questions": [
            "Does the float test work for sourdough starter?",
            "Why didn't my starter float even though it doubled in size?",
            "Should I always use the float test before baking?",
            "Is the float test accurate for levain readiness?",
            "How do I know when my starter is ready to bake without floating?",
        ],
        "answer": "The float test only measures trapped gas and often fails if stirred or made with heavy rye flour. A starter is ready when it doubles or triples in volume, shows a domed bubbly top, and smells pleasantly fruity.",
    },
    {
        "category": "starter_health",
        "questions": [
            "What is the standard feeding ratio for a sourdough starter?",
            "How much flour and water should I feed my starter?",
            "What does a 1:1:1 feeding ratio mean?",
            "What ratio should I use for sourdough starter maintenance?",
            "How much discard should I keep when feeding?",
        ],
        "answer": "A standard maintenance ratio is 1:1:1 by weight: equal parts starter seed, flour, and room temperature water. For long rises or hot rooms, use 1:2:2 or 1:5:5 to give the yeast more food.",
    },

    # 2. Bulk Fermentation
    {
        "category": "bulk_fermentation",
        "questions": [
            "How do I know when bulk fermentation is finished?",
            "How much should sourdough rise during bulk fermentation?",
            "When should I stop bulk fermentation and shape my loaf?",
            "What are the visual signs that bulk fermentation is complete?",
            "How do I know my sourdough dough is ready to shape?",
        ],
        "answer": "Bulk fermentation is complete when the dough is puffy, aerated, slightly domed with rounded edges, jiggles when shaken, and shows translucent bubbles under the skin. Look for a 30% to 50% volume rise at warm temps.",
    },
    {
        "category": "bulk_fermentation",
        "questions": [
            "What does under-fermented sourdough look like?",
            "How can I tell if my dough is under-proofed?",
            "Why is my sourdough loaf dense at the bottom with giant holes at the top?",
            "What causes fool's crumb in sourdough?",
            "Why did my sourdough bread turn out flat and heavy with tunnel holes?",
        ],
        "answer": "Dense crumb at the bottom with large tunneling holes at the top (fool's crumb) is the classic sign of under-fermentation. The yeast did not have enough time to aerate the entire dough matrix.",
    },
    {
        "category": "bulk_fermentation",
        "questions": [
            "What does over-fermented sourdough dough look like?",
            "How do I know if I over-proofed my sourdough?",
            "My sourdough dough turned into soup and won't hold a shape.",
            "Why is my dough sticky, flat, and tearing easily?",
            "Can I save over-proofed sourdough dough?",
        ],
        "answer": "Over-fermented dough collapses, smells strongly sour, tears easily, and turns sticky or soupy because acid has degraded the gluten network. Bake it immediately in a loaf tin or use it for focaccia.",
    },
    {
        "category": "bulk_fermentation",
        "questions": [
            "How do I perform the poke test on proofed dough?",
            "What is the poke test for sourdough?",
            "How do I know if my shaped sourdough is ready to bake using the finger dent test?",
            "What does the poke test tell you about bread dough?",
            "My dough sprang back immediately after poking it.",
        ],
        "answer": "Flour your finger and gently press 1/2 inch into the dough. If it springs back immediately, it is under-proofed. If it springs back slowly leaving a small indentation, it is ready. If it collapses, it is over-proofed.",
    },
    {
        "category": "bulk_fermentation",
        "questions": [
            "How many stretch and folds should I do during bulk fermentation?",
            "How often do you stretch and fold sourdough?",
            "Why do we stretch and fold sourdough dough?",
            "When should I stop doing stretch and folds?",
            "What is the interval between coil folds?",
        ],
        "answer": "Perform 3 to 4 sets of stretch and folds spaced 30 minutes apart during the first 2 hours of bulk fermentation. Then let the dough rest undisturbed for the remainder of bulk to build aeration.",
    },
    {
        "category": "bulk_fermentation",
        "questions": [
            "What is the ideal ambient temperature for sourdough bulk fermentation?",
            "How does room temperature affect sourdough rise time?",
            "Why is my sourdough taking 10 hours to rise?",
            "What is the best dough temperature for sourdough?",
            "Does cold temperature stop sourdough fermentation?",
        ],
        "answer": "The ideal dough temperature for sourdough bulk fermentation is 75°F to 80°F (24°C to 27°C), taking 4 to 6 hours. In cooler rooms (68°F / 20°C), bulk fermentation can easily take 8 to 12 hours.",
    },
    {
        "category": "bulk_fermentation",
        "questions": [
            "What is the windowpane test in bread baking?",
            "How do I check if gluten is developed in sourdough?",
            "How do I do the windowpane test?",
            "Why does my dough tear when I stretch it thin?",
            "When should my dough pass the windowpane test?",
        ],
        "answer": "With wet hands, gently stretch a small piece of dough in all directions. If you can stretch it thin enough to see light through without tearing, your gluten structure is sufficiently developed.",
    },

    # 3. Hydration & Shaping
    {
        "category": "hydration_shaping",
        "questions": [
            "My sourdough dough is too sticky to handle. What should I do?",
            "How do I work with sticky high-hydration sourdough dough?",
            "Why is my sourdough dough sticking to my hands and counter?",
            "Should I add more flour if my sourdough is sticky?",
            "How do you shape sticky sourdough dough?",
        ],
        "answer": "Wet your hands and bench knife with water instead of adding excess flour, which dries out the crumb. Use quick, confident motions and build surface tension during pre-shaping.",
    },
    {
        "category": "hydration_shaping",
        "questions": [
            "How do I prevent sourdough dough from sticking to the banneton basket?",
            "My sourdough bread stuck to the proofing basket and tore.",
            "What flour should I dust my banneton with?",
            "Does rice flour stop dough from sticking to bannetons?",
            "How do I flour a proofing basket so it never sticks?",
        ],
        "answer": "Dust your banneton with a 50/50 mix of rice flour and bread flour. Rice flour contains no gluten, does not absorb dough moisture, and ensures your loaf slides out cleanly every time.",
    },
    {
        "category": "hydration_shaping",
        "questions": [
            "Why is cold proofing in the fridge beneficial for sourdough?",
            "What does an overnight cold retard do for sourdough?",
            "Do I have to proof sourdough in the refrigerator?",
            "Can I leave sourdough in the fridge for 24 hours before baking?",
            "Why do bakers refrigerate dough overnight?",
        ],
        "answer": "A cold retard in the fridge (38°F / 3°C) for 12 to 24 hours develops complex lactic and acetic acid flavors, stiffens the dough for clean scoring, and produces a blistered crust.",
    },
    {
        "category": "hydration_shaping",
        "questions": [
            "What is autolyse and why is it important in sourdough?",
            "Should I autolyse my flour and water before adding starter?",
            "What does autolyse do for bread dough?",
            "How long should an autolyse rest last?",
            "Can I skip the autolyse step?",
        ],
        "answer": "Autolyse is resting flour and water together for 30 to 60 minutes before adding starter and salt. It fully hydrates the starches, starts enzymatic breakdown, and naturally builds gluten without kneading.",
    },
    {
        "category": "hydration_shaping",
        "questions": [
            "What hydration percentage should a beginner baker start with?",
            "What is a good hydration for beginner sourdough?",
            "Why is 80% hydration too high for new bakers?",
            "How much water should I use for my first sourdough loaf?",
            "Is 65% or 70% hydration easier to shape?",
        ],
        "answer": "Beginners should start with 65% to 70% hydration. This provides enough moisture for a tender, open crumb while keeping the dough manageable and easy to shape without spreading flat.",
    },

    # 4. Scoring, Baking & Crust
    {
        "category": "scoring_baking",
        "questions": [
            "Why didn't my sourdough bread develop an ear?",
            "How do I get a pronounced ear on my sourdough loaf?",
            "What angle should I score sourdough bread with a lame?",
            "Why does my sourdough score open flat without an ear?",
            "What causes an ear to form on sourdough?",
        ],
        "answer": "Hold your razor lame at a 30 to 45 degree shallow angle and make one swift cut 1/4 to 1/2 inch deep. An ear requires strong surface tension during shaping, proper proofing, and abundant oven steam.",
    },
    {
        "category": "scoring_baking",
        "questions": [
            "Why is steam necessary when baking sourdough bread?",
            "What happens if you bake sourdough without steam?",
            "Why do we bake sourdough inside a closed Dutch oven?",
            "How does steam affect oven spring and crust blisters?",
            "Can I bake good sourdough bread without a Dutch oven?",
        ],
        "answer": "Steam keeps the outer dough skin moist and flexible during the first 20 minutes, allowing maximum oven spring before the crust hardens. It also gelatinizes surface starches to create a crisp, blistered crust.",
    },
    {
        "category": "scoring_baking",
        "questions": [
            "Why is the inside of my sourdough loaf gummy or wet?",
            "What causes a gummy, sticky texture inside baked sourdough?",
            "My sourdough bread looks baked outside but is wet inside.",
            "How long should I wait before slicing sourdough bread?",
            "Did I slice my sourdough too early?",
        ],
        "answer": "A gummy crumb occurs when bread is sliced while still hot, or if under-baked. Let your loaf cool completely on a wire rack for at least 2 hours. Internal temperature should reach 205°F to 210°F (96°C to 99°C).",
    },
    {
        "category": "scoring_baking",
        "questions": [
            "Why is the bottom of my sourdough bread burnt or too hard?",
            "How do I prevent a burnt bottom crust in a Dutch oven?",
            "The bottom of my sourdough loaf burns before the top is brown.",
            "How to stop Dutch oven from scorching bread bottom?",
            "My sourdough bottom crust is black.",
        ],
        "answer": "Place an empty baking sheet or pizza stone on the oven rack directly beneath your Dutch oven to deflect direct radiant heat, or sprinkle cornmeal or coarse semolina under your parchment paper.",
    },
    {
        "category": "scoring_baking",
        "questions": [
            "What temperature and time should I bake sourdough at in a Dutch oven?",
            "How long do I bake sourdough covered vs uncovered?",
            "What oven temp is best for sourdough bread?",
            "When should I remove the Dutch oven lid when baking bread?",
            "How hot should the oven be for baking sourdough?",
        ],
        "answer": "Preheat your oven and Dutch oven to 450°F to 475°F (230°C to 245°C). Bake covered with the lid on for 20 minutes with trapped steam, then remove the lid and bake 20 to 25 minutes until deeply golden brown.",
    },
    {
        "category": "scoring_baking",
        "questions": [
            "Why is my sourdough crust pale and not browning?",
            "What causes a dull or pale sourdough crust?",
            "Why won't my sourdough bread brown in the oven?",
            "How do I get a golden dark brown blistered sourdough crust?",
            "Does over-proofing cause a pale crust?",
        ],
        "answer": "A pale crust is often caused by over-fermentation, where hungry yeast consumed all sugars needed for the Maillard reaction. It can also result from baking too cool or insufficient steam during the first bake phase.",
    },

    # 5. Baker's Math & Formulas
    {
        "category": "bakers_math",
        "questions": [
            "What is Baker's Percentage in bread baking?",
            "How does Baker's Math work for sourdough?",
            "Why is total flour always 100% in baker's percentages?",
            "How do I calculate ingredients using baker's math?",
            "What does 75% hydration mean in baker's percentage?",
        ],
        "answer": "Baker's percentage expresses every ingredient weight as a percentage of total flour weight, which is always 100%. For example, 75% hydration with 500g flour means 375g of water.",
    },
    {
        "category": "bakers_math",
        "questions": [
            "What is a standard recipe ratio for a sourdough loaf?",
            "What are the baseline percentages for an artisan sourdough loaf?",
            "How much starter and salt should I use for 500g of flour?",
            "What is the basic formula for classic sourdough bread?",
            "What is the standard sourdough ratio by baker's percentages?",
        ],
        "answer": "A standard artisan sourdough formula is 100% flour, 70% to 75% water, 20% active starter or levain, and 2% salt. For a 500g flour loaf: 350g water, 100g starter, and 10g salt.",
    },
    {
        "category": "bakers_math",
        "questions": [
            "Why is salt essential in sourdough bread?",
            "What happens if I forget to add salt to sourdough dough?",
            "Can I reduce or eliminate salt in sourdough bread?",
            "What role does salt play in gluten development?",
            "How much salt should be in sourdough bread?",
        ],
        "answer": "Salt tightens the gluten structure, regulates yeast fermentation rate, and provides essential flavor. Without salt (standard 2%), dough ferments too rapidly, turns sticky and slack, and tastes flat and insipid.",
    },
]
