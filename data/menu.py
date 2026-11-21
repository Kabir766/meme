"""Authoritative local menu catalog for Desi Bites."""

from __future__ import annotations

from dataclasses import dataclass, field
from difflib import get_close_matches
from typing import Literal

DietaryType = Literal["Veg", "Non-Veg"]

CATEGORIES: list[str] = [
    "Starters",
    "Main Course",
    "Breads",
    "Rice and Biryani",
    "Snacks",
    "Desserts",
    "Beverages",
]

DIETARY_TYPES: list[str] = ["Veg", "Non-Veg"]

SPICE_LEVELS: list[str] = ["Mild", "Medium", "Spicy"]


@dataclass(frozen=True)
class MenuItem:
    """Represents a single dish on the Desi Bites menu."""

    id: str
    name: str
    category: str
    dietary: DietaryType
    price_inr: int
    description: str
    ingredients: list[str]
    spice_level: str
    customizable_spice: bool = True
    customizations: list[str] = field(default_factory=list)
    prep_time_mins: int = 18
    featured: bool = False
    todays_special: bool = False
    aliases: list[str] = field(default_factory=list)
    image_path: str | None = None


MENU_ITEMS: list[MenuItem] = [
    # =========================
    # STARTERS
    # =========================
    MenuItem(
        id="veg-paneer-tikka-angara",
        name="Paneer Tikka Angara",
        category="Starters",
        dietary="Veg",
        price_inr=289,
        description="Charcoal-roasted cottage cheese marinated in hung curd, Kashmiri chili, and smoked kasuri methi, served with mint chutney.",
        ingredients=["paneer", "hung curd", "Kashmiri chili", "bell peppers", "red onion", "kasuri methi", "mint chutney"],
        spice_level="Medium",
        customizable_spice=True,
        customizations=["Extra Mint Chutney", "No Onion", "Charred Extra", "Jain Style (No Onion/Garlic)"],
        prep_time_mins=16,
        featured=True,
        aliases=["paneer tikka", "angara paneer"],
        image_path="assets/images/veg_paneer_tikka.jpg",
    ),
    MenuItem(
        id="veg-hara-bhara-kebab",
        name="Hara Bhara Kebab",
        category="Starters",
        dietary="Veg",
        price_inr=229,
        description="Pan-seared spinach, green pea, and roasted chana patties stuffed with spiced cashew crumble.",
        ingredients=["spinach", "green peas", "potato", "roasted chana", "cashew", "ginger", "green chili"],
        spice_level="Mild",
        customizable_spice=True,
        customizations=["Extra Mint Chutney", "No Cashew", "Crispy Seared"],
        prep_time_mins=14,
        aliases=["hara bhara", "veg kebab"],
    ),
    MenuItem(
        id="veg-dahi-ke-sholey",
        name="Dahi Ke Sholey",
        category="Starters",
        dietary="Veg",
        price_inr=249,
        description="Crisp golden bread rolls filled with spiced hung curd, grated paneer, bell peppers, and fresh coriander.",
        ingredients=["hung curd", "paneer", "bell peppers", "coriander", "black pepper", "bread"],
        spice_level="Mild",
        customizable_spice=True,
        customizations=["Extra Tamarind Dip", "Extra Mint Chutney"],
        prep_time_mins=15,
        todays_special=True,
        aliases=["dahi sholey", "curd rolls"],
    ),
    MenuItem(
        id="veg-crispy-lotus-stem",
        name="Crispy Lotus Stem Chaat",
        category="Starters",
        dietary="Veg",
        price_inr=259,
        description="Wok-tossed crunchy lotus stem glazed with tamarind, roasted cumin, chili oil, and toasted sesame.",
        ingredients=["lotus stem", "tamarind glaze", "chili oil", "cumin", "sesame", "scallions"],
        spice_level="Medium",
        customizable_spice=True,
        customizations=["Less Sweet Glaze", "No Sesame", "Extra Crispy"],
        prep_time_mins=15,
        aliases=["lotus stem", "crispy kamal kakdi"],
    ),
    MenuItem(
        id="nonveg-tandoori-murgh-tikka",
        name="Tandoori Murgh Tikka",
        category="Starters",
        dietary="Non-Veg",
        price_inr=339,
        description="Boneless chicken thighs marinated overnight in smoked yogurt, ginger-garlic, and tandoori spices, flame-grilled to perfection.",
        ingredients=["boneless chicken", "yogurt", "ginger", "garlic", "Kashmiri chili", "mustard oil", "chaat masala"],
        spice_level="Medium",
        customizable_spice=True,
        customizations=["Extra Mint Chutney", "Butter Basted", "Extra Charred"],
        prep_time_mins=18,
        featured=True,
        aliases=["chicken tikka", "murgh tikka"],
    ),
    MenuItem(
        id="nonveg-amritsari-fish-fry",
        name="Amritsari Ajwaini Fish",
        category="Starters",
        dietary="Non-Veg",
        price_inr=369,
        description="Crisp gram-flour battered river sole fillets infused with carom seeds, lemon, and yellow chili, served with pickled radish.",
        ingredients=["fish fillet", "besan (gram flour)", "ajwain (carom seeds)", "lemon juice", "turmeric", "garlic"],
        spice_level="Medium",
        customizable_spice=True,
        customizations=["Extra Lemon Wedges", "Extra Tartar Mint Dip"],
        prep_time_mins=16,
        todays_special=True,
        aliases=["amritsari fish", "fish fry"],
    ),
    MenuItem(
        id="nonveg-lamb-seekh-kebab",
        name="Old Delhi Lamb Seekh",
        category="Starters",
        dietary="Non-Veg",
        price_inr=389,
        description="Hand-minced lamb skewers spiced with royal cumin, mint, green chili, and caramelized shallots, cooked in the clay tandoor.",
        ingredients=["minced lamb", "mint", "coriander", "shallots", "garam masala", "ginger", "ghee"],
        spice_level="Spicy",
        customizable_spice=True,
        customizations=["Extra Onion Rings", "Less Ghee", "Extra Mint Chutney"],
        prep_time_mins=20,
        aliases=["seekh kebab", "lamb seekh", "mutton seekh"],
    ),
    MenuItem(
        id="nonveg-pepper-chicken-65",
        name="Curry Leaf Chicken 65",
        category="Starters",
        dietary="Non-Veg",
        price_inr=319,
        description="Southern-style crisp chicken morsels tempered with crackling curry leaves, crushed black pepper, and garlic.",
        ingredients=["chicken", "curry leaves", "black pepper", "garlic", "rice flour", "yogurt", "red chili"],
        spice_level="Spicy",
        customizable_spice=True,
        customizations=["Extra Curry Leaves", "Dry Style", "Semi-Gravy"],
        prep_time_mins=15,
        aliases=["chicken 65", "pepper chicken"],
    ),

    # =========================
    # MAIN COURSE
    # =========================
    MenuItem(
        id="veg-paneer-tikka-masala",
        name="Paneer Tikka Masala",
        category="Main Course",
        dietary="Veg",
        price_inr=329,
        description="Smoky tandoori paneer cubes simmered in a rich, spiced tomato-cashew gravy finished with cream and kasuri methi.",
        ingredients=["paneer", "tomatoes", "cashews", "cream", "butter", "kasuri methi", "garam masala"],
        spice_level="Medium",
        customizable_spice=True,
        customizations=["Extra Paneer", "Less Oil/Butter", "No Cream", "Extra Gravy"],
        prep_time_mins=20,
        featured=True,
        aliases=["paneer masala", "ptm"],
        image_path="assets/images/veg_paneer_tikka.jpg",
    ),
    MenuItem(
        id="veg-dal-makhani",
        name="24-Hour Dal Makhani",
        category="Main Course",
        dietary="Veg",
        price_inr=279,
        description="Whole black urad lentils slow-simmered overnight over charcoal with plum tomatoes, white butter, and fresh cream.",
        ingredients=["black urad dal", "rajma", "tomato puree", "white butter", "cream", "ginger", "fenugreek"],
        spice_level="Mild",
        customizable_spice=True,
        customizations=["Extra Butter", "Less Cream", "No Garlic"],
        prep_time_mins=15,
        featured=True,
        todays_special=True,
        aliases=["dal makhani", "black dal"],
    ),
    MenuItem(
        id="veg-palak-paneer",
        name="Lasooni Palak Paneer",
        category="Main Course",
        dietary="Veg",
        price_inr=309,
        description="Silky baby spinach puree tempered with golden roasted garlic, cumin, and soft cubes of fresh cottage cheese.",
        ingredients=["spinach", "paneer", "garlic", "cumin", "onion", "green chili", "cream"],
        spice_level="Mild",
        customizable_spice=True,
        customizations=["Extra Roasted Garlic", "No Cream", "Less Oil"],
        prep_time_mins=18,
        aliases=["palak paneer", "spinach paneer"],
    ),
    MenuItem(
        id="veg-kadai-subz",
        name="Kadai Subz Miloni",
        category="Main Course",
        dietary="Veg",
        price_inr=269,
        description="Seasonal garden vegetables and bell peppers tossed in freshly pounded coriander-red chili kadai masala.",
        ingredients=["carrot", "beans", "cauliflower", "bell peppers", "paneer", "coriander seeds", "tomatoes"],
        spice_level="Medium",
        customizable_spice=True,
        customizations=["Extra Spicy Kadai", "Less Oil", "No Onion/No Garlic"],
        prep_time_mins=18,
        aliases=["kadai veg", "mix veg", "kadai subz"],
    ),
    MenuItem(
        id="veg-malai-kofta",
        name="Saffron Malai Kofta",
        category="Main Course",
        dietary="Veg",
        price_inr=319,
        description="Melt-in-mouth paneer and potato dumplings stuffed with pistachio & raisin, served in velvety saffron cashew korma.",
        ingredients=["paneer", "potato", "cashews", "saffron", "cardamom", "cream", "pistachio"],
        spice_level="Mild",
        customizable_spice=False,
        customizations=["Gravy Packed Separately", "No Raisins"],
        prep_time_mins=22,
        aliases=["malai kofta", "kofta"],
    ),
    MenuItem(
        id="nonveg-butter-chicken",
        name="Old Delhi Butter Chicken",
        category="Main Course",
        dietary="Non-Veg",
        price_inr=379,
        description="Char-grilled chicken tikka folded into a silky, smoky tomato-butter makhani sauce scented with fenugreek.",
        ingredients=["chicken tikka", "plum tomatoes", "butter", "cream", "cashews", "kasuri methi", "ginger"],
        spice_level="Mild",
        customizable_spice=True,
        customizations=["Boneless", "Extra Butter", "Less Sweet / Spicier", "Extra Gravy"],
        prep_time_mins=20,
        featured=True,
        aliases=["butter chicken", "murgh makhani"],
        image_path="assets/images/desi_bites_hero.jpg",
    ),
    MenuItem(
        id="nonveg-kashmiri-rogan-josh",
        name="Kashmiri Mutton Rogan Josh",
        category="Main Course",
        dietary="Non-Veg",
        price_inr=449,
        description="Succulent slow-braised lamb cuts in an aromatic Kashmiri chili, fennel, dry ginger, and cardamom gravy.",
        ingredients=["bone-in mutton", "Kashmiri red chili", "fennel powder", "dry ginger", "yogurt", "cardamom", "ghee"],
        spice_level="Medium",
        customizable_spice=True,
        customizations=["Extra Gravy", "Less Ghee", "Make It Spicy"],
        prep_time_mins=25,
        todays_special=True,
        aliases=["rogan josh", "mutton rogan josh", "lamb curry"],
    ),
    MenuItem(
        id="nonveg-chicken-tikka-lababdar",
        name="Chicken Tikka Lababdar",
        category="Main Course",
        dietary="Non-Veg",
        price_inr=369,
        description="Tandoori chicken morsels cooked in a robust onion-tomato masala enriched with grated paneer and roasted spices.",
        ingredients=["chicken tikka", "onion", "tomato", "capsicum", "cream", "ginger juliennes", "coriander"],
        spice_level="Medium",
        customizable_spice=True,
        customizations=["Extra Gravy", "Less Cream", "Extra Ginger Juliennes"],
        prep_time_mins=20,
        aliases=["chicken lababdar", "lababdar"],
    ),
    MenuItem(
        id="nonveg-malabar-prawn-curry",
        name="Malabar Coconut Prawn Curry",
        category="Main Course",
        dietary="Non-Veg",
        price_inr=459,
        description="Jumbo prawns gently poached in roasted coconut milk, Malabar tamarind, mustard seeds, and fresh curry leaves.",
        ingredients=["tiger prawns", "coconut milk", "curry leaves", "Malabar tamarind", "shallots", "turmeric"],
        spice_level="Medium",
        customizable_spice=True,
        customizations=["Extra Curry Leaves", "Mild Coconut Forward", "Spicy Pepper Finish"],
        prep_time_mins=20,
        aliases=["prawn curry", "malabar prawns"],
    ),

    # =========================
    # BREADS
    # =========================
    MenuItem(
        id="veg-garlic-butter-naan",
        name="Garlic Butter Naan",
        category="Breads",
        dietary="Veg",
        price_inr=79,
        description="Pillowy leavened clay-oven flatbread blistered in the tandoor and brushed with roasted garlic and salted butter.",
        ingredients=["refined flour", "yogurt", "roasted garlic", "butter", "coriander"],
        spice_level="Mild",
        customizable_spice=False,
        customizations=["Extra Garlic", "Less Butter", "Crisp Baked"],
        prep_time_mins=8,
        featured=True,
        aliases=["garlic naan", "butter garlic naan"],
    ),
    MenuItem(
        id="veg-butter-naan",
        name="Classic Butter Naan",
        category="Breads",
        dietary="Veg",
        price_inr=65,
        description="Soft, charred tandoor-baked naan finished with melted cultured butter.",
        ingredients=["refined flour", "yogurt", "milk", "butter"],
        spice_level="Mild",
        customizable_spice=False,
        customizations=["No Butter (Plain Naan)", "Extra Crisp"],
        prep_time_mins=8,
        aliases=["butter naan", "naan", "plain naan"],
    ),
    MenuItem(
        id="veg-tandoori-roti",
        name="Whole Wheat Tandoori Roti",
        category="Breads",
        dietary="Veg",
        price_inr=49,
        description="Traditional 100% whole wheat flatbread slapped onto the hot clay tandoor wall for a smoky, rustic bite.",
        ingredients=["whole wheat flour", "water", "salt", "optional butter"],
        spice_level="Mild",
        customizable_spice=False,
        customizations=["With Butter", "Plain (No Butter)", "Crisp Kadak"],
        prep_time_mins=7,
        aliases=["tandoori roti", "roti", "butter roti"],
    ),
    MenuItem(
        id="veg-laccha-paratha",
        name="Flaky Laccha Paratha",
        category="Breads",
        dietary="Veg",
        price_inr=69,
        description="Multi-layered whole wheat spiral paratha brushed with desi ghee and baked until flaky and golden.",
        ingredients=["whole wheat flour", "desi ghee", "ajwain", "salt"],
        spice_level="Mild",
        customizable_spice=False,
        customizations=["Mint Pudina Dusting", "Red Chili Dusting", "Less Ghee"],
        prep_time_mins=10,
        aliases=["laccha paratha", "paratha"],
    ),
    MenuItem(
        id="veg-truffle-cheese-kulcha",
        name="Chili Cheese Kulcha",
        category="Breads",
        dietary="Veg",
        price_inr=119,
        description="Stuffed tandoori kulcha oozing aged cheddar, mozzarella, green chili, and caramelized onion.",
        ingredients=["flour", "cheddar", "mozzarella", "green chili", "onion", "butter"],
        spice_level="Medium",
        customizable_spice=True,
        customizations=["No Green Chili", "Extra Cheese", "No Onion"],
        prep_time_mins=12,
        aliases=["cheese kulcha", "kulcha"],
    ),

    # =========================
    # RICE AND BIRYANI
    # =========================
    MenuItem(
        id="veg-subz-dum-biryani",
        name="Nizami Subz Dum Biryani",
        category="Rice and Biryani",
        dietary="Veg",
        price_inr=299,
        description="Long-grain aged basmati layered with spiced seasonal vegetables, saffron milk, rose water, and crispy birista; served with burhani raita.",
        ingredients=["aged basmati rice", "mixed vegetables", "saffron", "mint", "fried onions", "yogurt raita", "whole spices"],
        spice_level="Medium",
        customizable_spice=True,
        customizations=["Extra Raita", "Less Ghee", "No Onion"],
        prep_time_mins=22,
        aliases=["veg biryani", "subz biryani"],
    ),
    MenuItem(
        id="veg-paneer-tikka-biryani",
        name="Smoked Paneer Tikka Biryani",
        category="Rice and Biryani",
        dietary="Veg",
        price_inr=329,
        description="Charred paneer tikka pieces slow-steamed with fragrant saffron basmati, caramelized onions, and mint; served with raita.",
        ingredients=["basmati rice", "tandoori paneer", "saffron", "mint", "fried onions", "cashews", "raita"],
        spice_level="Medium",
        customizable_spice=True,
        customizations=["Extra Raita", "No Cashews", "Extra Spicy Mirchi Salan"],
        prep_time_mins=22,
        todays_special=True,
        aliases=["paneer biryani"],
    ),
    MenuItem(
        id="veg-jeera-pulao",
        name="Ghee-Tempered Jeera Rice",
        category="Rice and Biryani",
        dietary="Veg",
        price_inr=189,
        description="Fluffy aged basmati rice tempered with crackling cumin seeds, bay leaf, and fresh coriander.",
        ingredients=["basmati rice", "cumin seeds", "ghee", "bay leaf", "coriander"],
        spice_level="Mild",
        customizable_spice=False,
        customizations=["Steamed Plain Rice Instead", "Less Ghee"],
        prep_time_mins=12,
        aliases=["jeera rice", "steamed rice", "rice"],
    ),
    MenuItem(
        id="nonveg-hyderabadi-chicken-biryani",
        name="Hyderabadi Chicken Dum Biryani",
        category="Rice and Biryani",
        dietary="Non-Veg",
        price_inr=389,
        description="Authentic kacchi-style dum biryani with spiced marinated chicken, saffron basmati, crisp birista, and mint; served with mirchi ka salan & raita.",
        ingredients=["chicken", "aged basmati rice", "saffron", "mint", "fried onions", "yogurt", "ghee", "raita"],
        spice_level="Spicy",
        customizable_spice=True,
        customizations=["Boneless Chicken", "Extra Raita", "Extra Salan", "Medium Spice"],
        prep_time_mins=25,
        featured=True,
        todays_special=True,
        aliases=["chicken biryani", "hyderabadi biryani", "dum biryani"],
        image_path="assets/images/nonveg_biryani_handi.jpg",
    ),
    MenuItem(
        id="nonveg-lucknowi-mutton-biryani",
        name="Lucknowi Mutton Dum Biryani",
        category="Rice and Biryani",
        dietary="Non-Veg",
        price_inr=469,
        description="Delicate Awadhi-style slow-cooked goat meat layered with rose-infused basmati, saffron, and aromatic yakhni stock; served with raita.",
        ingredients=["mutton", "basmati rice", "saffron", "kewra water", "ghee", "caramelized onions", "raita"],
        spice_level="Medium",
        customizable_spice=True,
        customizations=["Extra Raita", "Less Ghee"],
        prep_time_mins=28,
        aliases=["mutton biryani", "lamb biryani", "lucknowi biryani"],
    ),

    # =========================
    # SNACKS
    # =========================
    MenuItem(
        id="veg-punjabi-samosa-duo",
        name="Punjabi Samosa Duo",
        category="Snacks",
        dietary="Veg",
        price_inr=119,
        description="Two crisp, flaky pastry triangles stuffed with spiced potatoes, green peas, and roasted coriander; served with tamarind & mint chutneys.",
        ingredients=["refined flour", "potatoes", "green peas", "coriander seeds", "amchur", "tamarind chutney"],
        spice_level="Medium",
        customizable_spice=True,
        customizations=["Extra Chutneys", "Crushed Chaat Style with Curd"],
        prep_time_mins=10,
        aliases=["samosa", "veg samosa"],
    ),
    MenuItem(
        id="veg-mumbai-pav-bhaji",
        name="Mumbai Masala Pav Bhaji",
        category="Snacks",
        dietary="Veg",
        price_inr=199,
        description="Rich buttered spiced vegetable mash simmered on an iron tawa, served with two toasted butter pav buns, chopped onion, and lime.",
        ingredients=["potatoes", "cauliflower", "peas", "tomatoes", "pav bhaji masala", "butter", "pav buns"],
        spice_level="Medium",
        customizable_spice=True,
        customizations=["Extra Butter Pav (1 pc)", "Extra Cheese Grating", "No Onion"],
        prep_time_mins=14,
        featured=True,
        aliases=["pav bhaji", "mumbai pav bhaji"],
    ),
    MenuItem(
        id="veg-old-delhi-aloo-chaat",
        name="Old Delhi Kurkure Aloo Chaat",
        category="Snacks",
        dietary="Veg",
        price_inr=149,
        description="Crisp fried baby potatoes tossed in roasted cumin, black salt, pomegranate, sweet tamarind, and tangy mint chutney.",
        ingredients=["potatoes", "pomegranate", "tamarind chutney", "mint chutney", "chaat masala", "sev"],
        spice_level="Medium",
        customizable_spice=True,
        customizations=["Add Sweet Curd", "Extra Sev", "No Onion"],
        prep_time_mins=12,
        aliases=["aloo chaat", "chaat"],
    ),
    MenuItem(
        id="nonveg-keema-samosa",
        name="Spiced Lamb Keema Samosa",
        category="Snacks",
        dietary="Non-Veg",
        price_inr=189,
        description="Two crisp cocktail samosas filled with slow-cooked minced lamb, green peas, mint, and crushed black pepper.",
        ingredients=["minced lamb", "pastry", "green peas", "mint", "ginger", "garam masala"],
        spice_level="Medium",
        customizable_spice=True,
        customizations=["Extra Mint Chutney", "Extra Spicy"],
        prep_time_mins=12,
        aliases=["keema samosa", "mutton samosa"],
    ),
    MenuItem(
        id="nonveg-chicken-kathi-roll",
        name="Kolkata Chicken Tikka Kathi Roll",
        category="Snacks",
        dietary="Non-Veg",
        price_inr=229,
        description="Flaky egg-washed paratha rolled around smoky chicken tikka, pickled onions, green chili, and mint chutney.",
        ingredients=["chicken tikka", "laccha paratha", "egg", "pickled onion", "mint chutney", "chaat masala"],
        spice_level="Medium",
        customizable_spice=True,
        customizations=["No Egg Wash", "Extra Mint Chutney", "No Onion"],
        prep_time_mins=14,
        aliases=["chicken roll", "kathi roll"],
    ),

    # =========================
    # DESSERTS
    # =========================
    MenuItem(
        id="veg-saffron-gulab-jamun",
        name="Saffron Gulab Jamun (2 pcs)",
        category="Desserts",
        dietary="Veg",
        price_inr=139,
        description="Warm, melt-in-mouth khoya dumplings soaked in saffron-cardamom rose syrup and finished with slivered pistachios.",
        ingredients=["khoya (milk solids)", "saffron", "cardamom", "rose water", "sugar syrup", "pistachio"],
        spice_level="Sweet",
        customizable_spice=False,
        customizations=["Warm Syrup Extra", "No Nuts"],
        prep_time_mins=8,
        featured=True,
        aliases=["gulab jamun", "jamun"],
        image_path="assets/images/dessert_chai_duo.jpg",
    ),
    MenuItem(
        id="veg-pistachio-rasmalai",
        name="Kesar Pistachio Rasmalai",
        category="Desserts",
        dietary="Veg",
        price_inr=169,
        description="Chilled delicate cottage cheese medallions steeped in saffron-infused thickened milk with roasted almonds and pistachios.",
        ingredients=["chenna (paneer)", "milk", "saffron", "cardamom", "pistachio", "almonds"],
        spice_level="Sweet",
        customizable_spice=False,
        customizations=["Less Sweet", "No Nuts"],
        prep_time_mins=6,
        aliases=["rasmalai", "kesar rasmalai"],
    ),
    MenuItem(
        id="veg-moong-dal-halwa",
        name="Warm Moong Dal Halwa",
        category="Desserts",
        dietary="Veg",
        price_inr=179,
        description="Slow-roasted split yellow lentil fudge cooked in pure desi ghee, saffron milk, and toasted cashews.",
        ingredients=["yellow moong dal", "desi ghee", "milk", "saffron", "sugar", "cashews", "cardamom"],
        spice_level="Sweet",
        customizable_spice=False,
        customizations=["No Nuts", "Served Extra Hot"],
        prep_time_mins=10,
        todays_special=True,
        aliases=["moong dal halwa", "halwa"],
    ),

    # =========================
    # BEVERAGES
    # =========================
    MenuItem(
        id="veg-kulhad-masala-chai",
        name="Kulhad Adrak Masala Chai",
        category="Beverages",
        dietary="Veg",
        price_inr=79,
        description="Assam CTC tea brewed with crushed fresh ginger, green cardamom, cinnamon, and whole milk, packed piping hot.",
        ingredients=["Assam black tea", "milk", "ginger", "green cardamom", "cinnamon", "sugar"],
        spice_level="Mild",
        customizable_spice=False,
        customizations=["Less Sugar", "Sugar-Free (On Side)", "Extra Ginger"],
        prep_time_mins=6,
        featured=True,
        aliases=["masala chai", "chai", "tea"],
        image_path="assets/images/dessert_chai_duo.jpg",
    ),
    MenuItem(
        id="veg-alphonso-mango-lassi",
        name="Alphonso Mango Lassi",
        category="Beverages",
        dietary="Veg",
        price_inr=149,
        description="Velvety churned probiotic yogurt blended with sweet Ratnagiri Alphonso mango pulp and a pinch of cardamom.",
        ingredients=["yogurt", "Alphonso mango pulp", "cardamom", "sugar", "pistachio garnish"],
        spice_level="Refreshing",
        customizable_spice=False,
        customizations=["Less Sugar", "No Nuts", "No Ice"],
        prep_time_mins=5,
        featured=True,
        aliases=["mango lassi", "lassi"],
    ),
    MenuItem(
        id="veg-nimbu-shikanji",
        name="Old Delhi Masala Shikanji",
        category="Beverages",
        dietary="Veg",
        price_inr=99,
        description="Sparkling chilled fresh lime cooler spiced with roasted cumin, black salt, mint leaves, and a hint of ginger.",
        ingredients=["fresh lime", "sparkling water", "black salt", "roasted cumin", "mint", "sugar"],
        spice_level="Refreshing",
        customizable_spice=False,
        customizations=["Sweet & Salty", "Salty Only (Zero Sugar)", "No Ice"],
        prep_time_mins=5,
        aliases=["shikanji", "masala soda", "nimbu pani"],
    ),
    MenuItem(
        id="veg-filter-kaapi",
        name="Madras Brass Filter Kaapi",
        category="Beverages",
        dietary="Veg",
        price_inr=89,
        description="Authentic Chikmagalur Arabica-chicory decoction frothed with steamed farm milk.",
        ingredients=["filter coffee decoction", "steamed milk", "sugar"],
        spice_level="Refreshing",
        customizable_spice=False,
        customizations=["Less Sugar", "Sugar-Free", "Strong Decoction"],
        prep_time_mins=6,
        aliases=["filter coffee", "kaapi", "coffee"],
    ),
]

