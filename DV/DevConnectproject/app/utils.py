import random
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# ⚠️ الكلمات التي يتم تجاهلها
STOP_WORDS = {
    "developer", "engineer", "specialist", "expert", "consultant", "architect", 
    "coder", "programmer", "technologist", "professional", "dev", "technician",
    "senior", "junior", "lead", "staff", "principal", "entry", "mid", "associate", 
    "software", "development", "programming", "master", "mastering", "ninja", 
    "rockstar", "guru", "enthusiast", "freelancer", "instructor", "certified",
}

# ⚠️ المجالات الكبرى - وزن 5
CORE_FIELDS = {
    "frontend", "backend", "mobile", "ui", "ux", "ml", "ai",
    "devops", "data", "cloud", "security", "testing",
    "gamedev", "blockchain", "embedded", "pm"
}

# ⚠️ المفاهيم العامة - وزن 1
RELATED_FIELDS = {
    "api", "rest", "graphql", "microservices", "mvc", "orm", "web",
    "nlp", "vision", "prediction", "analytics", "dataset", "neural",
    "prototype", "wireframe", "branding", "usability", "designsystem",
    "pwa", "native", "hybrid", "crossplatform", "sdk",
    "pipeline", "automation", "container", "serverless", "infrastructure", "cicd",
    "encryption", "vulnerability", "automationtesting", "e2e",
    "agile", "scrum", "roadmap", "stakeholder", "fullstack"
}

# ⚠️ الأدوات واللغات والـ Stacks - وزن 2
ALIASES = {
    "frontend": {
        "react", "vue", "angular", "svelte", "next", "nuxt", "solidjs", "qwik",
        "html", "css", "javascript", "typescript", "js", "ts", "jsx", "tsx",
        "tailwind", "bootstrap", "sass", "less", "webpack", "vite", "babel", "npm",
        "mern", "mean", "mevn", "jamstack", "reactjs", "nextjs", "vuejs", # Stacks & JS versions
    },
    "backend": {
        "django", "flask", "fastapi", "node", "nodejs", "express", "nestjs",
        "laravel", "php", "symfony", "codeigniter", "spring", "springboot", "java",
        "asp", "dotnet", "csharp", "c#", "rails", "ruby", "golang", "go", "rust",
        "python", "elixir", "phoenix", "mern", "mean", "mevn", "lamp", "lemp",# Stacks & Servers
    },
    "mobile": {
        "flutter", "dart", "reactnative", "ios", "android",
        "swift", "swiftui", "uikit", "kotlin", "java", "jetpack", "expo"
    },
    "ui": {
        "figma", "adobe", "xd", "photoshop", "illustrator", "sketch", "framer", 
        "ux", "userexperience", "userinterface", "uiux"
    },
    "ux": {
        "figma", "adobe", "xd", "photoshop", "illustrator", "sketch", "framer", 
        "ux", "userexperience", "userinterface", "uiux",
    },
    "ml": {
        "pytorch", "tensorflow", "keras", "scikit-learn", "sklearn", "numpy", "pandas",
        "opencv", "langchain", "openai", "huggingface", "llm", "machinelearning"
    },
    "devops": {
        "docker", "kubernetes", "k8s", "aws", "azure", "gcp", "linux", "terraform",
        "ansible", "jenkins", "githubactions", "nginx", "apache"
    },
    "data": {
        "sql", "mysql", "postgresql", "postgres", "mongodb", "redis", "oracle",
        "mssql", "cassandra", "elasticsearch", "firebase", "supabase", "spark"
    },
    "security": {
        "cybersecurity", "infosec", "pentesting", "hacking", "firewall", "jwt", "oauth"
    },
    "testing": {
        "jest", "cypress", "selenium", "mocha", "playwright", "tdd", "bdd"
    },
    "gamedev": {
        "unity", "unreal", "c++", "cpp", "cplusplus", "godot", "shader", "opengl"
    },
    "blockchain": {
        "solidity", "web3", "ethereum", "smartcontract", "nft", "metamask", "truffle"
    },
    "embedded": {
        "arduino", "raspberry", "iot", "firmware", "esp32", "rtos", "microcontroller"
    }
}


# تجميع كل كلمات الـ Aliases في مجموعة واحدة لسهولة البحث عن الوزن
ALL_TOOL_KEYWORDS = set()
for tools in ALIASES.values():
    ALL_TOOL_KEYWORDS.update(tools)


ORIGINAL_WORD_BONUS = 3


