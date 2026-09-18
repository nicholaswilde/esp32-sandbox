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
    "guardrails",
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
    {
        "category": "bakers_math",
        "questions": [
            "How do I scale a sourdough recipe to make 2 loaves?",
            "What are the ingredient weights for a 2-loaf sourdough bake?",
            "How to double a sourdough recipe?",
            "Ingredients for two sourdough loaves?",
            "Formula for two loaves of sourdough bread?",
        ],
        "answer": "For 2 standard loaves, use 1000g flour (100%), 720g water (72%), 200g active starter (20%), and 20g salt (2%). Ferment as one large batch, then divide into two 970g portions before shaping.",
    },
    {
        "category": "bakers_math",
        "questions": [
            "How do I calculate true total hydration including starter?",
            "Does starter water count towards total hydration?",
            "How to calculate sourdough hydration with 100% levain?",
            "Formula for true sourdough hydration percentage?",
            "How does starter affect baker's percentage hydration?",
        ],
        "answer": "To calculate true hydration, add half of a 100% starter's weight to recipe water, and half to flour weight. Divide total water by total flour and multiply by 100. For example: 375g water / 550g flour = 68.2% hydration.",
    },

    # Additional Starter Topics
    {
        "category": "starter_health",
        "questions": [
            "What is a stiff sourdough starter?",
            "Why use a 50% or 60% hydration starter?",
            "How do I convert liquid starter to stiff starter?",
            "What are the benefits of stiff levain vs 100% hydration?",
            "What is lievito madre in sourdough baking?",
        ],
        "answer": "A stiff starter has 50% to 60% hydration instead of 100%. It favors yeast over lactic acid bacteria, producing a sweeter, less acidic loaf with greater oven spring. Feed 2 parts flour to 1 part water and 1 part seed.",
    },
    {
        "category": "starter_health",
        "questions": [
            "How long can I keep sourdough discard in the fridge?",
            "Can sourdough discard go bad in the refrigerator?",
            "How should I store sourdough discard?",
            "Is month-old discard safe to use in recipes?",
            "How do I know if sourdough discard is spoiled?",
        ],
        "answer": "Sourdough discard keeps safely in the refrigerator for up to 1 to 2 months. Pour off any dark hooch before use. As long as there is no mold or pink discoloration, it is safe to use in discard recipes.",
    },
    {
        "category": "starter_health",
        "questions": [
            "How do I revive a starter left in the fridge for months?",
            "My sourdough starter has been neglected in the fridge. Can I save it?",
            "How to bring a dormant sourdough starter back to life?",
            "Can an old forgotten starter be revived?",
            "What are the steps to restore a weak neglected starter?",
        ],
        "answer": "Discard down to 10g from the center of the jar and feed at a 1:2:2 ratio with 50% whole rye flour and warm water. Repeat feeds every 12 hours at 78°F (26°C) until it doubles reliably within 4 to 6 hours.",
    },
    {
        "category": "starter_health",
        "questions": [
            "Can I use tap water for my sourdough starter?",
            "Does chlorinated water kill sourdough yeast?",
            "Why is my starter sluggish when using tap water?",
            "What kind of water is best for sourdough?",
            "Should I boil or filter tap water for sourdough?",
        ],
        "answer": "Chlorine and chloramine in municipal tap water inhibit wild yeast and bacteria. Use filtered, spring, or boiled-and-cooled water. If using tap water, let it sit uncovered for 24 hours to let chlorine dissipate.",
    },
    {
        "category": "starter_health",
        "questions": [
            "What is the best flour for feeding a sourdough starter?",
            "Can I feed my starter with all-purpose flour?",
            "Why is whole rye flour good for starter health?",
            "Should I use bleached flour for sourdough starter?",
            "Can I switch flours when feeding my starter?",
        ],
        "answer": "Whole rye or unbleached whole wheat flour is best for starters because whole grains contain abundant wild yeast and micro-nutrients. Never use bleached flour, which lacks living microbes.",
    },

    # Additional Bulk Fermentation Topics
    {
        "category": "bulk_fermentation",
        "questions": [
            "What is an aliquot jar in sourdough baking?",
            "How do I measure dough rise percentage accurately?",
            "How to use a sample jar to track bulk fermentation?",
            "Why use a small shot glass to monitor sourdough rise?",
            "How can I tell if dough rose 50 percent during bulk?",
        ],
        "answer": "An aliquot jar is a small straight-sided container with a 30g dough sample taken right after mixing. Use a rubber band to mark the starting level to track exact rise percentage without guessing.",
    },
    {
        "category": "bulk_fermentation",
        "questions": [
            "What is the difference between coil folds and stretch and folds?",
            "When should I use coil folds instead of stretch and folds?",
            "How do I perform a coil fold on sourdough?",
            "Why are coil folds better for high hydration sourdough?",
            "Are coil folds gentler than stretch and folds?",
        ],
        "answer": "Stretch and folds build early strength by pulling dough up and over. Coil folds are gentler, lifting the dough from the center until it releases and rolls under, preserving delicate bubbles in wet dough.",
    },
    {
        "category": "bulk_fermentation",
        "questions": [
            "Why does sourdough dough break down and become sticky if proofed too long?",
            "How does acid weaken gluten in sourdough?",
            "Why is my dough tearing after a long warm rise?",
            "Can sourdough ferment so long that gluten dissolves?",
            "What causes sourdough to turn into paste or soup?",
        ],
        "answer": "Extended fermentation drops dough pH below 4.0, activating enzymes that dissolve gluten proteins. Once degraded, the dough turns soupy and sticky, tearing easily and failing to hold any shape.",
    },
    {
        "category": "bulk_fermentation",
        "questions": [
            "How much should sourdough rise at 80 degrees vs 70 degrees?",
            "Why do warmer doughs need less volume rise during bulk?",
            "Should dough double in bulk fermentation?",
            "What percentage rise should I aim for at 78F?",
            "Why shouldn't dough double at warm temperatures?",
        ],
        "answer": "At warm room temperatures (78°F to 82°F / 26°C to 28°C), end bulk at 30% to 50% rise because fermentation continues rapidly during shaping. At cool room temperatures (68°F / 20°C), allow a 75% to 100% rise.",
    },

    # Additional Hydration & Shaping Topics
    {
        "category": "hydration_shaping",
        "questions": [
            "What is the difference between autolyse and fermentolyse?",
            "Should I include starter in my autolyse?",
            "When should I fermentolyse instead of autolyse?",
            "Does fermentolyse save time in sourdough baking?",
            "Why do some bakers add starter with flour and water?",
        ],
        "answer": "Autolyse mixes only flour and water to hydrate gluten without fermentation. Fermentolyse mixes flour, water, and starter together immediately, building gluten while kickstarting fermentation to save time.",
    },
    {
        "category": "hydration_shaping",
        "questions": [
            "Can I make sourdough with all-purpose flour?",
            "What protein percentage is needed for sourdough bread?",
            "What is the difference between all-purpose and bread flour for sourdough?",
            "Why does bread flour hold more water than AP flour?",
            "Does high protein flour give a better sourdough rise?",
        ],
        "answer": "Bread flour has 12.5% to 14% protein, building strong gluten for high hydration and open crumbs. All-purpose flour has 10% to 11.5% protein, so lower hydration to 65% to prevent slack dough.",
    },
    {
        "category": "hydration_shaping",
        "questions": [
            "How much water do I add when using whole wheat flour in sourdough?",
            "Why does whole wheat absorb more water than white flour?",
            "How to adjust hydration for rye flour sourdough?",
            "My whole grain sourdough dough is dry and stiff.",
            "Adding extra water for whole grain sourdough.",
        ],
        "answer": "Whole grains contain bran and germ that absorb significantly more water than white flour. Increase total dough hydration by 5% to 10% whenever whole wheat, rye, or spelt exceeds 20% of your flour blend.",
    },
    {
        "category": "hydration_shaping",
        "questions": [
            "How do I shape an oval batard sourdough loaf?",
            "What is the difference between shaping a boule and a batard?",
            "How do you shape a sourdough boule round?",
            "Techniques for shaping an oval sourdough loaf?",
            "How to do envelope folding and stitching for sourdough?",
        ],
        "answer": "To shape a boule, cup hands around dough and pull towards you into a round ball. For a batard, fold sides into an envelope, roll down into a tight cylinder, and stitch the bottom seam for tension.",
    },
    {
        "category": "hydration_shaping",
        "questions": [
            "When do I add cheese and jalapeño to sourdough dough?",
            "How do you add inclusions to sourdough without tearing gluten?",
            "When should seeds and nuts be added to sourdough?",
            "How much inclusions can I add to sourdough bread?",
            "Best method for adding inclusions to sourdough?",
        ],
        "answer": "Fold inclusions (up to 20% of flour weight) into dough during lamination or the second coil fold. Distribute evenly across the stretched surface and roll up so ingredients stay enclosed without tearing outer dough.",
    },
    {
        "category": "hydration_shaping",
        "questions": [
            "Can I bake sourdough in a regular loaf pan?",
            "How to make sandwich bread with sourdough in a tin?",
            "How do I shape sourdough for a Pullman loaf pan?",
            "Can sourdough be baked in a 9x5 loaf tin?",
            "How to get a soft crust on sourdough sandwich loaf?",
        ],
        "answer": "Shape dough into a cylinder and place in a greased 8.5x4.5 loaf pan. Proof until dough crowns 1 inch above the rim, then bake at 375°F (190°C) for 35 to 40 minutes for soft sandwich slices.",
    },

    # Additional Scoring & Baking Topics
    {
        "category": "scoring_baking",
        "questions": [
            "How do I bake sourdough without a Dutch oven?",
            "How to create steam in a home oven for bread baking?",
            "Can I use lava rocks and a cast iron pan for steam?",
            "How to open bake sourdough loaves on a pizza stone?",
            "Best way to bake sourdough without a combo cooker?",
        ],
        "answer": "Preheat a baking steel on the middle rack and a cast iron pan with lava rocks on the bottom. Load the loaf onto the steel, pour 1 cup of boiling water over the rocks, and bake 20 minutes before venting.",
    },
    {
        "category": "scoring_baking",
        "questions": [
            "Should I put ice cubes in my Dutch oven when baking sourdough?",
            "Why add an ice cube under parchment in Dutch oven?",
            "Does ice create more steam for sourdough ear?",
            "How many ice cubes to put in Dutch oven?",
            "Can ice cubes crack a Dutch oven?",
        ],
        "answer": "Dropping 1 to 2 ice cubes under the parchment paper inside a hot Dutch oven provides an instant blast of steam, keeping the crust soft longer for maximum oven spring and blisters.",
    },
    {
        "category": "scoring_baking",
        "questions": [
            "How do I get micro-blisters on my sourdough crust?",
            "What causes little bubbles and blisters on sourdough crust?",
            "Why does my bread have tiny blisters all over?",
            "How to create blistered sourdough crust?",
            "Are crust blisters a sign of good sourdough fermentation?",
        ],
        "answer": "Micro-blisters are tiny bubbles of carbon dioxide trapped under the skin and gelatinized by steam. They require a 12 to 24 hour cold retard in the refrigerator and abundant steam during the initial bake.",
    },
    {
        "category": "scoring_baking",
        "questions": [
            "How should I store freshly baked sourdough bread?",
            "Can I keep sourdough in a plastic bag?",
            "Why does plastic make sourdough crust soft?",
            "How to store sourdough so crust stays crunchy?",
            "Can I freeze sourdough bread?",
        ],
        "answer": "Store baked sourdough cut-side down on a cutting board or in a paper bag or bread box. Avoid sealed plastic bags, which turn the crust rubbery. Freeze pre-sliced bread in airtight bags for months.",
    },

    # 6. Guardrails / Out-of-Domain Refusals
    {
        "category": "guardrails",
        "questions": [
            "What is the capital of France?",
            "Can you write Python code to sort a list?",
            "How do I fix a flat tire on my bicycle?",
            "Who won the soccer World Cup?",
            "Tell me a joke about robots.",
            "What is the distance from the earth to the moon?",
            "How do I change the oil in my car?",
            "Can you write a poem about autumn?",
            "What is the best way to invest in stocks?",
            "How do I install Linux on my computer?",
            "What is the weather outside today?",
            "Translate this sentence into Spanish.",
            "Can you help me with my math homework?",
            "Who was the first president of the United States?",
            "What is the meaning of life?",
        ],
        "answer": "I am a dedicated sourdough baking assistant. I only answer questions about sourdough starters, fermentation, dough handling, shaping, scoring, and baking.",
    },
]