_ITEMS_BY_ID: dict[str, MenuItem] = {item.id: item for item in MENU_ITEMS}


def get_all_menu_items() -> list[MenuItem]:
    """Return all menu items in catalog order."""
    return list(MENU_ITEMS)


def get_menu_item_by_id(item_id: str) -> MenuItem | None:
    """Lookup a menu item by exact ID."""
    return _ITEMS_BY_ID.get(item_id)


def get_menu_by_dietary(dietary: DietaryType) -> list[MenuItem]:
    """Filter menu items by Veg or Non-Veg."""
    return [item for item in MENU_ITEMS if item.dietary == dietary]


def get_featured_items() -> list[MenuItem]:
    """Return curated featured dishes."""
    return [item for item in MENU_ITEMS if item.featured]


def get_todays_specials() -> list[MenuItem]:
    """Return chef's today specials."""
    return [item for item in MENU_ITEMS if item.todays_special]


def search_menu(
    query: str = "",
    dietary: str | None = None,
    category: str | None = None,
) -> list[MenuItem]:
    """Search and filter menu items by text query, dietary label, and category."""
    q = query.strip().lower()
    results: list[MenuItem] = []

    for item in MENU_ITEMS:
        if dietary and dietary != "All" and item.dietary != dietary:
            continue
        if category and category != "All" and item.category != category:
            continue
        if q:
            haystack = " ".join(
                [
                    item.name.lower(),
                    item.category.lower(),
                    item.description.lower(),
                    " ".join(item.ingredients).lower(),
                    " ".join(item.aliases).lower(),
                    item.spice_level.lower(),
                ]
            )
            if q not in haystack:
                continue
        results.append(item)

    return results