# --- الدوال المساعدة ---
def normalize_specialization(text):
    if not text:
        return set()

    text = text.lower()
    
    # 1. صنع نسخة مدمجة (إزالة الوصلات والشرطات تماماً)
    # "Full-Stack" -> "fullstack" | "Node.js" -> "nodejs"
    text_compact = text.replace("-", "").replace("_", "").replace(".", "")
    
    # 2. صنع نسخة مفككة (استبدال الرموز بمسافات)
    # "Full-Stack" -> "full stack"
    text_spaced = text
    for ch in "-_./&()+,":
        text_spaced = text_spaced.replace(ch, " ")

    # 3. دمج النتائج في مجموعة واحدة
    # إذا كتب المستخدم "React-Native" سيحصل النظام على: {"react", "native", "reactnative"}
    words = set(text_spaced.split()) | set(text_compact.split())

    return words - STOP_WORDS


def expand_words(words):
    expanded = set(words)
    for key, values in ALIASES.items():
        if key in words or (words & values):
            expanded |= values
            expanded.add(key)
    return expanded



def similarity_score(words1_expanded, words2_expanded, words1_normalized, words2_normalized):
    intersection_expanded = words1_expanded & words2_expanded
    score = 0
    
    for w in intersection_expanded:
        if w in CORE_FIELDS:
            score += 5  # التخصص الرئيسي
        elif w in ALL_TOOL_KEYWORDS:
            score += 2  # الأدوات واللغات (طلبك: الـ Aliases قيمتها 2)
        elif w in RELATED_FIELDS:
            score += 1  # المفاهيم العامة (طلبك: الـ Related قيمتها 1)
        else:
            score += 1  # أي كلمة أخرى غير مصنفة
            
    # مكافأة التطابق المباشر في الكلمات التي كتبها المستخدم فعلياً
    original_intersection = words1_normalized & words2_normalized
    score += len(original_intersection) * ORIGINAL_WORD_BONUS

    # كسر ثبات الترتيب لضمان التجديد في كل استدعاء
    return score + (random.random() * 0.01)

#  شرح الكود:
# هلاً بكِ في جولة المراجعة النهائية! بما أننا وصلنا إلى الكود "الخارق" والشامل، دعيني أرسم لكِ الصورة الكاملة لكيفية عمله عند كل استدعاء (Refresh):
# 1. العدد الإجمالي المقترح

# النظام مبرمج ليقترح 8 مستخدمين فقط كحد أقصى في كل مرة.
# 2. توزيع الأصناف (الأولوية)

# النظام لا يستخدم "حصصاً ثابتة" (مثل 2 قوي و 3 متوسط)، بل يستخدم مبدأ "الأفضلية للأعلى درجة". إليكِ كيف يملأ الـ 8 مقاعد:

#     المقاعد من 1 إلى 8 (الأولوية للـ Scored): يبحث النظام في كل الأشخاص الذين لديهم "علاقة" بتخصصك (الذين حصلوا على درجة ≥1).

#         إذا وجد 8 أشخاص أو أكثر في مجالك، ستكون القائمة بالكامل Strong & Medium.

#         إذا وجد 5 أشخاص فقط في مجالك، سيضعهم في البداية، ثم ينتقل للبحث عن "تكملة".

#     تكملة العدد (الـ Fallback): إذا لم يكتمل العدد 8 من الأشخاص ذوي الصلة، يذهب النظام إلى قائمة الأشخاص الذين تخصصهم بعيد تماماً (Zero-Score) ويختار منهم عشوائياً ليكمل العدد إلى 8.

# 3. كيف يتغير الترتيب في كل استدعاء؟

# هنا يكمن ذكاء الكود؛ الترتيب يتغير بطريقتين مختلفتين حسب "قوة" الشخص:
# أولاً: الترتيب بين أصحاب التخصص (الـ Tie-Breaker)

# استخدمنا معادلة الدرجة التالية:
# FinalScore=WeightedScore+(Random×0.01)

#     النتيجة: لو كنتِ "React Developer"، وظهر لكِ شخصان "Vue" و "Angular" وكلاهما درجته (8 نقاط).

#         في المرة الأولى: Vue (8.009) يسبق Angular (8.002).

#         في المرة الثانية: Angular (8.007) يسبق Vue (8.001).

#     الهدف: التبديل بين الأشخاص المتساويين في الكفاءة لكي لا يمل المستخدم من رؤية نفس الوجه في المركز الأول دائماً، لكن مع ضمان أن الشخص الذي درجته (11) سيبقى دائماً فوق الشخص الذي درجته (8).

# ثانياً: الترتيب في الـ Fallback (الخلط الكامل)

#     الآلية: بالنسبة للأشخاص الذين لا علاقة لهم بتخصصك (أصحاب الدرجة صفر)، يتم استخدام random.shuffle().

#     النتيجة: في كل مرة يظهر فيها "شخص غريب" لتكملة العدد، سيكون شخصاً مختلفاً تماماً عن المرة السابقة وبترتيب عشوائي بحت.
