import os
import urllib.request
import urllib.error
from pathlib import Path

_WORD_LIST_URL = "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt"
_CACHE_DIR = Path(__file__).parent / ".cache"
_CACHE_FILE = _CACHE_DIR / "words_alpha.txt"

_known_words: set = None
_len_index: dict = None


_FALLBACK_WORDS = {
    "a", "aa", "aaa", "aaron", "ab", "aba", "aback", "abandon", "abandoned",
    "abbreviation", "abc", "abdicate", "abdomen", "abide", "ability", "able",
    "abnormal", "aboat", "abolish", "abominable", "aboriginal", "abort",
    "abortion", "about", "above", "abroad", "absence", "absent", "absolute",
    "absolutely", "absorb", "absorption", "abstract", "absurd", "abuse",
    "academic", "academy", "accent", "accept", "acceptable", "access",
    "accessory", "accident", "accidental", "accommodate", "accommodation",
    "accompany", "accomplish", "accord", "according", "account", "accountant",
    "accumulate", "accuracy", "accurate", "accuse", "accustom", "ache",
    "achieve", "achievement", "acid", "acknowledge", "acoustic", "acquaint",
    "acquaintance", "acquire", "acquisition", "acre", "acrobat", "act",
    "action", "active", "activity", "actor", "actual", "actually", "acute",
    "ad", "adapt", "add", "addict", "addition", "additional", "address",
    "adequate", "adhere", "adjacent", "adjective", "adjust", "administration",
    "admire", "admission", "admit", "adolescent", "adopt", "adult", "advance",
    "advanced", "advantage", "adventure", "advertise", "advertisement", "advice",
    "advise", "advocate", "affair", "affect", "affection", "affiliate",
    "affirm", "afraid", "africa", "african", "after", "afternoon", "afterward",
    "again", "against", "age", "agency", "agenda", "agent", "aggressive",
    "ago", "agree", "agreement", "agriculture", "ahead", "aid", "aim", "air",
    "aircraft", "airline", "airplane", "airport", "alarm", "album", "alcohol",
    "alert", "alien", "alike", "alive", "all", "allegation", "allow",
    "allowance", "ally", "almost", "alone", "along", "already", "also",
    "alter", "alternative", "although", "altogether", "always", "amateur",
    "amazing", "ambassador", "ambition", "ambulance", "america", "american",
    "among", "amount", "ample", "amuse", "analysis", "analyze", "ancestor",
    "ancient", "anger", "angle", "angry", "animal", "ankle", "anniversary",
    "announce", "announcement", "annual", "anonymous", "another", "answer",
    "anticipate", "anxiety", "anxious", "any", "anybody", "anyhow", "anyone",
    "anything", "anyway", "anywhere", "apart", "apartment", "apologize",
    "apology", "apparent", "apparently", "appeal", "appear", "appearance",
    "apple", "application", "apply", "appoint", "appointment", "appreciate",
    "approach", "appropriate", "approval", "approve", "approximate", "arbitrary",
    "arch", "architecture", "area", "argue", "argument", "arise", "arm",
    "armed", "armor", "army", "around", "arrange", "arrangement", "array",
    "arrest", "arrival", "arrive", "arrow", "art", "article", "artist",
    "artistic", "as", "ascend", "ashamed", "aside", "ask", "asleep", "aspect",
    "assault", "assemble", "assertion", "assign", "assignment", "assist",
    "assistance", "assistant", "associate", "association", "assume",
    "assumption", "assurance", "astonish", "astronaut", "astronomy", "at",
    "athlete", "atmosphere", "atom", "attach", "attack", "attempt", "attend",
    "attention", "attitude", "attorney", "attract", "attraction", "attractive",
    "attribute", "audience", "august", "aunt", "author", "authority", "auto",
    "automatic", "automobile", "autumn", "available", "avenue", "average",
    "avoid", "awake", "award", "aware", "away", "awesome", "awful", "awkward",
    "baby", "back", "background", "backward", "bacon", "bad", "badly", "bag",
    "baggage", "bake", "balance", "ball", "balloon", "ban", "banana", "band",
    "bank", "bar", "bare", "barely", "bargain", "base", "baseball",
    "basement", "basic", "basin", "basis", "basket", "basketball", "bat",
    "batch", "bath", "bathroom", "battery", "battle", "bay", "beach", "bean",
    "bear", "beard", "beast", "beat", "beautiful", "beauty", "because", "become",
    "bed", "bedroom", "bee", "beef", "beer", "before", "beg", "begin",
    "beginning", "behavior", "behind", "being", "belief", "believe", "bell",
    "belong", "below", "belt", "bench", "bend", "beneath", "beneficial",
    "benefit", "beside", "besides", "best", "bet", "better", "between", "beyond",
    "bible", "bicycle", "big", "bike", "bill", "billion", "bind", "biology",
    "bird", "birth", "birthday", "bit", "bite", "bitter", "black", "blade",
    "blame", "blanket", "blast", "bleed", "blend", "blind", "block", "blood",
    "blow", "blue", "board", "boat", "body", "boil", "bold", "bomb", "bond",
    "bone", "book", "boom", "boot", "border", "born", "borrow", "boss", "both",
    "bother", "bottle", "bottom", "bounce", "bound", "boundary", "bowl", "box",
    "boy", "brain", "brake", "branch", "brand", "brave", "bread", "break",
    "breakfast", "breast", "breath", "breathe", "brick", "bridge", "brief",
    "bright", "brilliant", "bring", "broad", "broadcast", "brother", "brown",
    "brush", "budget", "build", "building", "bullet", "bundle", "burden",
    "burn", "burst", "bury", "bus", "business", "busy", "but", "and", "butter",
    "button", "buy", "buyer", "cabin", "cabinet", "cable", "cafe", "cage",
    "cake", "calculate", "calendar", "call", "calm", "camera", "camp",
    "campaign", "campus", "can", "canal", "cancel", "cancer", "candidate",
    "candle", "candy", "cap", "capability", "capable", "capacity", "capital",
    "captain", "capture", "car", "carbon", "card", "care", "career", "careful",
    "carelessly", "carry", "cart", "case", "cash", "cast", "castle", "casual",
    "cat", "catalog", "catch", "category", "cattle", "cause", "caution",
    "cautious", "cave", "ceiling", "celebrate", "celebration", "cell", "center",
    "central", "century", "ceremony", "certain", "certainly", "chain", "chair",
    "chairman", "challenge", "chamber", "champion", "championship", "chance",
    "change", "channel", "chapter", "character", "characteristic", "charge",
    "charity", "chart", "chase", "cheap", "cheat", "check", "cheek", "cheese",
    "chef", "chemical", "chemistry", "chest", "chicken", "chief", "child",
    "childhood", "chill", "chin", "china", "chinese", "chip", "chocolate",
    "choice", "choose", "christian", "christmas", "church", "cigarette",
    "circle", "circumstance", "cite", "citizen", "city", "civil", "claim",
    "clash", "class", "classic", "classroom", "clean", "clear", "clearly",
    "clerk", "clever", "click", "client", "climate", "climb", "clinic",
    "clock", "close", "closet", "cloth", "clothes", "clothing", "cloud",
    "club", "cluster", "coach", "coal", "coast", "coat", "code", "coffee",
    "coin", "cold", "collapse", "collar", "colleague", "collect", "collection",
    "college", "colonial", "color", "column", "combat", "combination", "combine",
    "come", "comedy", "comfort", "comfortable", "command", "commander",
    "comment", "commerce", "commercial", "commission", "commit", "commitment",
    "committee", "common", "communicate", "communication", "community", "company",
    "compare", "comparison", "compel", "compete", "competition", "competitive",
    "complain", "complaint", "complete", "completely", "complex", "complicate",
    "component", "compose", "composition", "compound", "comprehend",
    "comprehensive", "computer", "concentrate", "concentration", "concept",
    "concern", "concerned", "concert", "conclude", "conclusion", "concrete",
    "condition", "conduct", "conductor", "conference", "confess", "confidence",
    "confident", "confirm", "conflict", "confront", "confuse", "confusion",
    "congratulate", "congress", "connect", "connection", "conscious",
    "consciousness", "consensus", "consent", "consequence", "consequently",
    "conservation", "conservative", "consider", "considerable", "consideration",
    "consist", "consistent", "constant", "constantly", "constitution",
    "construct", "construction", "consult", "consultant", "consume",
    "consumption", "contact", "contain", "container", "contemporary", "content",
    "contest", "context", "continent", "continue", "contract", "contradiction",
    "contrary", "contrast", "contribute", "contribution", "control",
    "controversial", "controversy", "convenience", "convenient", "convention",
    "conventional", "conversation", "convert", "convince", "cook", "cookie",
    "cooking", "cool", "cooperation", "coordinate", "cope", "copy", "core",
    "corn", "corner", "corporation", "correct", "correction", "correspond",
    "cost", "cotton", "couch", "could", "council", "count", "counter",
    "country", "county", "couple", "courage", "course", "court", "cousin",
    "cover", "cow", "crack", "craft", "crash", "crawl", "crazy", "cream",
    "create", "creation", "creative", "creature", "credit", "crew", "crime",
    "criminal", "crisis", "criteria", "critic", "critical", "criticism",
    "criticize", "crop", "cross", "crowd", "crowded", "crucial", "cruel",
    "cry", "cultural", "culture", "cup", "cure", "curious", "currency",
    "current", "curriculum", "curtain", "curve", "custom", "customer", "cut",
    "cycle", "dad", "daily", "damage", "dance", "danger", "dangerous", "dare",
    "dark", "darkness", "data", "database", "date", "daughter", "day", "dead",
    "deal", "dealer", "dear", "death", "debate", "debt", "decade", "decay",
    "decision", "deck", "declaration", "declare", "decline", "decorate",
    "decrease", "dedicate", "deep", "defeat", "defect", "defense", "defensive",
    "define", "definition", "degree", "delay", "deliver", "delivery",
    "demand", "democracy", "democratic", "demonstrate", "demonstration",
    "denial", "dense", "department", "depend", "dependent", "deposit",
    "depression", "depth", "derive", "describe", "description", "desert",
    "deserve", "design", "designer", "desire", "desk", "desperate",
    "destination", "destroy", "destruction", "detail", "detect", "determine",
    "develop", "development", "device", "devote", "dialogue", "diagram",
    "diamond", "diet", "differ", "difference", "different", "difficult",
    "difficulty", "dig", "digital", "dimension", "dining", "dinner", "direct",
    "direction", "director", "dirty", "disability", "disagree", "disappear",
    "disaster", "discipline", "discourse", "discover", "discovery",
    "discrimination", "discuss", "discussion", "disease", "dish", "dismiss",
    "disorder", "display", "dispute", "distance", "distant", "distinct",
    "distinction", "distinguish", "distribute", "distribution", "district",
    "diverse", "diversion", "divide", "division", "divorce", "doctor",
    "document", "dog", "doll", "dollar", "domain", "domestic", "dominant",
    "dominate", "door", "double", "doubt", "down", "download", "downtown",
    "dozen", "draft", "drag", "dragon", "drain", "drama", "dramatic", "draw",
    "drawing", "dream", "dress", "drink", "drive", "driver", "drop", "drug",
    "drum", "drunk", "dry", "due", "dump", "during", "dust", "duty", "each",
    "eager", "eagle", "ear", "early", "earn", "earnings", "earth", "ease",
    "easily", "east", "eastern", "easy", "eat", "economic", "economics",
    "economist", "economy", "edge", "edition", "editor", "educate", "education",
    "educational", "effect", "effective", "efficiency", "efficient", "effort",
    "egg", "eight", "either", "elderly", "elect", "election", "electric",
    "electrical", "electricity", "electronic", "element", "elementary", "eliminate",
    "elite", "else", "email", "embarrass", "emerge", "emergency", "emission",
    "emotion", "emotional", "emphasis", "emphasize", "empire", "employ",
    "employee", "employer", "employment", "empty", "enable", "encounter",
    "encourage", "end", "enemy", "energy", "enforce", "engage", "engagement",
    "engine", "engineer", "engineering", "english", "enhance", "enjoy",
    "enormous", "enough", "ensure", "enter", "enterprise", "entertainment",
    "entire", "entirely", "entrance", "entry", "envelope", "environment",
    "environmental", "episode", "equal", "equally", "equipment", "era", "error",
    "escape", "essay", "essential", "essentially", "establish", "establishment",
    "estate", "estimate", "etc", "ethics", "ethnic", "evaluate", "evaluation",
    "evening", "event", "eventually", "ever", "every", "everybody", "everyday",
    "everyone", "everything", "everywhere", "evidence", "evolution", "evolve",
    "exact", "exactly", "exam", "examination", "examine", "example", "exceed",
    "excellent", "except", "exception", "exchange", "excite", "excited",
    "excitement", "exciting", "exclude", "exclusive", "excuse", "execute",
    "executive", "exercise", "exhibit", "exhibition", "exist", "existence",
    "exit", "expand", "expansion", "expect", "expectation", "expense",
    "expensive", "experience", "experiment", "experimental", "expert",
    "explain", "explanation", "explode", "exploit", "explore", "export",
    "expose", "express", "expression", "extend", "extension", "extensive",
    "extent", "external", "extra", "extraordinary", "extreme", "eye", "fabric",
    "face", "facility", "fact", "factor", "factory", "faculty", "fail",
    "failure", "fair", "fairly", "faith", "fake", "fall", "false", "fame",
    "familiar", "family", "famous", "fan", "fantastic", "far", "farm",
    "farmer", "fashion", "fast", "fat", "fate", "father", "fault", "favor",
    "favorite", "fear", "feature", "february", "federal", "fee", "feed",
    "feedback", "feel", "feeling", "fellow", "female", "fence", "festival",
    "fetch", "fever", "few", "fiber", "fiction", "field", "fierce", "fifteen",
    "fifth", "fifty", "fight", "fighter", "fighting", "figure", "file",
    "fill", "film", "final", "finally", "finance", "financial", "find",
    "finding", "fine", "finger", "finish", "fire", "firm", "first", "fish",
    "fishing", "fit", "fitness", "five", "fix", "fixed", "flag", "flame",
    "flash", "flat", "flavor", "flee", "fleet", "flesh", "flexibility",
    "flexible", "flight", "float", "flood", "floor", "flow", "flower",
    "fly", "focus", "fold", "folk", "follow", "following", "food", "foot",
    "football", "for", "force", "forecast", "foreign", "forest", "forever",
    "forget", "forgive", "fork", "form", "formal", "format", "formation",
    "former", "formula", "forth", "fortune", "forty", "forward", "fossil",
    "foster", "found", "foundation", "founder", "four", "fourth", "fox",
    "fraction", "frame", "framework", "free", "freedom", "freeze", "frequency",
    "frequent", "frequently", "fresh", "friend", "friendly", "friendship",
    "from", "front", "frontier", "fruit", "frustration", "fuel", "full",
    "fully", "fun", "function", "fund", "fundamental", "funding", "funeral",
    "funny", "furniture", "furthermore", "future", "gain", "gallery", "game",
    "gap", "garage", "garbage", "garden", "gas", "gate", "gather", "gay",
    "gear", "gender", "gene", "general", "generally", "generate", "generation",
    "genetic", "gentleman", "genuine", "gesture", "get", "ghost", "giant", "gift",
    "girl", "give", "glad", "glass", "global", "glory", "goal", "god", "gold",
    "golden", "golf", "good", "goods", "government", "governor", "grab",
    "grade", "gradually", "graduate", "grain", "grand", "grant", "graph",
    "grasp", "grass", "grateful", "grave", "gravity", "gray", "great",
    "greatest", "green", "grey", "grid", "grief", "gross", "ground", "group",
    "grow", "growth", "guarantee", "guard", "guess", "guest", "guidance",
    "guide", "guideline", "guilty", "guitar", "gun", "guy", "habit",
    "habitat", "hair", "half", "hall", "hand", "handle", "handsome", "hang",
    "happen", "happy", "harbor", "hard", "hardly", "hardware", "harm",
    "harmful", "hat", "hate", "have", "has", "had", "is", "are", "was", "were", "head", "headline", "headquarters",
    "health", "healthy", "hear", "hearing", "heart", "heat", "heaven",
    "heavy", "height", "helicopter", "hell", "hello", "help", "helpful",
    "her", "here", "heritage", "hero", "herself", "hide", "high", "highlight",
    "highly", "hill", "him", "himself", "hint", "hip", "hire", "his",
    "historical", "history", "hit", "hold", "hole", "holiday", "hollow",
    "holy", "home", "homeless", "honest", "honey", "honor", "hope",
    "horizon", "horror", "horse", "hospital", "host", "hotel", "hour",
    "house", "household", "housing", "how", "however", "huge", "human",
    "humor", "hundred", "hungry", "hunt", "hunter", "hurry", "hurt",
    "husband", "ice", "idea", "ideal", "identify", "identity", "ignore",
    "ill", "illegal", "illness", "illustrate", "image", "imagination",
    "imagine", "immediate", "immediately", "immigrant", "immigration",
    "impact", "implement", "implementation", "implication", "imply",
    "import", "importance", "important", "impose", "impossible",
    "impression", "improve", "improvement", "incident", "include",
    "including", "income", "increase", "increased", "increasingly",
    "incredible", "indeed", "independence", "independent", "index",
    "indicate", "indication", "individual", "indoor", "industry", "infant",
    "infection", "inflation", "influence", "inform", "information",
    "initial", "initially", "injury", "inner", "innocent", "innovation",
    "input", "inquiry", "inside", "insight", "insist", "inspect",
    "inspection", "inspiration", "install", "instance", "instant",
    "instead", "institution", "institutional", "instruction", "instructor",
    "instrument", "insurance", "intellectual", "intelligence", "intend",
    "intense", "intensity", "intention", "interaction", "interest",
    "interested", "interesting", "internal", "international", "internet",
    "interpret", "intervention", "interview", "introduce", "introduction",
    "invasion", "invest", "investigate", "investment", "investor",
    "invite", "involve", "involved", "iron", "island", "issue", "item",
    "its", "itself", "jacket", "jail", "january", "japan", "japanese",
    "job", "join", "joint", "joke", "journal", "journalist", "journey",
    "joy", "judge", "judgment", "juice", "jump", "junior", "jury", "just",
    "justice", "justify", "keep", "key", "keyboard", "kick", "kid", "kill",
    "kind", "kingdom", "kiss", "kitchen", "knee", "knife", "knock", "know",
    "knowledge", "lab", "label", "labor", "lack", "lady", "lake", "land",
    "landscape", "language", "lap", "large", "largely", "laser", "last",
    "late", "lately", "later", "latin", "latter", "laugh", "launch",
    "law", "lawyer", "layer", "lead", "leader", "leadership", "leading",
    "leaf", "league", "learn", "learning", "least", "leather", "leave",
    "lecture", "left", "leg", "legal", "legend", "legislation", "leisure",
    "lend", "length", "less", "lesson", "let", "letter", "level", "liberal",
    "library", "license", "lid", "life", "lifetime", "lift", "light",
    "like", "likely", "limit", "limitation", "limited", "line", "link",
    "lion", "lip", "liquid", "list", "listen", "literature", "little",
    "live", "living", "load", "loan", "local", "locate", "location",
    "lock", "long", "look", "loose", "lord", "lose", "loss", "lost",
    "lot", "loud", "love", "lovely", "lover", "low", "lower", "luck",
    "lucky", "lunch", "machine", "mad", "magazine", "magic", "main",
    "mainly", "maintain", "maintenance", "major", "majority", "make",
    "male", "mall", "man", "manage", "management", "manager", "manner",
    "manufacturing", "many", "map", "margin", "mark", "market",
    "marketing", "marriage", "married", "marry", "massive", "master",
    "match", "mate", "material", "math", "matter", "maximum", "maybe",
    "mayor", "meal", "mean", "meaning", "meanwhile", "measure",
    "measurement", "meat", "mechanism", "media", "medical", "medicine",
    "medium", "meet", "meeting", "member", "membership", "memory",
    "mental", "mention", "menu", "mere", "merely", "merger", "merit",
    "mess", "message", "metal", "meter", "method", "middle", "midnight",
    "may", "might", "mile", "military", "milk", "mill", "million", "mind",
    "mine", "minimum", "minister", "ministry", "minor", "minute", "miracle",
    "mirror", "miss", "missile", "mission", "mistake", "mix", "mixture",
    "mobile", "mode", "model", "modern", "modest", "modify", "mom",
    "moment", "momentum", "money", "monitor", "month", "mood", "moon",
    "moral", "moreover", "morning", "mortgage", "most", "mostly", "mother",
    "motion", "motivate", "motivation", "motor", "mountain", "mouse",
    "mouth", "move", "movement", "movie", "much", "multiple", "murder",
    "muscle", "museum", "music", "musical", "musician", "must", "mutual",
    "myself", "mystery", "myth", "nail", "naked", "name", "narrow",
    "nation", "national", "native", "natural", "nature", "near", "nearby",
    "nearly", "necessarily", "necessary", "neck", "need", "negative",
    "negotiate", "negotiation", "neighbor", "neighborhood", "neither",
    "nerve", "nervous", "net", "network", "neutral", "never", "nevertheless",
    "new", "newly", "news", "newspaper", "next", "nice", "night", "nine",
    "no", "nobody", "nod", "noise", "nomination", "none", "nonetheless",
    "nor", "normal", "normally", "north", "northern", "nose", "not",
    "note", "nothing", "notice", "notification", "notion", "novel",
    "nowhere", "nuclear", "number", "numerous", "nurse", "nut", "object",
    "objective", "obligation", "observation", "observe", "observer",
    "obstacle", "obtain", "obvious", "occasionally", "occupation", "occur",
    "ocean", "october", "odd", "odds", "off", "offer", "office", "officer",
    "official", "often", "oil", "okay", "old", "olympic", "once", "one",
    "ongoing", "online", "only", "onto", "open", "opening", "openly",
    "operate", "operation", "operational", "operator", "opinion", "opponent",
    "opportunity", "oppose", "opposite", "opposition", "option", "oral",
    "orange", "order", "ordinary", "organic", "organization", "organize",
    "orientation", "origin", "original", "otherwise", "ought", "our",
    "ourselves", "out", "outcome", "outdoor", "outer", "output", "outside",
    "outstanding", "overall", "overcome", "overlook", "overnight", "overseas",
    "overtake", "owner", "ownership", "pace", "pack", "package", "page",
    "pain", "painful", "paint", "painter", "painting", "pair", "palace",
    "pale", "palm", "pan", "panel", "panic", "paper", "paragraph", "parallel",
    "parameter", "parent", "park", "parking", "part", "participant",
    "participate", "participation", "particular", "particularly", "partly",
    "partner", "partnership", "party", "pass", "passage", "passenger",
    "passion", "past", "patch", "path", "patient", "pattern", "pause", "pay",
    "payment", "peace", "peaceful", "peak", "peer", "pen", "penalty",
    "pencil", "pension", "people", "per", "perceive", "percent",
    "percentage", "perception", "perfect", "perfectly", "performance",
    "perhaps", "period", "permanent", "permission", "permit", "person",
    "personal", "personality", "personally", "personnel", "perspective",
    "persuade", "phase", "phenomenon", "philosophy", "phone", "photo",
    "photograph", "photographer", "phrase", "physical", "physician", "piano",
    "pick", "picture", "piece", "pile", "pilot", "pine", "pink", "pioneer",
    "pipe", "pitch", "pizza", "place", "plain", "plan", "plane", "planet",
    "planning", "plant", "plastic", "plate", "platform", "play", "player",
    "please", "pleasure", "pledge", "plot", "plus", "pocket", "poem", "poet",
    "poetry", "point", "pole", "police", "policy", "political", "politically",
    "politician", "politics", "poll", "pollution", "pool", "poor", "pop",
    "popular", "population", "port", "portrait", "pose", "position",
    "positive", "possess", "possession", "possibility", "possible",
    "possibly", "post", "potentially", "potato", "potential", "pound",
    "pour", "poverty", "power", "powerful", "practical", "practice",
    "pray", "prayer", "precisely", "predict", "prediction", "prefer",
    "preference", "pregnancy", "pregnant", "preliminary", "premier",
    "premise", "premium", "prepare", "prepared", "prescription", "presence",
    "present", "presentation", "preserve", "president", "press", "pressure",
    "pretend", "pretty", "prevent", "previous", "price", "pride", "primary",
    "prime", "principal", "principle", "print", "prior", "priority",
    "prison", "private", "privilege", "prize", "probably", "problem",
    "procedure", "proceed", "process", "produce", "producer", "product",
    "production", "profession", "professional", "professor", "profile",
    "profit", "program", "progress", "project", "prominent", "promise",
    "promote", "prompt", "proof", "proper", "properly", "property",
    "proportion", "proposal", "propose", "proposed", "proposition",
    "prosecute", "prospect", "protect", "protection", "protein", "protest",
    "proud", "provide", "provider", "province", "provision", "psychological",
    "psychologist", "public", "publication", "publicity", "publish", "pull",
    "pump", "punch", "punish", "punishment", "purchase", "pure", "purpose",
    "pursue", "push", "put", "qualify", "quality", "quarter", "queen",
    "question", "quick", "quickly", "quiet", "quietly", "quit", "quite",
    "quote", "race", "racial", "radical", "radio", "rage", "rail", "rain",
    "raise", "range", "rank", "rapid", "rapidly", "rare", "rarely", "rate",
    "rather", "ratio", "raw", "reach", "react", "reaction", "reader",
    "reading", "ready", "real", "realistic", "reality", "realize", "really",
    "reason", "reasonable", "recall", "receive", "recent", "recently",
    "reception", "recipe", "recipient", "recognition", "recognize",
    "recommend", "recommendation", "record", "recover", "recovery",
    "recruitment", "red", "reduce", "reduction", "refer", "reference",
    "reflect", "reflection", "reform", "refugee", "refuse", "regard",
    "regarding", "regardless", "region", "regional", "register", "regular",
    "regularly", "regulate", "regulation", "reinforce", "reject", "relate",
    "relation", "relationship", "relative", "relatively", "relax",
    "release", "relevant", "reliable", "relief", "religion", "religious",
    "rely", "remain", "remaining", "remarkable", "remember", "remind",
    "remote", "remove", "repeat", "repeatedly", "replace", "reply",
    "report", "reporter", "represent", "representation", "representative",
    "republic", "reputation", "request", "require", "requirement", "research",
    "researcher", "resemble", "reservation", "reserve", "resident",
    "residential", "resign", "resist", "resistance", "resolution", "resolve",
    "resort", "resource", "respect", "respond", "response", "responsibility",
    "responsible", "rest", "restaurant", "restore", "restriction", "result",
    "retain", "retire", "retirement", "return", "reveal", "revenue",
    "reverse", "review", "revision", "revolution", "reward", "rhythm",
    "rice", "rich", "ride", "ridge", "ridiculous", "right", "ring", "riot",
    "rise", "risk", "river", "road", "rob", "robot", "rock", "role",
    "roll", "romantic", "roof", "room", "root", "rope", "rose", "rough",
    "roughly", "round", "route", "routine", "row", "royal", "rub", "rude",
    "ruin", "rule", "run", "running", "rural", "rush", "sacrifice", "sad",
    "safe", "safety", "sail", "salad", "salary", "sale", "sales", "salt",
    "same", "sample", "sanction", "sand", "satellite", "satisfaction",
    "satisfy", "saturday", "save", "scale", "scandal", "scared", "scenario",
    "scene", "schedule", "scheme", "scholar", "scholarship", "school",
    "science", "scientific", "scientist", "scope", "score", "scratch",
    "screen", "script", "sea", "search", "season", "seat", "second",
    "secondary", "secret", "secretary", "section", "sector", "secure",
    "security", "see", "seed", "seek", "seem", "segment", "seize",
    "select", "selection", "self", "sell", "senator", "send", "senior",
    "sense", "sensitive", "sentence", "separate", "sequence", "series",
    "serious", "seriously", "servant", "serve", "service", "session", "set",
    "setting", "settle", "settlement", "seven", "several", "severe", "sex",
    "sexual", "shade", "shadow", "shake", "shall", "shame", "shape",
    "share", "sharp", "she", "shed", "sheet", "shelf", "shell", "shift",
    "shine", "ship", "shirt", "shock", "shoe", "shoot", "shop", "shopping",
    "shore", "short", "shortly", "shot", "should", "shoulder", "shout",
    "show", "shower", "shut", "side", "sight", "sign", "signal",
    "signature", "significance", "significant", "silence", "silent", "silver",
    "similar", "similarly", "simple", "simply", "since", "sing", "singer",
    "single", "sink", "sister", "site", "situation", "six", "size", "skill",
    "skin", "sky", "slave", "sleep", "slice", "slide", "slight", "slightly",
    "slim", "slip", "slope", "small", "smart", "smell", "smile", "smoke",
    "smooth", "snap", "snow", "so", "or", "if", "soccer", "social", "society", "sock",
    "soft", "software", "soil", "solar", "soldier", "solid", "solution",
    "solve", "some", "somebody", "somehow", "someone", "something",
    "sometimes", "somewhat", "somewhere", "son", "song", "soon", "sorry",
    "sort", "soul", "sound", "soup", "source", "south", "southern", "space",
    "speak", "speaker", "special", "specialist", "species", "specific",
    "specifically", "specify", "specimen", "spectacular", "speech", "speed",
    "spell", "spelling", "spend", "spin", "spirit", "spiritual", "split",
    "spokesperson", "sport", "spot", "spread", "spring", "square", "stable",
    "staff", "stage", "stair", "stake", "stand", "standard", "star", "stare",
    "start", "state", "statement", "station", "statistical", "statistics",
    "status", "stay", "steady", "steak", "steal", "steam", "steel", "step",
    "stick", "still", "stock", "stomach", "stone", "stop", "storage",
    "store", "storm", "story", "straight", "strange", "stranger",
    "strategic", "strategy", "stream", "street", "strength", "stress",
    "stretch", "strict", "strike", "string", "strip", "stroke", "strong",
    "strongly", "structure", "struggle", "student", "studio", "study",
    "stuff", "stupid", "style", "subject", "submit", "subsequent",
    "substance", "substantial", "succeed", "success", "successful",
    "successfully", "such", "sudden", "suddenly", "suffer", "sufficient",
    "suggest", "suggestion", "suit", "suitable", "sum", "summary", "summer",
    "summit", "sun", "super", "supply", "support", "suppose", "supposed",
    "supreme", "sure", "surely", "surface", "surgery", "surprise",
    "surprised", "surprising", "surround", "survey", "survival", "survive",
    "suspect", "suspend", "sustain", "sweep", "sweet", "swim", "swing",
    "switch", "symbol", "symptom", "system", "table", "tackle", "tactic",
    "tail", "take", "talent", "talk", "tall", "tank", "tap", "tape",
    "target", "task", "taste", "tax", "taxi", "tea", "teach", "teacher",
    "team", "tear", "technical", "technique", "technology", "teenager",
    "telephone", "television", "tell", "temperature", "temple", "temporary",
    "ten", "tend", "tendency", "tender", "tennis", "tense", "tension",
    "tent", "term", "terminal", "terrible", "territory", "terror", "test",
    "testimony", "text", "than", "thank", "that", "theater", "theft",
    "their", "them", "theme", "themselves", "then", "theory", "therapy",
    "there", "thereby", "therefore", "these", "they", "thick", "thin",
    "thing", "think", "third", "thirsty", "thirteen", "thirty", "this",
    "thorough", "those", "though", "thought", "thousand", "thread",
    "threat", "three", "throat", "through", "throughout", "throw",
    "thus", "ticket", "tide", "tight", "time", "tiny", "tip", "tire",
    "tired", "tissue", "title", "the", "to", "today", "toe", "together", "tomato",
    "tomorrow", "tone", "tonight", "too", "tool", "tooth", "top", "topic",
    "toss", "total", "totally", "touch", "tough", "tour", "tourism",
    "tourist", "tournament", "toward", "towards", "tower", "town", "toy",
    "trace", "track", "trade", "tradition", "traditional", "traffic",
    "tragedy", "trail", "train", "trainer", "training", "transfer",
    "transform", "transformation", "transition", "translate", "translation",
    "transparent", "transport", "transportation", "travel", "treasure",
    "treat", "treatment", "treaty", "tree", "tremendous", "trend", "trial",
    "tribe", "trick", "trigger", "trim", "trip", "troop", "tropical",
    "trouble", "truck", "true", "truly", "trust", "truth", "try", "tube",
    "tune", "turn", "twelve", "twenty", "twice", "twin", "twist", "type",
    "typical", "ugly", "ultimate", "ultimately", "unable", "uncertain",
    "unclear", "under", "undergo", "understand", "understanding", "undertake",
    "unemployment", "unexpected", "unfair", "unfortunately", "uniform",
    "union", "unique", "unit", "united", "universal", "universe",
    "university", "unknown", "unless", "unlike", "unlikely", "until",
    "unusual", "up", "update", "upon", "upper", "urban", "urge", "urgent",
    "us", "use", "used", "useful", "user", "usual", "usually", "utility",
    "vacation", "valley", "valuable", "value", "variable", "variation",
    "variety", "various", "vary", "vast", "vegetable", "vehicle", "venture",
    "version", "versus", "very", "vessel", "victim", "victory", "video",
    "view", "village", "violate", "violence", "virtual", "virtue", "virus",
    "visible", "vision", "visit", "visitor", "visual", "vital", "voice",
    "volume", "volunteer", "vote", "vote", "wage", "wait", "wake", "walk",
    "wall", "wander", "want", "war", "warm", "warn", "warning", "wash",
    "waste", "watch", "water", "wave", "way", "weak", "wealth", "weapon",
    "wear", "weather", "website", "wedding", "wednesday", "week", "weekend",
    "weekly", "weigh", "weight", "weird", "welcome", "welfare", "well",
    "west", "western", "wet", "what", "whatever", "wheel", "when", "whenever",
    "where", "wherever", "whether", "which", "while", "whisper", "white",
    "who", "whoever", "whole", "whom", "whose", "why", "wide", "widely",
    "wife", "wild", "will", "willing", "win", "wind", "window", "wine",
    "wing", "winner", "winter", "wire", "wisdom", "wise", "wish", "with",
    "withdraw", "within", "without", "witness", "woman", "wonder", "wood",
    "wooden", "wool", "word", "work", "worker", "working", "works",
    "workshop", "world", "worried", "worry", "worth", "would", "wound",
    "wrap", "write", "writer", "writing", "wrong", "yard", "yeah", "year",
    "yellow", "yes", "yesterday", "yet", "yield", "you", "young", "your",
    "yours", "yourself", "youth", "zone",
}