def find_menu_item(query: str) -> MenuItem | None:
    """Resolve an item ID, exact name, alias, or close fuzzy match to a MenuItem."""
    if not query:
        return None

    cleaned = query.strip().lower()
    if cleaned in _ITEMS_BY_ID:
        return _ITEMS_BY_ID[cleaned]

    # Exact name or alias match
    for item in MENU_ITEMS:
        if item.name.lower() == cleaned:
            return item
        if any(alias.lower() == cleaned for alias in item.aliases):
            return item

    # Substring match on name or aliases
    for item in MENU_ITEMS:
        if cleaned in item.name.lower() or item.name.lower() in cleaned:
            return item
        if any(cleaned in alias.lower() for alias in item.aliases):
            return item

    # Fuzzy close match on dish names + aliases
    name_map: dict[str, MenuItem] = {}
    for item in MENU_ITEMS:
        name_map[item.name.lower()] = item
        for alias in item.aliases:
            name_map[alias.lower()] = item

    matches = get_close_matches(cleaned, list(name_map.keys()), n=1, cutoff=0.72)
    if matches:
        return name_map[matches[0]]

    return None


def format_menu_for_llm(items: list[MenuItem] | None = None) -> str:
    """Format menu items cleanly as authoritative ground-truth text for Gemini."""
    target = items if items is not None else MENU_ITEMS
    lines: list[str] = []
    for item in target:
        custom_str = ", ".join(item.customizations) if item.customizations else "None"
        ingredients_str = ", ".join(item.ingredients)
        spice_note = (
            f"Default Spice: {item.spice_level} (Adjustable: Mild/Medium/Spicy)"
            if item.customizable_spice
            else f"Style/Spice: {item.spice_level} (Fixed)"
        )
        lines.append(
            f"- ID: `{item.id}` | Name: {item.name} | Dietary: {item.dietary} | "
            f"Category: {item.category} | Price: ₹{item.price_inr} | {spice_note} | "
            f"Ingredients: {ingredients_str} | Allowed Customizations: {custom_str} | "
            f"Description: {item.description}"
        )
    return "\n".join(lines)