def _ensure_word_list():
    global _known_words, _len_index
    if _known_words is not None:
        return

    _CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if _CACHE_FILE.exists():
        try:
            with open(_CACHE_FILE, "r", encoding="utf-8") as f:
                _known_words = {line.strip().lower() for line in f if line.strip()}
            _build_index()
            return
        except Exception:
            pass

    _known_words = set(_FALLBACK_WORDS)
    _build_index()

    import threading
    threading.Thread(target=_try_download_and_reload, daemon=True).start()


def _try_download_and_reload():
    try:
        import socket
        socket.setdefaulttimeout(5)
        req = urllib.request.Request(
            _WORD_LIST_URL, headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = response.read()
        with open(_CACHE_FILE, "wb") as f:
            f.write(data)
        global _known_words, _len_index
        with open(_CACHE_FILE, "r", encoding="utf-8") as f:
            _known_words = {line.strip().lower() for line in f if line.strip()}
        _build_index()
    except Exception:
        pass


def _build_index():
    global _len_index
    _len_index = {}
    for w in _known_words:
        _len_index.setdefault(len(w), []).append(w)


def unknown(words):
    _ensure_word_list()
    return {w for w in words if w.lower() not in _known_words}


def correction(word):
    _ensure_word_list()
    word_lower = word.lower()
    if word_lower in _known_words:
        return None
    result = _closest_word(word_lower)
    if result == word_lower:
        return None
    return result


def _closest_word(word, max_distance=2):
    if len(word) < 3:
        return word

    candidates = []
    for delta in range(-max_distance, max_distance + 1):
        target_len = len(word) + delta
        if target_len >= 3 and target_len in _len_index:
            candidates.extend(_len_index[target_len])

    best = None
    best_dist = max_distance + 1
    for known in candidates:
        dist = _levenshtein(word, known)
        if dist < best_dist:
            best_dist = dist
            best = known
            if dist == 1:
                break
    return best if best is not None else word


def _levenshtein(a, b):
    if len(a) < len(b):
        a, b = b, a
    if len(b) == 0:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            curr.append(min(
                prev[j + 1] + 1,
                curr[j] + 1,
                prev[j] + (0 if ca == cb else 1),
            ))
        prev = curr
    return prev[-1]